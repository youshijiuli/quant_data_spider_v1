"""QuantScheduler — APScheduler wrapper for scheduled data sync jobs."""

import tomli
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class QuantScheduler:
    """Thin wrapper around APScheduler's AsyncIOScheduler."""

    def __init__(self, config_path: str | None = None):
        from config.settings import CONFIG_DIR

        self._scheduler = AsyncIOScheduler()
        self._config_path = config_path or str(CONFIG_DIR / "schedules.toml")
        self._job_funcs: dict[str, callable] = {}

    def register(self, name: str, func: callable) -> None:
        self._job_funcs[name] = func

    def load_and_start(self) -> None:
        """Load schedules.toml, register jobs, and start the scheduler."""
        with open(self._config_path, "rb") as f:
            data = tomli.load(f)

        jobs_cfg = data.get("jobs", {})
        for name, cfg in jobs_cfg.items():
            if not cfg.get("enabled", False):
                continue
            func = self._job_funcs.get(name)
            if func is None:
                continue

            cron = cfg.get("cron", {})
            trigger = CronTrigger(
                year=cron.get("year", "*"),
                month=cron.get("month", "*"),
                day=cron.get("day", "*"),
                week=cron.get("week", "*"),
                day_of_week=cron.get("day_of_week", "*"),
                hour=cron.get("hour", "*"),
                minute=cron.get("minute", "*"),
                second=cron.get("second", "0"),
            )
            self._scheduler.add_job(
                func,
                trigger=trigger,
                id=name,
                name=cfg.get("description", name),
                replace_existing=True,
            )

        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def get_jobs(self) -> list[dict]:
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    def pause_job(self, job_id: str) -> bool:
        job = self._scheduler.get_job(job_id)
        if job:
            self._scheduler.pause_job(job_id)
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._scheduler.get_job(job_id)
        if job:
            self._scheduler.resume_job(job_id)
            return True
        return False

    def run_job_now(self, job_id: str) -> bool:
        job = self._scheduler.get_job(job_id)
        if job:
            job.func()
            return True
        return False
