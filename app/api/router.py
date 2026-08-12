from fastapi import APIRouter

from app.api.routes import conversation, gallery, home, stage, track

api_router = APIRouter()
api_router.include_router(conversation.router, prefix="/users/me", tags=["conversation"])
api_router.include_router(gallery.router, prefix="/users/me", tags=["gallery"])
api_router.include_router(home.router, prefix="/users/me", tags=["home"])
api_router.include_router(stage.router, prefix="/stages", tags=["stage"])
api_router.include_router(track.router, prefix="/tracks", tags=["track"])
api_router.include_router(
    track.track_session_router,
    prefix="/users/me/track-sessions",
    tags=["track"],
)
api_router.include_router(
    stage.stage_session_router,
    prefix="/users/me/stage-sessions",
    tags=["stage"],
)
