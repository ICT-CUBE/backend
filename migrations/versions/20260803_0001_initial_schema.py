"""Create the initial schema from docs/erd.md.

Revision ID: 20260803_0001
Revises:
Create Date: 2026-08-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260803_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _id() -> sa.Column:
    return sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True)


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def _soft_delete() -> sa.Column:
    return sa.Column("deleted_at", sa.DateTime(), nullable=True)


def _enum(*values: str, name: str, length: int) -> sa.Enum:
    return sa.Enum(
        *values,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=length,
    )


def _fk(
    name: str,
    target: str,
    *,
    nullable: bool = False,
    unique: bool = False,
    index: bool = True,
) -> sa.Column:
    return sa.Column(
        name,
        sa.BigInteger(),
        sa.ForeignKey(target),
        nullable=nullable,
        unique=unique,
        index=index and not unique,
    )


def _metadata() -> sa.MetaData:
    """Return a frozen schema snapshot for this migration revision."""
    metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)

    sa.Table(
        "users",
        metadata,
        _id(),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "login_provider",
            _enum("EMAIL", "GOOGLE", "APPLE", name="login_provider", length=20),
            nullable=False,
        ),
        sa.Column("provider_user_id", sa.String(255), nullable=True),
        sa.Column("nickname", sa.String(8), nullable=True),
        sa.Column("profile_character_img_code", sa.String(50), nullable=True),
        sa.Column("chat_violation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            _enum("ACTIVE", "WITHDRAWN", "SUSPENDED", name="user_status", length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "auth_sessions",
        metadata,
        _id(),
        _fk("user_id", "users.id"),
        sa.Column("token_jti", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "status",
            _enum("ACTIVE", "REVOKED", name="auth_session_status", length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("device_id", sa.String(255), nullable=True),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "notifications",
        metadata,
        _id(),
        _fk("user_id", "users.id"),
        sa.Column(
            "notification_type",
            _enum("ALL", "MISSION", "EVENT", "MARKET", name="notification_type", length=30),
            nullable=False,
        ),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("content", sa.String(500), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "sent_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        *_timestamps(),
    )
    sa.Table(
        "user_settings",
        metadata,
        _id(),
        _fk("user_id", "users.id", unique=True),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "new_conversation_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "affinity_change_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "daily_mission_refresh_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "trade_completed_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("trade_offer_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "community_comment_notice_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        *_timestamps(),
    )

    sa.Table(
        "cubes",
        metadata,
        _id(),
        sa.Column("serial_number", sa.String(100), nullable=False, unique=True),
        sa.Column("product_name", sa.String(150), nullable=False),
        sa.Column("ownership_code_hash", sa.String(255), nullable=False),
        sa.Column("artist_name", sa.String(20), nullable=False),
        sa.Column(
            "status",
            _enum(
                "UNREGISTERED",
                "OWNED",
                "TRADE_PENDING",
                "DISABLED",
                name="cube_status",
                length=20,
            ),
            nullable=False,
            server_default="UNREGISTERED",
        ),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "cube_verifications",
        metadata,
        _id(),
        _fk("user_id", "users.id"),
        _fk("cube_id", "cubes.id"),
        sa.Column(
            "verification_status",
            _enum(
                "PENDING",
                "SUCCESS",
                "FAILED",
                "EXPIRED",
                name="verification_status",
                length=20,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("code_expires_at", sa.DateTime(), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        *_timestamps(),
    )
    sa.Table(
        "cube_ownerships",
        metadata,
        _id(),
        _fk("user_id", "users.id"),
        _fk("cube_id", "cubes.id"),
        sa.Column("avatar_nickname", sa.String(30), nullable=True),
        sa.Column(
            "ownership_status",
            _enum("ACTIVE", "TRANSFERRED", "REVOKED", name="ownership_status", length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("is_last_accessed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acquired_at", sa.DateTime(), nullable=False),
        sa.Column("transferred_at", sa.DateTime(), nullable=True),
        *_timestamps(),
    )

    sa.Table(
        "reward_items",
        metadata,
        _id(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column(
            "reward_type",
            _enum(
                "AFFINITY_POINT",
                "CONVERSATION_COUNT",
                "COMMENT_TYPE",
                "SPECIAL_COMMENT",
                "AVATAR_FIRST_TALK",
                "BADGE",
                name="reward_type",
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("reward_count", sa.Integer(), nullable=False),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "levels",
        metadata,
        _id(),
        _fk("reward_item_id", "reward_items.id"),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("level_xp", sa.Integer(), nullable=False),
        sa.Column(
            "level_name",
            _enum("Intro", "Friend", "Close", "Special", name="level_name", length=30),
            nullable=False,
        ),
        *_timestamps(),
    )
    sa.Table(
        "affinities",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id", unique=True),
        _fk("level_id", "levels.id"),
        sa.Column("current_xp", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    sa.Table(
        "missions",
        metadata,
        _id(),
        _fk("reward_item_id", "reward_items.id"),
        sa.Column(
            "mission_type",
            _enum("DAILY", "EVENT", name="mission_type", length=20),
            nullable=False,
        ),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("mission_info", sa.String(500), nullable=True),
        sa.Column(
            "target_action",
            _enum(
                "HOME_VIEW",
                "CONVERSATION",
                "ALBUM_PLAY",
                "OPEN_GALLERY",
                "COMMUNITY_POST",
                "ALBUM_CONVERSATION",
                "PLAY_MUSIC_VIDEO",
                name="mission_target_action",
                length=50,
            ),
            nullable=False,
        ),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "mission_progresses",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        _fk("mission_id", "missions.id"),
        sa.Column("current_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            _enum(
                "IN_PROGRESS",
                "COMPLETED",
                "REWARDED",
                name="mission_progress_status",
                length=20,
            ),
            nullable=False,
            server_default="IN_PROGRESS",
        ),
        sa.Column("reward_claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "cube_ownership_id",
            "mission_id",
            name="uq_mission_progresses_ownership_mission",
        ),
    )
    sa.Table(
        "user_rewards",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        _fk("reward_item_id", "reward_items.id"),
        sa.Column(
            "acquired_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        *_timestamps(),
        sa.UniqueConstraint(
            "cube_ownership_id",
            "reward_item_id",
            name="uq_user_rewards_ownership_reward",
        ),
    )

    sa.Table(
        "albums",
        metadata,
        _id(),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("artist_name", sa.String(100), nullable=False),
        sa.Column("artist_company", sa.String(100), nullable=False),
        sa.Column("track_count", sa.Integer(), nullable=False),
        sa.Column("track_total_second", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_code", sa.String(500), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        *_timestamps(),
    )
    sa.Table(
        "stages",
        metadata,
        _id(),
        _fk("album_id", "albums.id"),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("video_code", sa.String(500), nullable=False),
        sa.Column(
            "video_type",
            _enum("MUSIC_VIDEO", "CONCERT_VIDEO", name="video_type", length=20),
            nullable=False,
        ),
        sa.Column("thumbnail_code", sa.String(500), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_title_video", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    sa.Table(
        "stage_sessions",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        _fk("stage_id", "stages.id"),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("last_position_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("viewed_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "view_mode",
            _enum("NORMAL", "AR", name="stage_view_mode", length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum(
                "PLAYING", "COMPLETED", "CANCELLED", name="stage_session_status", length=20
            ),
            nullable=False,
            server_default="PLAYING",
        ),
        *_timestamps(),
    )
    sa.Table(
        "stage_captures",
        metadata,
        _id(),
        _fk("stage_session_id", "stage_sessions.id"),
        sa.Column("stage_capture_img_code", sa.String(500), nullable=False),
        sa.Column("captured_position_seconds", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "tracks",
        metadata,
        _id(),
        _fk("album_id", "albums.id"),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("artist_name", sa.String(100), nullable=False),
        sa.Column("audio_code", sa.String(500), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("lyrics", sa.String(5000), nullable=False),
        sa.Column("track_number", sa.Integer(), nullable=False),
        sa.Column("is_title_track", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_timestamps(),
    )
    sa.Table(
        "track_sessions",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        _fk("track_id", "tracks.id"),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("last_position_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("viewed_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "play_mode",
            _enum("NORMAL", "SPECIAL", name="track_play_mode", length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum(
                "PLAYING", "COMPLETED", "CANCELLED", name="track_session_status", length=20
            ),
            nullable=False,
            server_default="PLAYING",
        ),
        *_timestamps(),
    )
    sa.Table(
        "track_captures",
        metadata,
        _id(),
        _fk("track_session_id", "track_sessions.id"),
        sa.Column("track_capture_img_code", sa.String(500), nullable=False),
        sa.Column("captured_position_seconds", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        *_timestamps(),
        _soft_delete(),
    )
    sa.Table(
        "album_images",
        metadata,
        _id(),
        _fk("album_id", "albums.id"),
        sa.Column("title", sa.String(150), nullable=True),
        sa.Column(
            "image_type",
            _enum(
                "ALBUM_IMAGE",
                "CONCERT_STILLCUT",
                "YEZUL_FRAME",
                name="album_image_type",
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("album_contents_img_code", sa.String(500), nullable=False),
        *_timestamps(),
    )

    sa.Table(
        "avatar_conversation_sessions",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        sa.Column(
            "conversation_type",
            _enum("TEXT", "VOICE", name="conversation_type", length=20),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("audio_code", sa.String(500), nullable=True),
        sa.Column("audio_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("conversation_title", sa.String(50), nullable=True),
        sa.Column(
            "status",
            _enum(
                "ACTIVE", "NOT_ACTIVE", name="conversation_session_status", length=20
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
        *_timestamps(),
    )
    sa.Table(
        "avatar_conversation_messages",
        metadata,
        _id(),
        _fk("conversation_session_id", "avatar_conversation_sessions.id"),
        sa.Column(
            "sender_type",
            _enum("USER", "AVATAR", name="conversation_sender_type", length=20),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("is_text_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "status",
            _enum("ALLOWED", "BLOCKED", name="conversation_message_status", length=20),
            nullable=False,
            server_default="ALLOWED",
        ),
        sa.Column(
            "violation_type",
            _enum(
                "PROFANITY", "SEXUAL", "THREAT", name="conversation_violation_type", length=20
            ),
            nullable=True,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        *_timestamps(),
    )
    sa.Table(
        "avatar_conversation_images",
        metadata,
        _id(),
        _fk("conversation_session_id", "avatar_conversation_sessions.id"),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("sent_image_code", sa.String(500), nullable=False),
        *_timestamps(),
    )
    sa.Table(
        "conversation_reports",
        metadata,
        _id(),
        _fk(
            "conversation_message_id",
            "avatar_conversation_messages.id",
            unique=True,
        ),
        sa.Column(
            "reason",
            _enum(
                "INCORRECT_PERSONA",
                "HALLUCINATION",
                "INAPPROPRIATE_EXPRESSION",
                "IMPERSONATION_OR_PRIVATE",
                name="conversation_report_reason",
                length=50,
            ),
            nullable=False,
        ),
        sa.Column("detail_reason", sa.String(500), nullable=True),
        *_timestamps(),
    )
    sa.Table(
        "avatar_interaction_sessions",
        metadata,
        _id(),
        _fk("cube_ownership_id", "cube_ownerships.id"),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            _enum("ACTIVE", "COMPLETED", name="avatar_interaction_status", length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        *_timestamps(),
    )
    sa.Table(
        "avatar_interaction_pictures",
        metadata,
        _id(),
        _fk("interaction_session_id", "avatar_interaction_sessions.id"),
        sa.Column("picture_img_code", sa.String(500), nullable=True),
        sa.Column("pictured_at", sa.DateTime(), nullable=True),
        *_timestamps(),
        _soft_delete(),
    )

    return metadata


def upgrade() -> None:
    """Create all v1 tables in foreign-key-safe order."""
    _metadata().create_all(bind=op.get_bind(), checkfirst=False)


def downgrade() -> None:
    """Drop all v1 tables in reverse foreign-key order."""
    _metadata().drop_all(bind=op.get_bind(), checkfirst=False)
