import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel, Field

from app import telemetry


DB_PATH = Path(os.getenv("ORDER_DB_PATH", "data/orders.db"))
STATUSES = {"received", "preparing", "shipped", "delivered"}

# Initialise the tracer/meter/logger providers before the app is created so
# the FastAPI instrumentation below wires into them.
telemetry.setup_telemetry()
log = telemetry.get_logger()


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with connect() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                item TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        if db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            now = datetime.now(timezone.utc)
            previous_month_end = now.replace(day=1) - timedelta(days=1)
            for order in (
                ("standard-1001", "Avery", "Notebook", "standard", "received", now),
                ("express-1002", "Sam", "Headphones", "express", "preparing", previous_month_end),
                ("standard-1003", "Riley", "Water bottle", "standard", "shipped", now),
            ):
                db.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
                    (*order[:5], order[5].isoformat()),
                )


def as_dict(row):
    return dict(row) if row else None


def order_detail(row):
    order = as_dict(row)
    if order["priority"] == "express":
        placed_at = datetime.fromisoformat(order["created_at"])
        # Add days with timedelta so the estimate rolls over month/year
        # boundaries. Do NOT use `placed_at.replace(day=placed_at.day + 2)`:
        # it raises ValueError ("day is out of range for month") for orders
        # placed near month end (e.g. day 30 -> day 32), which 500s the
        # express order lookup (see incident: express-1002 5xx).
        estimated_at = placed_at + timedelta(days=2)
        order["estimated_delivery"] = estimated_at.date().isoformat()
    return order


class NewOrder(BaseModel):
    customer: str = Field(min_length=1, max_length=80)
    item: str = Field(min_length=1, max_length=120)
    priority: str = "standard"


class StatusUpdate(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Order Tracker", lifespan=lifespan)

# Auto-generate a trace span for every request (route + status + timing).
FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def record_request_metric(request: Request, call_next):
    """Record the request-count metric and a log line for every request.

    Unhandled exceptions (e.g. the express 500) propagate past the routing
    layer as exceptions rather than responses, so we catch them here to make
    sure the 5xx is still counted before re-raising.
    """
    method = request.method
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        route = request.scope.get("route")
        route_path = getattr(route, "path", request.url.path)
        telemetry.record_request(route_path, method, 500)
        log.error(
            "request failed route=%s method=%s status=500",
            route_path,
            method,
        )
        raise

    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)
    telemetry.record_request(route_path, method, status_code)
    log.info(
        "request route=%s method=%s status=%s",
        route_path,
        method,
        status_code,
    )
    return response


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")


@app.get("/healthz")
def health():
    with connect() as db:
        db.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/orders")
def list_orders():
    with connect() as db:
        rows = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    return [as_dict(row) for row in rows]


@app.get("/api/orders/{order_id}")
def get_order(order_id: str):
    log.info("order lookup requested order_id=%s", order_id)
    with connect() as db:
        row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        log.warning("order lookup miss order_id=%s", order_id)
        raise HTTPException(404, "Order not found")
    detail = order_detail(row)
    log.info("order lookup hit order_id=%s priority=%s", order_id, detail["priority"])
    return detail


@app.post("/api/orders", status_code=201)
def create_order(order: NewOrder):
    if order.priority not in {"standard", "express"}:
        raise HTTPException(422, "Priority must be standard or express")
    order_id = str(uuid4())
    with connect() as db:
        db.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, order.customer, order.item, order.priority, "received",
             datetime.now(timezone.utc).isoformat()),
        )
    return get_order(order_id)


@app.patch("/api/orders/{order_id}")
def update_status(order_id: str, update: StatusUpdate):
    if update.status not in STATUSES:
        raise HTTPException(422, "Invalid status")
    with connect() as db:
        cursor = db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (update.status, order_id),
        )
    if cursor.rowcount == 0:
        raise HTTPException(404, "Order not found")
    return get_order(order_id)
