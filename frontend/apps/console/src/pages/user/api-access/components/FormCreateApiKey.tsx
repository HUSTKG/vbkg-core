import { AppForm, FieldConfig, toast } from "@/components";
import { useCreateAPIKey } from "@vbkg/api-client";
import { APIKey } from "@vbkg/types";
import z from "zod";

const CreateApiKeySchema = z.object({
	name: z.string().min(1, "API Key Name is required"),
	description: z.string().optional(),
	rate_limit: z.string().optional(),
	expires_at: z.date().optional(),
	allowed_ips: z
		.string()
		.optional()
		.transform((val) => (val ? val.split(",").map((ip) => ip.trim()) : [])),
});

interface CreateApiKeyProps {
	setShowCreateModal: (show: boolean) => void;
	onApiKeyCreated: (apiKey: APIKey) => void;
}

export default function FormCreateApiKey({
	setShowCreateModal,
	onApiKeyCreated,
}: CreateApiKeyProps) {
	const { mutate: createApiKey } = useCreateAPIKey({
		onSuccess: (data) => {
			toast.success("API Key created successfully!");
			setShowCreateModal(false);
			onApiKeyCreated({
				...data.data,
			});
		},
		onError: (error) => {
			toast.error(`Error creating API Key: ${error.message}`);
		},
	});

	const apiKeyFormFields: FieldConfig[] = [
		{
			name: "name",
			type: "text",
			label: "Tên",
			placeholder: "Nhập tên cho API Key",
			required: true,
		},
		{
			name: "description",
			type: "textarea",
			label: "Mô tả",
			placeholder: "Nhập mô tả cho API Key (tùy chọn)",
		},
		{
			name: "rate_limit",
			type: "text",
			label: "Giới hạn (Tùy chọn)",
			placeholder: "e.g., 1000 req/hour",
		},
		{
			name: "allowed_ips",
			type: "textarea",
			label: "Địa chỉ IP được phép (Tùy chọn)",
			placeholder:
				"Nhập địa chỉ IP được phép sử dụng API Key, cách nhau bằng dấu phẩy",
		},
		{
			name: "expires_at",
			type: "date",
			label: "Ngày hết hạn (Tùy chọn)",
			placeholder: "YYYY-MM-DD",
		},
	];

	// Handle create API key
	const handleCreateApiKey = (formData: any) => {
		const newKey = {
			...formData,
		};

		createApiKey(newKey);

		setShowCreateModal(false);
	};

	return (
		<AppForm
			fields={apiKeyFormFields}
			schema={CreateApiKeySchema}
			onSubmit={handleCreateApiKey}
			submitButtonText={"Tạo mới"}
		/>
	);
}
