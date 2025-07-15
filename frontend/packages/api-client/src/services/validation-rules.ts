import {
	ICreateValidationRuleRequest,
	ICreateValidationRuleResponse,
	IGetValidationRulesRequest,
	IGetValidationRulesResponse,
	IGetValidationRuleRequest,
	IGetValidationRuleResponse,
	IUpdateValidationRuleRequest,
	IUpdateValidationRuleResponse,
	IDeleteValidationRuleRequest,
	IDeleteValidationRuleResponse,
	IToggleValidationRuleRequest,
	IToggleValidationRuleResponse,
	IExecuteValidationRuleRequest,
	IExecuteValidationRuleResponse,
	IExecuteBatchValidationRulesRequest,
	IExecuteBatchValidationRulesResponse,
	IGetValidationExecutionsRequest,
	IGetValidationExecutionsResponse,
	IGetValidationExecutionRequest,
	IGetValidationExecutionResponse,
	IGetValidationViolationsRequest,
	IGetValidationViolationsResponse,
	IUpdateValidationViolationRequest,
	IUpdateValidationViolationResponse,
	IBulkUpdateValidationViolationsRequest,
	IBulkUpdateValidationViolationsResponse,
	IGetValidationDashboardResponse,
	IGetValidationPerformanceRequest,
	IGetValidationPerformanceResponse,
	IGetValidationSummaryResponse,
	IGetValidationTemplatesResponse,
	ICreateRuleFromTemplateRequest,
	ICreateRuleFromTemplateResponse,
	IAddValidationToPipelineRequest,
	IAddValidationToPipelineResponse,
} from "@vbkg/types";

import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

// Validation Rules CRUD
const createValidationRule = async (input: ICreateValidationRuleRequest) => {
	return await api().post<ICreateValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULES,
		input,
	);
};

const getValidationRules = async (
	input: IGetValidationRulesRequest,
): Promise<IGetValidationRulesResponse> => {
	return await api().get(API_ENDPOINTS.VALIDATION_RULES, {
		params: {
			...input,
		},
	});
};

const getValidationRule = async (input: IGetValidationRuleRequest) => {
	return await api().get<IGetValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULE(input.rule_id),
	);
};

const updateValidationRule = async (input: IUpdateValidationRuleRequest) => {
	const { rule_id, ...updateData } = input;
	return await api().put<IUpdateValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULE(rule_id),
		updateData,
	);
};

const deleteValidationRule = async (input: IDeleteValidationRuleRequest) => {
	return await api().delete<IDeleteValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULE(input.rule_id),
	);
};

const toggleValidationRule = async (input: IToggleValidationRuleRequest) => {
	return await api().post<IToggleValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULE_TOGGLE(input.rule_id),
	);
};

// Rule Execution
const executeValidationRule = async (input: IExecuteValidationRuleRequest) => {
	const { rule_id, ...executionData } = input;
	return await api().post<IExecuteValidationRuleResponse>(
		API_ENDPOINTS.VALIDATION_RULE_EXECUTE(rule_id),
		executionData,
	);
};

const executeBatchValidationRules = async (
	input: IExecuteBatchValidationRulesRequest,
) => {
	return await api().post<IExecuteBatchValidationRulesResponse>(
		API_ENDPOINTS.VALIDATION_RULES_EXECUTE_BATCH,
		input,
	);
};

const getValidationExecutions = async (
	input: IGetValidationExecutionsRequest,
): Promise<IGetValidationExecutionsResponse> => {
	return await api().get(API_ENDPOINTS.VALIDATION_EXECUTIONS, {
		params: {
			...input,
		},
	});
};

const getValidationExecution = async (
	input: IGetValidationExecutionRequest,
) => {
	return await api().get<IGetValidationExecutionResponse>(
		API_ENDPOINTS.VALIDATION_EXECUTION(input.execution_id),
	);
};

// Violations Management
const getValidationViolations = async (
	input: IGetValidationViolationsRequest,
): Promise<IGetValidationViolationsResponse> => {
	return await api().get(API_ENDPOINTS.VALIDATION_VIOLATIONS, {
		params: {
			...input,
		},
	});
};

const updateValidationViolation = async (
	input: IUpdateValidationViolationRequest,
) => {
	const { violation_id, ...updateData } = input;
	return await api().put<IUpdateValidationViolationResponse>(
		API_ENDPOINTS.VALIDATION_VIOLATION(violation_id),
		updateData,
	);
};

const bulkUpdateValidationViolations = async (
	input: IBulkUpdateValidationViolationsRequest,
) => {
	return await api().post<IBulkUpdateValidationViolationsResponse>(
		API_ENDPOINTS.VALIDATION_VIOLATIONS_BULK_UPDATE,
		input,
	);
};

// Dashboard & Statistics
const getValidationDashboard =
	async () => {
		return await api().get<IGetValidationDashboardResponse>(
			API_ENDPOINTS.VALIDATION_DASHBOARD,
		);
	};

const getValidationPerformance = async (
	input: IGetValidationPerformanceRequest,
): Promise<IGetValidationPerformanceResponse> => {
	return await api().get(API_ENDPOINTS.VALIDATION_PERFORMANCE, {
		params: {
			rule_ids: input.rule_ids?.join(","),
		},
	});
};

const getValidationSummary = async () => {
	return await api().get<IGetValidationSummaryResponse>(
		API_ENDPOINTS.VALIDATION_SUMMARY,
	);
};

// Templates
const getValidationTemplates = async () => {
	return await api().get<IGetValidationTemplatesResponse>(
		API_ENDPOINTS.VALIDATION_TEMPLATES,
	);
};

const createRuleFromTemplate = async (
	input: ICreateRuleFromTemplateRequest,
) => {
	const { template_id, ...ruleData } = input;
	return await api().post<ICreateRuleFromTemplateResponse>(
		API_ENDPOINTS.VALIDATION_TEMPLATE_CREATE_RULE(template_id),
		ruleData,
	);
};

// Pipeline Integration
const addValidationToPipeline = async (
	input: IAddValidationToPipelineRequest,
) => {
	const { pipeline_id, ...validationData } = input;
	return await api().post<IAddValidationToPipelineResponse>(
		API_ENDPOINTS.VALIDATION_ADD_TO_PIPELINE(pipeline_id),
		validationData,
	);
};

export const ValidationRulesService = {
	// CRUD Operations
	createValidationRule,
	getValidationRules,
	getValidationRule,
	updateValidationRule,
	deleteValidationRule,
	toggleValidationRule,

	// Execution
	executeValidationRule,
	executeBatchValidationRules,
	getValidationExecutions,
	getValidationExecution,

	// Violations
	getValidationViolations,
	updateValidationViolation,
	bulkUpdateValidationViolations,

	// Dashboard & Statistics
	getValidationDashboard,
	getValidationPerformance,
	getValidationSummary,

	// Templates
	getValidationTemplates,
	createRuleFromTemplate,

	// Pipeline Integration
	addValidationToPipeline,
};
