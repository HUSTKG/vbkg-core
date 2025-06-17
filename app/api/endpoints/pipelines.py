from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from fastapi import status as HttpStatus

from app.api.deps import PermissionChecker, validate_rate_limits
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.pipeline import (Pipeline, PipelineCreate,
                                  PipelineCreateFromTemplate, PipelineRun,
                                  PipelineUpdate, StartPipelineRequest)
from app.schemas.pipeline_step import (PipelineStep, PipelineStepRun,
                                       PipelineStepType)
from app.schemas.user import User
from app.services.pipeline import PipelineService
from app.services.pipeline_step import PipelineStepService

router = APIRouter(
    dependencies=[Depends(validate_rate_limits)],  # Add rate limiting
        )

check_read_permission = PermissionChecker("pipeline:read")
check_write_permission = PermissionChecker("pipeline:write")


@router.get("", response_model=PaginatedResponse[Pipeline])
async def read_pipelines(
    skip: int = 0,
    limit: int = 100,
    pipeline_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[Pipeline]:
    """
    Retrieve pipelines.
    """
    pipeline_service = PipelineService()

    pipelines = await pipeline_service.get_pipelines(
        skip=skip, limit=limit, pipeline_type=pipeline_type, is_active=is_active
    )
    return PaginatedResponse(
        data=pipelines.data,
        meta=PaginatedMeta(
            skip=skip,
            limit=limit,
            total=pipelines.count if pipelines.count else 0,
        ),
        status=HttpStatus.HTTP_200_OK,
        message="Pipelines retrieved successfully",
    )


@router.post("", response_model=ApiResponse[Pipeline])
async def create_pipeline(
    pipeline_in: PipelineCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Create new pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.create_pipeline(
        pipeline_in=pipeline_in,
        user_id=current_user["id"],
    )

    return ApiResponse(
        data=Pipeline(**pipeline),
        status=HttpStatus.HTTP_201_CREATED,
        message="Pipeline created successfully",
    )


@router.get("/{pipeline_id}/runs")
async def get_pipeline_runs(
    pipeline_id: Annotated[str, Path()],
    status: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> PaginatedResponse[PipelineRun]:
    """
    Get pipeline run history with optional filtering
    """
    try:
        runs_response = await pipeline_service.get_pipeline_runs(
            pipeline_id=pipeline_id, _status=status, limit=limit, skip=skip
        )

        return PaginatedResponse(
            data=[PipelineRun(**data) for data in runs_response.data],
            meta=PaginatedMeta(
                total=runs_response.count if runs_response.count else 0,
                limit=limit,
                skip=skip,
            ),
            status=HttpStatus.HTTP_200_OK,
            message="Pipeline runs retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline runs: {str(e)}"
        )


@router.get("/{pipeline_id}/runs/{run_id}", response_model=ApiResponse[PipelineRun])
async def read_pipeline_run(
    pipeline_id: Annotated[str, Path()],
    run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineRun]:
    """
    Get a specific pipeline run.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline_run = await pipeline_service.get_pipeline_run(
        run_id=run_id, pipeline_id=pipeline_id
    )
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )
    return ApiResponse(
        data=PipelineRun(**pipeline_run),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline run retrieved successfully",
    )


@router.get("/{pipeline_id}/runs/{run_id}/logs")
async def get_pipeline_run_logs(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> Dict[str, Any]:
    """
    Get detailed logs for a pipeline run
    """
    try:
        logs = await pipeline_service.get_pipeline_run_logs(run_id)
        return logs

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline logs: {str(e)}"
        )


@router.get("/{pipeline_id}/runs/{run_id}/status")
async def get_pipeline_run_status(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
    step_service: PipelineStepService = Depends(lambda: PipelineStepService()),
) -> Dict[str, Any]:
    """
    Get the detailed status of a pipeline run including step progress
    """
    try:
        # Get pipeline run details
        pipeline_run = await pipeline_service.get_pipeline_run(
            run_id=run_id, pipeline_id=pipeline_id
        )

        # Get step runs for this pipeline run
        step_runs_response = await step_service.get_pipeline_step_runs(run_id)
        step_runs = step_runs_response.data

        # Calculate progress
        total_steps = len(step_runs) if step_runs else 0
        completed_steps = (
            len([s for s in step_runs if s["status"] == "completed"])
            if step_runs
            else 0
        )
        failed_steps = (
            len([s for s in step_runs if s["status"] == "failed"]) if step_runs else 0
        )
        running_steps = (
            len([s for s in step_runs if s["status"] == "running"]) if step_runs else 0
        )

        progress_percentage = (
            (completed_steps / total_steps * 100) if total_steps > 0 else 0
        )

        return {
            "pipeline_run": pipeline_run,
            "step_runs": step_runs,
            "progress": {
                "percentage": round(progress_percentage, 2),
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "running_steps": running_steps,
            },
            "overall_status": pipeline_run["status"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline run status: {str(e)}"
        )


@router.post("/{pipeline_id}/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> ApiResponse[None]:
    """
    Cancel a running pipeline
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    isCanceled = await pipeline_service.cancel_pipeline_run(
        run_id=run_id, pipeline_id=pipeline_id
    )
    if not isCanceled:
        raise HTTPException(
            status_code=HttpStatus.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return ApiResponse(
        data=None,
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline retrieved successfully",
    )


@router.get("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def read_pipeline(
    pipeline_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[Pipeline]:
    """
    Get a specific pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=HttpStatus.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return ApiResponse(
        data=Pipeline(**pipeline),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline retrieved successfully",
    )


@router.put("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def update_pipeline(
    pipeline_id: Annotated[str, Path()],
    pipeline_in: PipelineUpdate,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Update a pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    pipeline = await pipeline_service.update_pipeline(
        pipeline_id=pipeline_id, pipeline_in=pipeline_in
    )
    return ApiResponse(
        data=Pipeline(**pipeline),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline updated successfully",
    )


@router.delete("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def delete_pipeline(
    pipeline_id: Annotated[str, Path()],
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Delete a pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    pipeline = await pipeline_service.delete_pipeline(pipeline_id=pipeline_id)

    return ApiResponse(
        data=Pipeline(**pipeline),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline deleted successfully",
    )


@router.post("/{pipeline_id}/run", response_model=Dict[str, Any])
async def execute_pipeline(
    pipeline_id: str,
    request: StartPipelineRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> Dict[str, Any]:
    """
    Execute a pipeline with optional input parameters
    """
    try:
        result = await pipeline_service.execute_pipeline(
            pipeline_id=pipeline_id,
            user_id=current_user["id"],
            input_parameters=request.input_parameters,
        )

        return {
            "success": True,
            "pipeline_run_id": result["id"],
            "celery_task_id": result["celery_task_id"],
            "status": result["status"],
            "message": result["message"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute pipeline: {str(e)}"
        )


@router.get("/{pipeline_id}/metrics", response_model=Dict[str, Any])
async def get_pipeline_metrics(
    pipeline_id: str, current_user: Dict = Depends(check_read_permission)
):
    """Get pipeline execution metrics"""
    try:
        pipeline_service = PipelineService()
        metrics = await pipeline_service.get_pipeline_execution_metrics(pipeline_id)
        return {"success": True, "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}/steps", response_model=PaginatedResponse[PipelineStep])
async def get_pipeline_steps(
    pipeline_id: Annotated[str, Path()],
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_steps(
        pipeline_id=pipeline_id, skip=skip, limit=limit
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return PaginatedResponse(
        data=[PipelineStep(**data) for data in step.data],
        meta=PaginatedMeta(
            total=step.count if step.count else 0,
            limit=limit,
            skip=skip,
        ),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get("/{pipeline_id}/steps/{step_id}", response_model=ApiResponse[PipelineStep])
async def get_pipeline_step(
    pipeline_id: Annotated[str, Path()],
    step_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_step(
        pipeline_id=pipeline_id, step_id=step_id
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return ApiResponse(
        data=PipelineStep(**step),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get(
    "/runs/{pipeline_run_id}/steps", response_model=PaginatedResponse[PipelineStepRun]
)
async def get_pipeline_step_runs(
    pipeline_run_id: Annotated[str, Path()],
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[PipelineStepRun]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_step_runs(
        pipeline_run_id=pipeline_run_id, skip=skip, limit=limit
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )

    return PaginatedResponse(
        data=[PipelineStepRun(**data) for data in step.data],
        meta=PaginatedMeta(
            total=step.count if step.count else 0,
            limit=limit,
            skip=skip,
        ),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get(
    "/runs/{pipeline_run_id}/steps/{step_run_id}",
    response_model=ApiResponse[PipelineStepRun],
)
async def get_pipeline_step_run(
    pipeline_run_id: Annotated[str, Path()],
    step_run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step_run = await pipeline_step_service.get_pipeline_step_run(
        step_run_id=step_run_id, pipeline_run_id=pipeline_run_id
    )
    if not step_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    return ApiResponse(
        data=PipelineStep(**step_run),
        status=HttpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.post("/from-template", response_model=ApiResponse[Dict[str, Any]])
async def create_pipeline_from_datasource_template(
    template_request: PipelineCreateFromTemplate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Create pipeline from data source template"""

    pipeline_service = PipelineService()

    try:
        pipeline = await pipeline_service.create_pipeline_from_template(
            template_request, current_user["id"]
        )

        return ApiResponse(
            data=pipeline,
            status=HttpStatus.HTTP_201_CREATED,
            message="Pipeline created from template successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline from template: {str(e)}",
        )


@router.get("/{pipeline_id}/with-datasources")
async def get_pipeline_with_datasources(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Get pipeline with data source information"""

    pipeline_service = PipelineService()

    try:
        pipeline = await pipeline_service.get_pipeline_with_datasources(pipeline_id)

        return ApiResponse(
            data=pipeline,
            status=HttpStatus.HTTP_200_OK,
            message="Pipeline with data sources retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline: {str(e)}",
        )


@router.get("/{pipeline_id}/validate-datasources")
async def validate_pipeline_datasources(
    pipeline_id: str,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Validate data sources used in pipeline"""

    pipeline_service = PipelineService()

    try:
        validation = await pipeline_service.validate_pipeline_datasources(pipeline_id)

        return ApiResponse(
            data=validation,
            status=HttpStatus.HTTP_200_OK,
            message="Pipeline data source validation completed",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate: {str(e)}",
        )


@router.get("/steps/{step_type}/compatible-datasources")
async def get_compatible_datasources_for_step(
    step_type: str,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Get data sources compatible with a specific step type"""

    pipeline_service = PipelineService()

    try:
        datasources = await pipeline_service.get_available_datasources_for_step(
            step_type
        )

        return ApiResponse(
            data=datasources,
            status=HttpStatus.HTTP_200_OK,
            message=f"Compatible data sources for {step_type} retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compatible data sources: {str(e)}",
        )


@router.get("/step-types/", response_model=Dict[str, Any])
async def get_available_step_types(current_user: Dict = Depends(check_read_permission)):
    """Get all available pipeline step types"""
    try:
        step_types = [
            {
                "value": step_type.value,
                "name": step_type.name,
                "category": _get_step_category(step_type),
                "description": _get_step_description(step_type),
                "supports_incremental": _supports_incremental(step_type),
                "complexity": _get_step_complexity(step_type),
            }
            for step_type in PipelineStepType
        ]

        # Group by category
        categorized_steps = {}
        for step in step_types:
            category = step["category"]
            if category not in categorized_steps:
                categorized_steps[category] = []
            categorized_steps[category].append(step)

        return {
            "success": True,
            "data": {"step_types": step_types, "categories": categorized_steps},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-config", response_model=Dict[str, Any])
async def validate_pipeline_config(
    config_data: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(check_read_permission),
):
    """Validate pipeline configuration"""
    try:
        # Basic validation
        errors = []
        warnings = []

        # Validate pipeline structure
        if "steps" not in config_data:
            errors.append("Pipeline must have steps")
        else:
            steps = config_data["steps"]
            if not isinstance(steps, list) or len(steps) == 0:
                errors.append("Pipeline must have at least one step")

            # Validate step dependencies
            step_ids = {step.get("id") for step in steps if step.get("id")}
            for step in steps:
                depends_on = step.get("depends_on", [])
                for dep_id in depends_on:
                    if dep_id not in step_ids:
                        errors.append(
                            f"Step dependency '{dep_id}' not found in pipeline"
                        )

        # Check for circular dependencies
        if "steps" in config_data:
            try:
                # This would need the actual dependency checking logic
                # For now, just a placeholder
                pass
            except Exception as e:
                errors.append(f"Circular dependency detected: {str(e)}")

        is_valid = len(errors) == 0

        return {
            "success": True,
            "data": {"is_valid": is_valid, "errors": errors, "warnings": warnings},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================== HELPER FUNCTIONS ==================


def _get_step_category(step_type: PipelineStepType) -> str:
    """Get category for step type"""
    categories = {
        # Data Acquisition
        PipelineStepType.FILE_READER: "Data Acquisition",
        PipelineStepType.API_FETCHER: "Data Acquisition",
        PipelineStepType.DATABASE_EXTRACTOR: "Data Acquisition",
        PipelineStepType.WEB_SCRAPER: "Data Acquisition",
        # Data Preprocessing
        PipelineStepType.TEXT_EXTRACTOR: "Data Preprocessing",
        PipelineStepType.DATA_CLEANER: "Data Preprocessing",
        PipelineStepType.DATA_VALIDATOR: "Data Preprocessing",
        PipelineStepType.FORMAT_CONVERTER: "Data Preprocessing",
        # Knowledge Extraction
        PipelineStepType.LLM_ENTITY_EXTRACTOR: "Knowledge Extraction",
        PipelineStepType.NER_EXTRACTOR: "Knowledge Extraction",
        PipelineStepType.RELATION_EXTRACTOR: "Knowledge Extraction",
        PipelineStepType.ENTITY_LINKER: "Knowledge Extraction",
        # Ontology Management
        PipelineStepType.ONTOLOGY_MAPPER: "Ontology Management",
        PipelineStepType.FIBO_MAPPER: "Ontology Management",
        PipelineStepType.SCHEMA_MATCHER: "Ontology Management",
        PipelineStepType.ONTOLOGY_MERGER: "Ontology Management",
        # Entity Processing
        PipelineStepType.ENTITY_RESOLUTION: "Entity Processing",
        PipelineStepType.ENTITY_FUSION: "Entity Processing",
        PipelineStepType.ENTITY_CLUSTERING: "Entity Processing",
        PipelineStepType.DUPLICATE_DETECTION: "Entity Processing",
        # Knowledge Graph Operations
        PipelineStepType.KNOWLEDGE_GRAPH_WRITER: "Knowledge Graph Operations",
        PipelineStepType.GRAPH_VALIDATOR: "Knowledge Graph Operations",
        PipelineStepType.GRAPH_REASONER: "Knowledge Graph Operations",
        PipelineStepType.LINK_PREDICTOR: "Knowledge Graph Operations",
        # Quality Assurance
        PipelineStepType.QUALITY_CHECKER: "Quality Assurance",
        PipelineStepType.CONSISTENCY_VALIDATOR: "Quality Assurance",
        PipelineStepType.COMPLETENESS_CHECKER: "Quality Assurance",
        PipelineStepType.PROVENANCE_TRACKER: "Quality Assurance",
        # Utilities
        PipelineStepType.CUSTOM_PYTHON: "Utilities",
        PipelineStepType.WORKFLOW_CONTROLLER: "Utilities",
        PipelineStepType.NOTIFICATION_SENDER: "Utilities",
    }
    return categories.get(step_type, "Other")


def _get_step_description(step_type: PipelineStepType) -> str:
    """Get description for step type"""
    descriptions = {
        PipelineStepType.FILE_READER: "Read and process files from various sources",
        PipelineStepType.API_FETCHER: "Fetch data from REST APIs and web services",
        PipelineStepType.DATABASE_EXTRACTOR: "Extract data from relational databases",
        PipelineStepType.WEB_SCRAPER: "Scrape and extract data from web pages",
        PipelineStepType.TEXT_EXTRACTOR: "Extract text content from documents",
        PipelineStepType.DATA_CLEANER: "Clean and normalize data",
        PipelineStepType.DATA_VALIDATOR: "Validate data quality and integrity",
        PipelineStepType.FORMAT_CONVERTER: "Convert data between different formats",
        PipelineStepType.LLM_ENTITY_EXTRACTOR: "Extract entities using Large Language Models",
        PipelineStepType.NER_EXTRACTOR: "Named Entity Recognition using NLP models",
        PipelineStepType.RELATION_EXTRACTOR: "Extract relationships between entities",
        PipelineStepType.ENTITY_LINKER: "Link entities to knowledge bases",
        PipelineStepType.ONTOLOGY_MAPPER: "Map data to ontology concepts",
        PipelineStepType.FIBO_MAPPER: "Map financial data to FIBO ontology",
        PipelineStepType.SCHEMA_MATCHER: "Match schemas between data sources",
        PipelineStepType.ONTOLOGY_MERGER: "Merge multiple ontologies",
        PipelineStepType.ENTITY_RESOLUTION: "Resolve duplicate entities",
        PipelineStepType.ENTITY_FUSION: "Fuse information from multiple entities",
        PipelineStepType.ENTITY_CLUSTERING: "Cluster similar entities",
        PipelineStepType.DUPLICATE_DETECTION: "Detect duplicate records",
        PipelineStepType.KNOWLEDGE_GRAPH_WRITER: "Write data to knowledge graph",
        PipelineStepType.GRAPH_VALIDATOR: "Validate knowledge graph structure",
        PipelineStepType.GRAPH_REASONER: "Apply reasoning rules to graph",
        PipelineStepType.LINK_PREDICTOR: "Predict missing links in graph",
        PipelineStepType.QUALITY_CHECKER: "Assess overall data quality",
        PipelineStepType.CONSISTENCY_VALIDATOR: "Check data consistency",
        PipelineStepType.COMPLETENESS_CHECKER: "Check data completeness",
        PipelineStepType.PROVENANCE_TRACKER: "Track data lineage and provenance",
        PipelineStepType.CUSTOM_PYTHON: "Execute custom Python code",
        PipelineStepType.WORKFLOW_CONTROLLER: "Control workflow execution",
        PipelineStepType.NOTIFICATION_SENDER: "Send notifications and alerts",
    }
    return descriptions.get(step_type, "Custom pipeline step")


def _supports_incremental(step_type: PipelineStepType) -> bool:
    """Check if step type supports incremental processing"""
    incremental_types = {
        PipelineStepType.FILE_READER,
        PipelineStepType.API_FETCHER,
        PipelineStepType.DATABASE_EXTRACTOR,
        PipelineStepType.WEB_SCRAPER,
        PipelineStepType.LLM_ENTITY_EXTRACTOR,
        PipelineStepType.ENTITY_RESOLUTION,
        PipelineStepType.KNOWLEDGE_GRAPH_WRITER,
        PipelineStepType.QUALITY_CHECKER,
    }
    return step_type in incremental_types


def _get_step_complexity(step_type: PipelineStepType) -> str:
    """Get complexity level for step type"""
    high_complexity = {
        PipelineStepType.LLM_ENTITY_EXTRACTOR,
        PipelineStepType.ENTITY_RESOLUTION,
        PipelineStepType.ONTOLOGY_MERGER,
        PipelineStepType.GRAPH_REASONER,
        PipelineStepType.CUSTOM_PYTHON,
    }

    medium_complexity = {
        PipelineStepType.RELATION_EXTRACTOR,
        PipelineStepType.ENTITY_LINKER,
        PipelineStepType.ONTOLOGY_MAPPER,
        PipelineStepType.ENTITY_FUSION,
        PipelineStepType.GRAPH_VALIDATOR,
        PipelineStepType.QUALITY_CHECKER,
    }

    if step_type in high_complexity:
        return "high"
    elif step_type in medium_complexity:
        return "medium"
    else:
        return "low"
