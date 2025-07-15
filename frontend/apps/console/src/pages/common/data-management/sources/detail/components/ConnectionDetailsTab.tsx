import {
	Button,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Switch,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
	Textarea,
} from "@/components";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
	ApiConnectionConfig,
	ConnectionConfig,
	DatabaseConnectionConfig,
	FileConnectionConfig,
	UrlConnectionConfig,
} from "@vbkg/types";
import { Plus, X } from "lucide-react";

interface ConnectionDetailsTabProps {
	source_type?: string;
	isEditing: boolean;
	connection_details: ConnectionConfig;
	validationErrors: Record<string, string>;
	updateConnectionDetail: (key: string, value: any) => void;
}

export const ConnectionDetailsTab = ({
	source_type,
	isEditing,
	validationErrors,
	connection_details,
	updateConnectionDetail,
}: ConnectionDetailsTabProps) => {
	const details = connection_details;

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
							</div>
						</div>
						<div className="space-y-2">
							<Label>Định dạng file</Label>
							<Select
								value={fileDetails.file_format}
								disabled
								onValueChange={(value) =>
									updateConnectionDetail("file_format", value)
								}
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
								onChange={(e) => updateConnectionDetail("url", e.target.value)}
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

					{apiDetails.headers && Object.keys(apiDetails.headers).length > 0 && (
						<div>
							<Label>Headers</Label>
							<div className="border rounded-md overflow-hidden mt-1">
								<Table>
									<TableHeader>
										<TableRow>
											<TableHead>Key</TableHead>
											<TableHead>Value</TableHead>
											{isEditing && <TableHead className="w-16"></TableHead>}
										</TableRow>
									</TableHeader>
									<TableBody>
										{Object.entries(apiDetails.headers).map(([key, value]) => (
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
																updateConnectionDetail("headers", newHeaders);
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
																updateConnectionDetail("headers", newHeaders);
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
							<Label>Loại CSDL</Label>
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
								onChange={(e) => updateConnectionDetail("host", e.target.value)}
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

					{urlDetails.headers && Object.keys(urlDetails.headers).length > 0 && (
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
										{Object.entries(urlDetails.headers).map(([key, value]) => (
											<TableRow key={key}>
												<TableCell>{key}</TableCell>
												<TableCell>{value}</TableCell>
											</TableRow>
										))}
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
