import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  ISearchEntitiesRequest,
  ISearchEntitiesResponse,
  IFindSimilarEntitiesRequest,
  IFindSimilarEntitiesResponse,
  IGraphSearchRequest,
  IGraphSearchResponse,
} from "@vbkg/types";
import { SearchService } from "../../services/search";

// Search entities
export const useSearchEntities = (
  input: ISearchEntitiesRequest,
  options?: Partial<UseQueryOptions<ISearchEntitiesResponse, Error>>,
) => {
  return useQuery<ISearchEntitiesResponse, Error>({
    queryKey: ["searchEntities", input],
    queryFn: () => SearchService.searchEntities(input),
    ...options,
  });
};

// Find similar entities
export const useFindSimilarEntities = (
  input: IFindSimilarEntitiesRequest,
  options?: Partial<UseQueryOptions<IFindSimilarEntitiesResponse, Error>>,
) => {
  return useQuery<IFindSimilarEntitiesResponse, Error>({
    queryKey: ["findSimilarEntities", input],
    queryFn: () => SearchService.findSimilarEntities(input),
    ...options,
  });
};

// Graph search
export const useGraphSearch = (
  input: IGraphSearchRequest,
  options?: Partial<UseQueryOptions<IGraphSearchResponse, Error>>,
) => {
  return useQuery<IGraphSearchResponse, Error>({
    queryKey: ["graphSearch", input],
    queryFn: () => SearchService.graphSearch(input),
    ...options,
  });
};
