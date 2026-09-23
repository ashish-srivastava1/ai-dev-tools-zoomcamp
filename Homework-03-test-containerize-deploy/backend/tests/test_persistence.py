"""Proves data actually survives in a real database, not just in memory.

The other test files use an in-memory SQLite DB shared for one test via a
single connection (see conftest.py) — that isolates tests from each other
but doesn't prove persistence. These tests use a real file on disk and
open it through *separate* engine/session instances, standing in for
"the app restarted" / "a second process reads the same database".
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base
from backend.store import PartyNotFoundError, PartyStore


def _connect(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return engine, session


def test_party_survives_a_new_connection_to_the_same_file(tmp_path):
    db_path = tmp_path / "persistence.db"

    engine1, session1 = _connect(db_path)
    created = PartyStore(session1).add(
        name="Persisted", party_size=2, phone_number="555-999-0000", notes="should survive"
    )
    party_id = created.id
    session1.close()
    engine1.dispose()

    # A brand new engine/session against the same file — nothing in memory
    # is shared with the connection above.
    engine2, session2 = _connect(db_path)
    reloaded = PartyStore(session2).get(party_id)

    assert reloaded.name == "Persisted"
    assert reloaded.status == "waiting"
    assert reloaded.notes == "should survive"
    session2.close()
    engine2.dispose()


def test_status_change_survives_a_new_connection_to_the_same_file(tmp_path):
    db_path = tmp_path / "persistence.db"

    engine1, session1 = _connect(db_path)
    store1 = PartyStore(session1)
    party = store1.add(name="Chen", party_size=3, phone_number="555-999-1111", notes="")
    party_id = party.id
    store1.call(party_id)
    store1.seat(party_id)
    session1.close()
    engine1.dispose()

    engine2, session2 = _connect(db_path)
    reloaded = PartyStore(session2).get(party_id)

    assert reloaded.status == "seated"
    assert reloaded.called_at is not None
    assert reloaded.seated_at is not None
    session2.close()
    engine2.dispose()


def test_deleting_the_database_file_loses_data_but_a_fresh_one_starts_clean(tmp_path):
    """Sanity check that the two tests above are actually exercising disk,
    not some connection-level cache: a fresh file has no history at all."""
    db_path = tmp_path / "persistence.db"

    engine1, session1 = _connect(db_path)
    party = PartyStore(session1).add(name="Nguyen", party_size=2, phone_number="555-999-2222", notes="")
    party_id = party.id
    session1.close()
    engine1.dispose()

    db_path.unlink()

    engine2, session2 = _connect(db_path)
    try:
        PartyStore(session2).get(party_id)
        raised = False
    except PartyNotFoundError:
        raised = True
    assert raised
    session2.close()
    engine2.dispose()
