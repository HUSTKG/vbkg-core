import { Button } from "@/components";
import { APIKey } from "@vbkg/types";
import { Check, Copy, Eye, EyeOff, Trash2 } from "lucide-react";
import { useState } from "react";
import RevokeApiKeyDialog from "./RevokeConfirmDialog";

export const ApiKeyCard = ({
	apiKey,
}: {
	apiKey: APIKey;
}) => {
	const [showKey, setShowKey] = useState(false);
	const [copied, setCopied] = useState(false);

	const [showDelete, setShowDelete] = useState(false);

	const handleCopyKey = () => {
		if (!apiKey?.token) return;
		navigator.clipboard.writeText(apiKey.token);
		setCopied(true);
		setTimeout(() => setCopied(false), 2000);
	};

	const formatKey = (key?: string) => {
		if (!key) return "";
		if (showKey) return key;
		if (key.length <= 12) return key + ".".repeat(12); // If key is short, just return it
		return (
			key.substring(0, 8) +
			"•".repeat(Math.min(24, key.length - 12)) +
			key.substring(key.length - 4)
		);
	};

	const getStatusColor = (is_active: boolean) => {
		return is_active
			? "bg-green-100 text-green-800"
			: "bg-red-100 text-red-800";
	};

	return (
		<>
			<div className="bg-white border rounded-lg p-6 hover:shadow-md transition-shadow">
				<div className="flex items-start justify-between mb-4">
					<div className="flex-1 min-w-0">
						<h3 className="text-lg font-medium truncate">{apiKey.name}</h3>
						<p className="text-sm text-gray-600 mt-1 line-clamp-2">
							{apiKey.description}
						</p>
					</div>
					<div className="flex items-center space-x-2 ml-4 flex-shrink-0">
						<span
							className={`px-2 py-1 text-xs rounded-full whitespace-nowrap ${getStatusColor(apiKey.is_active)}`}
						>
							{apiKey.is_active ? "Kích hoạt" : "Đã thu hồi"}
						</span>
						<div className="flex items-center space-x-1">
							{apiKey.is_active && (
								<Button
									onClick={() => setShowDelete(true)}
									className="p-1 hover:bg-orange-50 rounded text-orange-600"
									variant="ghost"
									title="Thu hồi API Key"
								>
									<Trash2 size={16} />
								</Button>
							)}
						</div>
					</div>
				</div>

				<div className="space-y-3">
					<div>
						<label className="text-xs font-medium text-gray-500 uppercase">
							API Key
						</label>
						<div className="flex items-center space-x-2 mt-1">
							<code className="flex-1 min-w-0 p-2 bg-gray-50 rounded text-sm font-mono break-all">
								{formatKey(apiKey?.token || apiKey?.key_prefix )}
							</code>
							{apiKey?.token && (
								<>
									<Button
										onClick={() => setShowKey(!showKey)}
										className="p-2 hover:bg-gray-100 rounded flex-shrink-0"
										variant="ghost"
										title={showKey ? "Ẩn Key" : "Hiện Key"}
									>
										{showKey ? (
											<EyeOff size={16} />
										) : (
											<Eye size={16} className="opacity-50" />
										)}
									</Button>
									<Button
										onClick={handleCopyKey}
										variant="ghost"
										className="p-2 hover:bg-gray-100 rounded flex-shrink-0"
										title="Copy Key"
									>
										{copied ? (
											<Check size={16} className="text-green-500" />
										) : (
											<Copy size={16} />
										)}
									</Button>
								</>
							)}
						</div>
					</div>

					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<span className="text-gray-500">Ngày tạo:</span>
							<div className="font-medium">
								{new Date(apiKey.created_at).toLocaleDateString("vi-VN")}
							</div>
						</div>
						<div>
							<span className="text-gray-500">Lần cuối sử dụng:</span>
							<div className="font-medium">
								{apiKey.last_used
									? new Date(apiKey.last_used).toLocaleDateString("vi-VN")
									: "Chưa sử dụng"}
							</div>
						</div>
						<div>
							<span className="text-gray-500">Số lần gọi:</span>
							<div className="font-medium">
								{apiKey.usage_count?.toLocaleString("vi-VN") || 0}
							</div>
						</div>
						<div>
							<span className="text-gray-500">Giới hạn:</span>
							<div className="font-medium">
								{apiKey.rate_limit || "Không giới hạn"}
							</div>
						</div>
					</div>
				</div>
			</div>
			<RevokeApiKeyDialog
				open={showDelete}
				onOpenChange={setShowDelete}
				apiKey={apiKey}
			/>
		</>
	);
};
