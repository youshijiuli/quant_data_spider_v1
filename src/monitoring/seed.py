"""Seed monitoring_rules table from config/thresholds.toml."""

import logging
import tomli
from sqlalchemy import text

from config.settings import CONFIG_DIR

logger = logging.getLogger(__name__)


def seed_monitoring_rules(session_factory) -> int:
    """Insert or update monitoring rules from thresholds.toml. Returns count of rules seeded."""
    toml_path = CONFIG_DIR / "thresholds.toml"
    if not toml_path.exists():
        logger.warning(f"thresholds.toml not found at {toml_path}")
        return 0

    with open(toml_path, "rb") as f:
        data = tomli.load(f)

    rules_data = data.get("rules", {})
    session = session_factory()
    count = 0
    try:
        for key, cfg in rules_data.items():
            rule_code = cfg.get("rule_code", key)
            # Check if rule exists
            existing = session.execute(
                text("SELECT id FROM monitoring_rules WHERE rule_code = :rule_code"),
                {"rule_code": rule_code},
            ).fetchone()

            if existing:
                session.execute(
                    text(
                        "UPDATE monitoring_rules SET "
                        "rule_name = :rule_name, target_table = :target_table, "
                        "target_column = :target_column, check_type = :check_type, "
                        "threshold_min = :threshold_min, threshold_max = :threshold_max, "
                        "threshold_value = :threshold_value, lookback_hours = :lookback_hours, "
                        "severity = :severity, is_active = :is_active "
                        "WHERE rule_code = :rule_code"
                    ),
                    _rule_params(rule_code, cfg),
                )
            else:
                session.execute(
                    text(
                        "INSERT INTO monitoring_rules (rule_code, rule_name, target_table, target_column, "
                        "check_type, threshold_min, threshold_max, threshold_value, lookback_hours, "
                        "severity, is_active) "
                        "VALUES (:rule_code, :rule_name, :target_table, :target_column, :check_type, "
                        ":threshold_min, :threshold_max, :threshold_value, :lookback_hours, "
                        ":severity, :is_active)"
                    ),
                    _rule_params(rule_code, cfg),
                )
            count += 1
        session.commit()
        logger.info(f"Seeded {count} monitoring rules from thresholds.toml")
    finally:
        session.close()
    return count


def _rule_params(rule_code: str, cfg: dict) -> dict:
    return {
        "rule_code": rule_code,
        "rule_name": cfg.get("rule_name", rule_code),
        "target_table": cfg.get("target_table", ""),
        "target_column": cfg.get("target_column") or None,
        "check_type": cfg.get("check_type", ""),
        "threshold_min": cfg.get("threshold_min"),
        "threshold_max": cfg.get("threshold_max"),
        "threshold_value": cfg.get("threshold_value"),
        "lookback_hours": cfg.get("lookback_hours", 24),
        "severity": cfg.get("severity", "warning"),
        "is_active": cfg.get("is_active", True),
    }
