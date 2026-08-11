"""Azure Blob Storage 파일 업로드 기능."""

from typing import BinaryIO
from uuid import uuid4

from azure.storage.blob import BlobServiceClient, ContentSettings

from app.core.config import get_settings

IMAGE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


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
