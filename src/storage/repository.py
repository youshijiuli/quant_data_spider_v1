"""Generic SQLAlchemy repository with MySQL bulk upsert support."""

from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from src.core.models import Base

T = TypeVar("T", bound=Base)


class BaseRepository:
    """Generic repository with common CRUD and MySQL-specific bulk_upsert."""

    def __init__(self, session: Session, model: type[Base]):
        self.session = session
        self.model = model

    def bulk_upsert(self, rows: list[dict], unique_cols: list[str]) -> int:
        """INSERT ... ON DUPLICATE KEY UPDATE for MySQL.

        Returns the number of rows inserted.
        """
        if not rows:
            return 0

        stmt = mysql_insert(self.model).values(rows)

        pk_cols = {c.name for c in inspect(self.model).primary_key}
        data_cols = set(rows[0].keys())
        update_cols = {}
        for c in self.model.__table__.columns:
            if c.name not in unique_cols and c.name not in pk_cols and c.name in data_cols:
                update_cols[c.name] = getattr(stmt.inserted, c.name)

        stmt = stmt.on_duplicate_key_update(**update_cols)
        result = self.session.execute(stmt)
        return result.rowcount

    def find_all(self, limit: int | None = None, offset: int = 0) -> list[T]:
        q = self.session.query(self.model)
        if limit is not None:
            q = q.limit(limit).offset(offset)
        return q.all()

    def find_by_id(self, id_val: int) -> T | None:
        return self.session.get(self.model, id_val)

    def count(self) -> int:
        return self.session.query(self.model).count()

    def insert(self, item: T) -> T:
        self.session.add(item)
        return item

    def delete_all(self) -> int:
        return self.session.query(self.model).delete()
