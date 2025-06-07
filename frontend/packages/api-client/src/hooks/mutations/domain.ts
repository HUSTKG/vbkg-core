import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
  ICreateDomainRequest,
  ICreateDomainResponse,
  IUpdateDomainRequest,
  IUpdateDomainResponse,
  IDeleteDomainRequest,
  IDeleteDomainResponse,
  ICreateEntityTypeRequest,
  ICreateEntityTypeResponse,
  IUpdateEntityTypeRequest,
  IUpdateEntityTypeResponse,
  IDeleteEntityTypeRequest,
  IDeleteEntityTypeResponse,
  ICreateRelationshipTypeRequest,
  ICreateRelationshipTypeResponse,
  IUpdateRelationshipTypeRequest,
  IUpdateRelationshipTypeResponse,
  IDeleteRelationshipTypeRequest,
  IDeleteRelationshipTypeResponse,
  IAddEntityTypeToDomainRequest,
  IAddEntityTypeToDomainResponse,
  IRemoveEntityTypeFromDomainRequest,
  IRemoveEntityTypeFromDomainResponse,
  IAddRelationshipTypeToDomainRequest,
  IAddRelationshipTypeToDomainResponse,
  IRemoveRelationshipTypeFromDomainRequest,
  IRemoveRelationshipTypeFromDomainResponse,
  IValidateTypeConstraintsRequest,
  IValidateTypeConstraintsResponse,
} from "@vbkg/types";
import { DomainService } from "../../services/domain";

// =============================================
// DOMAIN MUTATION HOOKS
// =============================================

export const useCreateDomain = (
  options?: UseMutationOptions<
    ICreateDomainResponse,
    Error,
    ICreateDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.createDomain,
    ...options,
  });
};

export const useUpdateDomain = (
  options?: UseMutationOptions<
    IUpdateDomainResponse,
    Error,
    IUpdateDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.updateDomain,
    ...options,
  });
};

export const useDeleteDomain = (
  options?: UseMutationOptions<
    IDeleteDomainResponse,
    Error,
    IDeleteDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.deleteDomain,
    ...options,
  });
};

// =============================================
// ENTITY TYPE MUTATION HOOKS
// =============================================

export const useCreateEntityType = (
  options?: UseMutationOptions<
    ICreateEntityTypeResponse,
    Error,
    ICreateEntityTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.createEntityType,
    ...options,
  });
};

export const useUpdateEntityType = (
  options?: UseMutationOptions<
    IUpdateEntityTypeResponse,
    Error,
    IUpdateEntityTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.updateEntityType,
    ...options,
  });
};

export const useDeleteEntityType = (
  options?: UseMutationOptions<
    IDeleteEntityTypeResponse,
    Error,
    IDeleteEntityTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.deleteEntityType,
    ...options,
  });
};

// =============================================
// RELATIONSHIP TYPE MUTATION HOOKS
// =============================================

export const useCreateRelationshipType = (
  options?: UseMutationOptions<
    ICreateRelationshipTypeResponse,
    Error,
    ICreateRelationshipTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.createRelationshipType,
    ...options,
  });
};

export const useUpdateRelationshipType = (
  options?: UseMutationOptions<
    IUpdateRelationshipTypeResponse,
    Error,
    IUpdateRelationshipTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.updateRelationshipType,
    ...options,
  });
};

export const useDeleteRelationshipType = (
  options?: UseMutationOptions<
    IDeleteRelationshipTypeResponse,
    Error,
    IDeleteRelationshipTypeRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.deleteRelationshipType,
    ...options,
  });
};

// =============================================
// DOMAIN MAPPING MUTATION HOOKS
// =============================================

export const useAddEntityTypeToDomain = (
  options?: UseMutationOptions<
    IAddEntityTypeToDomainResponse,
    Error,
    IAddEntityTypeToDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.addEntityTypeToDomain,
    ...options,
  });
};

export const useRemoveEntityTypeFromDomain = (
  options?: UseMutationOptions<
    IRemoveEntityTypeFromDomainResponse,
    Error,
    IRemoveEntityTypeFromDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.removeEntityTypeFromDomain,
    ...options,
  });
};

export const useAddRelationshipTypeToDomain = (
  options?: UseMutationOptions<
    IAddRelationshipTypeToDomainResponse,
    Error,
    IAddRelationshipTypeToDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.addRelationshipTypeToDomain,
    ...options,
  });
};

export const useRemoveRelationshipTypeFromDomain = (
  options?: UseMutationOptions<
    IRemoveRelationshipTypeFromDomainResponse,
    Error,
    IRemoveRelationshipTypeFromDomainRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.removeRelationshipTypeFromDomain,
    ...options,
  });
};

// =============================================
// VALIDATION MUTATION HOOKS
// =============================================

export const useValidateTypeConstraints = (
  options?: UseMutationOptions<
    IValidateTypeConstraintsResponse,
    Error,
    IValidateTypeConstraintsRequest
  >,
) => {
  return useMutation({
    mutationFn: DomainService.validateTypeConstraints,
    ...options,
  });
};

