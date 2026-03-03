import uuid


def short_id() -> str:
    """
    Generates a unique ID using UUIDv4.

    Note: This implementation uses UUIDs, which are not time-sortable
    like the previous Snowflake implementation. The generated string is also
    longer.
    """
    return str(uuid.uuid4())
