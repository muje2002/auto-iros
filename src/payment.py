"""전자민원캐시 결제 정보 관리 모듈

issueType이 발급(0) 또는 열람(1)인 경우 선불전자지급수단(전자민원캐시) 필요.
issueType이 고유번호조회(2) 또는 원문데이터(3)인 경우 결제 불필요.

demo/sandbox 환경에서는 결제 검증을 건너뜀 (테스트 데이터만 반환).
production 환경에서만 결제 정보 필수.
"""

from .config import Config
from .codef_api import ISSUE_TYPES


def requires_payment(issue_type: str) -> bool:
    """해당 발급유형이 결제를 필요로 하는지 확인.

    Args:
        issue_type: 발급유형 한글명 (발급/열람/고유번호조회/원문데이터)

    Returns:
        결제 필요 여부
    """
    code = ISSUE_TYPES.get(issue_type, "1")
    return code in ("0", "1")


def validate_payment_config(config: Config, issue_type: str) -> str | None:
    """결제가 필요한 경우 결제 정보가 설정되어 있는지 검증.

    demo/sandbox 환경에서는 결제 검증을 건너뛴다.
    production 환경에서만 결제 정보가 필수.

    Args:
        config: 설정 객체
        issue_type: 발급유형 한글명

    Returns:
        오류 메시지 (없으면 None)
    """
    if not requires_payment(issue_type):
        return None

    # demo/sandbox는 결제 없이 API 호출 허용
    if config.env in ("demo", "sandbox"):
        return None

    # production: 결제 정보 필수
    if not config.eprepay_no:
        return (
            f"'{issue_type}' 요청에는 전자민원캐시가 필요합니다.\n"
            "EPREPAY_NO, EPREPAY_PASS를 .env에 설정하세요.\n"
            "전자민원캐시는 인터넷등기소(iros.go.kr)에서 구매할 수 있습니다."
        )

    if len(config.eprepay_no) != 12:
        return f"EPREPAY_NO는 12자리여야 합니다. (현재: {len(config.eprepay_no)}자리)"

    if not config.eprepay_pass:
        return "EPREPAY_PASS가 설정되지 않았습니다."

    return None
