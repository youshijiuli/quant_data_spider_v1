"""Tests for web route endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.web.app import create_app


@pytest.fixture
def test_app(sqlite_engine, sqlite_session_factory):
    """Create a test FastAPI app with SQLite."""
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Mock the scheduler to avoid APScheduler issues in tests
    import sys as _sys
    import src.scheduler.scheduler as _sched_mod

    class MockQuantScheduler:
        def __init__(self, *a, **kw):
            pass
        def register(self, *a, **kw):
            pass
        def load_and_start(self):
            pass
        def shutdown(self):
            pass
        def get_jobs(self):
            return []
        def pause_job(self, jid):
            return True
        def resume_job(self, jid):
            return True
        def run_job_now(self, jid):
            return True

    _sched_mod.QuantScheduler = MockQuantScheduler

    from src.monitoring.seed import seed_monitoring_rules
    seed_monitoring_rules(sqlite_session_factory)

    app = create_app(sqlite_engine, sqlite_session_factory)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestDashboardRoutes:
    def test_home_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "量化数据" in resp.text or "Quant" in resp.text

    def test_data_stocks(self, client):
        resp = client.get("/data/stocks")
        assert resp.status_code == 200

    def test_data_indexes(self, client):
        resp = client.get("/data/indexes")
        assert resp.status_code == 200

    def test_data_financials(self, client):
        resp = client.get("/data/financials")
        assert resp.status_code == 200

    def test_data_sources(self, client):
        resp = client.get("/data/sources")
        assert resp.status_code == 200


class TestChartRoutes:
    def test_chart_home(self, client):
        resp = client.get("/charts/")
        assert resp.status_code == 200

    def test_chart_stock_data(self, client):
        resp = client.get("/charts/stock/000001.SZ/data")
        assert resp.status_code in (200, 404)


class TestSyncRoutes:
    def test_sync_page(self, client):
        resp = client.get("/sync/")
        assert resp.status_code == 200

    def test_sync_history(self, client):
        resp = client.get("/sync/history")
        assert resp.status_code == 200


class TestMonitoringRoutes:
    def test_monitoring_page(self, client):
        resp = client.get("/monitoring/")
        assert resp.status_code == 200

    def test_alerts_table(self, client):
        resp = client.get("/monitoring/alerts/table")
        assert resp.status_code == 200

    def test_alerts_table_filtered(self, client):
        resp = client.get("/monitoring/alerts/table?severity=critical&status=open")
        assert resp.status_code == 200

    def test_rules_page(self, client):
        resp = client.get("/monitoring/rules")
        assert resp.status_code == 200
        assert "daily_null_rate" in resp.text


class TestSchedulerRoutes:
    def test_scheduler_page(self, client):
        resp = client.get("/scheduler/")
        assert resp.status_code == 200


class TestApiRoutes:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "db" in data

    def test_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "stocks" in data

    def test_search_stock(self, client):
        resp = client.get("/api/search/stock?q=000001")
        assert resp.status_code == 200
