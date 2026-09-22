"""마이페이지 프로필·활동 요약·내가 쓴 글·댓글 단 글 조회와 프로필 수정 로직."""

from typing import NoReturn

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session

from app.community.models import Comment, Post, PostLike
from app.core.enums import CommentStatus, PostStatus
from app.core.exceptions import ApiError
from app.mypage.schemas import (
    MyPageActivityResponse,
    MyPagePaginationResponse,
    MyPagePostItemResponse,
    MyPagePostsResponse,
    MyPageResponse,
    MyPageUserResponse,
)
from app.user.models import User
from app.user.profile import ProfileCharacterCode, to_profile_image_url

MY_POSTS_PAGE_SIZE = 20
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
        _raise_user_missing()

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


def get_my_posts(
    *,
    db: Session,
    current_user_id: int,
    page: int,
    size: int,
) -> MyPagePostsResponse:
    """현재 사용자가 작성한 삭제되지 않은 게시글을 최신순으로 한 페이지 조회합니다."""
    statement = _select_visible_posts(current_user_id=current_user_id).where(
        Post.user_id == current_user_id
    )
    return _get_posts_page(db=db, statement=statement, page=page, size=size)


def get_my_commented_posts(
    *,
    db: Session,
    current_user_id: int,
    page: int,
    size: int,
) -> MyPagePostsResponse:
    """현재 사용자가 댓글을 단 서로 다른 게시글을 최신순으로 한 페이지 조회합니다."""
    # JOIN 대신 EXISTS로 걸러야 댓글을 여러 개 단 게시글도 한 번만 조회됩니다.
    has_my_comment = (
        select(Comment.id)
        .where(
            Comment.post_id == Post.id,
            Comment.user_id == current_user_id,
            Comment.status.in_(VISIBLE_COMMENT_STATUSES),
            Comment.deleted_at.is_(None),
        )
        .exists()
    )
    statement = _select_visible_posts(current_user_id=current_user_id).where(
        has_my_comment
    )
    return _get_posts_page(db=db, statement=statement, page=page, size=size)


def _select_visible_posts(
    *, current_user_id: int
) -> Select[tuple[Post, str | None, int, int, bool]]:
    """삭제되지 않은 게시글과 작성자 닉네임·좋아요·댓글 수를 조회하는 select입니다."""
    return (
        select(
            Post,
            User.nickname,
            _post_like_count(),
            _active_comment_count(),
            _post_liked_by(current_user_id=current_user_id),
        )
        .join(User, User.id == Post.user_id)
        .where(
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
    )


def _get_posts_page(
    *,
    db: Session,
    statement: Select[tuple[Post, str | None, int, int, bool]],
    page: int,
    size: int,
) -> MyPagePostsResponse:
    """게시글 select를 최신순으로 한 페이지 조회해 응답으로 변환합니다."""
    rows = db.execute(
        statement.order_by(Post.created_at.desc(), Post.id.desc())
        .offset(page * size)
        # 다음 페이지 존재 여부를 알기 위해 한 건 더 조회합니다.
        .limit(size + 1)
    ).all()

    page_rows = rows[:size]
    return MyPagePostsResponse(
        posts=[
            MyPagePostItemResponse(
                id=post.id,
                board_type=post.board_type,
                title=post.title,
                content=post.content,
                author_nickname=author_nickname,
                created_at=post.created_at,
                like_count=like_count,
                comment_count=comment_count,
                is_liked=bool(is_liked),
            )
            for post, author_nickname, like_count, comment_count, is_liked in page_rows
        ],
        pagination=MyPagePaginationResponse(
            page=page,
            size=size,
            has_next=len(rows) > size,
        ),
    )


def _post_like_count() -> ColumnElement[int]:
    """게시글의 현재 좋아요 수를 세는 상관 서브쿼리를 만듭니다."""
    return (
        select(func.count(PostLike.id))
        .where(
            PostLike.post_id == Post.id,
            PostLike.is_liked.is_(True),
        )
        .scalar_subquery()
    )


def _active_comment_count() -> ColumnElement[int]:
    """게시글의 삭제되지 않은 ACTIVE 댓글 수를 세는 상관 서브쿼리를 만듭니다."""
    return (
        select(func.count(Comment.id))
        .where(
            Comment.post_id == Post.id,
            Comment.status == CommentStatus.ACTIVE,
            Comment.deleted_at.is_(None),
        )
        .scalar_subquery()
    )


def _post_liked_by(*, current_user_id: int) -> ColumnElement[bool]:
    """현재 사용자가 게시글에 좋아요를 눌렀는지 확인하는 상관 서브쿼리를 만듭니다."""
    return (
        select(PostLike.id)
        .where(
            PostLike.post_id == Post.id,
            PostLike.user_id == current_user_id,
            PostLike.is_liked.is_(True),
        )
        .exists()
    )


def update_my_profile(
    *,
    db: Session,
    current_user_id: int,
    nickname: str,
    profile_character_code: ProfileCharacterCode,
) -> None:
    """현재 사용자의 닉네임과 프로필 캐릭터 이미지 URL을 함께 수정합니다."""
    user = db.scalar(
        select(User)
        .where(User.id == current_user_id)
        .limit(1)
    )
    if user is None:
        _raise_user_missing()

    user.nickname = nickname
    user.profile_character_img_url = to_profile_image_url(profile_character_code)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _raise_user_missing() -> NoReturn:
    # 인증 단계에서 활성 사용자를 이미 확인하므로 여기서는 공통 500으로 처리합니다.
    raise ApiError(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="서버 내부 오류가 발생했습니다.",
    )
