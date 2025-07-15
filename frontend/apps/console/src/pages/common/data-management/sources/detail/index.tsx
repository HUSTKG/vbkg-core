import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router";
import {
	FileText,
	Globe,
	Link as LinkIcon,
	Upload,
	RefreshCw,
	ChevronLeft,
	Shield,
	Info,
	Edit,
	Plus,
	Files,
	Database,
	Save,
	AlertTriangle,
} from "lucide-react";
import {
	ApiConnectionConfig,
	DatabaseConnectionConfig,
	FileConnectionConfig,
	SourceType,
} from "@vbkg/types";
import {
	Alert,
	AlertDescription,
	AlertTitle,
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	cn,
	Input,
	Label,
	Switch,
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
	Textarea,
	toast,
} from "@/components";
import {
	useDatasource,
	useFileUploads,
	useUpdateDatasource,
	useUploadFile,
} from "@vbkg/api-client";
import DownloadFileButton from "../../../../../components/button/DownloadFileButton";
import FileSelectorDialog, {
	SelectedFile,
} from "../../../../../components/dialog/file-selector";
import { formatBytes } from "@/utils/formatBytes";
import { CredentialTab } from "./components/CredentialTab";
import { ConnectionDetailsTab } from "./components/ConnectionDetailsTab";
import { PipelineTemplateDialog } from "./components/pipeline-template";

// Form data types
interface EditFormData {
	name: string;
	description: string;
	connection_details: Record<string, any>;
	credentials: Record<string, any>;
	is_active: boolean;
	trust_score: number;
}

// Component chính cho trang chi tiết DataSource
const DataSourceDetailPage: React.FC = () => {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();

	const { data: dataSource, refetch } = useDatasource(
		{
			id: id!,
		},
		{
			enabled: !!id,
		},
	);

	const { data: files } = useFileUploads({
		datasource_id: id,
	});

	const {
		source_type,
		connection_details,
		credentials,
		created_at,
		created_by,
		updated_at,
		is_active,
		description,
		name,
		trust_score,
	} = dataSource?.data || {};

	const { mutate: updateDatasource, isPending: isUpdating } =
		useUpdateDatasource({
			onSuccess: () => {
				toast("Cập nhật nguồn dữ liệu thành công", {
					className: "bg-green-500",
				});
				setIsEditing(false);
				refetch();
			},
			onError: (error: any) => {
				toast(
					"Cập nhật nguồn dữ liệu thất bại: " + error.response.data.detail,
					{
						className: "bg-red-500",
					},
				);
			},
		});

	// States
	const [searchParam, setSearchParam] = useSearchParams();
	const [isEditing, setIsEditing] = useState(
		searchParam.get("edit") === "true",
	);
	const [showPipelineTemplateDialog, setShowPipelineTemplateDialog] =
		useState(false);
	const [showUploadDialog, setShowUploadDialog] = useState(false);
	const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

	// Form data state
	const [formData, setFormData] = useState<EditFormData>({
		name: "",
		description: "",
		connection_details: {},
		credentials: {},
		is_active: true,
		trust_score: 0,
	});

	// Validation errors
	const [validationErrors, setValidationErrors] = useState<
		Record<string, string>
	>({});

	// Initialize form data when dataSource loads
	useEffect(() => {
		if (dataSource?.data) {
			setFormData({
				name: name || "",
				description: description || "",
				connection_details: connection_details || {},
				credentials: credentials || {},
				is_active: is_active || false,
				trust_score: trust_score || 0,
			});
		}
	}, [
		dataSource,
		name,
		description,
		connection_details,
		credentials,
		is_active,
	]);

	// Watch for unsaved changes
	useEffect(() => {
		if (!dataSource?.data) return;

		const hasChanges =
			formData.name !== (name || "") ||
			formData.description !== (description || "") ||
			JSON.stringify(formData.connection_details) !==
				JSON.stringify(connection_details || {}) ||
			JSON.stringify(formData.credentials) !==
				JSON.stringify(credentials || {}) ||
			formData.is_active !== (is_active || false);

		setHasUnsavedChanges(hasChanges);
	}, [
		formData,
		dataSource,
		name,
		description,
		connection_details,
		credentials,
		is_active,
	]);

	// Format date
	const formatDate = (dateString?: string) => {
		if (!dateString) return "";
		const date = new Date(dateString);
		return new Intl.DateTimeFormat("vi-VN", {
			year: "numeric",
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		}).format(date);
	};

	// Validation functions
	const validateForm = (): boolean => {
		const errors: Record<string, string> = {};

		// Validate name
		if (!formData.name.trim()) {
			errors.name = "Tên nguồn dữ liệu không được để trống";
		}

		// Validate connection details based on source type
		if (source_type === "api") {
			const details = formData.connection_details as ApiConnectionConfig;
			if (!details.url) {
				errors.url = "URL không được để trống";
			} else if (!isValidUrl(details.url)) {
				errors.url = "URL không hợp lệ";
			}
		} else if (source_type === "database") {
			const details = formData.connection_details as DatabaseConnectionConfig;
			if (!details.host) errors.host = "Host không được để trống";
			if (!details.database)
				errors.database = "Tên database không được để trống";
			if (!details.username) errors.username = "Username không được để trống";
		} else if (source_type === "file") {
			const details = formData.connection_details as FileConnectionConfig;
			if (!details.file_path)
				errors.file_path = "Đường dẫn file không được để trống";
		}

		setValidationErrors(errors);
		return Object.keys(errors).length === 0;
	};

	const isValidUrl = (string: string) => {
		try {
			new URL(string);
			return true;
		} catch (_) {
			return false;
		}
	};

	// Lấy icon tương ứng với loại datasource
	const getSourceTypeIcon = (type?: string) => {
		switch (type) {
			case "file":
				return <FileText className="h-5 w-5 text-blue-500" />;
			case "api":
				return <Globe className="h-5 w-5 text-green-500" />;
			case "database":
				return <Database className="h-5 w-5 text-purple-500" />;
			case "url":
				return <LinkIcon className="h-5 w-5 text-orange-500" />;
			default:
				return null;
		}
	};

	const { mutateAsync: uploadFileMutation } = useUploadFile({
		onSuccess: () => {
			toast("Tải lên thành công");
		},
		onError: (error: any) => {
			toast.error("Tải lên thất bại: " + error.response.data.detail);
		},
	});

	// Xử lý upload file
	const handleUploadFile = (files: SelectedFile[]) => {
		if (!files) return;
		files.forEach((file) => {
			uploadFileMutation({
				datasource_id: id!,
				file: file.file,
				metadata: file.metadata,
			});
		});
	};

	// Handle form field updates
	const updateFormField = (field: keyof EditFormData, value: any) => {
		setFormData((prev) => ({
			...prev,
			[field]: value,
		}));
	};

	const updateConnectionDetail = (key: string, value: any) => {
		setFormData((prev) => ({
			...prev,
			connection_details: {
				...prev.connection_details,
				[key]: value,
			},
		}));
	};

	const updateCredential = (key: string, value: any) => {
		setFormData((prev) => ({
			...prev,
			credentials: {
				...prev.credentials,
				[key]: value,
			},
		}));
	};

	// Handle save
	const handleSave = () => {
		if (!validateForm()) {
			toast("Vui lòng kiểm tra lại thông tin đã nhập", {
				className: "bg-red-500",
			});
			return;
		}

		updateDatasource({
			id: id!,
			name: formData.name,
			description: formData.description,
			connection_details: formData.connection_details,
			credentials: formData.credentials,
			is_active: formData.is_active,
		});
	};

	// Handle cancel editing
	const handleCancelEdit = () => {
		if (hasUnsavedChanges) {
			if (window.confirm("Bạn có chắc chắn muốn hủy các thay đổi chưa lưu?")) {
				// Reset form data
				if (dataSource?.data) {
					setFormData({
						name: name || "",
						description: description || "",
						connection_details: connection_details || {},
						credentials: credentials || {},
						is_active: is_active || false,
						trust_score: trust_score || 0,
					});
				}
				setIsEditing(false);
				setValidationErrors({});
				setSearchParam((prev) => {
					prev.delete("edit");
					return prev;
				});
			}
		} else {
			setIsEditing(false);
			setSearchParam((prev) => {
				prev.delete("edit");
				return prev;
			});
		}
	};

	// Xử lý toggle active
	const handleToggleActive = () => {
		if (isEditing) {
			updateFormField("is_active", !formData.is_active);
		} else {
			updateDatasource({
				id: id!,
				is_active: !is_active,
			});
		}
	};

	return (
		<div className="container mx-auto py-6">
			<div className="flex items-center mb-6">
				<Button
					variant="outline"
					size="icon"
					className="mr-2"
					onClick={() => navigate("/admin/data/sources")}
				>
					<ChevronLeft className="h-5 w-5" />
				</Button>
				<h1 className="text-3xl font-bold">
					{isEditing ? "Chỉnh sửa" : "Chi tiết"}
				</h1>
			</div>

			{/* Unsaved changes warning */}
			{hasUnsavedChanges && isEditing && (
				<Alert className="mb-6">
					<AlertTriangle className="h-4 w-4" />
					<AlertTitle>Có thay đổi chưa lưu</AlertTitle>
					<AlertDescription>
						Bạn có thay đổi chưa được lưu. Nhấn "Lưu thay đổi" để lưu hoặc "Hủy"
						để bỏ qua.
					</AlertDescription>
				</Alert>
			)}

			<div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
				{/* Sidebar */}
				<div className="lg:col-span-1 space-y-6">
					<Card>
						<CardHeader className="pb-2">
							<CardTitle>Thông tin cơ bản</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<div className="flex items-center">
								<div>
									<p className="text-sm font-medium">Loại nguồn</p>
									<p className="text-sm flex items-center capitalize">
										{getSourceTypeIcon(source_type)}
										<span className="ml-3">{source_type}</span>
									</p>
								</div>
							</div>
							<div className="flex gap-1 flex-col">
								<p className="text-sm font-medium">Độ tin cậy</p>
								<div className="flex items-center gap-2">
									<div className="w-16 bg-muted rounded-full h-2">
										<div
											className={cn(
												"h-2 rounded-full",
												Number(trust_score) < 0.5
													? "bg-red-500"
													: Number(trust_score) < 0.8
														? "bg-yellow-500"
														: "bg-green-500",
											)}
											style={{ width: `${Number(trust_score) * 100}%` }}
										/>
									</div>
									<span className="text-sm">
										{Math.round(Number(trust_score) * 100)}%
									</span>
								</div>
							</div>

							<div>
								<p className="text-sm font-medium">Ngày tạo</p>
								<p className="text-sm">{formatDate(created_at)}</p>
							</div>

							<div>
								<p className="text-sm font-medium">Cập nhật lần cuối</p>
								<p className="text-sm">{formatDate(updated_at)}</p>
							</div>

							<div>
								<p className="text-sm font-medium">Người tạo</p>
								<p className="text-sm">
									{created_by?.full_name} -
									<span className="inline-flex">
										{created_by?.roles.map((role) => (
											<Badge
												key={role}
												variant="secondary"
												className="ml-1 uppercase text-[10px]"
											>
												{role}
											</Badge>
										))}
									</span>
								</p>
							</div>

							<div className="flex items-center justify-between pt-2">
								<p className="text-sm font-medium">Trạng thái</p>
								<Switch
									checked={isEditing ? formData.is_active : is_active}
									onCheckedChange={handleToggleActive}
								/>
							</div>
							<Badge
								variant={
									(isEditing ? formData.is_active : is_active)
										? "outline"
										: "destructive"
								}
								className="w-full justify-center py-1"
							>
								{(isEditing ? formData.is_active : is_active)
									? "Đang hoạt động"
									: "Ngừng hoạt động"}
							</Badge>
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="pb-2">
							<CardTitle>Hành động</CardTitle>
						</CardHeader>
						<CardContent className="space-y-2">
							<Button
								className="w-full justify-start"
								variant="outline"
								onClick={() => setShowPipelineTemplateDialog(true)}
							>
								<Plus className="mr-2 h-4 w-4" />
								Tạo pipeline
							</Button>
							<Button
								variant="outline"
								className="w-full justify-start"
								onClick={() => {
									if (isEditing) {
										handleCancelEdit();
									} else {
										setIsEditing(true);
										setSearchParam((prev) => {
											prev.set("edit", "true");
											return prev;
										});
									}
								}}
							>
								<Edit className="mr-2 h-4 w-4" />
								{isEditing ? "Hủy chỉnh sửa" : "Chỉnh sửa"}
							</Button>
						</CardContent>
					</Card>
				</div>

				{/* Main content */}
				<div className="lg:col-span-3">
					<Card>
						<CardHeader>
							{isEditing && (
								<div className="flex gap-2 ml-auto">
									<Button variant="outline" onClick={handleCancelEdit}>
										Hủy
									</Button>
									<Button onClick={handleSave} disabled={isUpdating}>
										{isUpdating ? (
											<>
												<RefreshCw className="mr-2 h-4 w-4 animate-spin" />
												Đang lưu...
											</>
										) : (
											<>
												<Save className="mr-2 h-4 w-4" />
												Lưu thay đổi
											</>
										)}
									</Button>
								</div>
							)}
							<div className="flex justify-between items-start">
								<div className="flex-1">
									{isEditing ? (
										<div className="space-y-4">
											<div className="space-y-2">
												<Label>Tên nguồn dữ liệu</Label>
												<Input
													value={formData.name}
													onChange={(e) =>
														updateFormField("name", e.target.value)
													}
													className={
														validationErrors.name ? "border-red-500" : ""
													}
													placeholder="Nhập tên nguồn dữ liệu"
												/>
												{validationErrors.name && (
													<p className="text-red-500 text-sm mt-1">
														{validationErrors.name}
													</p>
												)}
											</div>
											<div className="space-y-2">
												<Label>Độ tin cậy (0-1)</Label>
												<Input
													value={formData.trust_score}
													onChange={(e) =>
														updateFormField("trust_score", e.target.value)
													}
													className={
														validationErrors.name ? "border-red-500" : ""
													}
													placeholder="Nhập tên nguồn dữ liệu"
												/>
												{validationErrors.name && (
													<p className="text-red-500 text-sm mt-1">
														{validationErrors.name}
													</p>
												)}
											</div>
											<div className="space-y-2">
												<Label>Mô tả</Label>
												<Textarea
													value={formData.description}
													onChange={(e) =>
														updateFormField("description", e.target.value)
													}
													placeholder="Nhập mô tả cho nguồn dữ liệu"
													rows={3}
												/>
											</div>
										</div>
									) : (
										<div>
											<CardTitle className="text-2xl">{name}</CardTitle>
											{description && (
												<CardDescription className="mt-2">
													{description}
												</CardDescription>
											)}
										</div>
									)}
								</div>
							</div>
						</CardHeader>

						<CardContent>
							<Tabs defaultValue="details">
								<TabsList className={cn("grid mb-8 grid-cols-3")}>
									<TabsTrigger value="details" className="flex items-center">
										<Info className="h-4 w-4 mr-2" />
										<span>Thông tin</span>
									</TabsTrigger>
									<TabsTrigger
										value="credentials"
										className="flex items-center"
									>
										<Shield className="h-4 w-4 mr-2" />
										<span>Xác thực</span>
									</TabsTrigger>
									{source_type === SourceType.FILE && (
										<TabsTrigger value="files" className="flex items-center">
											<Files className="h-4 w-4 mr-2" />
											<span>Files</span>
										</TabsTrigger>
									)}
								</TabsList>

								<TabsContent value="details">
									<div className="space-y-8">
										<div>
											<h3 className="text-lg font-medium mb-4">
												Thông tin kết nối
											</h3>
											<ConnectionDetailsTab
												source_type={source_type}
												connection_details={formData.connection_details}
												isEditing={isEditing}
												updateConnectionDetail={updateConnectionDetail}
												validationErrors={validationErrors}
											/>
										</div>
									</div>
								</TabsContent>

								<TabsContent value="credentials">
									<div className="space-y-8">
										<div>
											<h3 className="text-lg font-medium mb-4">
												Thông tin xác thực
											</h3>
											<CredentialTab
												credentials={formData.credentials}
												isEditing={isEditing}
												updateCredential={updateCredential}
												updateFormField={updateFormField}
											/>
										</div>
									</div>
								</TabsContent>

								<TabsContent value="files">
									<div className="flex items-center gap-4 mb-4">
										<h3 className="text-lg font-medium">Files</h3>
										<Button
											variant="outline"
											className="ml-2"
											onClick={() => setShowUploadDialog(true)}
										>
											<Upload className="h-4 w-4 mr-1" />
											Tải lên
										</Button>
									</div>
									<div className="space-y-8">
										{files?.data && files?.data.length > 0 ? (
											<div>
												{files?.data?.map((file) => (
													<div
														key={file.id}
														className="flex items-center justify-between border-b py-2"
													>
														<div className="flex items-center">
															<Files className="h-5 w-5 text-blue-500 mr-2" />
															<span className="text-sm">{file.file_name}</span>
															<p className="text-sm ml-2">
																{file.file_size
																	? `(${formatBytes(file.file_size)})`
																	: ""}
															</p>
														</div>
														<DownloadFileButton file_id={file.id} />
													</div>
												))}
											</div>
										) : (
											<div>
												<p className="text-sm text-muted-foreground">
													Chưa có file nào được tải lên
												</p>
											</div>
										)}
									</div>
								</TabsContent>
							</Tabs>
						</CardContent>
					</Card>
				</div>
			</div>

			{/* Dialog upload file */}
			<FileSelectorDialog
				open={showUploadDialog}
				maxFiles={100}
				onOpenChange={setShowUploadDialog}
				onSelect={(file) => handleUploadFile(file)}
			/>
			<PipelineTemplateDialog
				open={showPipelineTemplateDialog}
				onOpenChange={setShowPipelineTemplateDialog}
				dataSourceId={id!}
				sourceType={source_type!}
			/>
		</div>
	);
};

export default DataSourceDetailPage;
