import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router";
import {
	FileText,
	Globe,
	Link as LinkIcon,
	Check,
	X,
	Upload,
	RefreshCw,
	Eye,
	EyeOff,
	ChevronLeft,
	Shield,
	Terminal,
	Clock,
	Info,
	Edit,
	Trash,
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
	FileUpload,
	SourceType,
	UrlConnectionConfig,
} from "@vbkg/types";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
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
	ScrollArea,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Separator,
	Switch,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
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
import { PipelineTemplateDialog } from "../components/dialog/pipeline-template";

// Định nghĩa kiểu dữ liệu cho lịch sử kết nối
interface ConnectionLog {
	id: string;
	datasource_id: string;
	status: "success" | "error";
	message: string;
	details?: string;
	created_at: string;
}

// Form data types
interface EditFormData {
	name: string;
	description: string;
	connection_details: Record<string, any>;
	credentials: Record<string, any>;
	is_active: boolean;
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
			onError: (error) => {
				toast("Cập nhật nguồn dữ liệu thất bại: " + error.message, {
					className: "bg-red-500",
				});
			},
		});

	// States
	const [connectionLogs, setConnectionLogs] = useState<ConnectionLog[]>([]);
	const [searchParam, setSearchParam] = useSearchParams();
	const [isEditing, setIsEditing] = useState(
		searchParam.get("edit") === "true",
	);
	const [showPassword, setShowPassword] = useState(false);
	const [showPipelineTemplateDialog, setShowPipelineTemplateDialog] =
		useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [testConnectionStatus, setTestConnectionStatus] = useState<
		null | "success" | "error"
	>(null);
	const [showUploadDialog, setShowUploadDialog] = useState(false);
	const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

	// Form data state
	const [formData, setFormData] = useState<EditFormData>({
		name: "",
		description: "",
		connection_details: {},
		credentials: {},
		is_active: true,
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

	// Xử lý kiểm tra kết nối
	const handleTestConnection = async () => {
		setIsLoading(true);
		setTestConnectionStatus(null);

		// Giả lập API call
		setTimeout(() => {
			// Random success/error để demo
			const isSuccess = Math.random() > 0.3;

			setTestConnectionStatus(isSuccess ? "success" : "error");

			// Thêm log mới
			const newLog: ConnectionLog = {
				id: `log-${Date.now()}`,
				datasource_id: id!,
				status: isSuccess ? "success" : "error",
				message: isSuccess ? "Kết nối thành công" : "Lỗi kết nối",
				details: isSuccess
					? "Đã đọc được 1,245 dòng dữ liệu"
					: "Không thể mở file: File không tồn tại hoặc không có quyền truy cập",
				created_at: new Date().toISOString(),
			};

			setConnectionLogs([newLog, ...connectionLogs]);
			setIsLoading(false);

			toast(isSuccess ? "Kết nối thành công" : "Kết nối thất bại", {
				description: isSuccess
					? "Đã kiểm tra kết nối thành công đến nguồn dữ liệu"
					: "Không thể kết nối đến nguồn dữ liệu. Vui lòng kiểm tra lại cấu hình",
				className: isSuccess ? "bg-green-500" : "bg-red-500",
			});
		}, 2000);
	};

	const { mutateAsync: uploadFileMutation } = useUploadFile({
		onSuccess: () => {
			toast("File uploaded successfully");
		},
		onError: (error) => {
			toast.error("File upload failed: " + error.message);
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

	// Render chi tiết kết nối dựa trên loại nguồn dữ liệu
	const renderConnectionDetails = () => {
		const details = formData.connection_details;

		switch (source_type) {
			case "file": {
				const fileDetails = details as FileConnectionConfig;
				return (
					<div className="space-y-4">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div className="space-y-2">
								<Label>Đường dẫn file</Label>
								<div className="flex mt-1">
									<div className="flex-1">
										<Input
											value={fileDetails.file_path || ""}
											onChange={(e) =>
												updateConnectionDetail("file_path", e.target.value)
											}
											readOnly={!isEditing}
											className={
												validationErrors.file_path ? "border-red-500" : ""
											}
										/>
										{validationErrors.file_path && (
											<p className="text-red-500 text-sm mt-1">
												{validationErrors.file_path}
											</p>
										)}
									</div>
									{source_type === "file" && (
										<Button
											variant="outline"
											className="ml-2"
											onClick={() => setShowUploadDialog(true)}
										>
											<Upload className="h-4 w-4 mr-1" />
											Tải lên
										</Button>
									)}
								</div>
							</div>
							<div className="space-y-2">
								<Label>Định dạng file</Label>
								<Select
									value={fileDetails.file_format}
									onValueChange={(value) =>
										updateConnectionDetail("file_format", value)
									}
									disabled={!isEditing}
								>
									<SelectTrigger>
										<SelectValue placeholder="Chọn định dạng file" />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="csv">CSV</SelectItem>
										<SelectItem value="json">JSON</SelectItem>
										<SelectItem value="xlsx">Excel (XLSX)</SelectItem>
										<SelectItem value="txt">Text (TXT)</SelectItem>
										<SelectItem value="pdf">PDF</SelectItem>
									</SelectContent>
								</Select>
							</div>
						</div>
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div className="space-y-2">
								<Label>Mã hóa</Label>
								<Select
									value={fileDetails.encoding}
									onValueChange={(value) =>
										updateConnectionDetail("encoding", value)
									}
									disabled={!isEditing}
								>
									<SelectTrigger>
										<SelectValue placeholder="Chọn mã hóa" />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="utf-8">UTF-8</SelectItem>
										<SelectItem value="ascii">ASCII</SelectItem>
										<SelectItem value="iso-8859-1">ISO-8859-1</SelectItem>
										<SelectItem value="windows-1252">Windows-1252</SelectItem>
									</SelectContent>
								</Select>
							</div>
							{fileDetails.file_format === "csv" && (
								<div className="space-y-2">
									<Label>Ký tự phân cách</Label>
									<Input
										value={fileDetails.delimiter || ","}
										onChange={(e) =>
											updateConnectionDetail("delimiter", e.target.value)
										}
										readOnly={!isEditing}
									/>
								</div>
							)}
						</div>
					</div>
				);
			}

			case "api": {
				const apiDetails = details as ApiConnectionConfig;
				return (
					<div className="space-y-4">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div className="md:col-span-2 space-y-2">
								<Label>URL</Label>
								<Input
									value={apiDetails.url}
									onChange={(e) =>
										updateConnectionDetail("url", e.target.value)
									}
									readOnly={!isEditing}
									className={validationErrors.url ? "border-red-500" : ""}
								/>
								{validationErrors.url && (
									<p className="text-red-500 text-sm mt-1">
										{validationErrors.url}
									</p>
								)}
							</div>
							<div>
								<Label>Phương thức</Label>
								<Select
									value={apiDetails.method}
									onValueChange={(value) =>
										updateConnectionDetail("method", value)
									}
									disabled={!isEditing}
								>
									<SelectTrigger>
										<SelectValue placeholder="Chọn phương thức" />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="GET">GET</SelectItem>
										<SelectItem value="POST">POST</SelectItem>
										<SelectItem value="PUT">PUT</SelectItem>
										<SelectItem value="DELETE">DELETE</SelectItem>
									</SelectContent>
								</Select>
							</div>
							<div className="space-y-2">
								<Label>Loại xác thực</Label>
								<Select
									value={apiDetails.auth_type || "none"}
									onValueChange={(value) =>
										updateConnectionDetail("auth_type", value)
									}
									disabled={!isEditing}
								>
									<SelectTrigger>
										<SelectValue placeholder="Chọn loại xác thực" />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="none">Không có</SelectItem>
										<SelectItem value="basic">Basic Auth</SelectItem>
										<SelectItem value="bearer">Bearer Token</SelectItem>
										<SelectItem value="api_key">API Key</SelectItem>
										<SelectItem value="oauth">OAuth 2.0</SelectItem>
									</SelectContent>
								</Select>
							</div>
						</div>

						{apiDetails.headers &&
							Object.keys(apiDetails.headers).length > 0 && (
								<div>
									<Label>Headers</Label>
									<div className="border rounded-md overflow-hidden mt-1">
										<Table>
											<TableHeader>
												<TableRow>
													<TableHead>Key</TableHead>
													<TableHead>Value</TableHead>
													{isEditing && (
														<TableHead className="w-16"></TableHead>
													)}
												</TableRow>
											</TableHeader>
											<TableBody>
												{Object.entries(apiDetails.headers).map(
													([key, value]) => (
														<TableRow key={key}>
															<TableCell>
																{isEditing ? (
																	<Input
																		value={key}
																		onChange={(e) => {
																			const newHeaders = {
																				...apiDetails.headers,
																			};
																			delete newHeaders[key];
																			newHeaders[e.target.value] = value;
																			updateConnectionDetail(
																				"headers",
																				newHeaders,
																			);
																		}}
																	/>
																) : (
																	key
																)}
															</TableCell>
															<TableCell>
																{isEditing ? (
																	<Input
																		value={value as string}
																		onChange={(e) => {
																			updateConnectionDetail("headers", {
																				...apiDetails.headers,
																				[key]: e.target.value,
																			});
																		}}
																	/>
																) : (
																	(value as string)
																)}
															</TableCell>
															{isEditing && (
																<TableCell>
																	<Button
																		size="sm"
																		variant="ghost"
																		onClick={() => {
																			const newHeaders = {
																				...apiDetails.headers,
																			};
																			delete newHeaders[key];
																			updateConnectionDetail(
																				"headers",
																				newHeaders,
																			);
																		}}
																	>
																		<X className="h-4 w-4" />
																	</Button>
																</TableCell>
															)}
														</TableRow>
													),
												)}
											</TableBody>
										</Table>
									</div>
									{isEditing && (
										<Button
											size="sm"
											variant="outline"
											className="mt-2"
											onClick={() => {
												updateConnectionDetail("headers", {
													...apiDetails.headers,
													"": "",
												});
											}}
										>
											<Plus className="h-4 w-4 mr-1" />
											Thêm header
										</Button>
									)}
								</div>
							)}
					</div>
				);
			}

			case "database": {
				const dbDetails = details as DatabaseConnectionConfig;
				return (
					<div className="space-y-4">
						<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
							<div className="space-y-2">
								<Label>Loại database</Label>
								<Select
									value={dbDetails.db_type}
									onValueChange={(value) =>
										updateConnectionDetail("db_type", value)
									}
									disabled={!isEditing}
								>
									<SelectTrigger>
										<SelectValue placeholder="Chọn loại database" />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="postgres">PostgreSQL</SelectItem>
										<SelectItem value="mysql">MySQL</SelectItem>
										<SelectItem value="mssql">SQL Server</SelectItem>
										<SelectItem value="oracle">Oracle</SelectItem>
										<SelectItem value="sqlite">SQLite</SelectItem>
									</SelectContent>
								</Select>
							</div>
							<div className="space-y-2">
								<Label>Host</Label>
								<Input
									value={dbDetails.host}
									onChange={(e) =>
										updateConnectionDetail("host", e.target.value)
									}
									readOnly={!isEditing}
									className={validationErrors.host ? "border-red-500" : ""}
								/>
								{validationErrors.host && (
									<p className="text-red-500 text-sm mt-1">
										{validationErrors.host}
									</p>
								)}
							</div>
							<div className="space-y-2">
								<Label>Port</Label>
								<Input
									value={dbDetails.port?.toString()}
									onChange={(e) =>
										updateConnectionDetail(
											"port",
											parseInt(e.target.value) || 5432,
										)
									}
									readOnly={!isEditing}
									type="number"
								/>
							</div>
						</div>

						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div className="space-y-2">
								<Label>Tên database</Label>
								<Input
									value={dbDetails.database}
									onChange={(e) =>
										updateConnectionDetail("database", e.target.value)
									}
									readOnly={!isEditing}
									className={validationErrors.database ? "border-red-500" : ""}
								/>
								{validationErrors.database && (
									<p className="text-red-500 text-sm mt-1">
										{validationErrors.database}
									</p>
								)}
							</div>
							<div className="space-y-2">
								<Label>Username</Label>
								<Input
									value={dbDetails.username}
									onChange={(e) =>
										updateConnectionDetail("username", e.target.value)
									}
									readOnly={!isEditing}
									className={validationErrors.username ? "border-red-500" : ""}
								/>
								{validationErrors.username && (
									<p className="text-red-500 text-sm mt-1">
										{validationErrors.username}
									</p>
								)}
							</div>
						</div>

						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<div className="flex items-center justify-between">
									<Label>SSL</Label>
									<Switch
										checked={dbDetails.ssl}
										onCheckedChange={(checked) =>
											updateConnectionDetail("ssl", checked)
										}
										disabled={!isEditing}
									/>
								</div>
							</div>
							{dbDetails.table && (
								<div className="space-y-2">
									<Label>Bảng</Label>
									<Input
										value={dbDetails.table}
										onChange={(e) =>
											updateConnectionDetail("table", e.target.value)
										}
										readOnly={!isEditing}
									/>
								</div>
							)}
						</div>

						{dbDetails.query && (
							<div>
								<Label>SQL Query</Label>
								<Textarea
									value={dbDetails.query}
									onChange={(e) =>
										updateConnectionDetail("query", e.target.value)
									}
									readOnly={!isEditing}
									className="font-mono text-sm"
									rows={3}
								/>
							</div>
						)}
					</div>
				);
			}

			case "url": {
				const urlDetails = details as UrlConnectionConfig;
				return (
					<div className="space-y-4">
						<div className="space-y-2">
							<Label>URL</Label>
							<Input
								value={urlDetails.url}
								onChange={(e) => updateConnectionDetail("url", e.target.value)}
								readOnly={!isEditing}
							/>
						</div>

						{urlDetails.headers &&
							Object.keys(urlDetails.headers).length > 0 && (
								<div>
									<Label>Headers</Label>
									<div className="border rounded-md overflow-hidden mt-1">
										<Table>
											<TableHeader>
												<TableRow>
													<TableHead>Key</TableHead>
													<TableHead>Value</TableHead>
												</TableRow>
											</TableHeader>
											<TableBody>
												{Object.entries(urlDetails.headers).map(
													([key, value]) => (
														<TableRow key={key}>
															<TableCell>{key}</TableCell>
															<TableCell>{value}</TableCell>
														</TableRow>
													),
												)}
											</TableBody>
										</Table>
									</div>
								</div>
							)}

						{urlDetails.scrape_config && (
							<div>
								<Label>Cấu hình Scrape</Label>
								<div className="border rounded-md p-4 mt-1">
									<div className="mb-4 space-y-2">
										<Label>Selector</Label>
										<Input
											value={urlDetails.scrape_config.selector}
											onChange={(e) =>
												updateConnectionDetail("scrape_config", {
													...urlDetails.scrape_config,
													selector: e.target.value,
												})
											}
											readOnly={!isEditing}
										/>
									</div>

									<Label>Fields Mapping</Label>
									<div className="border rounded-md overflow-hidden mt-1">
										<Table>
											<TableHeader>
												<TableRow>
													<TableHead>Field</TableHead>
													<TableHead>Selector</TableHead>
												</TableRow>
											</TableHeader>
											<TableBody>
												{Object.entries(urlDetails.scrape_config.fields).map(
													([key, value]) => (
														<TableRow key={key}>
															<TableCell>{key}</TableCell>
															<TableCell>{value as string}</TableCell>
														</TableRow>
													),
												)}
											</TableBody>
										</Table>
									</div>
								</div>
							</div>
						)}
					</div>
				);
			}

			default:
				return <p>Không có thông tin chi tiết</p>;
		}
	};

	// Render credentials
	const renderCredentials = () => {
		const creds = formData.credentials;

		if (!creds || Object.keys(creds).length === 0) {
			return (
				<div className="py-8 text-center">
					<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
						<Shield className="h-6 w-6 text-muted-foreground" />
					</div>
					<h3 className="mb-1 text-lg font-semibold">
						Chưa có thông tin xác thực
					</h3>
					<p className="text-sm text-muted-foreground mb-4">
						Thêm thông tin xác thực để kết nối đến nguồn dữ liệu này
					</p>
					{isEditing && (
						<Button
							variant="outline"
							onClick={() => updateCredential("auth_type", "api_key")}
						>
							<Plus className="mr-2 h-4 w-4" />
							Thêm thông tin xác thực
						</Button>
					)}
				</div>
			);
		}

		return (
			<div className="space-y-4">
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div className="space-y-2">
						<Label>Loại xác thực</Label>
						<Select
							value={creds.auth_type}
							onValueChange={(value) => updateCredential("auth_type", value)}
							disabled={!isEditing}
						>
							<SelectTrigger>
								<SelectValue placeholder="Chọn loại xác thực" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="api_key">API Key</SelectItem>
								<SelectItem value="oauth">OAuth 2.0</SelectItem>
								<SelectItem value="basic">Basic Auth</SelectItem>
								<SelectItem value="token">Token</SelectItem>
								<SelectItem value="certificate">Certificate</SelectItem>
							</SelectContent>
						</Select>
					</div>
				</div>

				<div className="border rounded-md overflow-hidden">
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Key</TableHead>
								<TableHead>Value</TableHead>
								{isEditing && <TableHead className="w-16"></TableHead>}
							</TableRow>
						</TableHeader>
						<TableBody>
							{Object.entries(creds).map(([key, value]) => (
								<TableRow key={key}>
									<TableCell>
										{isEditing ? (
											<Input
												value={key}
												onChange={(e) => {
													const newCreds = { ...creds };
													delete newCreds[key];
													newCreds[e.target.value] = value;
													updateFormField("credentials", newCreds);
												}}
											/>
										) : (
											key
										)}
									</TableCell>
									<TableCell>
										{key.toLowerCase().includes("password") ||
										key.toLowerCase().includes("secret") ||
										key.toLowerCase().includes("key") ? (
											<div className="flex items-center">
												<Input
													type={showPassword ? "text" : "password"}
													value={value as string}
													onChange={(e) =>
														updateCredential(key, e.target.value)
													}
													readOnly={!isEditing}
													className="font-mono"
												/>
												<Button
													size="icon"
													variant="outline"
													onClick={() => setShowPassword(!showPassword)}
													className="ml-2"
												>
													{showPassword ? (
														<EyeOff className="h-4 w-4" />
													) : (
														<Eye className="h-4 w-4" />
													)}
												</Button>
											</div>
										) : (
											<Input
												value={value as string}
												onChange={(e) => updateCredential(key, e.target.value)}
												readOnly={!isEditing}
											/>
										)}
									</TableCell>
									{isEditing && (
										<TableCell>
											<Button
												size="sm"
												variant="ghost"
												onClick={() => {
													const newCreds = { ...creds };
													delete newCreds[key];
													updateFormField("credentials", newCreds);
												}}
											>
												<X className="h-4 w-4" />
											</Button>
										</TableCell>
									)}
								</TableRow>
							))}
						</TableBody>
					</Table>
				</div>

				{isEditing && (
					<Button
						size="sm"
						variant="outline"
						onClick={() => updateCredential("", "")}
					>
						<Plus className="h-4 w-4 mr-1" />
						Thêm credential
					</Button>
				)}

				<div className="flex justify-end">
					<p className="text-sm text-muted-foreground">
						Cập nhật lần cuối: {formatDate(credentials?.updated_at)}
					</p>
				</div>
			</div>
		);
	};

	// Render connection logs
	const renderConnectionLogs = () => {
		return (
			<div>
				<div className="mb-4">
					<h3 className="text-lg font-medium mb-2">Lịch sử kết nối</h3>
					{connectionLogs.length === 0 ? (
						<p className="text-muted-foreground">Chưa có lịch sử kết nối</p>
					) : (
						<div className="border rounded-md overflow-hidden">
							<Table>
								<TableHeader>
									<TableRow>
										<TableHead>Thời gian</TableHead>
										<TableHead>Trạng thái</TableHead>
										<TableHead>Thông báo</TableHead>
									</TableRow>
								</TableHeader>
								<TableBody>
									{connectionLogs.map((log) => (
										<TableRow key={log.id}>
											<TableCell>{formatDate(log.created_at)}</TableCell>
											<TableCell>
												<Badge
													variant={
														log.status === "success" ? "default" : "destructive"
													}
												>
													{log.status === "success" ? (
														<div className="flex items-center">
															<Check className="h-3 w-3 mr-1" />
															<span>Thành công</span>
														</div>
													) : (
														<div className="flex items-center">
															<X className="h-3 w-3 mr-1" />
															<span>Lỗi</span>
														</div>
													)}
												</Badge>
											</TableCell>
											<TableCell>
												<Accordion type="single" collapsible>
													<AccordionItem value={log.id}>
														<AccordionTrigger>{log.message}</AccordionTrigger>
														<AccordionContent>{log.details}</AccordionContent>
													</AccordionItem>
												</Accordion>
											</TableCell>
										</TableRow>
									))}
								</TableBody>
							</Table>
						</div>
					)}
				</div>
			</div>
		);
	};

	return (
		<div className="container mx-auto py-6">
			<div className="flex items-center mb-6">
				<Button
					variant="outline"
					size="icon"
					className="mr-2"
					onClick={() => navigate(-1)}
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

			<div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
				{/* Sidebar */}
				<div className="lg:col-span-1 space-y-6">
					<Card>
						<CardHeader className="pb-2">
							<CardTitle>Thông tin cơ bản</CardTitle>
						</CardHeader>
						<CardContent className="space-y-4">
							<div className="flex items-center">
								{getSourceTypeIcon(source_type)}
								<div className="ml-3">
									<p className="text-sm font-medium">Loại nguồn</p>
									<p className="text-sm capitalize">{source_type}</p>
								</div>
							</div>

							<div>
								<p className="text-sm font-medium">ID</p>
								<p className="text-sm font-mono">{id}</p>
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
								<p className="text-sm">{created_by}</p>
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

							<Button variant="outline" className="w-full justify-start">
								<Trash className="mr-2 h-4 w-4" />
								Xóa nguồn dữ liệu
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
								<TabsList
									className={cn(
										"grid mb-8",
										source_type === SourceType.FILE
											? "grid-cols-3"
											: "grid-cols-4",
									)}
								>
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
									{source_type !== SourceType.FILE && (
										<TabsTrigger
											value="connection"
											className="flex items-center"
										>
											<Terminal className="h-4 w-4 mr-2" />
											<span>Kiểm tra kết nối</span>
										</TabsTrigger>
									)}
									{source_type === SourceType.FILE && (
										<TabsTrigger value="files" className="flex items-center">
											<Files className="h-4 w-4 mr-2" />
											<span>Files</span>
										</TabsTrigger>
									)}
									{source_type !== SourceType.FILE && (
										<TabsTrigger value="logs" className="flex items-center">
											<Clock className="h-4 w-4 mr-2" />
											<span>Lịch sử</span>
										</TabsTrigger>
									)}
								</TabsList>

								<TabsContent value="details">
									<div className="space-y-8">
										<div>
											<h3 className="text-lg font-medium mb-4">
												Thông tin kết nối
											</h3>
											{renderConnectionDetails()}
										</div>
									</div>
								</TabsContent>

								<TabsContent value="credentials">
									<div className="space-y-8">
										<div>
											<h3 className="text-lg font-medium mb-4">
												Thông tin xác thực
											</h3>
											{renderCredentials()}
										</div>
									</div>
								</TabsContent>

								<TabsContent value="files">
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
															<span>{file.file_name}</span>
														</div>
														<DownloadFileButton file_id={file.id} />
													</div>
												))}
											</div>
										) : (
											<div>
												<h3 className="text-lg font-medium mb-4">Files</h3>
												<p className="text-sm text-muted-foreground">
													Chưa có file nào được tải lên
												</p>
											</div>
										)}
									</div>
								</TabsContent>

								<TabsContent value="connection">
									<div className="space-y-8">
										<div className="space-y-4">
											<div className="flex justify-between items-center">
												<h3 className="text-lg font-medium">
													Kiểm tra kết nối
												</h3>
												<Button
													onClick={handleTestConnection}
													disabled={isLoading}
													className="flex items-center"
												>
													{isLoading ? (
														<>
															<RefreshCw className="mr-2 h-4 w-4 animate-spin" />
															<span>Đang kiểm tra...</span>
														</>
													) : (
														<>
															<Terminal className="mr-2 h-4 w-4" />
															<span>Kiểm tra kết nối</span>
														</>
													)}
												</Button>
											</div>

											{testConnectionStatus === "success" && (
												<Alert variant="default">
													<Check className="h-4 w-4" />
													<AlertTitle>Kết nối thành công</AlertTitle>
													<AlertDescription>
														Đã kiểm tra kết nối thành công đến nguồn dữ liệu.
													</AlertDescription>
												</Alert>
											)}

											{testConnectionStatus === "error" && (
												<Alert variant="destructive">
													<X className="h-4 w-4" />
													<AlertTitle>Kết nối thất bại</AlertTitle>
													<AlertDescription>
														Không thể kết nối đến nguồn dữ liệu. Vui lòng kiểm
														tra lại cấu hình và thông tin xác thực.
													</AlertDescription>
												</Alert>
											)}
										</div>

										{source_type === "file" && (
											<div className="space-y-4">
												<div className="flex justify-between items-center">
													<h3 className="text-lg font-medium">Upload file</h3>
													<Button onClick={() => setShowUploadDialog(true)}>
														<Upload className="mr-2 h-4 w-4" />
														<span>Tải lên file mới</span>
													</Button>
												</div>

												<p className="text-sm text-muted-foreground">
													Tải lên file mới để thay thế file hiện tại. Hệ thống
													sẽ tự động cập nhật đường dẫn file.
												</p>
											</div>
										)}

										<Separator />

										{renderConnectionLogs()}
									</div>
								</TabsContent>

								<TabsContent value="logs">
									<ScrollArea className="h-[500px] pr-4">
										{renderConnectionLogs()}
									</ScrollArea>
								</TabsContent>
							</Tabs>
						</CardContent>
					</Card>
				</div>
			</div>

			{/* Dialog upload file */}
			<FileSelectorDialog
				open={showUploadDialog}
				onOpenChange={setShowUploadDialog}
				onSelect={(file) => handleUploadFile(file)}
				datasource_id={id}
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
