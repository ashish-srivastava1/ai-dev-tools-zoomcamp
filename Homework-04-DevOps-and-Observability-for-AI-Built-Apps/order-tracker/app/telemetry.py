"""OpenTelemetry setup for Order Tracker.

Exposes three signals - metrics, logs and traces - for order lookups.

The exporter is chosen at startup with the ``TELEMETRY_EXPORTER`` env var:

* ``console`` (default) prints every signal to stdout, so you can read it with
  ``docker compose logs app``. Used in Question 2.
* ``otlp`` ships the signals over OTLP/gRPC to an OpenTelemetry Collector at
  ``OTEL_EXPORTER_OTLP_ENDPOINT``. Used from Question 3 onwards.

The key metric is ``http_server_requests`` - a counter with ``http_route`` and
``http_status_code`` attributes, so we can ask "how many requests hit this
route, and how many of them were 5xx?".
"""

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "order-tracker")
EXPORTER = os.getenv("TELEMETRY_EXPORTER", "console").lower()
# How often the console/OTLP metric reader flushes. Short so the homework
# lookups show up quickly in `docker compose logs app`.
METRIC_INTERVAL_MS = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "5000"))

_meter = None
_request_counter = None
_logger = logging.getLogger("order-tracker")


def _resource() -> Resource:
    return Resource.create({"service.name": SERVICE_NAME})


def _otlp_endpoint() -> str:
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")


def _span_exporter():
    if EXPORTER == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        return OTLPSpanExporter(endpoint=_otlp_endpoint(), insecure=True)
    return ConsoleSpanExporter()


def _metric_exporter():
    if EXPORTER == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )

        return OTLPMetricExporter(endpoint=_otlp_endpoint(), insecure=True)
    return ConsoleMetricExporter()


def _log_exporter():
    if EXPORTER == "otlp":
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
            OTLPLogExporter,
        )

        return OTLPLogExporter(endpoint=_otlp_endpoint(), insecure=True)
    return ConsoleLogExporter()


def setup_telemetry() -> None:
    """Configure the global tracer, meter and logger providers."""
    global _meter, _request_counter

    # "none" disables telemetry entirely - handy for tests, where exporting to
    # a console stream that pytest later closes would raise at shutdown.
    if EXPORTER == "none":
        return

    resource = _resource()

    # --- Traces ---
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(_span_exporter()))
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    reader = PeriodicExportingMetricReader(
        _metric_exporter(), export_interval_millis=METRIC_INTERVAL_MS
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter(SERVICE_NAME)
    _request_counter = _meter.create_counter(
        name="http_server_requests",
        unit="1",
        description="Count of HTTP requests by route, method and status code",
    )

    # --- Logs ---
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(_log_exporter())
    )
    set_logger_provider(logger_provider)
    otel_handler = LoggingHandler(
        level=logging.INFO, logger_provider=logger_provider
    )
    _logger.setLevel(logging.INFO)
    _logger.addHandler(otel_handler)
    # Also mirror to stdout so it is easy to read in `docker compose logs app`.
    _logger.addHandler(logging.StreamHandler())
    _logger.propagate = False

    _logger.info(
        "telemetry initialised",
        extra={"exporter": EXPORTER, "service.name": SERVICE_NAME},
    )


def record_request(route: str, method: str, status_code: int) -> None:
    """Increment the request counter with route + status code attributes."""
    if _request_counter is None:
        return
    _request_counter.add(
        1,
        {
            "http_route": route,
            "http_method": method,
            "http_status_code": status_code,
        },
    )


def get_logger() -> logging.Logger:
    return _logger
