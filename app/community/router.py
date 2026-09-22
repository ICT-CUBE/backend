"""커뮤니티 도메인 API 라우터."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Path,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.community.schemas import (
    CommunityBoardFilter,
    CommunityCommentCreateRequest,
    CommunityCommentCreateResponse,
    CommunityCommentLikeResponse,
    CommunityPostCreateResponse,
    CommunityPostDetailResponse,
    CommunityPostLikeResponse,
    CommunityPostsResponse,
)
from app.community.service import (
    COMMUNITY_PAGE_SIZE,
    create_community_comment,
    create_community_post,
    delete_community_comment,
    delete_community_post,
    get_community_post_detail,
    get_community_posts,
    toggle_community_comment_like,
    toggle_community_post_like,
)
from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.enums import BoardType
from app.core.schemas import ErrorResponse

router = APIRouter()


@router.get(
    "/posts",
    response_model=CommunityPostsResponse,
    summary="커뮤니티 조회",
    description=(
        "게시판 유형과 제목 검색어에 맞는 커뮤니티 게시글을 작성 시각 내림차순으로 "
        "요청한 size 단위로 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "지원하지 않는 boardType 또는 잘못된 page·size 값",
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
def read_community_posts(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    board_type: Annotated[
        CommunityBoardFilter,
        Query(alias="boardType"),
    ] = CommunityBoardFilter.ALL,
    keyword: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = COMMUNITY_PAGE_SIZE,
) -> CommunityPostsResponse:
    """GET /api/v1/community/posts"""
    return get_community_posts(
        db=db,
        current_user_id=current_user_id,
        board_type=board_type,
        keyword=keyword,
        page=page,
        size=size,
    )


@router.get(
    "/posts/{postId}",
    response_model=CommunityPostDetailResponse,
    summary="커뮤니티 상세 조회",
    description=(
        "삭제되지 않은 게시글의 본문과 첨부 이미지, 삭제되지 않은 댓글 전체를 "
        "댓글 작성 시각 오름차순으로 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "게시글이 존재하지 않거나 삭제됨",
            "content": {
                "application/json": {
                    "example": {
                        "code": "POST_NOT_FOUND",
                        "message": "게시글을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_community_post_detail(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> CommunityPostDetailResponse:
    """GET /api/v1/community/posts/{postId}"""
    return get_community_post_detail(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
    )


@router.post(
    "/posts",
    response_model=CommunityPostCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 게시글 작성",
    description=(
        "현재 사용자를 작성자로 게시글을 저장하고, 첨부 이미지를 Azure Blob "
        "Storage에 업로드한 뒤 이미지 URL을 DB에 저장합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "필수 multipart 필드가 없거나, 제목·내용이 비었거나, "
                "제목이 150자를 넘거나, 이미지가 5장을 넘거나, "
                "지원하지 않는 이미지 형식"
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
def create_post(
    board_type: Annotated[BoardType, Form(alias="boardType")],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    images: Annotated[
        list[UploadFile] | None,
        File(description="JPEG, PNG 또는 WebP 이미지 최대 5장"),
    ] = None,
) -> CommunityPostCreateResponse:
    """POST /api/v1/community/posts"""
    return create_community_post(
        db=db,
        current_user_id=current_user_id,
        board_type=board_type,
        title=title,
        content=content,
        images=[(image.file, image.content_type) for image in images or []],
    )


@router.delete(
    "/posts/{postId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="커뮤니티 게시글 삭제",
    description="현재 사용자가 작성한 게시글을 소프트 딜리트합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "게시글이 없거나 이미 삭제됐거나 현재 사용자의 게시글이 아님"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "code": "POST_NOT_FOUND",
                        "message": "게시글을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def delete_post(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """DELETE /api/v1/community/posts/{postId}"""
    delete_community_post(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/posts/{postId}/like",
    response_model=CommunityPostLikeResponse,
    summary="커뮤니티 게시글 좋아요 토글",
    description=(
        "현재 사용자의 게시글 좋아요 상태를 반전하고, 반전 이후의 좋아요 상태와 "
        "전체 좋아요 수를 반환합니다. 호출할 때마다 상태가 바뀝니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "게시글이 존재하지 않거나 삭제됨",
            "content": {
                "application/json": {
                    "example": {
                        "code": "POST_NOT_FOUND",
                        "message": "게시글을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def update_post_like(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> CommunityPostLikeResponse:
    """PATCH /api/v1/community/posts/{postId}/like"""
    return toggle_community_post_like(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
    )


@router.post(
    "/posts/{postId}/comments",
    response_model=CommunityCommentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 댓글 작성",
    description=(
        "현재 사용자를 작성자로 댓글을 저장하고 생성된 댓글 정보를 반환합니다. "
        "대댓글과 이미지 첨부는 지원하지 않습니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "content 필드가 없거나, 공백을 제거한 내용이 비었거나 1,000자를 넘음"
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
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "게시글이 존재하지 않거나 삭제됨",
            "content": {
                "application/json": {
                    "example": {
                        "code": "POST_NOT_FOUND",
                        "message": "게시글을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def create_comment(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    body: CommunityCommentCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> CommunityCommentCreateResponse:
    """POST /api/v1/community/posts/{postId}/comments"""
    return create_community_comment(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
        content=body.content,
    )


@router.delete(
    "/posts/{postId}/comments/{commentId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="커뮤니티 댓글 삭제",
    description="현재 사용자가 작성한 댓글을 소프트 딜리트합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "게시글 또는 삭제 가능한 본인 댓글이 존재하지 않음",
            "content": {
                "application/json": {
                    "examples": {
                        "postNotFound": {
                            "summary": "게시글 없음 또는 삭제됨",
                            "value": {
                                "code": "POST_NOT_FOUND",
                                "message": "게시글을 찾을 수 없습니다.",
                            },
                        },
                        "commentNotFound": {
                            "summary": "댓글 없음, 이미 삭제됨 또는 타인의 댓글",
                            "value": {
                                "code": "COMMENT_NOT_FOUND",
                                "message": "댓글을 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def delete_comment(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    comment_id: Annotated[int, Path(alias="commentId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> Response:
    """DELETE /api/v1/community/posts/{postId}/comments/{commentId}"""
    delete_community_comment(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
        comment_id=comment_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/posts/{postId}/comments/{commentId}/like",
    response_model=CommunityCommentLikeResponse,
    summary="커뮤니티 댓글 좋아요 토글",
    description=(
        "현재 사용자의 댓글 좋아요 상태를 반전하고, 반전 이후의 좋아요 상태와 "
        "해당 댓글의 전체 좋아요 수를 반환합니다. 호출할 때마다 상태가 바뀝니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "게시글 또는 좋아요를 처리할 수 있는 댓글이 존재하지 않음",
            "content": {
                "application/json": {
                    "examples": {
                        "postNotFound": {
                            "summary": "게시글 없음 또는 삭제됨",
                            "value": {
                                "code": "POST_NOT_FOUND",
                                "message": "게시글을 찾을 수 없습니다.",
                            },
                        },
                        "commentNotFound": {
                            "summary": "댓글 없음, 삭제됨 또는 다른 게시글의 댓글",
                            "value": {
                                "code": "COMMENT_NOT_FOUND",
                                "message": "댓글을 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def update_comment_like(
    post_id: Annotated[int, Path(alias="postId", ge=1)],
    comment_id: Annotated[int, Path(alias="commentId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> CommunityCommentLikeResponse:
    """PATCH /api/v1/community/posts/{postId}/comments/{commentId}/like"""
    return toggle_community_comment_like(
        db=db,
        current_user_id=current_user_id,
        post_id=post_id,
        comment_id=comment_id,
    )
