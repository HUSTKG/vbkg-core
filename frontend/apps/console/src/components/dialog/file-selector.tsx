import { Button, cn, Dialog, Input, ScrollArea } from "@/components";
import { ListIcon, Plus, Upload, X } from "lucide-react";
import React, { useState } from "react";
import { formatBytes } from "../../utils/formatBytes";
import { getFileIcon } from "../../utils/getFileIcon";

export type SelectedFile = {
	file: File;
	metadata: Record<string, string>;
};

interface FileSelectorProps {
	onSelect: (files: SelectedFile[]) => void;
	multiple?: boolean;
	maxFiles?: number;
	open: boolean;
	onOpenChange: (open: boolean) => void;
}

const FileSelectorDialog = ({
	onSelect,
	multiple = true,
	maxFiles = 10,
	open,
	onOpenChange,
}: FileSelectorProps) => {
	const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
	const [metadataDialogOpen, setMetadataDialogOpen] = useState(false);
	const [editingFile, setEditingFile] = useState<SelectedFile | null>(null);
	const [viewingFile, setViewingFile] = useState<SelectedFile | null>(null);
	const [currentMetadata, setCurrentMetadata] = useState<
		Record<string, string>
	>({});
	const [newMetadataKey, setNewMetadataKey] = useState("");
	const [newMetadataValue, setNewMetadataValue] = useState("");

	// Common metadata fields (can be customized based on your needs)
	const commonMetadataFields = [
		"author",
		"pages",
		"company",
		"department",
		"version",
		"status",
		"category",
		"project",
		"language",
		"confidentiality",
	];

	// Handle new file upload
	const handleFileUpload = async (
		event: React.ChangeEvent<HTMLInputElement>,
	) => {
		const files = event.target.files;
		if (files && files.length > 0) {
			const newFiles = Array.from(files).map((file) => ({
				file,
				metadata: {},
			}));

			if (!multiple) {
				// For single selection, replace existing files
				setSelectedFiles([
					{
						file: newFiles[0].file,
						metadata: newFiles[0].metadata,
					},
				]);
			} else {
				// For multiple selection, respect maxFiles
				setSelectedFiles((prev) => {
					const updatedFiles = [...prev, ...newFiles];
					if (updatedFiles.length > maxFiles) {
						return updatedFiles.slice(0, maxFiles);
					}
					return updatedFiles;
				});
			}
		}
	};

	// Clear uploaded files
	const clearUploadedFiles = () => {
		setSelectedFiles([]);
		setViewingFile(null);
	};

	// Remove a specific uploaded file
	const removeUploadedFile = (index: number) => {
		setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
		setViewingFile(null);
	};

	// Open metadata dialog for a file
	const openMetadataDialog = (file: SelectedFile) => {
		setEditingFile(file);
		setCurrentMetadata(file.metadata || {});
		setMetadataDialogOpen(true);
	};

	// Add a new metadata field
	const addMetadataField = () => {
		if (newMetadataKey.trim() && !currentMetadata[newMetadataKey]) {
			setCurrentMetadata((prev) => ({
				...prev,
				[newMetadataKey]: newMetadataValue,
			}));
			setNewMetadataKey("");
			setNewMetadataValue("");
		}
	};

	// Update a metadata field value
	const updateMetadataField = (key: string, value: string) => {
		setCurrentMetadata((prev) => ({
			...prev,
			[key]: value,
		}));
	};

	// Remove a metadata field
	const removeMetadataField = (key: string) => {
		setCurrentMetadata((prev) => {
			const newMetadata = { ...prev };
			delete newMetadata[key];
			return newMetadata;
		});
	};

	// Save metadata to the file
	const saveMetadata = () => {
		if (editingFile) {
			setSelectedFiles((prev) =>
				prev.map((file) =>
					file.file.name === editingFile.file.name
						? { ...file, metadata: currentMetadata }
						: file,
				),
			);
			setViewingFile({
				...editingFile,
				metadata: currentMetadata,
			});
			setMetadataDialogOpen(false);
			setEditingFile(null);
		}
	};

	// Handle final file selection
	const handleConfirmSelection = () => {
		if (selectedFiles.length > 0) {
			onSelect(selectedFiles);
			setSelectedFiles([]);
			setViewingFile(null);
		}
	};

	return (
		<Dialog
			open={open}
			showFooter={false}
			onOpenChange={onOpenChange}
			title="Chọn File"
			description="Chọn file để tải lên"
			size="2xl"
		>
			<div className="space-y-4">
				<div className="border-2 border-dashed rounded-md border-gray-300 p-8 text-center">
					<div>
						<Upload className="mx-auto h-12 w-12 text-gray-400" />
						<div className="mt-4 flex flex-col items-center">
							<p className="text-sm font-medium text-gray-900">
								Kéo và thả hoặc{" "}
								<span className="text-blue-600 cursor-pointer">chọn tệp</span>{" "}
								để tải lên
							</p>
							<p className="text-xs text-gray-500">Giới hạn tối đa 10MB</p>
							<label htmlFor="file-upload" className="mt-4 cursor-pointer">
								<div
									role="button"
									className="rounded-md bg-black/70 text-sm hover:bg-black p-2 text-white"
								>
									Chọn tệp
								</div>
								<input
									id="file-upload"
									name="file-upload"
									type="file"
									multiple={multiple}
									className="sr-only"
									onChange={handleFileUpload}
								/>
							</label>
						</div>
					</div>
				</div>

				{/* Uploaded files list */}
				{selectedFiles.length > 0 && (
					<div className="border rounded-md">
						<div className="p-3 border-b bg-gray-50 flex justify-between items-center">
							<h3 className="text-sm font-medium">
								File đã chọn ({selectedFiles.length}/{maxFiles})
							</h3>
							<Button size="sm" onClick={clearUploadedFiles}>
								Xóa tất cả
							</Button>
						</div>
						<ScrollArea className="max-h-[280px]">
							<div className="p-2 space-y-2">
								{selectedFiles.map((file, index) => (
									<div
										key={index}
										onClick={() => setViewingFile(file)}
										className={cn(
											"flex cursor-pointer hover:bg-gray-100 items-center justify-between p-2 border rounded-md",
											viewingFile?.file.name === file.file.name
												? "bg-sky-50 border-sky-200"
												: "",
										)}
									>
										<div className="flex items-center">
											{getFileIcon("pdf")}
											<div className="ml-1 flex-1 min-w-0">
												<p className="font-medium truncate text-xs">
													{file.file.name}
												</p>
												<p className="text-xs text-gray-500">
													{formatBytes(file.file.size)}
												</p>
											</div>
										</div>
										<div className="flex items-center gap-2">
											<Button
												size="icon"
												variant="outline"
												onClick={() => openMetadataDialog(file)}
											>
												<ListIcon size={16} />
											</Button>
											<Button
												size="icon"
												variant="outline"
												onClick={() => removeUploadedFile(index)}
											>
												<X size={16} />
											</Button>
										</div>
									</div>
								))}
							</div>
						</ScrollArea>
					</div>
				)}
			</div>

			{/* File details section */}
			{(viewingFile || selectedFiles.length > 0) && (
				<div className="mt-6 border rounded-md">
					<div className="p-3 border-b bg-gray-50 flex items-center justify-between">
						<h3 className="text-sm font-semibold">Thông tin chi tiết</h3>
						{viewingFile && (
							<Button
								size="icon"
								variant="outline"
								onClick={() => setViewingFile(null)}
							>
								<X size={16} />
							</Button>
						)}
					</div>
					<div className="p-4">
						{viewingFile ? (
							<div className="space-y-2">
								<div className="grid grid-cols-2 gap-2">
									<p className="text-sm font-medium">Tên tài liệu:</p>
									<p className="text-sm">{viewingFile.file.name}</p>

									<p className="text-sm font-medium">Loại:</p>
									<p className="text-sm">{viewingFile?.file.type}</p>

									<p className="text-sm font-medium">Dung lượng:</p>
									<p className="text-sm">
										{formatBytes(viewingFile?.file.size || 0)}
									</p>

									{viewingFile?.metadata &&
										Object.entries(viewingFile?.metadata || {}).map(
											([key, value]) => (
												<React.Fragment key={key}>
													<p className="text-sm font-medium">
														{key.charAt(0).toUpperCase() + key.slice(1)}:
													</p>
													<p className="text-sm">{value}</p>
												</React.Fragment>
											),
										)}
								</div>
							</div>
						) : selectedFiles.length > 0 ? (
							<div className="space-y-2">
								<div className="grid grid-cols-2 gap-2">
									<p className="text-sm font-medium">Số lượng:</p>
									<p className="text-sm">{selectedFiles.length}</p>

									<p className="text-sm font-medium">Tổng dung lượng:</p>
									<p className="text-sm">
										{formatBytes(
											selectedFiles.reduce(
												(total, file) => total + file.file.size,
												0,
											),
										)}
									</p>

									<p className="text-sm font-medium">Loại:</p>
									<p className="text-sm">
										{Array.from(
											new Set(
												selectedFiles.map(
													(file) => file.file.type.split("/")[1],
												),
											),
										).join(", ")}
									</p>

									<p className="text-sm font-medium">Tệp có Metadata:</p>
									<p className="text-sm">
										{
											selectedFiles.filter(
												(file) => Object.keys(file.metadata || {}).length > 0,
											).length
										}{" "}
										of {selectedFiles.length}
									</p>
								</div>
							</div>
						) : null}
					</div>
				</div>
			)}
			<div className="flex justify-between">
				<div className="flex ml-auto mt-4 space-x-2">
					<Button
						onClick={() => {
							setSelectedFiles([]);
							setViewingFile(null);
							onOpenChange(false);
						}}
						variant="outline"
					>
						Hủy
					</Button>
					<Button
						disabled={selectedFiles.length === 0}
						onClick={handleConfirmSelection}
					>
						Xác nhận
					</Button>
				</div>
			</div>
			<Dialog
				showFooter
				title="Sửa Metadata"
				primaryActionText="Lưu"
				onPrimaryAction={saveMetadata}
				open={metadataDialogOpen}
				onOpenChange={setMetadataDialogOpen}
			>
				<div className="space-y-4">
					<div className="flex items-center space-x-2">
						{editingFile && getFileIcon(editingFile.file.type)}
						<span className="font-medium text-sm truncate">
							{editingFile?.file.name}
						</span>
					</div>

					{/* Current metadata fields */}
					<div className="space-y-2">
						<div className="text-sm font-medium">Metadata hiện tại:</div>
						{Object.keys(currentMetadata).length === 0 && (
							<p className="text-sm text-gray-500">Chưa có Metadata.</p>
						)}
						{Object.entries(currentMetadata).map(([key, value]) => (
							<div key={key} className="flex items-center space-x-2">
								<Input
									value={value}
									onChange={(e) => updateMetadataField(key, e.target.value)}
									className="flex-1 h-8"
								/>
								<Button
									size="icon"
									variant="outline"
									onClick={() => removeMetadataField(key)}
									className="h-8 w-8 p-0"
								>
									<X size={14} />
								</Button>
							</div>
						))}
					</div>

					{/* Add new metadata field */}
					<div className="space-y-2 pt-2 border-t">
						<div className="text-sm font-medium">Thêm trường:</div>
						<div className="flex space-x-2">
							<div className="flex-1">
								<Input
									list="metadata-suggestions"
									placeholder="Tên trường"
									value={newMetadataKey}
									onChange={(e) => setNewMetadataKey(e.target.value)}
									className="h-8"
								/>
								<datalist id="metadata-suggestions">
									{commonMetadataFields
										.filter(
											(field) => !Object.keys(currentMetadata).includes(field),
										)
										.map((field) => (
											<option key={field} value={field} />
										))}
								</datalist>
							</div>
							<Input
								placeholder="Giá trị"
								value={newMetadataValue}
								onChange={(e) => setNewMetadataValue(e.target.value)}
								className="flex-1 h-8"
							/>
							<Button
								size="icon"
								variant="outline"
								onClick={addMetadataField}
								className="h-8 px-2"
								disabled={!newMetadataKey.trim()}
							>
								<Plus size={14} />
							</Button>
						</div>

						{/* Common fields suggestions */}
						<div className="flex flex-wrap gap-1 mt-2">
							{commonMetadataFields
								.filter(
									(field) => !Object.keys(currentMetadata).includes(field),
								)
								.slice(0, 5)
								.map((field) => (
									<Button
										key={field}
										type="button"
										variant="outline"
										size="sm"
										className="h-6 text-xs"
										onClick={() => setNewMetadataKey(field)}
									>
										{field}
									</Button>
								))}
						</div>
					</div>
				</div>
			</Dialog>
		</Dialog>
	);
};

export default FileSelectorDialog;
