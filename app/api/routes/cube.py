"""큐브 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.cube import CubeVerificationRequest, CubeVerificationResponse
from app.services.cube import verify_cube_code

router = APIRouter()


@router.post(
    "/verification",
    response_model=CubeVerificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="큐브 코드 인증",
    description="큐브 id와 4자리 인증번호를 확인하고 성공 시 큐브 소유권을 생성합니다.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "큐브 인증번호가 올바르지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "INVALID_CUBE_CODE",
                        "message": "큐브 인증번호가 올바르지 않습니다.",
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브가 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_NOT_FOUND",
                        "message": "큐브 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "소유권을 등록할 수 없는 큐브",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_NOT_REGISTRABLE",
                        "message": "소유권을 등록할 수 없는 큐브입니다.",
                    }
                }
            },
        },
    },
)
def create_cube_verification(
    body: CubeVerificationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> CubeVerificationResponse:
    """POST /api/v1/cubes/verification"""
    return verify_cube_code(
        db=db,
        current_user_id=current_user_id,
        body=body,
    )
