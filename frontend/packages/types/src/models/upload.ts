export interface FileUploadBase {
  data_source_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
}

export interface FileUploadCreate extends FileUploadBase {
  metadata?: Record<string, any>;
}

export enum FileUploadStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed",
}
export interface FileUpload extends FileUploadBase {
  id: string;
  upload_status: FileUploadStatus;
  processed: boolean;
  metadata?: Record<string, any>;
  uploaded_by?: string;
  uploaded_at: string;
}
