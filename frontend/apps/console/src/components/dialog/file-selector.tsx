import {
  Button,
  Dialog,
  Input,
  ScrollArea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@vbkg/ui";
import { CheckCircle, ListIcon, Plus, Search, Upload, X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { formatBytes } from "../../utils/formatBytes";
import { getFileIcon } from "../../utils/getFileIcon";
import { useFileUploads, useUploadFile } from "@vbkg/api-client";
import { FileUpload } from "@vbkg/types";

// Props for the FileSelectorDialog component
interface FileSelectorProps {
  onSelect: (files: FileUpload[]) => void;
  multiple?: boolean;
  maxFiles?: number;
  initialTab?: "existing" | "upload";
  open: boolean;
  datasource_id?: string;
  onOpenChange: (open: boolean) => void;
}

// Example files (replace with your actual data fetch)

const FileSelectorDialog = ({
  onSelect,
  multiple = true,
  maxFiles = 10,
  initialTab = "upload",
  datasource_id,
  open,
  onOpenChange,
}: FileSelectorProps) => {
  const [selectedFiles, setSelectedFiles] = useState<FileUpload[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<FileUpload[]>([]);
  const [activeTab, setActiveTab] = useState(initialTab);
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredFiles, setFilteredFiles] = useState<FileUpload[]>([]);
  const [metadataDialogOpen, setMetadataDialogOpen] = useState(false);
  const [editingFile, setEditingFile] = useState<FileUpload | null>(null);
  const [currentMetadata, setCurrentMetadata] = useState<
    Record<string, string>
  >({});
  const [newMetadataKey, setNewMetadataKey] = useState("");
  const [newMetadataValue, setNewMetadataValue] = useState("");

  const { mutateAsync: uploadFileMutation } = useUploadFile({});

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

  const { data: fileUploads } = useFileUploads({});

  const { data: existingFiles = [] } = fileUploads || {};

  // Filter files when search query changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredFiles(existingFiles);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredFiles(
        existingFiles.filter(
          (file) =>
            file.file_name.toLowerCase().includes(query) ||
            file.file_type.toLowerCase().includes(query) ||
            Object.values(file.metadata || {}).some((value) =>
              value.toLowerCase().includes(query),
            ),
        ),
      );
    }
  }, [searchQuery, existingFiles]);

  // Handle file selection from list
  const handleSelectFile = (file: FileUpload) => {
    if (!multiple) {
      // For single selection, replace the current selection
      setSelectedFiles([file]);
      return;
    }

    setSelectedFiles((prev) => {
      // Check if file is already selected
      const isSelected = prev.some((f) => f.id === file.id);

      if (isSelected) {
        // Remove file from selection
        return prev.filter((f) => f.id !== file.id);
      } else {
        // Add file to selection, respecting maxFiles
        if (prev.length >= maxFiles) {
          return prev;
        }
        return [...prev, file];
      }
    });
  };

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
        await uploadFileMutation(
          {
            datasource_id,
            file: newFiles[0].file,
            metadata: newFiles[0].metadata,
          },
          {
            onSuccess: (data) => {
              toast("File uploaded successfully");
              setUploadedFiles((prev) => [...prev, data.data]);
            },
          },
        );
      } else {
        // For multiple selection, respect maxFiles
        const _files = await Promise.all(
          newFiles.map((newFile) => {
            if (uploadedFiles.length < maxFiles) {
              return uploadFileMutation({
                datasource_id,
                file: newFile.file,
                metadata: newFile.metadata,
              });
            }
          }),
        );

        let files = _files
          .filter((file) => file !== undefined)
          .map((item) => item.data) as FileUpload[];

        if (files && files.length > 0) {
          toast("Files uploaded successfully");
          setUploadedFiles((prev) => [...prev, ...files]);
        }
      }
    }
  };

  // Clear uploaded files
  const clearUploadedFiles = () => {
    setUploadedFiles([]);
  };

  // Remove a specific uploaded file
  const removeUploadedFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Open metadata dialog for a file
  const openMetadataDialog = (file: FileUpload) => {
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
    if (activeTab === "existing" && selectedFiles.length > 0) {
      // Convert FileItem[] to UploadedFileWithMetadata[]
      onSelect(selectedFiles);
    } else if (activeTab === "upload" && uploadedFiles.length > 0) {
      onSelect(uploadedFiles);
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
      <Tabs
        defaultValue="existing"
        value={activeTab}
        onValueChange={(tab: any) => {
          setActiveTab(tab);
          setSelectedFiles([]);
          setUploadedFiles([]);
          setSearchQuery("");
        }}
      >
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="existing">Choose Existing</TabsTrigger>
          <TabsTrigger value="upload">Upload New</TabsTrigger>
        </TabsList>

        <TabsContent value="existing">
          <div className="flex flex-col space-y-4">
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-500" />
              <Input
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>

            {/* Fixed height scrollable grid */}
            <div className="relative">
              <ScrollArea className="h-[320px] border rounded-md">
                <div className="p-2 grid grid-cols-3 md:grid-cols-4 gap-2">
                  {filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      className={`flex flex-col items-center p-2 rounded-md cursor-pointer hover:bg-gray-100 border ${
                        selectedFiles.some((f) => f.id === file.id)
                          ? "bg-gray-100 ring-1 ring-primary"
                          : ""
                      }`}
                      onClick={() => handleSelectFile(file)}
                    >
                      <div className="flex items-center justify-center mb-1 relative">
                        {getFileIcon(file.file_type)}
                        {selectedFiles.some((f) => f.id === file.id) && (
                          <CheckCircle
                            className="absolute -top-1 -right-1 text-primary bg-white rounded-full"
                            size={14}
                          />
                        )}
                      </div>
                      <div className="w-full text-center">
                        <p className="font-medium truncate text-xs">
                          {file.file_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatBytes(file.file_size)}
                        </p>
                      </div>
                    </div>
                  ))}
                  {filteredFiles.length === 0 && (
                    <div className="col-span-3 py-8 text-center text-gray-500">
                      No files match your search
                    </div>
                  )}
                </div>
              </ScrollArea>

              <div className="mt-2 text-sm text-gray-500 flex justify-between">
                <div>
                  {selectedFiles.length === 0
                    ? "No files selected"
                    : `${selectedFiles.length} of ${maxFiles} file${maxFiles > 1 ? "s" : ""} selected`}
                </div>
                {filteredFiles.length > 0 && (
                  <div className="text-xs text-gray-400">
                    Showing {filteredFiles.length} of {existingFiles.length}{" "}
                    files
                  </div>
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="upload">
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
            {uploadedFiles.length > 0 && (
              <div className="border rounded-md">
                <div className="p-3 border-b bg-gray-50 flex justify-between items-center">
                  <h3 className="text-sm font-medium">
                    Uploaded Files ({uploadedFiles.length}/{maxFiles})
                  </h3>
                  <Button size="sm" onClick={clearUploadedFiles}>
                    Clear All
                  </Button>
                </div>
                <ScrollArea className="max-h-[280px]">
                  <div className="p-2 space-y-2">
                    {uploadedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex hover:bg-gray-100 items-center justify-between p-2 border rounded-md"
                      >
                        <div className="flex items-center">
                          {getFileIcon("pdf")}
                          <div className="ml-1 flex-1 min-w-0">
                            <p className="font-medium truncate text-xs">
                              {file.file_name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {formatBytes(file.file_size)}
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
        </TabsContent>
      </Tabs>

      {/* File details section */}
      {(getSelectedFileForDetails() || uploadedFiles.length > 0) && (
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
                    {getSelectedFileForDetails()?.file_name}
                  </p>

                  <p className="text-sm font-medium">Type:</p>
                  <p className="text-sm">
                    {getSelectedFileForDetails()?.file_type}
                  </p>

                  <p className="text-sm font-medium">Size:</p>
                  <p className="text-sm">
                    {formatBytes(getSelectedFileForDetails()?.file_size || 0)}
                  </p>

                  <p className="text-sm font-medium">Upload Date:</p>
                  <p className="text-sm">
                    {getSelectedFileForDetails()?.uploaded_at}
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
            ) : uploadedFiles.length > 0 ? (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <p className="text-sm font-medium">Total Files:</p>
                  <p className="text-sm">{uploadedFiles.length}</p>

                  <p className="text-sm font-medium">Total Size:</p>
                  <p className="text-sm">
                    {formatBytes(
                      uploadedFiles.reduce(
                        (total, file) => total + file.file_size,
                        0,
                      ),
                    )}
                  </p>

                  <p className="text-sm font-medium">Types:</p>
                  <p className="text-sm">
                    {Array.from(
                      new Set(
                        uploadedFiles.map(
                          (file) => file.file_type.split("/")[1],
                        ),
                      ),
                    ).join(", ")}
                  </p>

                  <p className="text-sm font-medium">Files with Metadata:</p>
                  <p className="text-sm">
                    {
                      uploadedFiles.filter(
                        (file) => Object.keys(file.metadata || {}).length > 0,
                      ).length
                    }{" "}
                    of {uploadedFiles.length}
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
          {uploadedFiles.length > 0 && (
            <span className="text-sm text-gray-600">
              {uploadedFiles.length} file{uploadedFiles.length > 1 ? "s" : ""}{" "}
              to upload
            </span>
          )}
        </div>
        <div className="flex mt-4 space-x-2">
          <Button
            onClick={() => {
              setSelectedFiles([]);
              setUploadedFiles([]);
              setSearchQuery("");
              onOpenChange(false);
            }}
          >
            Cancel
          </Button>
          <Button
            disabled={
              (activeTab === "existing" && selectedFiles.length === 0) ||
              (activeTab === "upload" && uploadedFiles.length === 0)
            }
            onClick={handleConfirmSelection}
          >
            {activeTab === "existing" ? "Select" : "Upload & Select"}
          </Button>
        </div>
      </div>
      {/* Metadata Dialog */}
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
            {editingFile && getFileIcon(editingFile.file_type)}
            <span className="font-medium text-sm truncate">
              {editingFile?.file_name}
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
