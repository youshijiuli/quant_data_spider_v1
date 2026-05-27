"""Tests for BaseRepository."""

import pytest

from src.core.models import StockBasic
from src.storage.repository import BaseRepository


class TestBaseRepository:
    def test_insert_and_find_by_id(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        stock = StockBasic(
            ts_code="000001.SZ",
            symbol="000001",
            name="平安银行",
            exchange="SZ",
        )
        repo.insert(stock)
        sqlite_session.commit()

        found = repo.find_by_id(stock.id)
        assert found is not None
        assert found.ts_code == "000001.SZ"
        assert found.name == "平安银行"

    def test_find_by_id_not_found(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        assert repo.find_by_id(99999) is None

    def test_find_all(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        for i in range(5):
            repo.insert(StockBasic(
                ts_code=f"00000{i}.SZ",
                symbol=f"00000{i}",
                name=f"股票{i}",
                exchange="SZ",
            ))
        sqlite_session.commit()

        results = repo.find_all()
        assert len(results) == 5

    def test_find_all_with_limit(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        for i in range(10):
            repo.insert(StockBasic(
                ts_code=f"0000{i:02d}.SZ",
                symbol=f"0000{i:02d}",
                name=f"股票{i}",
                exchange="SZ",
            ))
        sqlite_session.commit()

        results = repo.find_all(limit=3)
        assert len(results) == 3

    def test_find_all_with_offset(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        for i in range(5):
            repo.insert(StockBasic(
                ts_code=f"00000{i}.SZ",
                symbol=f"00000{i}",
                name=f"股票{i}",
                exchange="SZ",
            ))
        sqlite_session.commit()

        results = repo.find_all(limit=2, offset=3)
        assert len(results) == 2

    def test_count_empty(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        assert repo.count() == 0

    def test_count(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        for i in range(7):
            repo.insert(StockBasic(
                ts_code=f"00000{i}.SZ",
                symbol=f"00000{i}",
                name=f"股票{i}",
                exchange="SZ",
            ))
        sqlite_session.commit()

        assert repo.count() == 7

    def test_delete_all(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        for i in range(3):
            repo.insert(StockBasic(
                ts_code=f"00000{i}.SZ",
                symbol=f"00000{i}",
                name=f"股票{i}",
                exchange="SZ",
            ))
        sqlite_session.commit()

        deleted = repo.delete_all()
        assert deleted == 3
        assert repo.count() == 0

    def test_bulk_upsert_empty_rows(self, sqlite_session):
        repo = BaseRepository(sqlite_session, StockBasic)
        result = repo.bulk_upsert([], ["ts_code"])
        assert result == 0
