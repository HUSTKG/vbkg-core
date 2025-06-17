import React, { useState } from "react";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Conflict, ConflictType, ResolutionMethod } from "@vbkg/types";
import { useResolveConflict } from "@vbkg/api-client";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Target } from "lucide-react";
import { AppForm, Dialog, FieldConfig, toast } from "@/components";

// Schema for manual resolution form based on ResolveConflictSchema
const manualResolutionSchema = z.object({
	resolution_method: z.enum(
		[
			"merge_entities",
			"keep_both",
			"keep_source",
			"keep_target",
			"create_new",
			"delete_conflicting",
			"manual_edit",
			"ai_resolution",
		],
		{
			required_error: "Vui lòng chọn phương pháp giải quyết",
		},
	),
	reasoning: z.string().min(10, {
		message: "Lý do phải có ít nhất 10 ký tự",
	}),
	confidence_score: z.number().min(0).max(1).default(0.8),
	validation_required: z.boolean().default(false),
	resolution_data: z.record(z.any()).default({}),
});

type ManualResolutionData = z.infer<typeof manualResolutionSchema>;

interface ManualResolutionDialogProps {
	conflict: Conflict | null;
	isOpen: boolean;
	onOpenChange: (open: boolean) => void;
	onSuccess?: (
		conflictId: string,
		resolutionData: ManualResolutionData,
	) => void;
}

const ManualResolutionDialog: React.FC<ManualResolutionDialogProps> = ({
	conflict,
	isOpen,
	onOpenChange,
	onSuccess,
}) => {
	const [isSubmitting, setIsSubmitting] = useState(false);
	const { mutate: resolveConflict } = useResolveConflict();

	// Dynamic form fields based on conflict type and selected resolution method
	const getFormFields = (
		formData: Partial<ManualResolutionData>,
	): FieldConfig[] => {
		const baseFields: FieldConfig[] = [
			{
				name: "resolution_method",
				label: "Phương pháp giải quyết",
				type: "select",
				required: true,
				placeholder: "Chọn phương pháp giải quyết",
				description: "Chọn cách thức giải quyết xung đột này",
				options: getResolutionMethodOptions(conflict?.conflict_type),
			},
			{
				name: "reasoning",
				label: "Lý do giải quyết",
				type: "textarea",
				required: true,
				placeholder:
					"Mô tả chi tiết lý do và cách thức giải quyết xung đột này...",
				description:
					"Giải thích tại sao bạn chọn phương pháp này và logic đằng sau quyết định",
			},
			{
				name: "confidence_score",
				label: "Độ tin cậy (0-1)",
				type: "number",
				defaultValue: 0.8,
				placeholder: "0.8",
				description: "Mức độ tin cậy vào giải pháp này (0-1)",
			},
			{
				name: "validation_required",
				label: "Yêu cầu validation",
				type: "switch",
				defaultValue: false,
				description: "Có cần validation thêm sau khi áp dụng giải pháp không?",
			},
		];

		// Add resolution_data fields based on conflict type and resolution method
		const resolutionDataFields = getResolutionDataFields(
			conflict?.conflict_type,
			formData.resolution_method,
		);

		if (resolutionDataFields.length > 0) {
			baseFields.push({
				name: "resolution_data",
				label: "Dữ liệu giải quyết",
				type: "object",
				description: "Thông tin chi tiết cho phương pháp giải quyết được chọn",
				fields: resolutionDataFields,
			});
		}

		return baseFields;
	};

	// Get resolution method options based on conflict type
	const getResolutionMethodOptions = (conflictType?: ConflictType) => {
		const allOptions = [
			{ label: "Gộp các entities", value: "merge_entities" },
			{ label: "Giữ cả hai", value: "keep_both" },
			{ label: "Giữ entity nguồn", value: "keep_source" },
			{ label: "Giữ entity đích", value: "keep_target" },
			{ label: "Tạo mới", value: "create_new" },
			{ label: "Xóa các phần tử xung đột", value: "delete_conflicting" },
			{ label: "Chỉnh sửa thủ công", value: "manual_edit" },
			{ label: "Giải quyết bằng AI", value: "ai_resolution" },
		];

		// Filter options based on conflict type
		switch (conflictType) {
			case ConflictType.DUPLICATE_ENTITY:
				return allOptions.filter((opt) =>
					[
						"merge_entities",
						"keep_source",
						"keep_target",
						"delete_conflicting",
						"manual_edit",
					].includes(opt.value),
				);
			case ConflictType.CONTRADICTORY_RELATIONSHIP:
				return allOptions.filter((opt) =>
					[
						"keep_source",
						"keep_target",
						"delete_conflicting",
						"manual_edit",
						"create_new",
					].includes(opt.value),
				);
			case ConflictType.ATTRIBUTE_MISMATCH:
				return allOptions.filter((opt) =>
					[
						"keep_source",
						"keep_target",
						"manual_edit",
						"ai_resolution",
					].includes(opt.value),
				);
			case ConflictType.TEMPORAL_CONFLICT:
				return allOptions.filter((opt) =>
					[
						"manual_edit",
						"keep_source",
						"keep_target",
						"ai_resolution",
					].includes(opt.value),
				);
			case ConflictType.MISSING_RELATIONSHIP:
				return allOptions.filter((opt) =>
					["create_new", "manual_edit"].includes(opt.value),
				);
			case ConflictType.SOURCE_CONFLICT:
				return allOptions.filter((opt) =>
					["keep_source", "keep_target", "manual_edit"].includes(opt.value),
				);
			case ConflictType.SCHEMA_MISMATCH:
				return allOptions.filter((opt) =>
					["manual_edit", "ai_resolution"].includes(opt.value),
				);
			default:
				return allOptions;
		}
	};

	// Get resolution data fields based on conflict type and method
	const getResolutionDataFields = (
		conflictType?: ConflictType,
		resolutionMethod?: string,
	): FieldConfig[] => {
		if (!conflictType || !resolutionMethod) return [];

		const fields: FieldConfig[] = [];

		// Common fields for all resolution methods
		if (resolutionMethod === "manual_edit") {
			fields.push({
				name: "edit_instructions",
				label: "Hướng dẫn chỉnh sửa",
				type: "textarea",
				required: true,
				placeholder: "Mô tả chi tiết các thay đổi cần thực hiện...",
				description:
					"Hướng dẫn cụ thể về cách chỉnh sửa để giải quyết xung đột",
			});
		}

		// Specific fields based on conflict type and resolution method
		switch (conflictType) {
			case ConflictType.DUPLICATE_ENTITY:
				if (resolutionMethod === "merge_entities") {
					fields.push(
						{
							name: "target_entity_id",
							label: "Entity đích (sẽ giữ lại)",
							type: "text",
							required: true,
							placeholder: "ID của entity sẽ được giữ lại",
							description: "Entity này sẽ chứa dữ liệu sau khi merge",
						},
						{
							name: "merge_attributes",
							label: "Thuộc tính cần merge",
							type: "array",
							arrayItemLabel: "Thuộc tính",
							description: "Danh sách thuộc tính cần merge từ entity nguồn",
							fields: [
								{
									name: "attribute_name",
									label: "Tên thuộc tính",
									type: "text",
									required: true,
								},
								{
									name: "merge_strategy",
									label: "Chiến lược merge",
									type: "select",
									required: true,
									options: [
										{ label: "Giữ giá trị từ nguồn", value: "keep_source" },
										{ label: "Giữ giá trị từ đích", value: "keep_target" },
										{ label: "Kết hợp cả hai", value: "combine" },
										{ label: "Chọn giá trị mới", value: "custom" },
									],
								},
								{
									name: "custom_value",
									label: "Giá trị tùy chỉnh",
									type: "text",
									placeholder: "Nhập giá trị mới (nếu chọn custom)",
								},
							],
						},
						{
							name: "preserve_relationships",
							label: "Bảo toàn quan hệ",
							type: "switch",
							defaultValue: true,
							description:
								"Chuyển tất cả quan hệ từ entity nguồn sang entity đích",
						},
					);
				}
				break;

			case ConflictType.CONTRADICTORY_RELATIONSHIP:
				if (resolutionMethod === "create_new") {
					fields.push(
						{
							name: "new_relationship_type",
							label: "Loại quan hệ mới",
							type: "text",
							required: true,
							placeholder: "Ví dụ: works_at, located_in, part_of",
						},
						{
							name: "relationship_properties",
							label: "Thuộc tính quan hệ",
							type: "textarea",
							placeholder: "JSON object chứa các thuộc tính của quan hệ",
						},
					);
				}
				break;

			case ConflictType.ATTRIBUTE_MISMATCH:
				fields.push(
					{
						name: "attribute_name",
						label: "Tên thuộc tính xung đột",
						type: "text",
						required: true,
						defaultValue: conflict?.conflicting_attributes
							? Object.keys(conflict.conflicting_attributes)[0]
							: "",
						description: "Thuộc tính đang gây ra xung đột",
					},
					{
						name: "resolved_value",
						label: "Giá trị sau giải quyết",
						type: "text",
						required: true,
						placeholder: "Giá trị đúng cho thuộc tính này",
					},
					{
						name: "apply_to_entity",
						label: "Áp dụng cho entity",
						type: "select",
						required: true,
						options: [
							{ label: "Entity nguồn", value: "source" },
							{ label: "Entity đích", value: "target" },
							{ label: "Cả hai", value: "both" },
						],
					},
				);
				break;

			case ConflictType.TEMPORAL_CONFLICT:
				fields.push({
					name: "timeline_correction",
					label: "Sửa chữa timeline",
					type: "array",
					arrayItemLabel: "Sự kiện",
					description: "Danh sách các sự kiện theo thứ tự thời gian đúng",
					fields: [
						{
							name: "event_id",
							label: "ID sự kiện",
							type: "text",
							required: true,
						},
						{
							name: "corrected_date",
							label: "Ngày đã sửa",
							type: "date",
							required: true,
						},
						{
							name: "confidence",
							label: "Độ tin cậy",
							type: "number",
							defaultValue: 0.8,
						},
					],
				});
				break;

			case ConflictType.MISSING_RELATIONSHIP:
				if (resolutionMethod === "create_new") {
					fields.push(
						{
							name: "entity1_id",
							label: "Entity 1 ID",
							type: "text",
							required: true,
							defaultValue: conflict?.source_entity_id || "",
						},
						{
							name: "entity2_id",
							label: "Entity 2 ID",
							type: "text",
							required: true,
							defaultValue: conflict?.target_entity_id || "",
						},
						{
							name: "relationship_type",
							label: "Loại quan hệ",
							type: "text",
							required: true,
							placeholder: "Ví dụ: works_at, located_in, part_of",
						},
						{
							name: "relationship_properties",
							label: "Thuộc tính quan hệ",
							type: "textarea",
							placeholder: "JSON object chứa các thuộc tính (optional)",
						},
					);
				}
				break;
		}

		return fields;
	};

	const handleSubmit = async (data: ManualResolutionData) => {
		if (!conflict) return;

		setIsSubmitting(true);
		try {
			resolveConflict({
				conflict_id: conflict.id,
				resolution_method: data.resolution_method as ResolutionMethod,
				reasoning: data.reasoning,
				confidence_score: data.confidence_score,
				validation_required: data.validation_required,
				resolution_data: data.resolution_data,
			});

			toast.success("Giải quyết thành công");

			onSuccess?.(conflict.id, data);
			onOpenChange(false);
		} catch (error) {
			toast.error("Có lỗi xảy ra khi giải quyết xung đột. Vui lòng thử lại.");
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleError = (errors: any) => {
		console.error("Form validation errors:", errors);
		toast.error("Vui lòng kiểm tra lại thông tin trong form");
	};

	if (!conflict) return null;

	// Get conflict type label
	const getConflictTypeLabel = (type: ConflictType) => {
		const labels = {
			[ConflictType.DUPLICATE_ENTITY]: "Entity trùng lặp",
			[ConflictType.CONTRADICTORY_RELATIONSHIP]: "Quan hệ mâu thuẫn",
			[ConflictType.MISSING_RELATIONSHIP]: "Thiếu quan hệ",
			[ConflictType.ATTRIBUTE_MISMATCH]: "Thuộc tính không khớp",
			[ConflictType.TEMPORAL_CONFLICT]: "Xung đột thời gian",
			[ConflictType.SOURCE_CONFLICT]: "Xung đột nguồn",
			[ConflictType.SCHEMA_MISMATCH]: "Schema không khớp",
		};
		return labels[type] || type;
	};

	return (
		<Dialog
			title="Giải quyết xung đột"
			description="Sử dụng form dưới đây để giải quyết xung đột đã phát hiện. Chọn phương pháp phù hợp và cung cấp lý do giải quyết."
			open={isOpen}
			onOpenChange={onOpenChange}
		>
			{/* Conflict Information */}
			<div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-6">
				<h4 className="font-medium text-gray-900 dark:text-white mb-3">
					Thông tin xung đột
				</h4>
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
					<div>
						<span className="text-gray-500 dark:text-gray-400">ID:</span>
						<span className="ml-2 font-mono">{conflict.id.slice(0, 8)}...</span>
					</div>
					<div>
						<span className="text-gray-500 dark:text-gray-400">Loại:</span>
						<Badge variant="outline" className="ml-2">
							{getConflictTypeLabel(conflict.conflict_type)}
						</Badge>
					</div>
					<div>
						<span className="text-gray-500 dark:text-gray-400">
							Độ nghiêm trọng:
						</span>
						<Badge
							variant={
								conflict.severity === "critical" ? "destructive" : "secondary"
							}
							className="ml-2"
						>
							{conflict.severity}
						</Badge>
					</div>
					<div>
						<span className="text-gray-500 dark:text-gray-400">
							Độ tin cậy:
						</span>
						<span className="ml-2">
							{Math.round(conflict.confidence_score * 100)}%
						</span>
					</div>
					<div className="md:col-span-2">
						<span className="text-gray-500 dark:text-gray-400">Mô tả:</span>
						<p className="ml-2 mt-1">{conflict.description}</p>
					</div>
					{conflict.context_data && (
						<div className="md:col-span-2">
							<span className="text-gray-500 dark:text-gray-400">
								Entities liên quan:
							</span>
							<div className="flex items-center space-x-2 mt-1">
								{conflict.context_data.entity1_text && (
									<Badge variant="outline">
										{conflict.context_data.entity1_text}
									</Badge>
								)}
								{conflict.context_data.entity1_text &&
									conflict.context_data.entity2_text && (
										<span className="text-gray-400">vs</span>
									)}
								{conflict.context_data.entity2_text && (
									<Badge variant="outline">
										{conflict.context_data.entity2_text}
									</Badge>
								)}
							</div>
						</div>
					)}
					{conflict.source_entity_id && (
						<div>
							<span className="text-gray-500 dark:text-gray-400">
								Entity nguồn:
							</span>
							<span className="ml-2 font-mono text-xs">
								{conflict.source_entity_id}
							</span>
						</div>
					)}
					{conflict.target_entity_id && (
						<div>
							<span className="text-gray-500 dark:text-gray-400">
								Entity đích:
							</span>
							<span className="ml-2 font-mono text-xs">
								{conflict.target_entity_id}
							</span>
						</div>
					)}
				</div>
			</div>

			{/* Manual Resolution Form */}
			<AppForm
				fields={getFormFields}
				schema={manualResolutionSchema}
				onSubmit={handleSubmit}
				onError={handleError}
				isLoading={isSubmitting}
				submitButtonText={
					isSubmitting ? "Đang xử lý..." : "Giải quyết xung đột"
				}
				resetButton={true}
				resetButtonText="Đặt lại"
				className="space-y-6"
				watchFields={["resolution_method"]}
				buttons={
					<div className="flex items-center justify-end space-x-3 pt-4 border-t">
						<Button
							type="button"
							variant="outline"
							onClick={() => onOpenChange(false)}
							disabled={isSubmitting}
						>
							Hủy
						</Button>
						<Button
							type="submit"
							disabled={isSubmitting}
							className="bg-blue-600 hover:bg-blue-700"
						>
							{isSubmitting ? (
								<>
									<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
									Đang xử lý...
								</>
							) : (
								<>
									<Target className="h-4 w-4 mr-2" />
									Giải quyết xung đột
								</>
							)}
						</Button>
					</div>
				}
			/>
		</Dialog>
	);
};

export default ManualResolutionDialog;
