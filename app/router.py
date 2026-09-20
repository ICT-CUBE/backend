from fastapi import APIRouter

from app.affinity import router as affinity
from app.album import router as album
from app.auth import router as auth
from app.avatar import router as avatar
from app.blockchain import router as blockchain
from app.community import router as community
from app.conversation import router as conversation
from app.cube import router as cube
from app.gallery import router as gallery
from app.home import router as home
from app.market import router as market
from app.mission import router as mission
from app.mypage import router as mypage
from app.stage import router as stage

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(affinity.router, prefix="/users/me", tags=["affinity"])
api_router.include_router(avatar.router, prefix="/users/me", tags=["avatar"])
api_router.include_router(conversation.router, prefix="/users/me", tags=["conversation"])
api_router.include_router(gallery.router, prefix="/users/me", tags=["gallery"])
api_router.include_router(home.router, prefix="/users/me", tags=["home"])
api_router.include_router(market.router, prefix="/users/me", tags=["market"])
api_router.include_router(mission.router, prefix="/users/me", tags=["mission"])
api_router.include_router(mypage.router, prefix="/users/me", tags=["mypage"])
api_router.include_router(cube.router, prefix="/cubes", tags=["cube"])
api_router.include_router(community.router, prefix="/community", tags=["community"])
api_router.include_router(
    blockchain.router,
    prefix="/internal/blockchain",
    tags=["blockchain"],
)
api_router.include_router(stage.router, prefix="/stages", tags=["stage"])
api_router.include_router(album.album_router, prefix="/album", tags=["album"])
api_router.include_router(album.router, prefix="/tracks", tags=["album"])
api_router.include_router(
    album.track_session_router,
    prefix="/users/me/track-sessions",
    tags=["album"],
)
api_router.include_router(
    stage.stage_session_router,
    prefix="/users/me/stage-sessions",
    tags=["stage"],
)
api_router.include_router(
    cube.cube_ownership_router,
    prefix="/users/me/cube-ownerships",
    tags=["cube"],
)
