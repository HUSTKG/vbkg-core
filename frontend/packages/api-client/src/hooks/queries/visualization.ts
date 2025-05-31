import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadVisualizationsRequest,
  IReadVisualizationRequest,
  IReadVisualizationResponse,
  IReadPublicVisualizationsRequest,
  IReadPublicVisualizationsResponse,
  IGetVisualizationDataRequest,
  IGetVisualizationDataResponse,
  IGetVisualizationTemplatesRequest,
  IGetVisualizationTemplatesResponse,
} from "@vbkg/types";
import { VisualizationService } from "../../services/visualization";

// Fetch all visualizations
export const useVisualizations = (
  input: IReadVisualizationsRequest,
  options?: UseQueryOptions<any, Error>,
) => {
  return useQuery<any, Error>({
    queryKey: ["visualizations", input],
    queryFn: () => VisualizationService.readVisualizations(input),
    ...options,
  });
};

// Fetch public visualizations
export const usePublicVisualizations = (
  input: IReadPublicVisualizationsRequest,
  options?: UseQueryOptions<IReadPublicVisualizationsResponse, Error>,
) => {
  return useQuery<IReadPublicVisualizationsResponse, Error>({
    queryKey: ["publicVisualizations", input],
    queryFn: () => VisualizationService.readPublicVisualizations(input),
    ...options,
  });
};

// Fetch a specific visualization
export const useVisualization = (
  input: IReadVisualizationRequest,
  options?: UseQueryOptions<IReadVisualizationResponse, Error>,
) => {
  return useQuery<IReadVisualizationResponse, Error>({
    queryKey: ["visualization", input.id],
    queryFn: () => VisualizationService.readVisualization(input),
    ...options,
  });
};

// Fetch visualization data
export const useVisualizationData = (
  input: IGetVisualizationDataRequest,
  options?: UseQueryOptions<IGetVisualizationDataResponse, Error>,
) => {
  return useQuery<IGetVisualizationDataResponse, Error>({
    queryKey: ["visualizationData", input.id],
    queryFn: () => VisualizationService.getVisualizationData(input),
    ...options,
  });
};

// Fetch visualization templates
export const useVisualizationTemplates = (
  input: IGetVisualizationTemplatesRequest,
  options?: UseQueryOptions<IGetVisualizationTemplatesResponse, Error>,
) => {
  return useQuery<IGetVisualizationTemplatesResponse, Error>({
    queryKey: ["visualizationTemplates", input],
    queryFn: () => VisualizationService.getVisualizationTemplates(input),
    ...options,
  });
};
