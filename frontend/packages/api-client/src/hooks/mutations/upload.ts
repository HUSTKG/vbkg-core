import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  IDeleteFileUploadRequest,
  IDeleteFileUploadResponse,
  IUpdateFileStatusRequest,
  IUpdateFileStatusResponse,
  IUploadFileRequest,
  IUploadFileResponse,
  IUpdateFileMetadataRequest,
  IUpdateFileMetadataResponse,
} from "@vbkg/types";
import { UploadService } from "../../services/upload";
import { QueryKeys } from "../../config/queryKeys";

// File upload operations
export const useUploadFile = (
  options: UseMutationOptions<IUploadFileResponse, Error, IUploadFileRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IUploadFileResponse, Error, IUploadFileRequest>({
    mutationFn: UploadService.uploadFile,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.fileUploads.list(),
      });
      options.onSuccess?.(...params);
    },
  });
};

export const useDeleteFileUpload = (
  options: UseMutationOptions<
    IDeleteFileUploadResponse,
    Error,
    IDeleteFileUploadRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IDeleteFileUploadResponse,
    Error,
    IDeleteFileUploadRequest
  >({
    mutationFn: UploadService.deleteFileUpload,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.fileUploads.list(),
      });
      options.onSuccess?.(...params);
    },
  });
};

export const useUpdateFileStatus = (
  options: UseMutationOptions<
    IUpdateFileStatusResponse,
    Error,
    IUpdateFileStatusRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IUpdateFileStatusResponse,
    Error,
    IUpdateFileStatusRequest
  >({
    mutationFn: UploadService.updateFileStatus,
    ...options,
    onSuccess: (data, input, ...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.fileUploads.details(input.id),
      });
      options.onSuccess?.(data, input, ...params);
    },
  });
};

export const useUpdateFileMetadata = (
  options: UseMutationOptions<
    IUpdateFileMetadataResponse,
    Error,
    IUpdateFileMetadataRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IUpdateFileMetadataResponse,
    Error,
    IUpdateFileMetadataRequest
  >({
    mutationFn: UploadService.updateFileMetadata,
    ...options,
    onSuccess: (data, input, ...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.fileUploads.details(input.id),
      });
      options.onSuccess?.(data, input, ...params);
    },
  });
};
