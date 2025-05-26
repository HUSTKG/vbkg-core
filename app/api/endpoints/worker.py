import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.api import ApiResponse
from app.schemas.worker import (CeleryStats, FlowerDashboardResponse, TaskInfo,
                                WorkerInfo, WorkerStats)
from app.services.worker import FlowerService

router = APIRouter()

logger = logging.getLogger(__name__)


def get_flower_service() -> FlowerService:
    """Dependency to get FlowerService instance"""
    flower_url = os.getenv("FLOWER_URL", "http://localhost:5555")
    return FlowerService(flower_url)


@router.get("/dashboard", response_model=ApiResponse[FlowerDashboardResponse])
async def get_celery_dashboard(
    flower_service: FlowerService = Depends(get_flower_service),
):
    """Get complete Celery dashboard data"""
    try:
        response = await flower_service.get_dashboard_data()
        return ApiResponse(
            data=response,
            message="Celery dashboard data retrieved successfully",
            status=200,
        )

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@router.get("/workers", response_model=List[WorkerInfo])
async def get_workers(flower_service: FlowerService = Depends(get_flower_service)):
    """Get all Celery workers"""
    return await flower_service.get_workers()


@router.get("/workers/stats", response_model=WorkerStats)
async def get_worker_stats(flower_service: FlowerService = Depends(get_flower_service)):
    """Get worker statistics"""
    return await flower_service.get_worker_stats()


@router.get("/tasks", response_model=List[TaskInfo])
async def get_tasks(
    limit: int = 50, flower_service: FlowerService = Depends(get_flower_service)
):
    """Get recent Celery tasks"""
    return await flower_service.get_tasks(limit)


@router.get("/stats", response_model=CeleryStats)
async def get_celery_stats(flower_service: FlowerService = Depends(get_flower_service)):
    """Get Celery task statistics"""
    return await flower_service.get_celery_stats()


@router.get("/health")
async def health_check(flower_service: FlowerService = Depends(get_flower_service)):
    """Health check for Flower connection"""
    try:
        await flower_service._make_request("/api/workers")
        return {"status": "healthy", "flower_url": flower_service.flower_url}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "flower_url": flower_service.flower_url,
            },
        )
