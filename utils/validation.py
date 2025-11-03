"""
회의록 입력 검증 및 날짜/시간 처리 모듈
"""
import datetime


def validate_title(title):
    """
    제목 입력값 검증

    Args:
        title (str): 사용자가 입력한 제목

    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): 검증 성공 여부
            - error_message (str): 에러 메시지 (검증 실패 시)
    """
    if not title or title.strip() == "":
        return False, "제목을 입력해 주세요."
    return True, None


def get_current_datetime_string():
    """
    현재 날짜와 시간을 문자열로 반환

    Returns:
        str: 현재 날짜/시간 문자열 (형식: "YYYY-MM-DD HH:MM:SS")
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_meeting_date(meeting_date):
    """
    회의 일시 파싱 및 검증

    Args:
        meeting_date (str): 사용자가 입력한 회의 일시 (형식: "YYYY-MM-DDTHH:MM" 또는 빈 문자열)

    Returns:
        str: 파싱된 회의 일시 문자열 (형식: "YYYY-MM-DD HH:MM:SS")
             입력이 없으면 현재 시간 반환
    """
    if not meeting_date or meeting_date.strip() == "":
        # 회의 일시가 비어있으면 현재 시간 반환
        return get_current_datetime_string()

    try:
        # datetime-local 형식 "YYYY-MM-DDTHH:MM"을 "YYYY-MM-DD HH:MM:SS"로 변환
        dt = datetime.datetime.fromisoformat(meeting_date)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # 파싱 실패 시 현재 시간 반환
        return get_current_datetime_string()
