"""친밀도 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.affinity.schemas import AffinityDetailResponse
from app.affinity.service import get_affinity
from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse

router = APIRouter()


@router.get(
    "/affinity",
    response_model=AffinityDetailResponse,
    summary="친밀도 상세 조회",
    description=(
        "현재 사용자의 친밀도 진행 상황, 현재·다음 레벨 보상, 오늘의 활동과 "
        "전체 레벨 정보를 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권 또는 친밀도 정보가 없음",
            "content": {
                "application/json": {
                    "examples": {
                        "cubeOwnershipNotFound": {
                            "summary": "큐브 소유권 없음",
                            "value": {
                                "code": "CUBE_OWNERSHIP_NOT_FOUND",
                                "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                            },
                        },
                        "cubeAffinityNotFound": {
                            "summary": "친밀도 정보 없음",
                            "value": {
                                "code": "CUBE_AFFINITY_NOT_FOUND",
                                "message": "큐브 친밀도 정보를 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_affinity(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> AffinityDetailResponse:
    """GET /api/v1/users/me/affinity"""
    return get_affinity(db=db, current_user_id=current_user_id)
