"""대법원 정기점검 시간 감지 모듈

대법원 정기점검: 매월 첫째주, 셋째주 목요일 21:00 ~ 익일 06:00
"""

from datetime import datetime, timedelta


def _is_nth_thursday(dt: datetime, n: int) -> bool:
    """해당 날짜가 n번째 목요일인지 확인 (n: 1 또는 3)"""
    if dt.weekday() != 3:  # 목요일 = 3
        return False
    day = dt.day
    week_num = (day - 1) // 7 + 1
    return week_num == n


def is_maintenance_period(now: datetime | None = None) -> bool:
    """현재 대법원 점검 시간대인지 확인.

    점검 시간: 매월 1째/3째 목요일 21:00 ~ 금요일 06:00

    Args:
        now: 기준 시각 (테스트용, None이면 현재 시각)

    Returns:
        점검 시간대 여부
    """
    if now is None:
        now = datetime.now()

    hour = now.hour

    # Case 1: 목요일 21:00~23:59 (1째/3째 목요일)
    if _is_nth_thursday(now, 1) or _is_nth_thursday(now, 3):
        if hour >= 21:
            return True

    # Case 2: 금요일 00:00~05:59 (직전 목요일이 1째/3째)
    yesterday = now - timedelta(days=1)
    if now.weekday() == 4 and hour < 6:  # 금요일 = 4
        if _is_nth_thursday(yesterday, 1) or _is_nth_thursday(yesterday, 3):
            return True

    return False


def get_maintenance_warning(now: datetime | None = None) -> str | None:
    """점검 시간대이면 경고 메시지 반환, 아니면 None.

    Args:
        now: 기준 시각 (테스트용)

    Returns:
        경고 메시지 또는 None
    """
    if is_maintenance_period(now):
        return (
            "현재 대법원 정기점검 시간대입니다 "
            "(매월 1/3째주 목요일 21:00 ~ 금요일 06:00). "
            "조회가 실패할 수 있습니다."
        )
    return None
