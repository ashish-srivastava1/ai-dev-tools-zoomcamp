"""OpenTelemetry: traces, metrics and structured JSON logs that share a trace_id.

Mode is chosen with ``TELEMETRY_EXPORTER``:

* ``none``    - no OTel providers (unit tests). JSON logs still go to stdout.
* ``console`` - print spans/metrics/logs to stdout (debugging).
* ``otlp``    - ship everything over OTLP/gRPC to ``OTEL_EXPORTER_OTLP_ENDPOINT``
                (the collector in docker compose, or Grafana Cloud in deploys).
* ``memory``  - in-memory exporters, used by the "no PII in telemetry" test.

Privacy rule (spec section 6): session topics, notes, the write token and the DB
URL never go to telemetry. Only ids, counts, durations, routes and status codes
are recorded. Request bodies and headers are never captured.
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from opentelemetry import trace
from sqlalchemy.engine import Engine

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "learnloop")
LOGGER_NAME = "learnloop"
logger = logging.getLogger(LOGGER_NAME)

# Fields of a LogRecord that are not user "extra" attributes.
_STD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """One JSON object per line, with trace_id / span_id of the active span."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "env": os.getenv("APP_ENV", "local"),
        }
        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            payload["trace_id"] = format(ctx.trace_id, "032x")
            payload["span_id"] = format(ctx.span_id, "016x")
        for key, value in vars(record).items():
            if key not in _STD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


@dataclass
class Telemetry:
    mode: str = "none"
    tracer_provider: object | None = None
    meter_provider: object | None = None
    logger_provider: object | None = None
    span_exporter: object | None = None
    log_exporter: object | None = None
    metric_reader: object | None = None
    _instruments: dict = field(default_factory=dict)

    # ---- custom metrics ------------------------------------------------
    def record_request(self, route: str, method: str, status: int, seconds: float) -> None:
        if not self._instruments:
            return
        attrs = {"http_route": route, "http_method": method, "http_status_code": status}
        self._instruments["requests"].add(1, attrs)
        self._instruments["duration"].record(seconds, attrs)

    def session_logged(self) -> None:
        if self._instruments:
            self._instruments["sessions_logged"].add(1)

    def shutdown(self) -> None:
        for p in (self.tracer_provider, self.meter_provider, self.logger_provider):
            if p is not None:
                try:
                    p.shutdown()
                except Exception:  # noqa: BLE001
                    pass


def _configure_stdout_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(getattr(h, "_learnloop_json", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._learnloop_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)


def setup_telemetry(app: FastAPI, engine: Engine, mode: str | None = None) -> Telemetry:
    mode = (mode or os.getenv("TELEMETRY_EXPORTER", "none")).lower()
    _configure_stdout_logging()
    tel = Telemetry(mode=mode)
    app.state.telemetry = tel
    _add_request_middleware(app, tel)
    if mode == "none":
        return tel

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, SimpleLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "service.version": os.getenv("APP_VERSION", "dev"),
            "deployment.environment": os.getenv("APP_ENV", "local"),
        }
    )
    interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "5000"))

    if mode == "memory":
        try:
            from opentelemetry.sdk._logs.export import (
                InMemoryLogRecordExporter as InMemoryLogExporter,
            )
        except ImportError:  # older SDKs
            from opentelemetry.sdk._logs.export import InMemoryLogExporter
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

        span_exp, log_exp = InMemorySpanExporter(), InMemoryLogExporter()
        reader = InMemoryMetricReader()
        span_proc, log_proc = SimpleSpanProcessor(span_exp), SimpleLogRecordProcessor(log_exp)
    elif mode == "console":
        from opentelemetry.sdk._logs.export import ConsoleLogExporter
        from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        span_exp, log_exp = ConsoleSpanExporter(), ConsoleLogExporter()
        reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), interval)
        span_proc, log_proc = BatchSpanProcessor(span_exp), BatchLogRecordProcessor(log_exp)
    else:  # otlp
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        # Endpoint/headers come from the standard OTEL_EXPORTER_OTLP_* env vars.
        span_exp, log_exp = OTLPSpanExporter(), OTLPLogExporter()
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(), interval)
        span_proc, log_proc = BatchSpanProcessor(span_exp), BatchLogRecordProcessor(log_exp)

    tp = TracerProvider(resource=resource)
    tp.add_span_processor(span_proc)
    mp = MeterProvider(resource=resource, metric_readers=[reader])
    lp = LoggerProvider(resource=resource)
    lp.add_log_record_processor(log_proc)

    if mode == "otlp":  # make them global for any library that uses the API directly
        from opentelemetry import metrics
        from opentelemetry._logs import set_logger_provider

        trace.set_tracer_provider(tp)
        metrics.set_meter_provider(mp)
        set_logger_provider(lp)

    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=lp)
    logger.addHandler(otel_handler)

    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tp, meter_provider=mp, excluded_urls="health"
    )
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=tp)

    meter = mp.get_meter(SERVICE_NAME)
    tel._instruments = {
        "requests": meter.create_counter(
            "learnloop_http_requests", unit="1", description="HTTP requests by route/method/status"
        ),
        "duration": meter.create_histogram(
            "learnloop_http_request_duration",
            unit="s",
            description="HTTP request latency by route/method/status",
            explicit_bucket_boundaries_advisory=[
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1,
                2.5,
                5,
                10,
            ],
        ),
        "sessions_logged": meter.create_counter(
            "learnloop_sessions_logged", unit="1", description="Study sessions logged"
        ),
    }
    tel.tracer_provider, tel.meter_provider, tel.logger_provider = tp, mp, lp
    tel.span_exporter, tel.log_exporter, tel.metric_reader = span_exp, log_exp, reader
    logger.info("telemetry initialised", extra={"telemetry_mode": mode})
    return tel


def _add_request_middleware(app: FastAPI, tel: Telemetry) -> None:
    """Per-request metric + one structured access log line (no bodies, no headers)."""

    @app.middleware("http")
    async def _observe(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            logger.exception(
                "unhandled error",
                extra={"http_method": request.method, "http_route": _route(request)},
            )
            raise
        finally:
            elapsed = time.perf_counter() - start
            route = _route(request)
            if route.startswith("/api/") or route == "/health":
                tel.record_request(route, request.method, status, elapsed)
                if route != "/health":
                    logger.info(
                        "request",
                        extra={
                            "http_method": request.method,
                            "http_route": route,
                            "http_status_code": status,
                            "duration_ms": round(elapsed * 1000, 2),
                        },
                    )


def _route(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"
