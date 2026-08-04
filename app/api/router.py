"""버전 1 API 라우터를 한곳에서 조립합니다."""

from fastapi import APIRouter

from app.api.routes import health, stages, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stages.router, prefix="/stages", tags=["stages"])

# 새 도메인 API를 추가할 때 아래 형태로 등록하세요.
# from app.api.routes import users
# api_router.include_router(users.router, prefix="/users", tags=["users"])

