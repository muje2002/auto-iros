"""maintenance.py 단위테스트"""

from datetime import datetime

from src.maintenance import is_maintenance_period, get_maintenance_warning


class TestIsMaintenancePeriod:
    def test_first_thursday_2100(self):
        """1째주 목요일 21:30 → 점검 중"""
        assert is_maintenance_period(datetime(2026, 3, 5, 21, 30)) is True

    def test_first_friday_0300(self):
        """1째주 금요일 03:00 → 점검 중"""
        assert is_maintenance_period(datetime(2026, 3, 6, 3, 0)) is True

    def test_first_friday_0700(self):
        """1째주 금요일 07:00 → 점검 끝"""
        assert is_maintenance_period(datetime(2026, 3, 6, 7, 0)) is False

    def test_second_thursday_2200(self):
        """2째주 목요일 22:00 → 점검 아님"""
        assert is_maintenance_period(datetime(2026, 3, 12, 22, 0)) is False

    def test_third_thursday_2100(self):
        """3째주 목요일 21:00 → 점검 중"""
        assert is_maintenance_period(datetime(2026, 3, 19, 21, 0)) is True

    def test_third_friday_0559(self):
        """3째주 금요일 05:59 → 점검 중"""
        assert is_maintenance_period(datetime(2026, 3, 20, 5, 59)) is True

    def test_first_thursday_daytime(self):
        """1째주 목요일 낮 → 점검 아님"""
        assert is_maintenance_period(datetime(2026, 3, 5, 14, 0)) is False

    def test_regular_weekday(self):
        """일반 평일 → 점검 아님"""
        assert is_maintenance_period(datetime(2026, 3, 10, 10, 0)) is False


class TestGetMaintenanceWarning:
    def test_returns_message_during_maintenance(self):
        msg = get_maintenance_warning(datetime(2026, 3, 5, 22, 0))
        assert msg is not None
        assert "정기점검" in msg

    def test_returns_none_outside_maintenance(self):
        assert get_maintenance_warning(datetime(2026, 3, 10, 10, 0)) is None
