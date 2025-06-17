import { Dialog } from "@/components";
import FormCreateApiKey from "./FormCreateApiKey";

interface CreateApiKeyDialogProps {
	open?: boolean;
	onOpenChange: (open: boolean) => void;
	onApiKeyCreated?: (apiKey: any) => void;
}

export default function CreateApiKeyDialog({
	open,
	onOpenChange,
	onApiKeyCreated,
}: CreateApiKeyDialogProps) {
	const handleApiKeyCreated = (newApiKey: any) => {
		// Đóng dialog ngay lập tức
		onOpenChange(false);
		// Callback để thêm API key mới vào danh sách với optimistic update
		onApiKeyCreated?.(newApiKey);
	};

	return (
		<Dialog
			open={open}
			onOpenChange={onOpenChange}
			title="Tạo API Key"
			description="Tạo một API Key mới để truy cập vào các dịch vụ của chúng tôi."
		>
			<FormCreateApiKey 
				setShowCreateModal={onOpenChange}
				onApiKeyCreated={handleApiKeyCreated}
			/>
		</Dialog>
	);
}
