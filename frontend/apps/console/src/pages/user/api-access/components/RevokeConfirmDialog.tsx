import { Dialog, toast } from "@/components";
import { useRevokeAPIKey } from "@vbkg/api-client";
import { APIKey } from "@vbkg/types";
import { AlertTriangle } from "lucide-react";

interface RevokeApiKeyDialogProps {
	open?: boolean;
	onOpenChange: (open: boolean) => void;
	apiKey: APIKey;
	isLoading?: boolean;
}

export default function RevokeApiKeyDialog({
	open,
	onOpenChange,
	apiKey,
	isLoading = false,
}: RevokeApiKeyDialogProps) {
	const { mutate: revokeApiKey } = useRevokeAPIKey({
		onSuccess: () => {
			toast.success("API key revoked successfully");
			onOpenChange(false);
		},
		onError: () => {
			toast.error("Failed to revoke API key");
		},
	});
	const handleConfirm = () => {
		revokeApiKey({ api_key_id: apiKey.id });
	};

	return (
		<Dialog
			open={open}
			onOpenChange={onOpenChange}
			title="Thu hồi API Key"
			description="Bạn có chắc chắn muốn thu hồi API Key này không?"
		>
			<div className="space-y-4">
				{/* Warning Notice */}
				<div className="bg-red-50 border border-red-200 rounded-lg p-4">
					<div className="flex items-start space-x-3">
						<AlertTriangle
							className="text-red-600 flex-shrink-0 mt-0.5"
							size={20}
						/>
						<div className="text-sm">
							<h4 className="font-semibold text-red-800 mb-1">Cảnh báo!</h4>
							<div className="text-red-700 space-y-1">
								<p>
									• API Key <strong>"{apiKey.name}"</strong> sẽ bị vô hiệu hóa
									ngay lập tức
								</p>
								<p>
									• Tất cả các ứng dụng đang sử dụng key này sẽ không thể truy
									cập
								</p>
								<p>• Hành động này không thể hoàn tác</p>
								<p>• Bạn có thể xóa hoàn toàn API Key sau khi thu hồi</p>
							</div>
						</div>
					</div>
				</div>

				{/* API Key Info */}
				<div className="bg-gray-50 rounded-lg p-3">
					<div className="text-sm">
						<span className="text-gray-600">API Key sẽ bị thu hồi:</span>
						<div className="font-medium text-gray-900 mt-1">{apiKey.name}</div>
					</div>
				</div>

				{/* Action Buttons */}
				<div className="flex justify-end space-x-3 pt-4 border-t">
					<button
						onClick={() => onOpenChange(false)}
						disabled={isLoading}
						className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
					>
						Hủy
					</button>
					<button
						onClick={handleConfirm}
						disabled={isLoading}
						className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center space-x-2"
					>
						{isLoading ? (
							<>
								<div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
								<span>Đang thu hồi...</span>
							</>
						) : (
							<>
								<AlertTriangle size={16} />
								<span>Thu hồi API Key</span>
							</>
						)}
					</button>
				</div>
			</div>
		</Dialog>
	);
}
