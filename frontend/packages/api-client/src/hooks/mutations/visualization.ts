import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
  ICreateVisualizationRequest,
  ICreateDefaultVisualizationRequest,
  ICreateDefaultVisualizationResponse,
  IUpdateVisualizationRequest,
  IUpdateVisualizationResponse,
  IDeleteVisualizationRequest,
  IDeleteVisualizationResponse,
} from "@vbkg/types";
import { VisualizationService } from "../../services/visualization";

// Create visualization
export const useCreateVisualization = (
  options: UseMutationOptions<any, Error, ICreateVisualizationRequest>,
) => {
  return useMutation<any, Error, ICreateVisualizationRequest>({
    mutationFn: VisualizationService.createVisualization,
    ...options,
  });
};

// Create default visualization
export const useCreateDefaultVisualization = (
  options: UseMutationOptions<
    ICreateDefaultVisualizationResponse,
    Error,
    ICreateDefaultVisualizationRequest
  >,
) => {
  return useMutation<
    ICreateDefaultVisualizationResponse,
    Error,
    ICreateDefaultVisualizationRequest
  >({
    mutationFn: VisualizationService.createDefaultVisualization,
    ...options,
  });
};

// Update visualization
export const useUpdateVisualization = (
  options: UseMutationOptions<
    IUpdateVisualizationResponse,
    Error,
    IUpdateVisualizationRequest
  >,
) => {
  return useMutation<
    IUpdateVisualizationResponse,
    Error,
    IUpdateVisualizationRequest
  >({
    mutationFn: VisualizationService.updateVisualization,
    ...options,
  });
};

// Delete visualization
export const useDeleteVisualization = (
  options: UseMutationOptions<
    IDeleteVisualizationResponse,
    Error,
    IDeleteVisualizationRequest
  >,
) => {
  return useMutation<
    IDeleteVisualizationResponse,
    Error,
    IDeleteVisualizationRequest
  >({
    mutationFn: VisualizationService.deleteVisualization,
    ...options,
  });
};
