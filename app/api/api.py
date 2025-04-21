# app/api/api.py
from fastapi import APIRouter

from app.api.endpoints import auth, users, notifications,datasources, fibo, pipelines,knowledge, search, visualization

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

api_router.include_router(datasources.router, prefix="/datasources", tags=["datasources"])
api_router.include_router(fibo.router, prefix="/fibo", tags=["fibo"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])

api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(visualization.router, prefix="/visualizations", tags=["visualizations"])
