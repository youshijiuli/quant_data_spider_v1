"""Rule evaluation engine — runs checks against database and creates alerts."""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import text

from src.monitoring.dispatcher import AlertDispatcher

logger = logging.getLogger(__name__)


class MonitoringEvaluator:
    """Evaluates monitoring rules against the database and creates alerts."""

    def __init__(self, session_factory, dispatcher: AlertDispatcher | None = None):
        self.session_factory = session_factory
        self.dispatcher = dispatcher or AlertDispatcher()

    def run_all_checks(self) -> list[dict]:
        """Run all active rules and return created alerts."""
        session = self.session_factory()
        try:
            rules = session.execute(
                text("SELECT * FROM monitoring_rules WHERE is_active = 1")
            ).fetchall()
        finally:
            session.close()

        alerts = []
        for rule in rules:
            try:
                result = self._evaluate(rule)
                if result["breached"]:
                    alert = self._create_alert(rule, result)
                    alerts.append(alert)
                    self.dispatcher.dispatch(alert)
            except Exception:
                logger.exception(f"Rule {rule.rule_code} evaluation failed")
        return alerts

    def _evaluate(self, rule) -> dict:
        check_type = rule.check_type
        if check_type == "null_rate":
            return self._check_null_rate(rule)
        elif check_type == "row_count":
            return self._check_row_count(rule)
        elif check_type == "stale_data":
            return self._check_stale_data(rule)
        elif check_type == "value_range":
            return self._check_value_range(rule)
        elif check_type == "duplicate_rate":
            return self._check_duplicate_rate(rule)
        return {"breached": False, "actual_value": None, "message": f"Unknown check type: {check_type}"}

    def _check_null_rate(self, rule) -> dict:
        table = rule.target_table
        col = rule.target_column
        lookback = rule.lookback_hours
        threshold = rule.threshold_max

        session = self.session_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback)
            row = session.execute(
                text(
                    f"SELECT COUNT(*) AS total, "
                    f"SUM(CASE WHEN `{col}` IS NULL THEN 1 ELSE 0 END) AS nulls "
                    f"FROM `{table}` WHERE created_at >= :cutoff"
                ),
                {"cutoff": cutoff},
            ).fetchone()

            total = row.total or 0
            nulls = row.nulls or 0
            rate = nulls / total if total > 0 else 0

            breached = rate > threshold
            message = (
                f"{table}.{col}: {nulls}/{total} null ({rate:.2%}), threshold={threshold:.2%}"
                if breached
                else ""
            )
            return {"breached": breached, "actual_value": rate, "message": message}
        finally:
            session.close()

    def _check_row_count(self, rule) -> dict:
        table = rule.target_table
        lookback = rule.lookback_hours
        threshold = rule.threshold_min

        session = self.session_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback)
            row = session.execute(
                text(f"SELECT COUNT(*) AS cnt FROM `{table}` WHERE created_at >= :cutoff"),
                {"cutoff": cutoff},
            ).fetchone()

            count = row.cnt if row else 0
            breached = count < threshold
            message = (
                f"{table}: {count} rows in last {lookback}h, minimum={threshold}"
                if breached
                else ""
            )
            return {"breached": breached, "actual_value": float(count), "message": message}
        finally:
            session.close()

    def _check_stale_data(self, rule) -> dict:
        table = rule.target_table
        col = rule.target_column
        lookback = rule.lookback_hours

        session = self.session_factory()
        try:
            row = session.execute(
                text(f"SELECT MAX(`{col}`) AS latest FROM `{table}`")
            ).fetchone()

            latest = row.latest if row else None
            if latest is None:
                return {"breached": True, "actual_value": None, "message": f"{table}.{col}: no data found"}

            latest_date = latest if isinstance(latest, date) else latest.date() if hasattr(latest, "date") else None
            if latest_date is None:
                return {"breached": False, "actual_value": None, "message": ""}

            max_allowed = date.today() - timedelta(hours=lookback)
            breached = latest_date < max_allowed
            message = (
                f"{table}.{col}: latest={latest_date}, max allowed={max_allowed}"
                if breached
                else ""
            )
            return {"breached": breached, "actual_value": None, "message": message}
        finally:
            session.close()

    def _check_value_range(self, rule) -> dict:
        table = rule.target_table
        col = rule.target_column
        lookback = rule.lookback_hours
        expected = rule.threshold_value

        session = self.session_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback)
            row = session.execute(
                text(f"SELECT COUNT(*) AS cnt FROM `{table}` "
                     f"WHERE `{col}` = :val AND started_at >= :cutoff"),
                {"val": "failed", "cutoff": cutoff},
            ).fetchone()

            count = row.cnt if row else 0
            breached = count > (expected or 0)
            message = (
                f"{table}.{col}: {count} failed sync(s) in last {lookback}h"
                if breached
                else ""
            )
            return {"breached": breached, "actual_value": float(count), "message": message}
        finally:
            session.close()

    def _check_duplicate_rate(self, rule) -> dict:
        table = rule.target_table
        lookback = rule.lookback_hours
        threshold = rule.threshold_max

        session = self.session_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback)
            row = session.execute(
                text(
                    f"SELECT COUNT(*) AS total, "
                    f"SUM(dup_cnt) AS dup_rows FROM ("
                    f"SELECT COUNT(*) AS dup_cnt FROM `{table}` "
                    f"WHERE created_at >= :cutoff "
                    f"GROUP BY ts_code, trade_date HAVING COUNT(*) > 1"
                    f") AS dups"
                ),
                {"cutoff": cutoff},
            ).fetchone()

            total_row = session.execute(
                text(f"SELECT COUNT(*) AS cnt FROM `{table}` WHERE created_at >= :cutoff"),
                {"cutoff": cutoff},
            ).fetchone()

            total = total_row.cnt if total_row else 0
            dup_rows = row.dup_rows if row and row.dup_rows else 0
            rate = dup_rows / total if total > 0 else 0

            breached = rate > threshold
            message = (
                f"{table}: {int(dup_rows)} dup rows / {total} total ({rate:.2%}), threshold={threshold:.2%}"
                if breached
                else ""
            )
            return {"breached": breached, "actual_value": rate, "message": message}
        finally:
            session.close()

    def _create_alert(self, rule, result: dict) -> dict:
        """Insert an alert into monitoring_alerts and return its data."""
        from src.core.models import MonitoringAlert

        session = self.session_factory()
        try:
            alert = MonitoringAlert(
                rule_code=rule.rule_code,
                alert_time=datetime.utcnow(),
                severity=rule.severity,
                title=rule.rule_name,
                message=result["message"],
                actual_value=result.get("actual_value"),
                threshold_value=rule.threshold_max or rule.threshold_min or rule.threshold_value,
                status="open",
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return {
                "id": alert.id,
                "rule_code": alert.rule_code,
                "alert_time": alert.alert_time,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "status": alert.status,
            }
        finally:
            session.close()
