from fastapi import APIRouter

from app.api.endpoints import (
    auth,
    datasources,
    domain,
    fibo,
    file_upload,
    knowledge_graph,
    notifications,
    pipelines,
    quality_management,
    search,
    users,
    visualization,
    worker,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)

api_router.include_router(
    datasources.router, prefix="/datasources", tags=["datasources"]
)
api_router.include_router(fibo.router, prefix="/fibo", tags=["fibo"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])

api_router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["knowledge_graph"]
)
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(
    visualization.router, prefix="/visualizations", tags=["visualizations"]
)
api_router.include_router(file_upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(
    quality_management.router, prefix="/quality", tags=["quality_management"]
)
api_router.include_router(
    domain.router,
    prefix="/domain",
    tags=["domain"],
)
api_router.include_router(
    worker.router,
    prefix="/celery",
    tags=["worker"],
)
