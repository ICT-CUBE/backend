"""커뮤니티 게시글 목록·상세 조회와 게시글 작성·삭제 로직."""

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, NoReturn

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session

from app.community.models import Comment, CommentLike, Post, PostLike, PostMedia
from app.community.schemas import (
    CommunityBoardFilter,
    CommunityCommentItemResponse,
    CommunityPaginationResponse,
    CommunityPostAuthorResponse,
    CommunityPostCreateResponse,
    CommunityPostDetailItemResponse,
    CommunityPostDetailResponse,
    CommunityPostItemResponse,
    CommunityPostsResponse,
)
from app.core.blob_storage import (
    normalize_image_content_type,
    upload_community_post_image,
)
from app.core.enums import BoardType, CommentStatus, PostStatus
from app.core.exceptions import ApiError
from app.core.search import LIKE_ESCAPE_CHARACTER, like_contains_pattern
from app.user.models import User

COMMUNITY_PAGE_SIZE = 20
KOREA_TIMEZONE = timezone(timedelta(hours=9))
POST_TITLE_MAX_LENGTH = 150
POST_IMAGE_MAX_COUNT = 5
# 삭제되지 않은 게시글·댓글로 취급하는 상태입니다.
VISIBLE_POST_STATUSES = (PostStatus.ACTIVE, PostStatus.REPORTED)
VISIBLE_COMMENT_STATUSES = (CommentStatus.ACTIVE, CommentStatus.REPORTED)


def get_community_posts(
    *,
    db: Session,
    current_user_id: int,
    board_type: CommunityBoardFilter,
    keyword: str | None,
    page: int,
    size: int,
) -> CommunityPostsResponse:
    """게시판 유형과 제목 검색어에 맞는 게시글을 최신순으로 한 페이지 조회합니다."""
    rows = db.execute(
        _select_visible_posts(
            current_user_id=current_user_id,
            board_type=board_type,
            keyword=keyword,
        )
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(page * size)
        .limit(size + 1)
    ).all()

    page_rows = rows[:size]
    return CommunityPostsResponse(
        posts=[
            CommunityPostItemResponse(
                id=post.id,
                board_type=post.board_type,
                title=post.title,
                content=post.content,
                author=CommunityPostAuthorResponse(
                    id=author.id,
                    nickname=author.nickname,
                    profile_image_url=author.profile_character_img_url,
                ),
                created_at=post.created_at,
                like_count=like_count,
                comment_count=comment_count,
                is_liked=bool(is_liked),
                is_mine=post.user_id == current_user_id,
            )
            for post, author, like_count, comment_count, is_liked in page_rows
        ],
        pagination=CommunityPaginationResponse(
            page=page,
            size=size,
            has_next=len(rows) > size,
        ),
    )


def _select_visible_posts(
    *,
    current_user_id: int,
    board_type: CommunityBoardFilter,
    keyword: str | None,
) -> Select[tuple[Post, User, int, int, bool]]:
    """삭제되지 않은 게시글과 작성자·좋아요·댓글 집계를 조회하는 select를 만듭니다."""
    comment_count = (
        select(func.count(Comment.id))
        .where(
            Comment.post_id == Post.id,
            Comment.status == CommentStatus.ACTIVE,
            Comment.deleted_at.is_(None),
        )
        .scalar_subquery()
    )
    statement = (
        select(
            Post,
            User,
            _post_like_count(),
            comment_count,
            _post_liked_by(current_user_id=current_user_id),
        )
        .join(User, User.id == Post.user_id)
        .where(
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
    )
    if board_type != CommunityBoardFilter.ALL:
        statement = statement.where(Post.board_type == BoardType(board_type.value))

    search_keyword = (keyword or "").strip()
    if not search_keyword:
        return statement
    return statement.where(
        Post.title.like(
            like_contains_pattern(search_keyword),
            escape=LIKE_ESCAPE_CHARACTER,
        )
    )


def get_community_post_detail(
    *,
    db: Session,
    current_user_id: int,
    post_id: int,
) -> CommunityPostDetailResponse:
    """삭제되지 않은 게시글의 본문·첨부 이미지·댓글을 조회합니다."""
    row = db.execute(
        select(
            Post,
            User,
            _post_like_count(),
            _post_liked_by(current_user_id=current_user_id),
        )
        .join(User, User.id == Post.user_id)
        .where(
            Post.id == post_id,
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
        .limit(1)
    ).first()
    if row is None:
        _raise_post_not_found()

    post, author, like_count, is_liked = row
    image_urls = list(
        db.scalars(
            select(PostMedia.post_image_url)
            .where(PostMedia.post_id == post.id)
            .order_by(PostMedia.id.asc())
        )
    )
    comments = _get_comments(db=db, current_user_id=current_user_id, post_id=post.id)

    return CommunityPostDetailResponse(
        post=CommunityPostDetailItemResponse(
            id=post.id,
            board_type=post.board_type,
            author=CommunityPostAuthorResponse(
                id=author.id,
                nickname=author.nickname,
                profile_image_url=author.profile_character_img_url,
            ),
            created_at=post.created_at,
            title=post.title,
            content=post.content,
            image_urls=image_urls,
            like_count=like_count,
            is_liked=bool(is_liked),
            comment_count=len(comments),
            is_mine=post.user_id == current_user_id,
            comments=comments,
        )
    )


def _get_comments(
    *,
    db: Session,
    current_user_id: int,
    post_id: int,
) -> list[CommunityCommentItemResponse]:
    """삭제되지 않은 댓글을 작성 시각 오름차순으로 조회합니다."""
    like_count = (
        select(func.count(CommentLike.id))
        .where(
            CommentLike.comment_id == Comment.id,
            CommentLike.is_liked.is_(True),
        )
        .scalar_subquery()
    )
    is_liked = (
        select(CommentLike.id)
        .where(
            CommentLike.comment_id == Comment.id,
            CommentLike.user_id == current_user_id,
            CommentLike.is_liked.is_(True),
        )
        .exists()
    )
    rows = db.execute(
        select(Comment, User, like_count, is_liked)
        .join(User, User.id == Comment.user_id)
        .where(
            Comment.post_id == post_id,
            Comment.status.in_(VISIBLE_COMMENT_STATUSES),
            Comment.deleted_at.is_(None),
        )
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    ).all()

    return [
        CommunityCommentItemResponse(
            id=comment.id,
            author=CommunityPostAuthorResponse(
                id=author.id,
                nickname=author.nickname,
                profile_image_url=author.profile_character_img_url,
            ),
            content=comment.content,
            created_at=comment.created_at,
            like_count=comment_like_count,
            is_liked=bool(comment_is_liked),
            is_mine=comment.user_id == current_user_id,
        )
        for comment, author, comment_like_count, comment_is_liked in rows
    ]


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


def create_community_post(
    *,
    db: Session,
    current_user_id: int,
    board_type: BoardType,
    title: str,
    content: str,
    images: Sequence[tuple[BinaryIO, str | None]],
) -> CommunityPostCreateResponse:
    """게시글을 저장하고 첨부 이미지를 업로드한 뒤 생성된 게시글 id를 반환합니다.

    `images`는 (파일, Content-Type) 순서쌍으로 전달받아 요청 순서대로 저장합니다.
    """
    stripped_title = title.strip()
    stripped_content = content.strip()
    if not stripped_title or len(stripped_title) > POST_TITLE_MAX_LENGTH:
        _raise_invalid_request()
    if not stripped_content:
        _raise_invalid_request()
    if len(images) > POST_IMAGE_MAX_COUNT:
        _raise_invalid_request()

    # 파일 용량은 제한하지 않고 합의한 이미지 Content-Type만 허용합니다.
    normalized_images: list[tuple[BinaryIO, str]] = []
    for image_file, content_type in images:
        normalized_content_type = normalize_image_content_type(content_type)
        if normalized_content_type is None:
            _raise_invalid_request()
        normalized_images.append((image_file, normalized_content_type))

    post = Post(
        user_id=current_user_id,
        board_type=board_type,
        title=stripped_title,
        content=stripped_content,
        status=PostStatus.ACTIVE,
        deleted_at=None,
    )
    try:
        db.add(post)
        # 이미지 Blob 경로에 게시글 id가 필요해 먼저 flush로 id를 발급받습니다.
        db.flush()
        post_id = post.id
        for image_file, normalized_content_type in normalized_images:
            db.add(
                PostMedia(
                    post_id=post_id,
                    post_image_url=_upload_post_image(
                        image_file=image_file,
                        content_type=normalized_content_type,
                        current_user_id=current_user_id,
                        post_id=post_id,
                    ),
                )
            )
        db.commit()
    except Exception:
        # Blob에 이미 올라간 이미지는 삭제하지 않고 DB만 롤백합니다.
        db.rollback()
        raise

    return CommunityPostCreateResponse(post_id=post_id)


def _upload_post_image(
    *,
    image_file: BinaryIO,
    content_type: str,
    current_user_id: int,
    post_id: int,
) -> str:
    """게시글 이미지를 업로드하고 실패는 공통 500으로 변환합니다."""
    try:
        return upload_community_post_image(
            file=image_file,
            content_type=content_type,
            user_id=current_user_id,
            post_id=post_id,
        )
    except Exception as exc:
        # DEBUG 설정과 무관하게 외부 저장소 오류를 공통 500 JSON으로 반환합니다.
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        ) from exc


def _raise_invalid_request() -> NoReturn:
    raise ApiError(
        status_code=400,
        code="INVALID_REQUEST",
        message="요청값이 올바르지 않습니다.",
    )


def delete_community_post(
    *,
    db: Session,
    current_user_id: int,
    post_id: int,
) -> None:
    """현재 사용자가 작성한 게시글을 소프트 삭제합니다."""
    post = db.scalar(
        select(Post)
        .where(
            Post.id == post_id,
            Post.user_id == current_user_id,
            Post.status.in_(VISIBLE_POST_STATUSES),
            Post.deleted_at.is_(None),
        )
        .limit(1)
        .with_for_update()
    )
    if post is None:
        _raise_post_not_found()

    # 첨부 이미지·댓글·좋아요는 그대로 두고 게시글만 삭제 상태로 바꿉니다.
    post.status = PostStatus.DELETED
    post.deleted_at = _kst_now_naive()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _kst_now_naive() -> datetime:
    """DB 저장 정책에 맞춰 한국시간 기준 timezone 없는 datetime을 반환합니다."""
    return datetime.now(KOREA_TIMEZONE).replace(tzinfo=None, microsecond=0)


def _raise_post_not_found() -> NoReturn:
    raise ApiError(
        status_code=404,
        code="POST_NOT_FOUND",
        message="게시글을 찾을 수 없습니다.",
    )
