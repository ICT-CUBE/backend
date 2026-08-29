"""마이페이지 프로필과 커뮤니티 활동 요약 조회 로직."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.community import Comment, Post
from app.models.enums import CommentStatus, PostStatus
from app.models.user import User
from app.schemas.mypage import (
    MyPageActivityResponse,
    MyPageResponse,
    MyPageUserResponse,
)

# 삭제되지 않은 게시글·댓글로 취급하는 상태입니다.
VISIBLE_POST_STATUSES = (PostStatus.ACTIVE, PostStatus.REPORTED)
VISIBLE_COMMENT_STATUSES = (CommentStatus.ACTIVE, CommentStatus.REPORTED)


def get_my_page(*, db: Session, current_user_id: int) -> MyPageResponse:
    """현재 사용자의 프로필과 작성·댓글 활동 수를 조회합니다."""
    user = db.scalar(
        select(User)
        .where(User.id == current_user_id)
        .limit(1)
    )
    if user is None:
        # 인증 단계에서 활성 사용자를 이미 확인하므로 여기서는 공통 500으로 처리합니다.
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        )

    return MyPageResponse(
        user=MyPageUserResponse(
            nickname=user.nickname,
            email=user.email,
            profile_character_img_url=user.profile_character_img_url,
        ),
        activity=MyPageActivityResponse(
            written_post_count=_get_written_post_count(
                db=db,
                current_user_id=current_user_id,
            ),
            commented_post_count=_get_commented_post_count(
                db=db,
                current_user_id=current_user_id,
            ),
        ),
    )


def _get_written_post_count(*, db: Session, current_user_id: int) -> int:
    """현재 사용자가 작성한 삭제되지 않은 게시글 수를 셉니다."""
    written_post_count = db.scalar(
        select(func.count(Post.id)).where(
            Post.user_id == current_user_id,
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
    )
    return int(written_post_count or 0)


def _get_commented_post_count(*, db: Session, current_user_id: int) -> int:
    """현재 사용자가 댓글을 단 서로 다른 게시글 수를 셉니다."""
    commented_post_count = db.scalar(
        select(func.count(Comment.post_id.distinct()))
        .join(Post, Post.id == Comment.post_id)
        .where(
            Comment.user_id == current_user_id,
            Comment.status.in_(VISIBLE_COMMENT_STATUSES),
            Comment.deleted_at.is_(None),
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
    )
    return int(commented_post_count or 0)
