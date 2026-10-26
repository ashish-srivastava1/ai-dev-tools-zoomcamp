import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from learnloop.config import normalise_db_url
from learnloop.db import Base
from learnloop.main import create_app
from tests.conftest import make_config

URL = os.getenv("INTEGRATION_DATABASE_URL")


@pytest.fixture
def pg_client():
    if not URL:
        pytest.skip("INTEGRATION_DATABASE_URL not set")
    url = normalise_db_url(URL)
    engine = create_engine(url)
    from learnloop import models  # noqa: F401

    Base.metadata.drop_all(engine)
    engine.dispose()
    app = create_app(make_config(url), telemetry_mode="none")
    with TestClient(app) as c:
        yield c
