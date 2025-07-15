import { CreateDataSourceSchema } from "@vbkg/schemas";
import { SourceType } from "@vbkg/types";
import { AppForm, FieldConfig, toast } from "@/components";
import { z } from "zod";
import { useCreateDatasource } from "@vbkg/api-client";

const formFields = (formData: z.infer<typeof CreateDataSourceSchema>) =>
	[
		{
			label: "Tên",
			name: "name",
			type: "text",
			placeholder: "Nhập tên nguồn dữ liệu",
			required: true,
		},
		{
			label: "Loại",
			name: "source_type",
			type: "select",
			placeholder: "Chọn loại nguồn dữ liệu",
			options: [
				{ value: SourceType.API, label: "REST API" },
				{ value: SourceType.DATABASE, label: "CSDL" },
				{ value: SourceType.FILE, label: "Tệp" },
			],
			required: true,
		},
		{
			label: "Độ tin cậy",
			name: "trust_score",
			type: "number",
			placeholder: "Nhập độ tin cậy (0-1)",
		},
		{
			label: "Mô tả",
			name: "description",
			type: "textarea",
			placeholder: "Nhập mô tả nguồn dữ liệu",
			required: false,
		},
		{
			label: "Thông tin kết nối",
			name: "connection_details",
			type: "object",
			placeholder: "Nhập thông tin kết nối",
			required: true,
			fields: formData?.source_type
				? getConnectionFields(formData.source_type)
				: [],
		},
		{
			label: "Thông tin xác thực",
			name: "credentials",
			type: "array",
			placeholder: "Nhập thông tin xác thực",
			arrayItemLabel: "Khóa",
			collapsible: true,
			required: false,
			fields: [
				{
					label: "Khóa",
					name: "key",
					type: "text",
					wrapperClassName: "col-span-6",
					placeholder: "Nhập khóa",
					required: true,
				},
				{
					label: "Giá trị",
					name: "value",
					wrapperClassName: "col-span-6",
					type: "text",
					placeholder: "Nhập giá trị",
					required: true,
				},
			],
		},
	] satisfies FieldConfig[];

const getConnectionFields = (type: SourceType): FieldConfig[] => {
	switch (type) {
		case SourceType.FILE:
			return [
				{
					label: "Đường dẫn tệp",
					name: "file_path",
					type: "text",
					placeholder: "Nhập đường dẫn tệp",
					description: "Đường dẫn đến tệp trên hệ thống tập tin",
					required: true,
				},
				{
					label: "Định dạng tệp",
					name: "file_format",
					type: "select",
					placeholder: "Chọn định dạng tệp",
					options: [
						{ value: "csv", label: "CSV" },
						{ value: "json", label: "JSON" },
						{ value: "txt", label: "TXT" },
						{ value: "pdf", label: "PDF" },
					],
					required: true,
				},
				{
					label: "Mã hóa",
					name: "encoding",
					type: "text",
					placeholder: "Nhập mã hóa (tùy chọn)",
					required: false,
				},
				{
					label: "Ký tự phân cách",
					name: "delimiter",
					type: "text",
					placeholder: "Nhập ký tự phân cách (tùy chọn)",
					required: false,
				},
			];
		case SourceType.DATABASE:
			return [
				{
					label: "Máy chủ",
					name: "host",
					type: "text",
					placeholder: "Nhập địa chỉ máy chủ cơ sở dữ liệu",
					required: true,
				},
				{
					label: "Cổng",
					name: "port",
					type: "number",
					placeholder: "Nhập cổng cơ sở dữ liệu",
					required: true,
				},
				{
					label: "Tên cơ sở dữ liệu",
					name: "database",
					type: "text",
					placeholder: "Nhập tên cơ sở dữ liệu",
					required: true,
				},
				{
					label: "Tên người dùng",
					name: "username",
					type: "text",
					placeholder: "Nhập tên người dùng",
					required: true,
				},
				{
					label: "Mật khẩu",
					name: "password",
					type: "password",
					placeholder: "Nhập mật khẩu (tùy chọn)",
					required: false,
				},
				{
					label: "Loại cơ sở dữ liệu",
					name: "db_type",
					type: "select",
					placeholder: "Chọn loại cơ sở dữ liệu",
					options: [
						{ value: "postgres", label: "PostgreSQL" },
						{ value: "mysql", label: "MySQL" },
						{ value: "mssql", label: "MS SQL Server" },
					],
					required: true,
				},
				{
					label: "Sử dụng SSL",
					name: "ssl",
					type: "switch",
					description: "Bật kết nối bảo mật",
					defaultValue: false,
					required: false,
				},
				{
					label: "Câu truy vấn SQL",
					name: "query",
					type: "textarea",
					placeholder: "Nhập câu truy vấn SQL (tùy chọn)",
					required: false,
				},
				{
					label: "Tên bảng",
					name: "table",
					type: "text",
					placeholder: "Nhập tên bảng (tùy chọn)",
					required: false,
				},
			];
		case SourceType.API:
			return [
				{
					label: "URL API",
					name: "url",
					type: "text",
					placeholder: "Nhập URL API (ví dụ: https://api.example.com/v1)",
					required: true,
				},
				{
					label: "Phương thức HTTP",
					name: "method",
					placeholder: "Chọn phương thức HTTP",
					type: "select",
					options: [
						{ value: "GET", label: "GET" },
						{ value: "POST", label: "POST" },
						{ value: "PUT", label: "PUT" },
						{ value: "DELETE", label: "DELETE" },
					],
					required: true,
				},
				{
					label: "Tiêu đề",
					name: "headers",
					type: "object",
					placeholder: "Nhập tiêu đề",
					required: false,
					fields: [
						{
							label: "Content-Type",
							name: "Content-Type",
							type: "text",
							placeholder: "application/json",
							required: false,
						},
						{
							label: "Accept",
							name: "Accept",
							type: "text",
							placeholder: "application/json",
							required: false,
						},
					],
				},
				{
					label: "Tham số truy vấn",
					name: "query_params",
					type: "object",
					placeholder: "Nhập tham số truy vấn",
					required: false,
				},
				{
					label: "Nội dung yêu cầu",
					name: "body",
					type: "textarea",
					placeholder: "Nhập nội dung yêu cầu (tùy chọn)",
					required: false,
				},
				{
					label: "Loại xác thực",
					name: "auth_type",
					type: "select",
					placeholder: "Chọn loại xác thực",
					options: [
						{ value: "BASIC", label: "Xác thực cơ bản" },
						{ value: "BEARER", label: "Bearer Token" },
					],
					required: false,
				},
				{
					label: "Cấu hình xác thực",
					name: "auth_config",
					type: "object",
					required: false,
					fields: [
						{
							label: "Tên người dùng",
							name: "username",
							type: "text",
							placeholder: "Nhập tên người dùng",
							required: false,
						},
						{
							label: "Mật khẩu",
							name: "password",
							type: "password",
							placeholder: "Nhập mật khẩu",
							required: false,
						},
						{
							label: "Token",
							name: "token",
							type: "text",
							placeholder: "Nhập bearer token",
							required: false,
						},
					],
				},
			];
		case SourceType.URL:
			return [
				{
					label: "URL",
					name: "url",
					type: "text",
					placeholder: "Nhập URL (ví dụ: https://example.com/data)",
					required: true,
				},
				{
					label: "Tiêu đề",
					name: "headers",
					type: "object",
					placeholder: "Nhập tiêu đề",
					required: false,
					fields: [
						{
							label: "User-Agent",
							name: "User-Agent",
							type: "text",
							placeholder: "Mozilla/5.0...",
							required: false,
						},
						{
							label: "Accept",
							name: "Accept",
							type: "text",
							placeholder: "text/html,application/xhtml+xml",
							required: false,
						},
					],
				},
				{
					label: "Cấu hình thu thập dữ liệu",
					name: "scrape_config",
					type: "object",
					required: false,
					fields: [
						{
							label: "CSS Selector",
							name: "selector",
							type: "text",
							placeholder: "Nhập CSS selector",
							required: false,
						},
						{
							label: "XPath",
							name: "xpath",
							type: "text",
							placeholder: "Nhập XPath",
							required: false,
						},
						{
							label: "Trích xuất bảng",
							name: "extract_tables",
							type: "switch",
							defaultValue: false,
							required: false,
						},
						{
							label: "Trích xuất liên kết",
							name: "extract_links",
							type: "switch",
							defaultValue: false,
							required: false,
						},
					],
				},
			];
		default:
			return [];
	}
};

interface FormCreateDataSourceProps {
	onCloseDialog?: () => void;
}

export const FormCreateDataSource = ({
	onCloseDialog,
}: FormCreateDataSourceProps) => {
	const { mutate: createDatasource } = useCreateDatasource({
		onSuccess: () => {
			toast.success("Tạo nguồn dữ liệu thành công");
			onCloseDialog?.();
		},
		onError: () => {
			toast.error("Lỗi khi tạo nguồn dữ liệu");
		},
	});

	return (
		<AppForm
			fields={formFields}
			schema={CreateDataSourceSchema}
			watchFields={["source_type"]}
			onSubmit={(values) =>
				createDatasource({
					name: values.name,
					description: values.description,
					source_type: values.source_type,
					trust_score: values.trust_score,
					credentials: values.credentials
						? Object.fromEntries(
								values.credentials.map((credential) => [
									credential.key,
									credential.value,
								]),
							)
						: undefined,
					connection_details: values.connection_details,
				})
			}
		/>
	);
};
