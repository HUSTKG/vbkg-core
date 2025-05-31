import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
  ICreateEntityRequest,
  ICreateEntityResponse,
  IUpdateEntityRequest,
  IUpdateEntityResponse,
  IDeleteEntityRequest,
  IDeleteEntityResponse,
  ICreateRelationshipRequest,
  ICreateRelationshipResponse,
  ICreateOrMergeEntityRequest,
  ICreateOrMergeEntityResponse,
} from "@vbkg/types";
import { KnowledgeService } from "../../services/knowledge";

// Create entity
export const useCreateEntity = (
  options: UseMutationOptions<
    ICreateEntityResponse,
    Error,
    ICreateEntityRequest
  >,
) => {
  return useMutation<ICreateEntityResponse, Error, ICreateEntityRequest>({
    mutationFn: KnowledgeService.createEntityRequest,
    ...options,
  });
};

// Update entity
export const useUpdateEntity = (
  options: UseMutationOptions<
    IUpdateEntityResponse,
    Error,
    IUpdateEntityRequest
  >,
) => {
  return useMutation<IUpdateEntityResponse, Error, IUpdateEntityRequest>({
    mutationFn: KnowledgeService.updateEntity,
    ...options,
  });
};

// Delete entity
export const useDeleteEntity = (
  options: UseMutationOptions<
    IDeleteEntityResponse,
    Error,
    IDeleteEntityRequest
  >,
) => {
  return useMutation<IDeleteEntityResponse, Error, IDeleteEntityRequest>({
    mutationFn: KnowledgeService.deleteEntity,
    ...options,
  });
};

// Create relationship
export const useCreateRelationship = (
  options: UseMutationOptions<
    ICreateRelationshipResponse,
    Error,
    ICreateRelationshipRequest
  >,
) => {
  return useMutation<
    ICreateRelationshipResponse,
    Error,
    ICreateRelationshipRequest
  >({
    mutationFn: KnowledgeService.createRelationship,
    ...options,
  });
};

// Create or merge entity
export const useCreateOrMergeEntity = (
  options: UseMutationOptions<
    ICreateOrMergeEntityResponse,
    Error,
    ICreateOrMergeEntityRequest
  >,
) => {
  return useMutation<
    ICreateOrMergeEntityResponse,
    Error,
    ICreateOrMergeEntityRequest
  >({
    mutationFn: KnowledgeService.createOrMergeEntity,
    ...options,
  });
};
