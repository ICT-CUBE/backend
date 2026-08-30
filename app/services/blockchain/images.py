"""NFT 메타데이터에 넣을 제품 이미지 준비."""

import base64

import httpx

from app.services.blockchain.errors import BlockchainError

# 블록체인 서버가 허용하는 디코딩 후 이미지 크기 상한입니다.
IMAGE_MAX_BYTES = 2 * 1024 * 1024
IMAGE_DOWNLOAD_TIMEOUT_SECONDS = 15


def prepare_product_image(*, image_url: str) -> tuple[str, str]:
    """제품 이미지를 내려받아 (base64 문자열, Content-Type)로 반환합니다."""
    image_bytes = _download(image_url)
    if len(image_bytes) > IMAGE_MAX_BYTES:
        raise BlockchainError(
            code="IMAGE_TOO_LARGE",
            message=f"제품 이미지가 {IMAGE_MAX_BYTES} 바이트를 초과합니다.",
        )

    mime_type = _detect_mime_type(image_bytes)
    if mime_type is None:
        raise BlockchainError(
            code="IMAGE_TYPE_NOT_SUPPORTED",
            message="지원하지 않는 제품 이미지 형식입니다.",
        )

    return base64.b64encode(image_bytes).decode(), mime_type


def _download(image_url: str) -> bytes:
    try:
        response = httpx.get(
            image_url,
            timeout=IMAGE_DOWNLOAD_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise BlockchainError(
            code="IMAGE_DOWNLOAD_FAILED",
            message="제품 이미지를 내려받지 못했습니다.",
        ) from exc
    return response.content


def _detect_mime_type(image_bytes: bytes) -> str | None:
    """블록체인 서버와 같은 매직 바이트 기준으로 형식을 판별합니다."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    return None
