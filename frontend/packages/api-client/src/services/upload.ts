import {
	IDeleteFileUploadRequest,
	IDeleteFileUploadResponse,
	IGetFileContentRequest,
	IUpdateFileMetadataRequest,
	IGetFileContentResponse,
	IGetFileUploadRequest,
	IGetFileUploadResponse,
	IGetFileUploadsRequest,
	IGetFileUploadsResponse,
	IUpdateFileStatusRequest,
	IUpdateFileStatusResponse,
	IUploadFileRequest,
	IUploadFileResponse,
	IGetFilePublicUrlRequest,
	IGetFilePublicUrlResponse,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const uploadFile = async (
	input: IUploadFileRequest,
) => {
	const formData = new FormData();
	formData.append("datasource_id", input.datasource_id || "");
	formData.append("file", input.file);
	formData.append("metadata", JSON.stringify(input.metadata));
	return await api()
		.post<IUploadFileResponse>(API_ENDPOINTS.UPLOAD_FILE, formData)
};

const readUploadFiles = async (
	input: IGetFileUploadsRequest,
) => {
	return await api()
		.get<IGetFileUploadsResponse>(API_ENDPOINTS.READ_FILE_UPLOADS, {
			params: {
				...input,
			},
		})
};

const readUploadFile = async (
	input: IGetFileUploadRequest,
) => {
	return await api()
		.get<IGetFileUploadResponse>(API_ENDPOINTS.READ_FILE_UPLOAD(input.id), {
			params: {
				...input,
			},
		})
};

const deleteFileUpload = async (
	input: IDeleteFileUploadRequest,
) => {
	return await api()
		.delete<IDeleteFileUploadResponse>(
			API_ENDPOINTS.DELETE_FILE_UPLOAD(input.id),
		)
};

const updateFileStatus = async (
	input: IUpdateFileStatusRequest,
) => {
	return await api()
		.patch<IUpdateFileStatusResponse>(
			API_ENDPOINTS.UPDATE_FILE_STATUS(input.id),
			input,
		)
};

const getFileContent = async (
	input: IGetFileContentRequest,
): Promise<IGetFileContentResponse> => {
	return await api()
		.get<IGetFileContentResponse>(API_ENDPOINTS.READ_FILE_CONTENT(input.id), {
			params: {
				...input,
			},
		})
};

const updateFileMetadata = async (
	input: IUpdateFileMetadataRequest,
) => {
	return await api()
		.patch<IUploadFileResponse>(
			API_ENDPOINTS.UPDATE_FILE_METADATA(input.id),
			input,
		)
};

const getFilePublicUrl = async (
	input: IGetFilePublicUrlRequest,
) => {
	return await api()
		.get<IGetFilePublicUrlResponse>(
			API_ENDPOINTS.GET_FILE_PUBLIC_URL(input.id),
			{
				params: {
					...input,
				},
			},
		)
};

export const UploadService = {
	uploadFile,
	readUploadFiles,
	readUploadFile,
	deleteFileUpload,
	updateFileStatus,
	getFileContent,
	updateFileMetadata,
	getFilePublicUrl,
};
