import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { QueryKeys } from "../../config/queryKeys";
import { QualityService } from "../../services/quality";
import {
  IGetQualityDashboardRequest,
  IGetQualityDashboardResponse,
  IGenerateQualityReportRequest,
  IGenerateQualityReportResponse,
  IGetConflictsRequest,
  IGetConflictsResponse,
} from "@vbkg/types";

// Quality Dashboard
export const useQualityDashboard = (
  input: IGetQualityDashboardRequest,
  options?: UseQueryOptions<IGetQualityDashboardResponse, Error>,
) => {
  return useQuery<IGetQualityDashboardResponse, Error>({
    queryKey: QueryKeys.quality.dashboard(),
    queryFn: () => QualityService.getQualityDashboard(input),
    ...options,
  });
};

export const useQualityReport = (
  input: IGenerateQualityReportRequest,
  options?: UseQueryOptions<IGenerateQualityReportResponse, Error>,
) => {
  return useQuery<IGenerateQualityReportResponse, Error>({
    queryKey: QueryKeys.quality.report(input.days_back),
    queryFn: () => QualityService.generateQualityReport(input),
    ...options,
  });
};

// Conflicts
export const useConflicts = (
  input: IGetConflictsRequest,
  options?: UseQueryOptions<IGetConflictsResponse, Error>,
) => {
  return useQuery<IGetConflictsResponse, Error>({
    queryKey: QueryKeys.quality.conflicts.list(input),
    queryFn: () => QualityService.getConflicts(input),
    ...options,
  });
};
