from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi import status as HttpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedResponse
from app.schemas.validation_rules import (ExecutionStatus,
                                          RulePerformanceMetrics,
                                          ValidationCategory,
                                          ValidationDashboardData,
                                          ValidationRule, ValidationRuleCreate,
                                          ValidationRuleExecution,
                                          ValidationRuleExecutionCreate,
                                          ValidationRuleTemplate,
                                          ValidationRuleUpdate,
                                          ValidationSeverity,
                                          ValidationSummary,
                                          ValidationViolation,
                                          ValidationViolationUpdate,
                                          ViolationStatus)
from app.services.validation_rules import ValidationRuleService

router = APIRouter()

# Permission checkers
check_read_permission = PermissionChecker("quality:read")
check_expert_permission = PermissionChecker("quality:expert")
check_admin_permission = PermissionChecker("quality:admin")


# =============================================
# VALIDATION RULES CRUD
# =============================================


@router.get("/rules", response_model=PaginatedResponse[ValidationRule])
async def get_validation_rules(
    category: Optional[ValidationCategory] = None,
    is_active: Optional[bool] = None,
    severity: Optional[ValidationSeverity] = None,
    entity_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[ValidationRule]:
    """Get validation rules with optional filters"""

    service = ValidationRuleService()

    try:
        rules = await service.get_rules(
            category=category,
            is_active=is_active,
            severity=severity,
            entity_type=entity_type,
            limit=limit,
            skip=skip,
        )

        return PaginatedResponse(
            data=rules,
            meta={"total": len(rules), "skip": skip, "limit": limit},
            status=HttpStatus.HTTP_200_OK,
            message="Validation rules retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation rules: {str(e)}",
        )


@router.get("/rules/{rule_id}", response_model=ApiResponse[ValidationRule])
async def get_validation_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[ValidationRule]:
    """Get a specific validation rule"""

    service = ValidationRuleService()

    try:
        rule = await service.get_rule(rule_id)

        if not rule:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Validation rule {rule_id} not found",
            )

        return ApiResponse(
            data=rule,
            status=HttpStatus.HTTP_200_OK,
            message="Validation rule retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation rule: {str(e)}",
        )


@router.post("/rules", response_model=ApiResponse[ValidationRule])
async def create_validation_rule(
    rule_data: ValidationRuleCreate,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[ValidationRule]:
    """Create a new validation rule"""

    service = ValidationRuleService()

    try:
        rule = await service.create_rule(rule_data, current_user["id"])

        return ApiResponse(
            data=rule,
            status=HttpStatus.HTTP_201_CREATED,
            message="Validation rule created successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create validation rule: {str(e)}",
        )


@router.put("/rules/{rule_id}", response_model=ApiResponse[ValidationRule])
async def update_validation_rule(
    rule_id: str,
    rule_data: ValidationRuleUpdate,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[ValidationRule]:
    """Update a validation rule"""

    service = ValidationRuleService()

    try:
        rule = await service.update_rule(rule_id, rule_data, current_user["id"])

        return ApiResponse(
            data=rule,
            status=HttpStatus.HTTP_200_OK,
            message="Validation rule updated successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validation rule: {str(e)}",
        )


@router.delete("/rules/{rule_id}")
async def delete_validation_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, str]]:
    """Delete (deactivate) a validation rule"""

    service = ValidationRuleService()

    try:
        success = await service.delete_rule(rule_id)

        if not success:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Validation rule {rule_id} not found",
            )

        return ApiResponse(
            data={"message": "Rule deactivated successfully"},
            status=HttpStatus.HTTP_200_OK,
            message="Validation rule deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete validation rule: {str(e)}",
        )


@router.post("/rules/{rule_id}/toggle", response_model=ApiResponse[ValidationRule])
async def toggle_validation_rule(
    rule_id: str,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[ValidationRule]:
    """Toggle validation rule active status"""

    service = ValidationRuleService()

    try:
        rule = await service.toggle_rule_status(rule_id, current_user["id"])

        status_text = "activated" if rule.is_active else "deactivated"

        return ApiResponse(
            data=rule,
            status=HttpStatus.HTTP_200_OK,
            message=f"Validation rule {status_text} successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle validation rule: {str(e)}",
        )


# =============================================
# RULE EXECUTION
# =============================================


@router.post(
    "/rules/{rule_id}/execute", response_model=ApiResponse[ValidationRuleExecution]
)
async def execute_validation_rule(
    rule_id: str,
    execution_data: Optional[ValidationRuleExecutionCreate] = None,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[ValidationRuleExecution]:
    """Execute a single validation rule"""

    service = ValidationRuleService()

    try:
        if not execution_data:
            execution_data = ValidationRuleExecutionCreate(
                rule_id=rule_id, triggered_by="manual"
            )

        execution = await service.execute_rule(rule_id, execution_data)

        return ApiResponse(
            data=execution,
            status=HttpStatus.HTTP_200_OK,
            message="Validation rule executed successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute validation rule: {str(e)}",
        )


@router.post("/rules/execute-batch")
async def execute_validation_rules_batch(
    background_tasks: BackgroundTasks,
    rule_ids: Optional[List[str]] = None,
    category: Optional[ValidationCategory] = None,
    entity_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, str]]:
    """Execute multiple validation rules in batch"""

    service = ValidationRuleService()

    # Run in background
    background_tasks.add_task(
        service.execute_rules_batch,
        rule_ids=rule_ids,
        category=category,
        entity_type=entity_type,
    )

    return ApiResponse(
        data={"message": "Batch execution started"},
        status=HttpStatus.HTTP_202_ACCEPTED,
        message="Validation rules batch execution started",
    )


@router.get("/executions", response_model=PaginatedResponse[ValidationRuleExecution])
async def get_rule_executions(
    rule_id: Optional[str] = None,
    status: Optional[ExecutionStatus] = None,
    limit: int = Query(default=50, le=100),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[ValidationRuleExecution]:
    """Get rule executions with filters"""

    service = ValidationRuleService()

    try:
        executions = await service.get_executions(
            rule_id=rule_id, status=status, limit=limit
        )

        return PaginatedResponse(
            data=executions,
            meta={"total": len(executions), "limit": limit},
            status=HttpStatus.HTTP_200_OK,
            message="Rule executions retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule executions: {str(e)}",
        )


@router.get(
    "/executions/{execution_id}", response_model=ApiResponse[ValidationRuleExecution]
)
async def get_rule_execution(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[ValidationRuleExecution]:
    """Get a specific rule execution"""

    service = ValidationRuleService()

    try:
        execution = await service.get_execution(execution_id)

        if not execution:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Execution {execution_id} not found",
            )

        return ApiResponse(
            data=execution,
            status=HttpStatus.HTTP_200_OK,
            message="Rule execution retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule execution: {str(e)}",
        )


# =============================================
# VIOLATIONS MANAGEMENT
# =============================================


@router.get("/violations", response_model=PaginatedResponse[ValidationViolation])
async def get_validation_violations(
    rule_id: Optional[str] = None,
    status: Optional[ViolationStatus] = None,
    severity: Optional[ValidationSeverity] = None,
    limit: int = Query(default=100, le=500),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[ValidationViolation]:
    """Get validation violations with filters"""

    service = ValidationRuleService()

    try:
        violations = await service.get_violations(
            rule_id=rule_id, status=status, severity=severity, limit=limit
        )

        return PaginatedResponse(
            data=violations,
            meta={"total": len(violations), "limit": limit},
            status=HttpStatus.HTTP_200_OK,
            message="Validation violations retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation violations: {str(e)}",
        )


@router.put("/violations/{violation_id}", response_model=ApiResponse[str])
async def update_validation_violation(
    violation_id: str,
    violation_data: ValidationViolationUpdate,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[str]:
    """Update validation violation status"""

    from app.core.supabase import get_supabase

    try:
        supabase = await get_supabase()

        # Prepare update data
        update_dict = violation_data.model_dump(exclude_unset=True)
        if update_dict:
            if violation_data.status in [
                ViolationStatus.RESOLVED,
                ViolationStatus.IGNORED,
            ]:
                update_dict["resolved_by"] = current_user["id"]
                update_dict["resolved_at"] = datetime.now().isoformat()

        response = (
            await supabase.table("validation_violations")
            .update(update_dict)
            .eq("id", violation_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=HttpStatus.HTTP_404_NOT_FOUND,
                detail=f"Violation {violation_id} not found",
            )

        return ApiResponse(
            data=violation_id,
            status=HttpStatus.HTTP_200_OK,
            message="Validation violation updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validation violation: {str(e)}",
        )


@router.post("/violations/bulk-update")
async def bulk_update_violations(
    violation_ids: List[str],
    violation_data: ValidationViolationUpdate,
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[Dict[str, int]]:
    """Bulk update multiple violations"""

    from datetime import datetime

    from app.core.supabase import get_supabase

    try:
        supabase = await get_supabase()

        # Prepare update data
        update_dict = violation_data.model_dump(exclude_unset=True)
        if update_dict:
            if violation_data.status in [
                ViolationStatus.RESOLVED,
                ViolationStatus.IGNORED,
            ]:
                update_dict["resolved_by"] = current_user["id"]
                update_dict["resolved_at"] = datetime.now().isoformat()

        response = (
            await supabase.table("validation_violations")
            .update(update_dict)
            .in_("id", violation_ids)
            .execute()
        )

        updated_count = len(response.data) if response.data else 0

        return ApiResponse(
            data={"updated_count": updated_count},
            status=HttpStatus.HTTP_200_OK,
            message=f"Updated {updated_count} violations successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update violations: {str(e)}",
        )


# =============================================
# STATISTICS & PERFORMANCE
# =============================================


@router.get("/dashboard", response_model=ApiResponse[ValidationDashboardData])
async def get_validation_dashboard(
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[ValidationDashboardData]:
    """Get validation dashboard data"""

    service = ValidationRuleService()

    try:
        # Get summary statistics
        summary = await service.get_validation_summary()

        # Get recent executions
        recent_executions = await service.get_executions(limit=10)

        # Get performance metrics
        performance_metrics = await service.get_rule_performance()

        # Get top violating rules (worst performance)
        top_violating = sorted(performance_metrics, key=lambda x: x.success_rate)[:5]

        dashboard_data = ValidationDashboardData(
            summary=summary,
            recent_executions=recent_executions,
            top_violating_rules=top_violating,
            violation_trends={"trend": "stable"},  # TODO: Implement trend calculation
            rule_performance=performance_metrics,
        )

        return ApiResponse(
            data=dashboard_data,
            status=HttpStatus.HTTP_200_OK,
            message="Validation dashboard data retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation dashboard: {str(e)}",
        )


@router.get("/performance", response_model=ApiResponse[List[RulePerformanceMetrics]])
async def get_rule_performance(
    rule_ids: Optional[List[str]] = Query(None),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[RulePerformanceMetrics]]:
    """Get performance metrics for validation rules"""

    service = ValidationRuleService()

    try:
        metrics = await service.get_rule_performance(rule_ids)

        return ApiResponse(
            data=metrics,
            status=HttpStatus.HTTP_200_OK,
            message="Rule performance metrics retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule performance: {str(e)}",
        )


@router.get("/summary", response_model=ApiResponse[ValidationSummary])
async def get_validation_summary(
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[ValidationSummary]:
    """Get validation summary statistics"""

    service = ValidationRuleService()

    try:
        summary = await service.get_validation_summary()

        return ApiResponse(
            data=summary,
            status=HttpStatus.HTTP_200_OK,
            message="Validation summary retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation summary: {str(e)}",
        )


# =============================================
# RULE TEMPLATES
# =============================================


@router.get("/templates", response_model=ApiResponse[List[ValidationRuleTemplate]])
async def get_rule_templates(
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[ValidationRuleTemplate]]:
    """Get all validation rule templates"""

    service = ValidationRuleService()

    try:
        templates = await service.get_templates()

        return ApiResponse(
            data=templates,
            status=HttpStatus.HTTP_200_OK,
            message="Rule templates retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule templates: {str(e)}",
        )


@router.post(
    "/templates/{template_id}/create-rule", response_model=ApiResponse[ValidationRule]
)
async def create_rule_from_template(
    template_id: str,
    rule_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(check_expert_permission),
) -> ApiResponse[ValidationRule]:
    """Create a new rule from a template"""

    service = ValidationRuleService()

    try:
        rule = await service.create_rule_from_template(
            template_id, rule_data, current_user["id"]
        )

        return ApiResponse(
            data=rule,
            status=HttpStatus.HTTP_201_CREATED,
            message="Rule created from template successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule from template: {str(e)}",
        )


# =============================================
# PIPELINE INTEGRATION
# =============================================


@router.post("/pipeline/{pipeline_id}/add-validation-step")
async def add_validation_step_to_pipeline(
    pipeline_id: str,
    rule_ids: Optional[List[str]] = None,
    category: Optional[ValidationCategory] = None,
    entity_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(check_admin_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Add validation step to existing pipeline"""

    from app.schemas.pipeline_step import PipelineStepCreate, PipelineStepType
    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()

    try:
        # Get existing steps to determine order
        existing_steps = await step_service.get_pipeline_steps(pipeline_id)
        next_order = max([s["run_order"] for s in existing_steps.data], default=0) + 1

        # Create validation step
        validation_step = PipelineStepCreate(
            id=f"validation_step_{next_order}",
            name="Data Validation",
            step_type=PipelineStepType.DATA_VALIDATION,
            config={
                "rule_ids": rule_ids,
                "category": category.value if category else None,
                "entity_type": entity_type,
                "fail_on_violations": False,
                "violation_threshold": 0.1,
            },
            run_order=next_order,
            inputs=[],
            enabled=True,
        )

        step_result = await step_service.create_pipeline_step(
            validation_step, pipeline_id
        )

        return ApiResponse(
            data={"step": step_result},
            status=HttpStatus.HTTP_201_CREATED,
            message="Validation step added to pipeline successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add validation step: {str(e)}",
        )
