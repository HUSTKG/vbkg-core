import { Conflict } from "@vbkg/types";
import { useState } from "react";
import { ConflictTypeIcon } from "./ConflictTypeIcon";
import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";
import { Dialog, EntityCard } from "@/components";
import { CheckCircle, Zap } from "lucide-react";
import { AISuggestionCard } from "@/components/AISuggestionCard";

interface ConflictDetailsDialogProps {
	conflict: Conflict | null;
	isOpen: boolean;
	onOpenChange: (isOpen: boolean) => void;
	onResolve: (conflictId: string) => void;
	onAutoResolve: (conflictId: string) => void;
	onApplySuggestion: (conflictId: string, suggestion: any) => Promise<void>;
}

export default function ConflictDetailsDialog({
	conflict,
	isOpen,
	onOpenChange,
	onResolve,
	onAutoResolve,
	onApplySuggestion,
}: ConflictDetailsDialogProps) {
	const [applyingIndex, setApplyingIndex] = useState<number | null>(null);

	console.log(conflict)

	if (!isOpen || !conflict) return null;

	const handleApplySuggestion = async (suggestion: any, index: number) => {
		setApplyingIndex(index);
		try {
			await onApplySuggestion(conflict.id, suggestion);
		} finally {
			setApplyingIndex(null);
		}
	};

	return (
		<Dialog
			title={`Chi tiết xung đột - ${conflict.id}`}
			description="Xem và quản lý chi tiết xung đột trong hệ thống."
			open={isOpen}
			onOpenChange={onOpenChange}
		>
			<div className="space-y-6">
				{/* Basic Info */}
				<div className="grid grid-cols-2 gap-4">
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Loại xung đột
						</label>
						<div className="flex items-center space-x-2">
							<ConflictTypeIcon type={conflict.conflict_type} />
							<span className="text-sm text-gray-900 dark:text-white capitalize">
								{conflict.conflict_type.replace("_", " ")}
							</span>
						</div>
					</div>
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Độ nghiêm trọng
						</label>
						<SeverityBadge severity={conflict.severity} />
					</div>
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Trạng thái
						</label>
						<StatusBadge status={conflict.status} />
					</div>
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Độ tin cậy
						</label>
						<span className="text-sm text-gray-900 dark:text-white">
							{Math.round(conflict.confidence_score * 100)}%
						</span>
					</div>
				</div>

				{/* Description */}
				<div>
					<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						Mô tả
					</label>
					<p className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
						{conflict.description}
					</p>
				</div>

				{/* Context Data - Entity Information */}
				{conflict.context_data && (
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
							Thông tin thực thể
						</label>
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<EntityCard
								id={conflict.source_entity_id!}
								description={conflict.context_data.entity1_type}
								type={"Thực thể nguồn"}
								properties={
									[]
								}
								name={conflict.context_data.entity1_text}
							/>
							<EntityCard
								id={conflict.target_entity_id!}
								description={conflict.context_data.entity2_type}
								type={"Thực thể đích"}
								properties={
									[]
								}
								name={conflict.context_data.entity2_text}
							/>
						</div>
					</div>
				)}

				{/* Similarity Scores */}
				{conflict.context_data?.similarity_scores && (
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Điểm tương đồng
						</label>
						<div className="grid grid-cols-2 md:grid-cols-5 gap-3">
							{Object.entries(conflict.context_data.similarity_scores).map(
								([key, value]: [string, any]) => (
									<div
										key={key}
										className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md text-center"
									>
										<div className="text-sm font-medium text-gray-900 dark:text-white">
											{Math.round(parseFloat(value) * 100)}%
										</div>
										<div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
											{key === "text"
												? "Văn bản"
												: key === "semantic"
													? "Ngữ nghĩa"
													: key === "attributes"
														? "Thuộc tính"
														: key === "exact"
															? "Chính xác"
															: key}
										</div>
									</div>
								),
							)}
						</div>
					</div>
				)}

				{/* Conflicting Attributes */}
				{conflict.conflicting_attributes && (
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Thuộc tính xung đột
						</label>
						<div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
							{Object.entries(conflict.conflicting_attributes).map(
								([key, values]) => (
									<div key={key} className="mb-2 last:mb-0">
										<span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
											{key}:
										</span>
										<div className="mt-1 space-y-1">
											{Array.isArray(values) ? (
												values.map((value, index) => (
													<div
														key={index}
														className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-2 rounded border"
													>
														{value}
													</div>
												))
											) : (
												<div className="text-sm text-gray-900 dark:text-white bg-white dark:bg-gray-800 p-2 rounded border">
													{values as any}
												</div>
											)}
										</div>
									</div>
								),
							)}
						</div>
					</div>
				)}

				{/* AI Suggestions */}
				{conflict.auto_resolution_suggestions &&
					conflict.auto_resolution_suggestions.length > 0 && (
						<div>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
								Gợi ý giải quyết từ AI
							</label>
							<div className="space-y-4">
								{conflict.auto_resolution_suggestions.map(
									(suggestion: any, index: number) => (
										<AISuggestionCard
											key={index}
											suggestion={suggestion}
											index={index}
											onApply={(suggestion: any) =>
												handleApplySuggestion(suggestion, index)
											}
											isApplying={applyingIndex === index}
										/>
									),
								)}
							</div>
						</div>
					)}

				{/* Detection Info */}
				<div className="grid grid-cols-2 gap-4">
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Phát hiện bởi
						</label>
						<span className="text-sm text-gray-900 dark:text-white">
							{conflict.detected_by}
						</span>
					</div>
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Thời gian phát hiện
						</label>
						<span className="text-sm text-gray-900 dark:text-white">
							{new Date(conflict.detected_at).toLocaleString()}
						</span>
					</div>
				</div>

				{/* Assignment Info */}
				{conflict.assigned_to && (
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Được giao cho
						</label>
						<span className="text-sm text-gray-900 dark:text-white">
							{conflict.assigned_to}
						</span>
					</div>
				)}

				{/* Resolution Info */}
				{conflict.resolution && (
					<div>
						<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Thông tin giải quyết
						</label>
						<div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-md">
							<p className="text-sm text-gray-900 dark:text-white">
								<strong>Phương pháp:</strong>{" "}
								{conflict.resolution.resolution_method}
							</p>
							{conflict.resolution.reasoning && (
								<p className="text-sm text-gray-900 dark:text-white mt-1">
									<strong>Lý do:</strong> {conflict.resolution.reasoning}
								</p>
							)}
						</div>
					</div>
				)}
			</div>

			{/* Actions */}
			<div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3">
				<button
					onClick={() => onOpenChange(false)}
					className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
				>
					Đóng
				</button>
				{conflict.status === "detected" && (
					<>
						<button
							onClick={() => onAutoResolve(conflict.id)}
							className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
						>
							<Zap size={14} className="mr-1" />
							Tự động giải quyết
						</button>
						<button
							onClick={() => onResolve(conflict.id)}
							className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 flex items-center"
						>
							<CheckCircle size={14} className="mr-1" />
							Giải quyết thủ công
						</button>
					</>
				)}
			</div>
		</Dialog>
	);
};
