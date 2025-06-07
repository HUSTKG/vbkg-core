import { Button, Dialog, Input, ScrollArea } from "@/components";
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
	};

	// Remove a specific uploaded file
	const removeUploadedFile = (index: number) => {
		setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
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
			// TODO: Add API call to save metadata
			setMetadataDialogOpen(false);
			setEditingFile(null);
		}
	};

	// Handle final file selection
	const handleConfirmSelection = () => {
		if (selectedFiles.length > 0) {
			onSelect(selectedFiles);
			setSelectedFiles([]);
		}
	};

	// Get currently selected file for details view
	const getSelectedFileForDetails = () => {
		if (selectedFiles.length > 0) {
			return selectedFiles[selectedFiles.length - 1]; // Show details of last selected file
		}
		return null;
	};

	return (
		<Dialog
			open={open}
			showFooter={false}
			onOpenChange={onOpenChange}
			title="File Selection"
			description="Choose existing files or upload new ones"
			size="2xl"
		>
			<div className="space-y-4">
				<div className="border-2 border-dashed rounded-md border-gray-300 p-8 text-center">
					<div>
						<Upload className="mx-auto h-12 w-12 text-gray-400" />
						<div className="mt-4 flex flex-col items-center">
							<p className="text-sm font-medium text-gray-900">
								Drag and drop or click to upload
							</p>
							<p className="text-xs text-gray-500">Up to 10MB per file</p>
							<label htmlFor="file-upload" className="mt-4 cursor-pointer">
								<div
									role="button"
									className="rounded-md bg-black/70 hover:bg-black p-2 text-white"
								>
									Select Files
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
								Uploaded Files ({selectedFiles.length}/{maxFiles})
							</h3>
							<Button size="sm" onClick={clearUploadedFiles}>
								Clear All
							</Button>
						</div>
						<ScrollArea className="max-h-[280px]">
							<div className="p-2 space-y-2">
								{selectedFiles.map((file, index) => (
									<div
										key={index}
										className="flex hover:bg-gray-100 items-center justify-between p-2 border rounded-md"
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
												size="sm"
												onClick={() => openMetadataDialog(file)}
											>
												<ListIcon size={16} />
											</Button>
											<Button
												size="sm"
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
			{(getSelectedFileForDetails() || selectedFiles.length > 0) && (
				<div className="mt-6 border rounded-md">
					<div className="p-3 border-b bg-gray-50">
						<h3 className="text-sm font-semibold">File Details</h3>
					</div>
					<div className="p-4">
						{getSelectedFileForDetails() ? (
							<div className="space-y-2">
								<div className="grid grid-cols-2 gap-2">
									<p className="text-sm font-medium">Name:</p>
									<p className="text-sm">
										{getSelectedFileForDetails()?.file.name}
									</p>

									<p className="text-sm font-medium">Type:</p>
									<p className="text-sm">
										{getSelectedFileForDetails()?.file.type}
									</p>

									<p className="text-sm font-medium">Size:</p>
									<p className="text-sm">
										{formatBytes(getSelectedFileForDetails()?.file.size || 0)}
									</p>

									{getSelectedFileForDetails()?.metadata &&
										Object.entries(
											getSelectedFileForDetails()?.metadata || {},
										).map(([key, value]) => (
											<React.Fragment key={key}>
												<p className="text-sm font-medium">
													{key.charAt(0).toUpperCase() + key.slice(1)}:
												</p>
												<p className="text-sm">{value}</p>
											</React.Fragment>
										))}
								</div>
							</div>
						) : selectedFiles.length > 0 ? (
							<div className="space-y-2">
								<div className="grid grid-cols-2 gap-2">
									<p className="text-sm font-medium">Total Files:</p>
									<p className="text-sm">{selectedFiles.length}</p>

									<p className="text-sm font-medium">Total Size:</p>
									<p className="text-sm">
										{formatBytes(
											selectedFiles.reduce(
												(total, file) => total + file.file.size,
												0,
											),
										)}
									</p>

									<p className="text-sm font-medium">Types:</p>
									<p className="text-sm">
										{Array.from(
											new Set(
												selectedFiles.map(
													(file) => file.file.type.split("/")[1],
												),
											),
										).join(", ")}
									</p>

									<p className="text-sm font-medium">Files with Metadata:</p>
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
				<div>
					{selectedFiles.length > 0 && (
						<span className="text-sm text-gray-600">
							{selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}{" "}
							selected
						</span>
					)}
					{selectedFiles.length > 0 && (
						<span className="text-sm text-gray-600">
							{selectedFiles.length} file{selectedFiles.length > 1 ? "s" : ""}{" "}
							to upload
						</span>
					)}
				</div>
				<div className="flex mt-4 space-x-2">
					<Button
						onClick={() => {
							setSelectedFiles([]);
							onOpenChange(false);
						}}
					>
						Cancel
					</Button>
					<Button
						disabled={selectedFiles.length === 0}
						onClick={handleConfirmSelection}
					>
						Upload
					</Button>
				</div>
			</div>
			<Dialog
				showFooter
				title="Edit Metadata"
				primaryActionText="Save Metadata"
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
						<div className="text-sm font-medium">Current Metadata:</div>
						{Object.keys(currentMetadata).length === 0 && (
							<p className="text-sm text-gray-500">No metadata added yet.</p>
						)}
						{Object.entries(currentMetadata).map(([key, value]) => (
							<div key={key} className="flex items-center space-x-2">
								<Input
									value={value}
									onChange={(e) => updateMetadataField(key, e.target.value)}
									className="flex-1 h-8"
								/>
								<Button
									size="sm"
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
						<div className="text-sm font-medium">Add Field:</div>
						<div className="flex space-x-2">
							<div className="flex-1">
								<Input
									list="metadata-suggestions"
									placeholder="Field name"
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
								placeholder="Value"
								value={newMetadataValue}
								onChange={(e) => setNewMetadataValue(e.target.value)}
								className="flex-1 h-8"
							/>
							<Button
								type="button"
								size="sm"
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
