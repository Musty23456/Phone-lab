import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.device.device_info import parse_meminfo_total_mb, _summarize_storage, _BATTERY_STATUS_MAP


def test_parse_meminfo_total_mb():
    sample = "MemTotal:        3872548 kB\nMemFree:          123456 kB\n"
    result = parse_meminfo_total_mb(sample)
    assert result == 3872548 // 1024


def test_parse_meminfo_missing():
    assert parse_meminfo_total_mb("no data here") is None


def test_summarize_storage_with_data_line():
    sample = (
        "Filesystem     1K-blocks     Used Available Use% Mounted on\n"
        "/dev/block/dm-1 111633152 45000000 65000000  42% /data\n"
    )
    summary = _summarize_storage(sample)
    assert "GB used" in summary
    assert "GB total" in summary


def test_summarize_storage_no_match():
    assert _summarize_storage("nothing relevant here") == "Unavailable"


def test_battery_status_map_known_values():
    assert _BATTERY_STATUS_MAP["2"] == "Charging"
    assert _BATTERY_STATUS_MAP["5"] == "Full"
