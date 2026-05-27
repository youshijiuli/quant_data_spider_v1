"""Tests for QuantScheduler."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.scheduler.scheduler import QuantScheduler


@pytest.fixture
def scheduler_config():
    import tomli
    tmp = Path(tempfile.mktemp(suffix=".toml"))
    tmp.write_text("[jobs]\n", encoding="utf-8")
    yield str(tmp)
    try:
        tmp.unlink(missing_ok=True)
    except Exception:
        pass


class TestQuantScheduler:
    def test_register_job(self, scheduler_config):
        sched = QuantScheduler(config_path=scheduler_config)
        called = []

        async def test_func():
            called.append(1)

        sched.register("test_job", test_func)
        assert "test_job" in sched._job_funcs

    def test_pause_resume_not_found(self, scheduler_config):
        sched = QuantScheduler(config_path=scheduler_config)
        assert sched.pause_job("nonexistent") is False
        assert sched.resume_job("nonexistent") is False

    def test_run_job_not_found(self, scheduler_config):
        sched = QuantScheduler(config_path=scheduler_config)
        assert sched.run_job_now("nonexistent") is False

    @pytest.mark.asyncio
    async def test_load_and_shutdown(self, scheduler_config):
        sched = QuantScheduler(config_path=scheduler_config)
        sched.load_and_start()
        jobs = sched.get_jobs()
        assert jobs == []
        sched.shutdown()
