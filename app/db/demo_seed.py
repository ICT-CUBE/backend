"""인증 없이 API를 실행하기 위한 데모 데이터를 중복 없이 생성합니다."""

import asyncio
from datetime import date, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionFactory, dispose_engine
from app.models.album import Album, Stage
from app.models.cube import Affinity, Cube, CubeOwnership
from app.models.enums import (
    CubeStatus,
    LevelName,
    LoginProvider,
    OwnershipStatus,
    RewardType,
    UserStatus,
    VideoType,
)
from app.models.reward import Level, RewardItem
from app.models.user import User

DEMO_REWARD_NAME = "DEMO_HOME_LEVEL_REWARD"
DEMO_CUBE_SERIAL_NUMBER = "DEMO-HOME-CUBE-001"
DEMO_ALBUM_TITLE = "DEMO ALBUM"
DEMO_STAGE_VIDEO_CODE = "DEMO-STAGE-VIDEO-001"


async def seed_demo_data() -> None:
    """데모 사용자와 홈 조회에 필요한 연관 데이터를 준비합니다."""
    settings = get_settings()
    if not settings.seed_demo_data:
        print("Demo data seed skipped: SEED_DEMO_DATA=false")
        return

    async with SessionFactory() as session, session.begin():
        user = (
            await session.execute(select(User).where(User.email == settings.demo_user_email))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=settings.demo_user_email,
                password_hash=None,
                login_provider=LoginProvider.EMAIL,
                nickname="데모사용자",
                profile_character_img_code="PROFILE_01",
                status=UserStatus.ACTIVE,
            )
            session.add(user)
            await session.flush()
        else:
            user.status = UserStatus.ACTIVE
            user.deleted_at = None
            user.nickname = "데모사용자"
            user.profile_character_img_code = "PROFILE_01"

        reward = (
            await session.execute(
                select(RewardItem).where(RewardItem.name == DEMO_REWARD_NAME)
            )
        ).scalar_one_or_none()
        if reward is None:
            reward = RewardItem(
                name=DEMO_REWARD_NAME,
                reward_type=RewardType.AFFINITY_POINT,
                description="홈 API 데모 데이터",
                reward_count=0,
            )
            session.add(reward)
            await session.flush()

        level = (
            await session.execute(
                select(Level)
                .where(Level.reward_item_id == reward.id, Level.level == 3)
                .limit(1)
            )
        ).scalar_one_or_none()
        if level is None:
            level = Level(
                reward_item_id=reward.id,
                level=3,
                level_xp=2000,
                level_name=LevelName.CLOSE,
            )
            session.add(level)
            await session.flush()

        cube = (
            await session.execute(
                select(Cube).where(Cube.serial_number == DEMO_CUBE_SERIAL_NUMBER)
            )
        ).scalar_one_or_none()
        if cube is None:
            cube = Cube(
                serial_number=DEMO_CUBE_SERIAL_NUMBER,
                product_name="JENNIE CUBE",
                ownership_code_hash="DEMO_DATA_NOT_FOR_AUTHENTICATION",
                artist_name="JENNIE",
                status=CubeStatus.OWNED,
            )
            session.add(cube)
            await session.flush()
        else:
            cube.status = CubeStatus.OWNED

        ownership = (
            await session.execute(
                select(CubeOwnership)
                .where(
                    CubeOwnership.user_id == user.id,
                    CubeOwnership.cube_id == cube.id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if ownership is None:
            ownership = CubeOwnership(
                user_id=user.id,
                cube_id=cube.id,
                avatar_nickname="젠득이",
                ownership_status=OwnershipStatus.ACTIVE,
                is_last_accessed=True,
                acquired_at=datetime(2026, 3, 19, 10, 30),
            )
            session.add(ownership)
            await session.flush()
        else:
            ownership.avatar_nickname = "젠득이"
            ownership.ownership_status = OwnershipStatus.ACTIVE
            ownership.is_last_accessed = True

        affinity = (
            await session.execute(
                select(Affinity).where(Affinity.cube_ownership_id == ownership.id)
            )
        ).scalar_one_or_none()
        if affinity is None:
            affinity = Affinity(cube_ownership_id=ownership.id, level_id=level.id)
            session.add(affinity)
        affinity.level_id = level.id
        affinity.current_xp = 1245

        album = (
            await session.execute(
                select(Album)
                .where(Album.title == DEMO_ALBUM_TITLE, Album.artist_name == "JENNIE")
                .limit(1)
            )
        ).scalar_one_or_none()
        if album is None:
            album = Album(
                title=DEMO_ALBUM_TITLE,
                artist_name="JENNIE",
                artist_company="OA ENTERTAINMENT",
                track_count=0,
                track_total_second=0,
                description="스테이지 API 데모 앨범",
                cover_image_code="DEMO-ALBUM-COVER-001",
                release_date=date(2025, 1, 1),
            )
            session.add(album)
            await session.flush()

        stage = (
            await session.execute(
                select(Stage).where(Stage.video_code == DEMO_STAGE_VIDEO_CODE).limit(1)
            )
        ).scalar_one_or_none()
        if stage is None:
            stage = Stage(
                album_id=album.id,
                title="DEMO STAGE",
                description="스테이지 재생 세션 생성 API 데모 영상",
                video_code=DEMO_STAGE_VIDEO_CODE,
                video_type=VideoType.MUSIC_VIDEO,
                thumbnail_code="DEMO-STAGE-THUMBNAIL-001",
                duration_seconds=180,
                recorded_at=datetime(2025, 1, 1, 12, 0),
                is_active=True,
                is_title_video=True,
            )
            session.add(stage)
            await session.flush()
        else:
            stage.is_active = True

        print(
            f"Demo data ready: user_id={user.id}, email={user.email}, stage_id={stage.id}"
        )


async def main() -> None:
    try:
        await seed_demo_data()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
