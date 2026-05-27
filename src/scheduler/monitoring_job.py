"""Monitoring job factory — creates a coroutine that runs all checks."""

import logging

logger = logging.getLogger(__name__)


def make_monitoring_job(session_factory):
    async def job():
        from src.monitoring.evaluator import MonitoringEvaluator

        logger.info("Scheduled: run monitoring checks")
        evaluator = MonitoringEvaluator(session_factory)
        alerts = evaluator.run_all_checks()
        logger.info(f"Monitoring done: {len(alerts)} alert(s) created")
        return alerts

    return job
