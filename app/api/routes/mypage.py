"""마이페이지 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.mypage import MyPageResponse
from app.services.mypage import get_my_page

router = APIRouter()


@router.get(
    "",
    response_model=MyPageResponse,
    summary="마이페이지 조회",
    description=(
        "현재 사용자의 프로필과 작성한 게시글 수, 댓글을 작성한 게시글 수를 조회합니다."
    ),
)
def read_my_page(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MyPageResponse:
    """GET /api/v1/users/me"""
    return get_my_page(db=db, current_user_id=current_user_id)
