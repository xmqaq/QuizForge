from datetime import datetime, timezone


def naive_utcnow() -> datetime:
    """Naive UTC timestamp matching the DB's TIMESTAMP WITHOUT TIME ZONE columns.

    ponytail: app uses naive timestamps throughout (func.now() defaults are naive);
    writing tz-aware values fails asyncpg, so normalize here.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
