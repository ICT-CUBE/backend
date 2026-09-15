"""여러 도메인이 함께 쓰는 LIKE 검색 패턴 헬퍼."""

# 검색 키워드에 들어온 LIKE 와일드카드를 문자 그대로 비교하기 위한 이스케이프 문자입니다.
LIKE_ESCAPE_CHARACTER = "\\"


def like_contains_pattern(keyword: str) -> str:
    """LIKE 와일드카드를 이스케이프해 키워드를 그대로 포함 검색하는 패턴을 만듭니다."""
    escaped_keyword = keyword
    for character in (LIKE_ESCAPE_CHARACTER, "%", "_"):
        escaped_keyword = escaped_keyword.replace(
            character, LIKE_ESCAPE_CHARACTER + character
        )
    return f"%{escaped_keyword}%"
