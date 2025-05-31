import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IGetFileContentRequest,
  IGetFileContentResponse,
  IGetFileUploadRequest,
  IGetFileUploadResponse,
  IGetFileUploadsRequest,
  IGetFileUploadsResponse,
  IGetFilePublicUrlRequest,
  IGetFilePublicUrlResponse,
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { UploadService } from "../../services/upload";

// Fetch all file uploads
export const useFileUploads = (
  input: IGetFileUploadsRequest,
  options?: UseQueryOptions<IGetFileUploadsResponse, Error>,
) => {
  return useQuery<IGetFileUploadsResponse, Error>({
    queryKey: QueryKeys.fileUploads.list(input),
    queryFn: () => UploadService.readUploadFiles(input),
    ...options,
  });
};

// Fetch a specific file upload
export const useFileUpload = (
  input: IGetFileUploadRequest,
  options?: UseQueryOptions<IGetFileUploadResponse, Error>,
) => {
  return useQuery<IGetFileUploadResponse, Error>({
    queryKey: QueryKeys.fileUploads.details(input.id),
    queryFn: () => UploadService.readUploadFile(input),
    ...options,
  });
};

// Fetch file content
export const useFileContent = (
  input: IGetFileContentRequest,
  options?: UseQueryOptions<IGetFileContentResponse, Error>,
) => {
  return useQuery<IGetFileContentResponse, Error>({
    queryKey: QueryKeys.fileUploads.content(input.id),
    queryFn: () => UploadService.getFileContent(input),
    ...options,
  });
};

export const useFilePublicUrl = (
  input: IGetFilePublicUrlRequest,
  options?: UseQueryOptions<IGetFilePublicUrlResponse, Error>,
) => {
  return useQuery<IGetFilePublicUrlResponse, Error>({
    queryKey: QueryKeys.fileUploads.publicUrl(input.id),
    queryFn: () => UploadService.getFilePublicUrl(input),
    ...options,
  });
};
