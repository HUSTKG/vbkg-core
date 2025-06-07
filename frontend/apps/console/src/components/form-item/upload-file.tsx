import { useState } from "react";
import { Upload, X } from "lucide-react";
import { Button, toast } from "@/components";
import { formatBytes } from "../../utils/formatBytes";
import FileSelectorDialog, { SelectedFile } from "../dialog/file-selector";
import { getFileIcon } from "../../utils/getFileIcon";
import { FileUpload } from "@vbkg/types";
import { useUploadFile } from "@vbkg/api-client";

interface FileUploadFormItemProps {
	onChange: (files: FileUpload[]) => void;
	multiple?: boolean;
	maxFiles?: number;
}

const FileUploadFormItem = ({
	onChange,
	multiple = true,
	maxFiles = 10,
}: FileUploadFormItemProps) => {
	const [dialogOpen, setDialogOpen] = useState(false);

	// Handles removing a file from the selection
	const handleRemoveFile = () => {
		setValue([])
	};

	const [value, setValue] = useState<FileUpload[]>([]);

	const { mutateAsync: uploadFile } = useUploadFile({
		onSuccess: () => {
			toast.success("File uploaded successfully");
		},
		onError: (error) => {
			toast.error(`Failed to upload file: ${error.message || "Unknown error"}`);
		},
	});

	// Handles files selected from the FileSelector component
	const handleFilesSelected = async (newFiles: SelectedFile[]) => {
		// If multiple is false, we only take the first file
		const filesToAdd = multiple ? newFiles : newFiles.slice(0, 1);

		// If there's a max limit, respect it
		const availableSlots = maxFiles - value.length;
		const limitedFiles =
			availableSlots > 0 ? filesToAdd.slice(0, availableSlots) : [];

		const response = await Promise.all(
			limitedFiles.map(async (file) => {
				// Create a FileUpload object
				return uploadFile({
					file: file.file,
					metadata: file.metadata || {},
				});
			}),
		);

		setValue((prev) => [...prev, ...response.map((item) => item.data)]);

		onChange(response.map((item) => item.data));

		setDialogOpen(false);
	};

	return (
		<>
			<div className="space-y-2">
				{/* File list */}
				{value.length > 0 && (
					<div className="space-y-1">
						{value.map((fileItem, index) => (
							<div
								key={index}
								className="flex items-center justify-between p-2 border rounded-md bg-gray-50"
							>
								<div className="flex items-center gap-2 overflow-hidden">
									{getFileIcon(fileItem.file_type)}
									<span className="text-sm truncate">{fileItem.file_name}</span>
									<span className="text-xs text-gray-500">
										{formatBytes(fileItem.file_size)}
									</span>
									{fileItem.metadata &&
										Object.keys(fileItem.metadata).length > 0 && (
											<span className="text-xs text-green-600">
												{Object.keys(fileItem.metadata).length} metadata fields
											</span>
										)}
								</div>
								<Button
									type="button"
									size="sm"
									className="h-7 w-7 p-0"
									onClick={() => handleRemoveFile()}
								>
									<X size={16} />
								</Button>
							</div>
						))}
					</div>
				)}

				{/* Upload button */}
				{(multiple || value.length === 0) && value.length < maxFiles && (
					<Button
						type="button"
						variant={value.length > 0 ? "secondary" : "default"}
						onClick={() => setDialogOpen(true)}
						className="w-full"
					>
						<Upload className="mr-2 h-4 w-4" />
						{value.length === 0 ? "Upload Files" : "Upload More Files"}
					</Button>
				)}
			</div>

			{/* File selector dialog */}
			<FileSelectorDialog
				open={dialogOpen}
				onOpenChange={setDialogOpen}
				maxFiles={maxFiles - value.length}
				multiple
				onSelect={handleFilesSelected}
			/>
		</>
	);
};

export default FileUploadFormItem;
