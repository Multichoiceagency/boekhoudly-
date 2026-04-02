"""
Cross-database compatibility types.
Uses PostgreSQL-native UUID/JSONB when available, falls back to String/JSON for SQLite.
"""
import json
from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.types import CHAR

try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
    _HAS_PG = True
except ImportError:
    _HAS_PG = False


class GUID(TypeDecorator):
    """Platform-independent UUID type. Uses PG UUID on PostgreSQL, CHAR(36) on SQLite."""
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PG:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        import uuid
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class JSONB(TypeDecorator):
    """Platform-independent JSON type. Uses PG JSONB on PostgreSQL, TEXT+JSON on SQLite."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and _HAS_PG:
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value
