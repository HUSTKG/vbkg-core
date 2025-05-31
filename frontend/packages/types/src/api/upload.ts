import {
  ApiResponse,
  FileUpload,
  FileUploadStatus,
  PaginatedResponse,
} from "../models";
export interface IUploadFileRequest {
  datasource_id?: string;
  file: File;
  metadata?: Record<string, any>;
}
export interface IUploadFileResponse extends ApiResponse<FileUpload> {}

export interface IGetFileUploadsRequest {
  datasource_id?: string;
  status?: FileUploadStatus;
  processed?: boolean;
  skip?: number;
  limit?: number;
}
export interface IGetFileUploadsResponse
  extends PaginatedResponse<FileUpload> {}

export interface IGetFileUploadRequest {
  id: string;
}
export interface IGetFileUploadResponse extends ApiResponse<FileUpload> {}

export interface IUpdateFileStatusRequest {
  id: string;
  status: FileUploadStatus;
  error_message?: string;
  processed?: boolean;
}
export interface IUpdateFileStatusResponse extends ApiResponse<FileUpload> {}

export interface IDeleteFileUploadRequest {
  id: string;
}
export interface IDeleteFileUploadResponse extends ApiResponse<unknown> {}

export interface IGetFileContentRequest {
  id: string;
}
export interface IGetFileContentResponse {}

export interface IUpdateFileMetadataRequest {
  id: string;
  metadata: Record<string, any>;
}

export interface IUpdateFileMetadataResponse extends ApiResponse<FileUpload> {}

export interface IGetFilePublicUrlRequest {
  id: string;
}

export interface IGetFilePublicUrlResponse extends ApiResponse<string> {}
