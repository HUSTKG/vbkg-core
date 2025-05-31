import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IGetValidationRulesRequest,
  IGetValidationRulesResponse,
  IGetValidationRuleRequest,
  IGetValidationRuleResponse,
  IGetValidationExecutionsRequest,
  IGetValidationExecutionsResponse,
  IGetValidationExecutionRequest,
  IGetValidationExecutionResponse,
  IGetValidationViolationsRequest,
  IGetValidationViolationsResponse,
  IGetValidationDashboardResponse,
  IGetValidationPerformanceRequest,
  IGetValidationPerformanceResponse,
  IGetValidationSummaryResponse,
  IGetValidationTemplatesResponse,
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { ValidationRulesService } from "../../services/validation-rules";

// Validation Rules Queries
export const useValidationRules = (
  input: IGetValidationRulesRequest,
  options?: UseQueryOptions<IGetValidationRulesResponse, Error>,
) => {
  return useQuery<IGetValidationRulesResponse, Error>({
    queryKey: QueryKeys.validationRules.list(input),
    queryFn: () => ValidationRulesService.getValidationRules(input),
    ...options,
  });
};

export const useValidationRule = (
  input: IGetValidationRuleRequest,
  options?: UseQueryOptions<IGetValidationRuleResponse, Error>,
) => {
  return useQuery<IGetValidationRuleResponse, Error>({
    queryKey: QueryKeys.validationRules.details(input.rule_id),
    queryFn: () => ValidationRulesService.getValidationRule(input),
    enabled: !!input.rule_id,
    ...options,
  });
};

// Rule Executions Queries
export const useValidationExecutions = (
  input: IGetValidationExecutionsRequest,
  options?: UseQueryOptions<IGetValidationExecutionsResponse, Error>,
) => {
  return useQuery<IGetValidationExecutionsResponse, Error>({
    queryKey: QueryKeys.validationRules.executions.list(input),
    queryFn: () => ValidationRulesService.getValidationExecutions(input),
    ...options,
  });
};

export const useValidationExecution = (
  input: IGetValidationExecutionRequest,
  options?: UseQueryOptions<IGetValidationExecutionResponse, Error>,
) => {
  return useQuery<IGetValidationExecutionResponse, Error>({
    queryKey: QueryKeys.validationRules.executions.details(input.execution_id),
    queryFn: () => ValidationRulesService.getValidationExecution(input),
    enabled: !!input.execution_id,
    ...options,
  });
};

// Violations Queries
export const useValidationViolations = (
  input: IGetValidationViolationsRequest,
  options?: UseQueryOptions<IGetValidationViolationsResponse, Error>,
) => {
  return useQuery<IGetValidationViolationsResponse, Error>({
    queryKey: QueryKeys.validationRules.violations.list(input),
    queryFn: () => ValidationRulesService.getValidationViolations(input),
    ...options,
  });
};

// Dashboard & Statistics Queries
export const useValidationDashboard = (
  options?: Partial<UseQueryOptions<IGetValidationDashboardResponse, Error>>,
) => {
  return useQuery<IGetValidationDashboardResponse, Error>({
    queryKey: QueryKeys.validationRules.dashboard(),
    queryFn: () => ValidationRulesService.getValidationDashboard(),
    ...options,
  });
};

export const useValidationPerformance = (
  input: IGetValidationPerformanceRequest,
  options?: Partial<UseQueryOptions<IGetValidationPerformanceResponse, Error>>,
) => {
  return useQuery<IGetValidationPerformanceResponse, Error>({
    queryKey: QueryKeys.validationRules.performance(input.rule_ids),
    queryFn: () => ValidationRulesService.getValidationPerformance(input),
    ...options,
  });
};

export const useValidationSummary = (
  options?: Partial<UseQueryOptions<IGetValidationSummaryResponse, Error>>,
) => {
  return useQuery<IGetValidationSummaryResponse, Error>({
    queryKey: QueryKeys.validationRules.summary(),
    queryFn: () => ValidationRulesService.getValidationSummary(),
    ...options,
  });
};

// Templates Queries
export const useValidationTemplates = (
  options?: UseQueryOptions<IGetValidationTemplatesResponse, Error>,
) => {
  return useQuery<IGetValidationTemplatesResponse, Error>({
    queryKey: QueryKeys.validationRules.templates(),
    queryFn: () => ValidationRulesService.getValidationTemplates(),
    ...options,
  });
};

// Combined Dashboard Query
export const useValidationDashboardData = (options?: {
  enableDashboard?: boolean;
  enableSummary?: boolean;
  enablePerformance?: boolean;
  performanceRuleIds?: string[];
}) => {
  const {
    enableDashboard = true,
    enableSummary = true,
    enablePerformance = true,
    performanceRuleIds,
  } = options || {};

  const dashboardQuery = useValidationDashboard({
    enabled: enableDashboard,
  });

  const summaryQuery = useValidationSummary({
    enabled: enableSummary,
  });

  const performanceQuery = useValidationPerformance(
    { rule_ids: performanceRuleIds },
    {
      enabled: enablePerformance,
    },
  );

  return {
    dashboard: dashboardQuery,
    summary: summaryQuery,
    performance: performanceQuery,
    isLoading:
      dashboardQuery.isLoading ||
      summaryQuery.isLoading ||
      performanceQuery.isLoading,
    isError:
      dashboardQuery.isError ||
      summaryQuery.isError ||
      performanceQuery.isError,
    error: dashboardQuery.error || summaryQuery.error || performanceQuery.error,
  };
};

// Rule Statistics Hook
export const useRuleStatistics = (ruleId: string) => {
  const ruleQuery = useValidationRule({ rule_id: ruleId });
  const executionsQuery = useValidationExecutions({
    rule_id: ruleId,
    limit: 10,
  });
  const violationsQuery = useValidationViolations({
    rule_id: ruleId,
    limit: 20,
  });

  return {
    rule: ruleQuery.data?.data,
    executions: executionsQuery.data?.data || [],
    violations: violationsQuery.data?.data || [],
    isLoading:
      ruleQuery.isLoading ||
      executionsQuery.isLoading ||
      violationsQuery.isLoading,
    isError:
      ruleQuery.isError || executionsQuery.isError || violationsQuery.isError,
    error: ruleQuery.error || executionsQuery.error || violationsQuery.error,
    refetch: () => {
      ruleQuery.refetch();
      executionsQuery.refetch();
      violationsQuery.refetch();
    },
  };
};

// Recent Activity Hook
export const useRecentValidationActivity = () => {
  const recentExecutions = useValidationExecutions({ limit: 10 });
  const recentViolations = useValidationViolations({ limit: 10 });

  return {
    executions: recentExecutions.data?.data || [],
    violations: recentViolations.data?.data || [],
    isLoading: recentExecutions.isLoading || recentViolations.isLoading,
    isError: recentExecutions.isError || recentViolations.isError,
    error: recentExecutions.error || recentViolations.error,
    refetch: () => {
      recentExecutions.refetch();
      recentViolations.refetch();
    },
  };
};
