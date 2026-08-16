"""갤러리 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.gallery import (
    GalleryArExperienceResponse,
    GalleryArExperienceSourceType,
    GalleryCategory,
    GalleryDeletableSourceType,
    GalleryResponse,
)
from app.services.gallery import (
    GALLERY_PAGE_SIZE,
    delete_gallery_item,
    get_gallery,
    get_gallery_ar_experience,
)

router = APIRouter()


@router.get(
    "/gallery",
    response_model=GalleryResponse,
    summary="갤러리 조회",
    description=(
        "앨범 이미지 전체와 현재 사용자의 활성 소유권에 속한 캡처 이미지를 "
        "요청한 size 단위로 조회합니다."
    ),
)
def read_gallery(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    category: Annotated[GalleryCategory, Query()] = GalleryCategory.ALL,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1)] = GALLERY_PAGE_SIZE,
) -> GalleryResponse:
    """GET /api/v1/users/me/gallery"""
    return get_gallery(
        db=db,
        current_user_id=current_user_id,
        category=category,
        page=page,
        size=size,
    )


@router.get(
    "/gallery/{sourceType}/{galleryItemId}/ar-experience",
    response_model=GalleryArExperienceResponse,
    response_model_exclude_none=True,
    summary="AR에서 다시 경험하기",
    description=(
        "현재 사용자의 활성 소유권에 속한 스테이지·트랙 캡처를 기준으로 "
        "AR 재경험에 필요한 원본 콘텐츠와 시작 위치를 조회합니다."
    ),
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "지원하지 않는 sourceType 또는 잘못된 Path 값",
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
            "description": "캡처가 없거나 현재 사용자의 활성 소유권 항목이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "GALLERY_ITEM_NOT_FOUND",
                        "message": "갤러리 항목을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_gallery_ar_experience(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    source_type: Annotated[
        GalleryArExperienceSourceType,
        Path(alias="sourceType"),
    ],
    gallery_item_id: Annotated[int, Path(alias="galleryItemId", ge=1)],
) -> GalleryArExperienceResponse:
    """GET /api/v1/users/me/gallery/{sourceType}/{galleryItemId}/ar-experience"""
    return get_gallery_ar_experience(
        db=db,
        current_user_id=current_user_id,
        source_type=source_type,
        gallery_item_id=gallery_item_id,
    )


@router.delete(
    "/gallery/{sourceType}/{galleryItemId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="갤러리 항목 삭제",
    description=(
        "현재 사용자의 활성 소유권에 속한 사용자 캡처 이미지를 "
        "deleted_at 저장 방식으로 소프트 딜리트합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "삭제할 캡처가 없거나 현재 사용자의 활성 소유권 항목이 아님",
            "content": {
                "application/json": {
                    "example": {
                        "code": "GALLERY_ITEM_NOT_FOUND",
                        "message": "삭제할 갤러리 항목을 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def delete_gallery_capture(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    source_type: Annotated[
        GalleryDeletableSourceType,
        Path(alias="sourceType"),
    ],
    gallery_item_id: Annotated[int, Path(alias="galleryItemId", ge=1)],
) -> Response:
    """DELETE /api/v1/users/me/gallery/{sourceType}/{galleryItemId}"""
    delete_gallery_item(
        db=db,
        current_user_id=current_user_id,
        source_type=source_type,
        gallery_item_id=gallery_item_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
