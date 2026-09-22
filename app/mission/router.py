"""미션 도메인 API 라우터."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.core.schemas import ErrorResponse
from app.mission.schemas import (
    MissionDailyDetailResponse,
    MissionListResponse,
    MissionRewardClaimRequest,
    MissionRewardClaimResponse,
)
from app.mission.service import (
    claim_mission_reward,
    get_daily_mission,
    get_missions,
)

router = APIRouter()


@router.get(
    "/missions",
    response_model=MissionListResponse,
    summary="미션 목록 조회",
    description="현재 사용자의 미션 화면 정보를 조회합니다.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "활성화된 마지막 접근 큐브 소유권이 존재하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "CUBE_OWNERSHIP_NOT_FOUND",
                        "message": "큐브 소유권 정보를 찾을 수 없습니다.",
                    }
                }
            },
        },
    },
)
def read_missions(
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MissionListResponse:
    """GET /api/v1/users/me/missions"""
    return get_missions(db=db, current_user_id=current_user_id)


@router.get(
    "/daily-missions/{missionId}",
    response_model=MissionDailyDetailResponse,
    summary="데일리 미션 상세 조회",
    description=(
        "현재 사용자의 활성 마지막 접근 큐브 소유권을 기준으로 활성 데일리 미션의 "
        "안내 문구와 연결된 보상 아이템을 조회합니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권 또는 조회 가능한 데일리 미션이 존재하지 않음",
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
                        "dailyMissionNotFound": {
                            "summary": "데일리 미션 없음 또는 보상 아이템 무효",
                            "value": {
                                "code": "DAILY_MISSION_NOT_FOUND",
                                "message": "데일리 미션 정보를 찾을 수 없습니다.",
                            },
                        },
                    }
                }
            },
        },
    },
)
def read_daily_mission(
    mission_id: Annotated[int, Path(alias="missionId", ge=1)],
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MissionDailyDetailResponse:
    """GET /api/v1/users/me/daily-missions/{missionId}"""
    return get_daily_mission(
        db=db,
        current_user_id=current_user_id,
        mission_id=mission_id,
    )


@router.post(
    "/missions/{missionId}/rewards",
    response_model=MissionRewardClaimResponse,
    summary="미션 보상 수령",
    description=(
        "완료한 미션의 보상을 현재 사용자의 활성 마지막 접근 큐브 소유권에 지급합니다. "
        "친밀도 포인트로 레벨이 오르면 도달한 레벨의 보상도 함께 지급하고 "
        "최종 레벨을 반환합니다. 중복 수령을 검사하지 않습니다."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "큐브 소유권, 수령 가능한 미션 또는 친밀도 정보가 없음",
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
                        "missionNotFound": {
                            "summary": "미션 없음, 유형 불일치 또는 보상 아이템 무효",
                            "value": {
                                "code": "MISSION_NOT_FOUND",
                                "message": "미션 정보를 찾을 수 없습니다.",
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
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "미션 진행 정보가 없거나 아직 완료하지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "code": "MISSION_NOT_COMPLETED",
                        "message": "완료되지 않은 미션입니다.",
                    }
                }
            },
        },
    },
)
def create_mission_reward(
    mission_id: Annotated[int, Path(alias="missionId", ge=1)],
    body: MissionRewardClaimRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> MissionRewardClaimResponse:
    """POST /api/v1/users/me/missions/{missionId}/rewards"""
    return claim_mission_reward(
        db=db,
        current_user_id=current_user_id,
        mission_id=mission_id,
        mission_type=body.mission_type,
    )
