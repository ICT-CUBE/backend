"""모든 SQLAlchemy 모델이 상속할 선언형 베이스."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """새 모델은 이 클래스를 상속해야 Alembic이 변경을 감지합니다."""

