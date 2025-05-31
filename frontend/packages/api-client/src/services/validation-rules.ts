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
const createValidationRule = async (
  input: ICreateValidationRuleRequest,
): Promise<ICreateValidationRuleResponse> => {
  return await api()
    .post<ICreateValidationRuleResponse>(API_ENDPOINTS.VALIDATION_RULES, input)
    .then((res) => res.data);
};

const getValidationRules = async (
  input: IGetValidationRulesRequest,
): Promise<IGetValidationRulesResponse> => {
  return await api()
    .get(API_ENDPOINTS.VALIDATION_RULES, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const getValidationRule = async (
  input: IGetValidationRuleRequest,
): Promise<IGetValidationRuleResponse> => {
  return await api()
    .get<IGetValidationRuleResponse>(
      API_ENDPOINTS.VALIDATION_RULE(input.rule_id),
    )
    .then((res) => res.data);
};

const updateValidationRule = async (
  input: IUpdateValidationRuleRequest,
): Promise<IUpdateValidationRuleResponse> => {
  const { rule_id, ...updateData } = input;
  return await api()
    .put<IUpdateValidationRuleResponse>(
      API_ENDPOINTS.VALIDATION_RULE(rule_id),
      updateData,
    )
    .then((res) => res.data);
};

const deleteValidationRule = async (
  input: IDeleteValidationRuleRequest,
): Promise<IDeleteValidationRuleResponse> => {
  return await api()
    .delete<IDeleteValidationRuleResponse>(
      API_ENDPOINTS.VALIDATION_RULE(input.rule_id),
    )
    .then((res) => res.data);
};

const toggleValidationRule = async (
  input: IToggleValidationRuleRequest,
): Promise<IToggleValidationRuleResponse> => {
  return await api()
    .post<IToggleValidationRuleResponse>(
      API_ENDPOINTS.VALIDATION_RULE_TOGGLE(input.rule_id),
    )
    .then((res) => res.data);
};

// Rule Execution
const executeValidationRule = async (
  input: IExecuteValidationRuleRequest,
): Promise<IExecuteValidationRuleResponse> => {
  const { rule_id, ...executionData } = input;
  return await api()
    .post<IExecuteValidationRuleResponse>(
      API_ENDPOINTS.VALIDATION_RULE_EXECUTE(rule_id),
      executionData,
    )
    .then((res) => res.data);
};

const executeBatchValidationRules = async (
  input: IExecuteBatchValidationRulesRequest,
): Promise<IExecuteBatchValidationRulesResponse> => {
  return await api()
    .post<IExecuteBatchValidationRulesResponse>(
      API_ENDPOINTS.VALIDATION_RULES_EXECUTE_BATCH,
      input,
    )
    .then((res) => res.data);
};

const getValidationExecutions = async (
  input: IGetValidationExecutionsRequest,
): Promise<IGetValidationExecutionsResponse> => {
  return await api()
    .get(API_ENDPOINTS.VALIDATION_EXECUTIONS, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const getValidationExecution = async (
  input: IGetValidationExecutionRequest,
): Promise<IGetValidationExecutionResponse> => {
  return await api()
    .get<IGetValidationExecutionResponse>(
      API_ENDPOINTS.VALIDATION_EXECUTION(input.execution_id),
    )
    .then((res) => res.data);
};

// Violations Management
const getValidationViolations = async (
  input: IGetValidationViolationsRequest,
): Promise<IGetValidationViolationsResponse> => {
  return await api()
    .get(API_ENDPOINTS.VALIDATION_VIOLATIONS, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const updateValidationViolation = async (
  input: IUpdateValidationViolationRequest,
): Promise<IUpdateValidationViolationResponse> => {
  const { violation_id, ...updateData } = input;
  return await api()
    .put<IUpdateValidationViolationResponse>(
      API_ENDPOINTS.VALIDATION_VIOLATION(violation_id),
      updateData,
    )
    .then((res) => res.data);
};

const bulkUpdateValidationViolations = async (
  input: IBulkUpdateValidationViolationsRequest,
): Promise<IBulkUpdateValidationViolationsResponse> => {
  return await api()
    .post<IBulkUpdateValidationViolationsResponse>(
      API_ENDPOINTS.VALIDATION_VIOLATIONS_BULK_UPDATE,
      input,
    )
    .then((res) => res.data);
};

// Dashboard & Statistics
const getValidationDashboard =
  async (): Promise<IGetValidationDashboardResponse> => {
    return await api()
      .get<IGetValidationDashboardResponse>(API_ENDPOINTS.VALIDATION_DASHBOARD)
      .then((res) => res.data);
  };

const getValidationPerformance = async (
  input: IGetValidationPerformanceRequest,
): Promise<IGetValidationPerformanceResponse> => {
  return await api()
    .get(API_ENDPOINTS.VALIDATION_PERFORMANCE, {
      params: {
        rule_ids: input.rule_ids?.join(","),
      },
    })
    .then((res) => res.data);
};

const getValidationSummary =
  async (): Promise<IGetValidationSummaryResponse> => {
    return await api()
      .get<IGetValidationSummaryResponse>(API_ENDPOINTS.VALIDATION_SUMMARY)
      .then((res) => res.data);
  };

// Templates
const getValidationTemplates =
  async (): Promise<IGetValidationTemplatesResponse> => {
    return await api()
      .get<IGetValidationTemplatesResponse>(API_ENDPOINTS.VALIDATION_TEMPLATES)
      .then((res) => res.data);
  };

const createRuleFromTemplate = async (
  input: ICreateRuleFromTemplateRequest,
): Promise<ICreateRuleFromTemplateResponse> => {
  const { template_id, ...ruleData } = input;
  return await api()
    .post<ICreateRuleFromTemplateResponse>(
      API_ENDPOINTS.VALIDATION_TEMPLATE_CREATE_RULE(template_id),
      ruleData,
    )
    .then((res) => res.data);
};

// Pipeline Integration
const addValidationToPipeline = async (
  input: IAddValidationToPipelineRequest,
): Promise<IAddValidationToPipelineResponse> => {
  const { pipeline_id, ...validationData } = input;
  return await api()
    .post<IAddValidationToPipelineResponse>(
      API_ENDPOINTS.VALIDATION_ADD_TO_PIPELINE(pipeline_id),
      validationData,
    )
    .then((res) => res.data);
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
