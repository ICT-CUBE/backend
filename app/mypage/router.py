"""마이페이지 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse
from app.mypage.schemas import (
    MyPagePostsResponse,
    MyPageProfileUpdateRequest,
    MyPageResponse,
)
from app.mypage.service import (
    MY_POSTS_PAGE_SIZE,
    get_my_commented_posts,
    get_my_page,
    get_my_posts,
    update_my_profile,
)

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


@router.patch(
    "/profile",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="사용자 프로필 수정",
    description=(
        "현재 사용자의 닉네임과 프로필 캐릭터를 함께 변경합니다. "
        "프로필 캐릭터 코드는 이미지 URL로 변환해 저장합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "필수 필드가 없거나, 닉네임이 1~20자가 아니거나, "
                "허용하지 않는 프로필 캐릭터 코드"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def update_profile(
    body: MyPageProfileUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """PATCH /api/v1/users/me/profile"""
    update_my_profile(
        db=db,
        current_user_id=current_user_id,
        nickname=body.nickname,
        profile_character_code=body.profile_character_code,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/posts",
    response_model=MyPagePostsResponse,
    summary="내가 쓴 글 조회",
    description=(
        "현재 사용자가 작성한 삭제되지 않은 게시글을 작성 시각 내림차순으로 "
        "요청한 size 단위로 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "page가 0보다 작거나 size가 1보다 작음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def read_my_posts(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = MY_POSTS_PAGE_SIZE,
) -> MyPagePostsResponse:
    """GET /api/v1/users/me/posts"""
    return get_my_posts(
        db=db,
        current_user_id=current_user_id,
        page=page,
        size=size,
    )


@router.get(
    "/commented-posts",
    response_model=MyPagePostsResponse,
    summary="댓글 단 글 조회",
    description=(
        "현재 사용자가 삭제되지 않은 댓글을 작성한 서로 다른 게시글을 "
        "게시글 작성 시각 내림차순으로 요청한 size 단위로 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "page가 0보다 작거나 size가 1보다 작음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_REQUEST",
                        "message": "요청값이 올바르지 않습니다.",
                    }
                }
            },
        },
    },
)
def read_my_commented_posts(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = MY_POSTS_PAGE_SIZE,
) -> MyPagePostsResponse:
    """GET /api/v1/users/me/commented-posts"""
    return get_my_commented_posts(
        db=db,
        current_user_id=current_user_id,
        page=page,
        size=size,
    )
