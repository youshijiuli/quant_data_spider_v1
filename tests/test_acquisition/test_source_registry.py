"""Tests for SourceRegistry."""

import tempfile
from pathlib import Path

import pytest

from src.acquisition.source_registry import SourceRegistry

TOML_CONTENT = """\
[akshare_stock_basic]
source_code = "akshare_stock_basic"
source_name = "A股股票基本信息"
source_type = "akshare"
endpoint = "stock_info_a_code_name"
is_active = true
rate_limit_rps = 1.0
retry_max = 3
retry_backoff = 2.0

[akshare_stock_daily]
source_code = "akshare_stock_daily"
source_name = "A股日线行情"
source_type = "akshare"
endpoint = "stock_zh_a_hist"
is_active = false
rate_limit_rps = 2.0
retry_max = 3
retry_backoff = 2.0

[sync_groups]
stock_daily = ["akshare_stock_daily"]
all_active = ["akshare_stock_basic"]
"""


@pytest.fixture
def temp_toml():
    tmp = Path(tempfile.mktemp(suffix=".toml"))
    tmp.write_text(TOML_CONTENT, encoding="utf-8")
    yield str(tmp)
    try:
        tmp.unlink(missing_ok=True)
    except Exception:
        pass


class TestSourceRegistry:
    def test_loads_sources(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        assert len(reg._sources) == 2
        assert "akshare_stock_basic" in reg._sources
        assert "akshare_stock_daily" in reg._sources

    def test_get_source(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        src = reg.get_source("akshare_stock_basic")
        assert src["source_name"] == "A股股票基本信息"
        assert src["is_active"] is True

    def test_get_source_not_found(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        with pytest.raises(ValueError, match="Unknown source"):
            reg.get_source("nonexistent")

    def test_list_active_sources(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        active = reg.list_active_sources()
        assert "akshare_stock_basic" in active
        assert "akshare_stock_daily" not in active

    def test_get_sync_group(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        groups = reg.get_sync_group("stock_daily")
        assert groups == ["akshare_stock_daily"]

    def test_get_sync_group_empty(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        groups = reg.get_sync_group("nonexistent_group")
        assert groups == []

    def test_get_client_akshare(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        client = reg.get_client("akshare_stock_basic")
        assert client.source_code == "akshare_stock_basic"

    def test_get_client_unknown_type(self, temp_toml):
        reg = SourceRegistry(config_path=temp_toml)
        reg._sources["bad_source"] = {"source_code": "bad_source", "source_type": "unknown"}
        with pytest.raises(ValueError, match="Unsupported source type"):
            reg.get_client("bad_source")
