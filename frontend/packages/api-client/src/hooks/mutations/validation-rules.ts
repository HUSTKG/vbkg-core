import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ICreateValidationRuleRequest,
  ICreateValidationRuleResponse,
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
  IUpdateValidationViolationRequest,
  IUpdateValidationViolationResponse,
  IBulkUpdateValidationViolationsRequest,
  IBulkUpdateValidationViolationsResponse,
  ICreateRuleFromTemplateRequest,
  ICreateRuleFromTemplateResponse,
  IAddValidationToPipelineRequest,
  IAddValidationToPipelineResponse,
} from "@vbkg/types";
import { ValidationRulesService } from "../../services/validation-rules";
import { QueryKeys } from "../../config/queryKeys";

// Validation Rules CRUD Mutations
export const useCreateValidationRule = (
  options?: UseMutationOptions<
    ICreateValidationRuleResponse,
    Error,
    ICreateValidationRuleRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    ICreateValidationRuleResponse,
    Error,
    ICreateValidationRuleRequest
  >({
    mutationFn: ValidationRulesService.createValidationRule,
    onSuccess: (data, variables, context) => {
      // Invalidate and refetch validation rules list
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.lists(),
      });

      // Invalidate dashboard and summary
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      // Set the new rule data in cache
      if (data.data) {
        queryClient.setQueryData(
          QueryKeys.validationRules.details(data.data.id),
          data,
        );
      }

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

export const useUpdateValidationRule = (
  options?: UseMutationOptions<
    IUpdateValidationRuleResponse,
    Error,
    IUpdateValidationRuleRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IUpdateValidationRuleResponse,
    Error,
    IUpdateValidationRuleRequest
  >({
    mutationFn: ValidationRulesService.updateValidationRule,
    onSuccess: (data, variables, context) => {
      // Invalidate lists
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.lists(),
      });

      // Update specific rule cache
      if (data.data) {
        queryClient.setQueryData(
          QueryKeys.validationRules.details(variables.rule_id),
          data,
        );
      }

      // Invalidate performance metrics
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.performance(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

export const useDeleteValidationRule = (
  options?: UseMutationOptions<
    IDeleteValidationRuleResponse,
    Error,
    IDeleteValidationRuleRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IDeleteValidationRuleResponse,
    Error,
    IDeleteValidationRuleRequest
  >({
    mutationFn: ValidationRulesService.deleteValidationRule,
    onSuccess: (data, variables, context) => {
      // Invalidate lists
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.lists(),
      });

      // Remove from cache
      queryClient.removeQueries({
        queryKey: QueryKeys.validationRules.details(variables.rule_id),
      });

      // Invalidate dashboard
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

export const useToggleValidationRule = (
  options?: UseMutationOptions<
    IToggleValidationRuleResponse,
    Error,
    IToggleValidationRuleRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IToggleValidationRuleResponse,
    Error,
    IToggleValidationRuleRequest
  >({
    mutationFn: ValidationRulesService.toggleValidationRule,
    onSuccess: (data, variables, context) => {
      // Update lists
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.lists(),
      });

      // Update specific rule cache
      if (data.data) {
        queryClient.setQueryData(
          QueryKeys.validationRules.details(variables.rule_id),
          data,
        );
      }

      // Update summary (active rules count changes)
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Rule Execution Mutations
export const useExecuteValidationRule = (
  options?: UseMutationOptions<
    IExecuteValidationRuleResponse,
    Error,
    IExecuteValidationRuleRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IExecuteValidationRuleResponse,
    Error,
    IExecuteValidationRuleRequest
  >({
    mutationFn: ValidationRulesService.executeValidationRule,
    onSuccess: (data, variables, context) => {
      // Invalidate executions list
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.executions.lists(),
      });

      // Invalidate violations (new violations might be created)
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.violations.lists(),
      });

      // Update rule statistics
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.details(variables.rule_id),
      });

      // Update dashboard
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

export const useExecuteBatchValidationRules = (
  options?: UseMutationOptions<
    IExecuteBatchValidationRulesResponse,
    Error,
    IExecuteBatchValidationRulesRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IExecuteBatchValidationRulesResponse,
    Error,
    IExecuteBatchValidationRulesRequest
  >({
    mutationFn: ValidationRulesService.executeBatchValidationRules,
    onSuccess: (data, variables, context) => {
      // Invalidate all execution-related queries
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.executions.all(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.violations.all(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.performance(),
      });

      // If specific rule IDs were provided, invalidate their details
      if (variables.rule_ids) {
        variables.rule_ids.forEach((ruleId) => {
          queryClient.invalidateQueries({
            queryKey: QueryKeys.validationRules.details(ruleId),
          });
        });
      }

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Violation Management Mutations
export const useUpdateValidationViolation = (
  options?: UseMutationOptions<
    IUpdateValidationViolationResponse,
    Error,
    IUpdateValidationViolationRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IUpdateValidationViolationResponse,
    Error,
    IUpdateValidationViolationRequest
  >({
    mutationFn: ValidationRulesService.updateValidationViolation,
    onSuccess: (data, variables, context) => {
      // Invalidate violations lists
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.violations.lists(),
      });

      // Update dashboard (violation counts might change)
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

export const useBulkUpdateValidationViolations = (
  options?: UseMutationOptions<
    IBulkUpdateValidationViolationsResponse,
    Error,
    IBulkUpdateValidationViolationsRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IBulkUpdateValidationViolationsResponse,
    Error,
    IBulkUpdateValidationViolationsRequest
  >({
    mutationFn: ValidationRulesService.bulkUpdateValidationViolations,
    onSuccess: (data, variables, context) => {
      // Invalidate violations lists
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.violations.lists(),
      });

      // Update dashboard
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Template Mutations
export const useCreateRuleFromTemplate = (
  options?: UseMutationOptions<
    ICreateRuleFromTemplateResponse,
    Error,
    ICreateRuleFromTemplateRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    ICreateRuleFromTemplateResponse,
    Error,
    ICreateRuleFromTemplateRequest
  >({
    mutationFn: ValidationRulesService.createRuleFromTemplate,
    onSuccess: (data, variables, context) => {
      // Invalidate rules list
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.lists(),
      });

      // Update template usage count
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.templates(),
      });

      // Set new rule in cache
      if (data.data) {
        queryClient.setQueryData(
          QueryKeys.validationRules.details(data.data.id),
          data,
        );
      }

      // Update dashboard
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.dashboard(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.validationRules.summary(),
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Pipeline Integration Mutations
export const useAddValidationToPipeline = (
  options?: UseMutationOptions<
    IAddValidationToPipelineResponse,
    Error,
    IAddValidationToPipelineRequest
  >,
) => {
  const queryClient = useQueryClient();

  return useMutation<
    IAddValidationToPipelineResponse,
    Error,
    IAddValidationToPipelineRequest
  >({
    mutationFn: ValidationRulesService.addValidationToPipeline,
    onSuccess: (data, variables, context) => {
      // Invalidate pipeline queries (assuming they exist)
      queryClient.invalidateQueries({
        queryKey: ["pipelines", variables.pipeline_id],
      });
      queryClient.invalidateQueries({
        queryKey: ["pipelines", "list"],
      });

      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Compound Mutations for Complex Operations
export const useValidationRuleOperations = () => {
  const createRule = useCreateValidationRule();
  const updateRule = useUpdateValidationRule();
  const deleteRule = useDeleteValidationRule();
  const toggleRule = useToggleValidationRule();
  const executeRule = useExecuteValidationRule();

  return {
    create: createRule,
    update: updateRule,
    delete: deleteRule,
    toggle: toggleRule,
    execute: executeRule,

    // Compound states
    isLoading:
      createRule.isPending ||
      updateRule.isPending ||
      deleteRule.isPending ||
      toggleRule.isPending ||
      executeRule.isPending,

    isError:
      createRule.isError ||
      updateRule.isError ||
      deleteRule.isError ||
      toggleRule.isError ||
      executeRule.isError,

    error:
      createRule.error ||
      updateRule.error ||
      deleteRule.error ||
      toggleRule.error ||
      executeRule.error,
  };
};
