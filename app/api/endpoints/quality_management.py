from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi import status as HttpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.conflict_resolution import (Conflict, ConflictResolution,
                                             ConflictResolutionRequest,
                                             ConflictStatus, ConflictType,
                                             KGEdit, QualityReport)
from app.services.conflict_detection import ConflictDetectionService
from app.services.conflict_resolution import ConflictResolutionService
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.quality_management import QualityManagementService

router = APIRouter()

# Permission checkers
check_read_permission = PermissionChecker("quality:read")
check_expert_permission = PermissionChecker("quality:expert")
check_admin_permission = PermissionChecker("quality:admin")


# Quality Dashboard & Reports
@router.get("/dashboard", response_model=ApiResponse[Dict[str, Any]])
async def get_quality_dashboard(
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Get quality management dashboard data"""

    quality_service = QualityManagementService()

    try:
        dashboard_data = await quality_service.get_quality_dashboard_data()

        return ApiResponse(
            data=dashboard_data,
            status=HttpStatus.HTTP_200_OK,
            message="Quality dashboard data retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}",
        )


@router.get("/report", response_model=ApiResponse[QualityReport])
async def generate_quality_report(
    days_back: int = 30,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[QualityReport]:
    """Generate comprehensive quality report"""

    quality_service = QualityManagementService()

    try:
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        report = await quality_service.generate_quality_report(start_date, end_date)

        return ApiResponse(
            data=report,
            status=HttpStatus.HTTP_200_OK,
            message="Quality report generated successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.post("/monitoring/run")
async def run_quality_monitoring(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(check_admin_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Run comprehensive quality monitoring pipeline"""

    quality_service = QualityManagementService()

    # Run monitoring in background
    background_tasks.add_task(quality_service.run_quality_monitoring)

    return ApiResponse(
        data={"status": "started", "message": "Quality monitoring pipeline started"},
        status=HttpStatus.HTTP_202_ACCEPTED,
        message="Quality monitoring started",
    )


# Conflict Management
@router.get("/conflicts", response_model=PaginatedResponse[Conflict])
async def get_conflicts(
    status: Optional[ConflictStatus] = None,
    conflict_type: Optional[ConflictType] = None,
    severity: Optional[str] = None,
    assigned_to_me: bool = False,
    limit: int = 50,
    skip: int = 0,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> PaginatedResponse[Conflict]:
    """Get conflicts for review"""

    conflict_service = ConflictResolutionService()

    try:
        # Filter by assignment if requested
        expert_id = current_user["id"] if assigned_to_me else None

        conflicts = await conflict_service.get_conflicts_for_review(
            expert_id=expert_id,
            status=status,
            severity=severity,
            conflict_type=conflict_type,
            limit=limit,
        )

        return PaginatedResponse(
            data=[Conflict(**conflict) for conflict in conflicts.data],
            meta=PaginatedMeta(
                total=conflicts.count if conflicts.count else 0, skip=skip, limit=limit
            ),
            status=HttpStatus.HTTP_200_OK,
            message="Conflicts retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conflicts: {str(e)}",
        )


@router.post("/conflicts/detect")
async def detect_conflicts(
    background_tasks: BackgroundTasks,
    entity_ids: Optional[List[str]] = None,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Trigger conflict detection"""

    from app.core.supabase import get_supabase

    async def detect_and_save_conflicts():
        conflict_detector = ConflictDetectionService()
        try:
            conflicts = await conflict_detector.detect_all_conflicts(
                entity_ids=entity_ids, batch_size=100
            )

            # Lưu conflicts vào database
            supabase = await get_supabase()
            for conflict in conflicts:
                try:
                    await supabase.table("conflicts").insert(
                        conflict.model_dump()
                    ).execute()
                except Exception as e:
                    print(f"Failed to save conflict: {e}")

            print(f"Detected and saved {len(conflicts)} conflicts")

        except Exception as e:
            print(f"Conflict detection failed: {e}")

    # Run detection and saving in background
    background_tasks.add_task(detect_and_save_conflicts)

    return ApiResponse(
        data={"status": "started"},
        status=HttpStatus.HTTP_202_ACCEPTED,
        message="Conflict detection started",
    )


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict_manually(
    conflict_id: str,
    resolution: ConflictResolutionRequest,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Manually resolve a conflict"""

    conflict_service = ConflictResolutionService()

    try:
        result = await conflict_service.resolve_conflict_manually(
            conflict_id=conflict_id,
            resolution=ConflictResolution(
                resolution_method=resolution.resolution_method,
                resolution_data=resolution.resolution_data,
                reasoning=resolution.reasoning,
                resolved_by=current_user["id"],
                resolution_timestamp=datetime.now(timezone.utc),
            ),
            expert_id=current_user["id"],
        )

        return ApiResponse(
            data=result,
            status=HttpStatus.HTTP_200_OK,
            message="Conflict resolved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {str(e)}",
        )


@router.post("/conflicts/{conflict_id}/auto-resolve")
async def auto_resolve_conflict(
    conflict_id: str,
    use_ai: bool = True,
    confidence_threshold: float = 0.8,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Attempt automatic conflict resolution"""

    conflict_service = ConflictResolutionService()

    try:
        result = await conflict_service.resolve_conflict_automatically(
            conflict_id=conflict_id,
            use_ai=use_ai,
            confidence_threshold=confidence_threshold,
        )

        return ApiResponse(
            data=result,
            status=HttpStatus.HTTP_200_OK,
            message="Auto-resolution completed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to auto-resolve conflict: {str(e)}",
        )


# Direct Knowledge Graph Editing
@router.post("/kg/edit", response_model=ApiResponse[Dict[str, Any]])
async def apply_kg_edit(
    edit: KGEdit,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Apply direct edit to knowledge graph"""

    kg_editor = KnowledgeGraphService()

    try:
        result = await kg_editor.apply_edit(
            edit=edit, user_id=current_user["id"], validate_permissions=True
        )

        return ApiResponse(
            data=result.dict(),
            status=(
                HttpStatus.HTTP_200_OK
                if result.success
                else HttpStatus.HTTP_400_BAD_REQUEST
            ),
            message="Edit applied successfully" if result.success else "Edit failed",
        )
    except PermissionError:
        raise HTTPException(
            status_code=HttpStatus.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this edit",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply edit: {str(e)}",
        )


@router.post("/kg/rollback")
async def rollback_kg_changes(
    rollback_info: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(check_admin_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Rollback knowledge graph changes"""

    kg_editor = KnowledgeGraphService()

    try:
        result = await kg_editor.rollback_changes(rollback_info)

        return ApiResponse(
            data=result,
            status=HttpStatus.HTTP_200_OK,
            message="Changes rolled back successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback changes: {str(e)}",
        )


# Workflow Integration with Pipelines
@router.post("/pipeline/{pipeline_id}/add-quality-steps")
async def add_quality_steps_to_pipeline(
    pipeline_id: str,
    include_validation: bool = True,
    include_conflict_detection: bool = True,
    include_auto_resolution: bool = False,
    current_user: Dict[str, Any] = Depends(check_admin_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Add quality management steps to existing pipeline"""

    from app.schemas.pipeline_step import PipelineStepCreate, PipelineStepType
    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()

    try:
        # Get existing steps to determine order
        existing_steps = await step_service.get_pipeline_steps(pipeline_id)
        next_order = max([s["run_order"] for s in existing_steps.data], default=0) + 1

        added_steps = []

        # Add data validation step
        if include_validation:
            validation_step = PipelineStepCreate(
                id=f"quality_validation_{next_order}",
                name="Data Quality Validation",
                step_type=PipelineStepType.DATA_VALIDATION,
                config={
                    "validation_rules": [],
                    "quality_threshold": 0.7,
                    "fail_on_invalid": False,
                },
                run_order=next_order,
                inputs=[],
                enabled=True,
            )

            step_result = await step_service.create_pipeline_step(
                validation_step, pipeline_id
            )
            added_steps.append(step_result)
            next_order += 1

        # Add conflict detection step
        if include_conflict_detection:
            detection_step = PipelineStepCreate(
                id=f"conflict_detection_{next_order}",
                name="Conflict Detection",
                step_type="conflict_detection",  # Custom step type
                config={"batch_size": 100, "auto_assign_experts": True},
                run_order=next_order,
                inputs=[],
                enabled=True,
            )

            step_result = await step_service.create_pipeline_step(
                detection_step, pipeline_id
            )
            added_steps.append(step_result)
            next_order += 1

        # Add auto-resolution step
        if include_auto_resolution:
            resolution_step = PipelineStepCreate(
                id=f"auto_resolution_{next_order}",
                name="Automatic Conflict Resolution",
                step_type="auto_resolution",  # Custom step type
                config={"confidence_threshold": 0.8, "use_ai": True, "max_attempts": 3},
                run_order=next_order,
                inputs=[],
                enabled=True,
            )

            step_result = await step_service.create_pipeline_step(
                resolution_step, pipeline_id
            )
            added_steps.append(step_result)

        return ApiResponse(
            data={"added_steps": added_steps},
            status=HttpStatus.HTTP_201_CREATED,
            message=f"Added {len(added_steps)} quality management steps to pipeline",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add quality steps: {str(e)}",
        )
