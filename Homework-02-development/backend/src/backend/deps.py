from .store import PartyStore

# Single shared store for the running app (single-restaurant, no multi-tenant
# support per the spec). Tests override this dependency with a fresh store.
_store = PartyStore()


def get_store() -> PartyStore:
    return _store
