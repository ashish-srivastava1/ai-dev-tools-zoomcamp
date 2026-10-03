import os

# Disable telemetry during tests so importing the app does not start the
# console exporters (which raise at shutdown once pytest closes stdout).
os.environ.setdefault("TELEMETRY_EXPORTER", "none")
