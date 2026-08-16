"""스테이지 재생 세션 생성·저장 로직."""

from datetime import datetime, timedelta, timezone
from typing import BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApiError
from app.models.cube import CubeOwnership
from app.models.enums import OwnershipStatus, StageSessionStatus
from app.models.stage import Stage, StageCapture, StageSession
from app.schemas.stage import (
    StageSessionCreateResponse,
    StageSessionEndStatus,
    StageSessionResponse,
    StageViewMode,
)
from app.services.blob_storage import normalize_image_content_type, upload_stage_capture

KOREA_TIMEZONE = timezone(timedelta(hours=9))


def create_stage_session(
    *,
    db: Session,
    current_user_id: int,
    stage_id: int,
    view_mode: StageViewMode,
) -> StageSessionCreateResponse:
    """활성 스테이지와 현재 사용자의 마지막 활성 소유권으로 세션을 만듭니다."""
    stage = db.scalar(
        select(Stage).where(Stage.id == stage_id, Stage.is_active.is_(True))
    )
    if stage is None:
        raise ApiError(
            status_code=404,
            code="STAGE_NOT_FOUND",
            message="스테이지 영상을 찾을 수 없습니다.",
        )

    # 소유권 행을 잠가 같은 사용자의 동시 생성 요청을 직렬화합니다.
    ownership = db.scalar(
        select(CubeOwnership)
        .where(
            CubeOwnership.user_id == current_user_id,
            CubeOwnership.ownership_status == OwnershipStatus.ACTIVE,
            CubeOwnership.is_last_accessed.is_(True),
        )
        .limit(1)
        .with_for_update()
    )
    if ownership is None:
        raise ApiError(
            status_code=404,
            code="CUBE_OWNERSHIP_NOT_FOUND",
            message="큐브 소유권 정보를 찾을 수 없습니다.",
        )

    stage_session = StageSession(
        cube_ownership_id=ownership.id,
        stage_id=stage.id,
        started_at=datetime.now(KOREA_TIMEZONE).replace(tzinfo=None),
        ended_at=None,
        last_position_seconds=0,
        viewed_seconds=0,
        view_mode=view_mode,
        status=StageSessionStatus.PLAYING,
    )
    try:
        db.add(stage_session)
        # INSERT를 실행해 DB가 만든 AUTO_INCREMENT id를 객체에 채웁니다.
        db.flush()
        stage_session_id = stage_session.id
        db.commit()
    except Exception:
        db.rollback()
        raise

    return StageSessionCreateResponse(
        stage_session=StageSessionResponse(id=stage_session_id, view_mode=view_mode)
    )


def save_stage_capture(
    *,
    db: Session,
    current_user_id: int,
    stage_session_id: int,
    image_file: BinaryIO,
    image_content_type: str | None,
    captured_position_seconds: int,
    captured_at: datetime,
) -> None:
    """현재 사용자의 세션에 속한 캡처를 Azure와 DB에 저장합니다."""
    # 세션 상태와 관람 모드는 프론트 흐름을 신뢰하고 검사하지 않습니다.
    stage_session = db.scalar(
        select(StageSession)
        .join(StageSession.cube_ownership)
        .where(
            StageSession.id == stage_session_id,
            CubeOwnership.user_id == current_user_id,
        )
        .limit(1)
    )
    if stage_session is None:
        raise ApiError(
            status_code=404,
            code="STAGE_SESSION_NOT_FOUND",
            message="스테이지 재생 세션을 찾을 수 없습니다.",
        )

    # 파일 용량은 제한하지 않고 합의한 이미지 Content-Type만 허용합니다.
    normalized_content_type = normalize_image_content_type(image_content_type)
    if normalized_content_type is None:
        raise ApiError(
            status_code=400,
            code="INVALID_REQUEST",
            message="요청값이 올바르지 않습니다.",
        )

    try:
        image_url = upload_stage_capture(
            file=image_file,
            content_type=normalized_content_type,
            user_id=current_user_id,
            stage_session_id=stage_session.id,
        )
    except Exception as exc:
        # DEBUG 설정과 무관하게 외부 저장소 오류를 공통 500 JSON으로 반환합니다.
        raise ApiError(
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="서버 내부 오류가 발생했습니다.",
        ) from exc
    capture = StageCapture(
        stage_session_id=stage_session.id,
        stage_capture_img_url=image_url,
        captured_position_seconds=captured_position_seconds,
        captured_at=captured_at,
        deleted_at=None,
    )
    try:
        db.add(capture)
        db.commit()
    except Exception:
        db.rollback()
        raise


def save_stage_session(
    *,
    db: Session,
    current_user_id: int,
    stage_session_id: int,
    end_status: StageSessionEndStatus,
    last_position_seconds: int,
    viewed_seconds: int,
) -> None:
    """현재 사용자의 PLAYING 세션을 종료 상태로 갱신합니다."""
    stage_session = db.scalar(
        select(StageSession)
        .join(StageSession.cube_ownership)
        .where(
            StageSession.id == stage_session_id,
            CubeOwnership.user_id == current_user_id,
        )
        .limit(1)
        .with_for_update()
    )

    if stage_session is None:
        raise ApiError(
            status_code=404,
            code="STAGE_SESSION_NOT_FOUND",
            message="스테이지 재생 세션을 찾을 수 없습니다.",
        )

    if stage_session.status != StageSessionStatus.PLAYING:
        db.rollback()
        raise ApiError(
            status_code=409,
            code="STAGE_SESSION_ALREADY_ENDED",
            message="이미 종료된 스테이지 재생 세션입니다.",
        )
    stage_session.status = StageSessionStatus(end_status.value)
    stage_session.last_position_seconds = last_position_seconds
    stage_session.viewed_seconds = viewed_seconds
    stage_session.ended_at = datetime.now(KOREA_TIMEZONE).replace(tzinfo=None)

    try:
        # 조회한 ORM 객체의 변경 사항은 commit 시 UPDATE로 반영됩니다.
        db.commit()
    except Exception:
        db.rollback()
        raise
