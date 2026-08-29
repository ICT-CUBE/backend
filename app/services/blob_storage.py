"""Azure Blob Storage 파일 업로드 기능."""

from typing import BinaryIO
from uuid import uuid4

from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import get_settings

IMAGE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
AUDIO_EXTENSIONS = {
    "audio/mp4": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/webm": "webm",
    "audio/x-m4a": "m4a",
}


def normalize_image_content_type(content_type: str | None) -> str | None:
    """지원하는 이미지 Content-Type을 비교 가능한 소문자 값으로 정규화합니다."""
    if content_type is None:
        return None
    normalized_content_type = content_type.lower()
    if normalized_content_type not in IMAGE_EXTENSIONS:
        return None
    return normalized_content_type


def normalize_audio_content_type(content_type: str | None) -> str | None:
    """지원하는 오디오 Content-Type을 비교 가능한 소문자 값으로 정규화합니다."""
    if content_type is None:
        return None
    normalized_content_type = content_type.lower()
    if normalized_content_type not in AUDIO_EXTENSIONS:
        return None
    return normalized_content_type


def upload_stage_capture(
    *,
    file: BinaryIO,
    content_type: str,
    user_id: int,
    stage_session_id: int,
) -> str:
    """스테이지 캡처를 Azure에 업로드하고 공개 Blob URL을 반환합니다."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    extension = IMAGE_EXTENSIONS[content_type]
    blob_name = (
        f"{settings.azure_storage_stage_capture_prefix}/"
        f"{user_id}/{stage_session_id}/{uuid4()}.{extension}"
    )
    blob = service.get_blob_client(
        container=settings.azure_storage_container_name,
        blob=blob_name,
    )
    blob.upload_blob(
        file,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob.url


def upload_track_capture(
    *,
    file: BinaryIO,
    content_type: str,
    user_id: int,
    track_session_id: int,
) -> str:
    """트랙 캡처를 Azure에 업로드하고 공개 Blob URL을 반환합니다."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    extension = IMAGE_EXTENSIONS[content_type]
    blob_name = (
        f"{settings.azure_storage_track_capture_prefix}/"
        f"{user_id}/{track_session_id}/{uuid4()}.{extension}"
    )
    blob = service.get_blob_client(
        container=settings.azure_storage_container_name,
        blob=blob_name,
    )
    blob.upload_blob(
        file,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob.url


def upload_avatar_interaction_picture(
    *,
    file: BinaryIO,
    content_type: str,
    user_id: int,
    avatar_interaction_session_id: int,
) -> str:
    """아바타 소환 사진을 Azure에 업로드하고 공개 Blob URL을 반환합니다."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    extension = IMAGE_EXTENSIONS[content_type]
    blob_name = (
        f"{settings.azure_storage_avatar_interaction_picture_prefix}/"
        f"{user_id}/{avatar_interaction_session_id}/{uuid4()}.{extension}"
    )
    blob = service.get_blob_client(
        container=settings.azure_storage_container_name,
        blob=blob_name,
    )
    blob.upload_blob(
        file,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob.url


def upload_community_post_image(
    *,
    file: BinaryIO,
    content_type: str,
    user_id: int,
    post_id: int,
) -> str:
    """커뮤니티 게시글 이미지를 Azure에 업로드하고 공개 Blob URL을 반환합니다."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    extension = IMAGE_EXTENSIONS[content_type]
    blob_name = (
        f"{settings.azure_storage_community_post_prefix}/"
        f"{user_id}/{post_id}/{uuid4()}.{extension}"
    )
    blob = service.get_blob_client(
        container=settings.azure_storage_container_name,
        blob=blob_name,
    )
    blob.upload_blob(
        file,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob.url


def upload_conversation_audio(
    *,
    file: BinaryIO,
    content_type: str,
    user_id: int,
    conversation_session_id: int,
) -> str:
    """음성 대화 녹음 파일을 Azure에 업로드하고 공개 Blob URL을 반환합니다."""
    settings = get_settings()
    service = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )
    extension = AUDIO_EXTENSIONS[content_type]
    blob_name = (
        f"{settings.azure_storage_conversation_audio_prefix}/"
        f"{user_id}/{conversation_session_id}/{uuid4()}.{extension}"
    )
    blob = service.get_blob_client(
        container=settings.azure_storage_container_name,
        blob=blob_name,
    )
    blob.upload_blob(
        file,
        overwrite=False,
        content_settings=ContentSettings(content_type=content_type),
    )
    return blob.url
