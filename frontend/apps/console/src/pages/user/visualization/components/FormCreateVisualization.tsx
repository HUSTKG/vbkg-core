import { AppForm, FieldConfig, toast } from "@/components";
import {
	useCreateVisualization,
	useUpdateVisualization,
} from "@vbkg/api-client";
import {
	CreateVisualizationSchema,
	UpdateVisualizationSchema,
} from "@vbkg/schemas";
import { Visualization, VisualizationType } from "@vbkg/types";
import z from "zod";

const visualizationFormFields = (
	data: z.infer<typeof CreateVisualizationSchema>,
) =>
	[
		{
			name: "visualization_type",
			type: "select",
			label: "Loại bảng biểu",
			defaultValue: VisualizationType.GRAPH,
			required: true,
			options: [
				{ value: VisualizationType.GRAPH, label: "Đồ thị" },
				{ value: VisualizationType.TABLE, label: "Bảng dữ liệu" },
				{ value: VisualizationType.CHART, label: "Biểu đồ/Phân tích" },
				{ value: VisualizationType.TREE, label: "Cây/Phân cấp" },
			],
		},
		{
			name: "name",
			type: "text",
			label: "Tên bảng biểu",
			placeholder: "Nhập tên bảng biểu của bạn",
			required: true,
		},
		{
			name: "description",
			type: "textarea",
			label: "Mô tả",
			placeholder: "Nhập mô tả cho bảng biểu (tùy chọn)",
		},
		{
			name: "entity_id",
			type: "text",
			label: "ID Thực thể",
			placeholder: "Nhập ID của thực thể liên quan (tùy chọn)",
		},
		{
			name: "query_id",
			type: "text",
			label: "ID Truy vấn",
			placeholder: "Nhập ID của truy vấn đã lưu (tùy chọn)",
		},
		{
			name: "cypher_query",
			type: "textarea",
			label: "Cypher Query",
			placeholder: "Nhập truy vấn Cypher để lấy dữ liệu (tùy chọn)",
		},
		{
			name: "is_public",
			type: "switch",
			label: "Công khai",
		},
		{
			name: "config",
			type: "object",
			required: true,
			label: "Cấu hình bảng biểu",
			fields: getVisualizationConfig(
				data.visualization_type as VisualizationType,
			),
		},
	] satisfies FieldConfig[];

interface FormCreateVisualizationProps {
	onOpenChange?: (open: boolean) => void;
	setEditingVisualization?: (visualization: any) => void;
	editingVisualization?: Visualization | null;
	mode?: "create" | "edit";
}

export default function FormCreateVisualization({
	onOpenChange,
	mode = "create",
	setEditingVisualization,
	editingVisualization,
}: FormCreateVisualizationProps) {
	const { mutate: updateVisualization } = useUpdateVisualization({
		onSuccess: () => {
			toast.success("Cập nhật Visualization thành công!");
			onOpenChange?.(false);
			setEditingVisualization?.(null);
		},
		onError: (error) => {
			toast.error(`Cập nhật thất bại: ${error.message}`);
		},
	});

	const { mutate: createVisualization } = useCreateVisualization({
		onSuccess: () => {
			toast.success("Tạo Visualization thành công!");
			onOpenChange?.(false);
		},
		onError: (error) => {
			toast.error(`Tạo thất bại: ${error.message}`);
		},
	});

	const handleCreateVisualization = (
		formData: z.infer<typeof CreateVisualizationSchema>,
	) => {
		const newVisualization = {
			...formData,
			visualization_type: formData.visualization_type as VisualizationType,
			config: formData.config,
			created_by: "current_user",
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString(),
		};
		createVisualization({
			...newVisualization,
		});
	};

	const handleUpdateVisualization = (
		formData: z.infer<typeof UpdateVisualizationSchema>,
	) => {
		const newVisualization = {
			...formData,
			visualization_type: formData.visualization_type as VisualizationType,
			config: formData.config,
			updated_at: new Date().toISOString(),
		};
		updateVisualization({
			id: editingVisualization?.id || "",
			...newVisualization,
		});
	};

	return mode === "create" ? (
		<AppForm
			fields={visualizationFormFields}
			schema={CreateVisualizationSchema}
			watchFields={["visualization_type"]}
			onSubmit={handleCreateVisualization}
			submitButtonText="Tạo Visualization"
		/>
	) : (
		<AppForm
			fields={visualizationFormFields}
			schema={UpdateVisualizationSchema}
			defaultValues={editingVisualization as any}
			watchFields={["visualization_type"]}
			onSubmit={handleUpdateVisualization}
			submitButtonText="Cập nhật Visualization"
		/>
	);
}

const getVisualizationConfig = (
	vizType: VisualizationType = VisualizationType.GRAPH,
): FieldConfig[] => {
	switch (vizType) {
		case VisualizationType.GRAPH:
			return [
				{
					name: "node_config",
					type: "object",
					label: "Cấu hình nút",
					fields: [
						{
							name: "color",
							type: "color",
							label: "Màu sắc",
							colSpan: 6,
							placeholder: "Nhập màu sắc cho nút",
						},
						{
							name: "size",
							type: "number",
							label: "Kích thước",
							colSpan: 6,
							placeholder: "Nhập kích thước nút",
						},
					],
				},
				{
					name: "edge_config",
					type: "object",
					label: "Cấu hình cạnh",
					fields: [
						{
							name: "color",
							type: "color",
							label: "Màu sắc cạnh",
							placeholder: "Nhập màu sắc cho cạnh",
						},
						{
							name: "width",
							type: "number",
							label: "Độ rộng cạnh",
							placeholder: "Nhập độ rộng cạnh",
						},
					],
				},
				{
					name: "layout",
					type: "object",
					label: "Bố cục đồ thị",
					fields: [
						{
							name: "type",
							type: "select",
							defaultValue: "grid",
							label: "Loại bố cục",
							options: [
								{ value: "circular", label: "Hình tròn" },
								{ value: "hierarchical", label: "Phân cấp" },
								{ value: "force-directed", label: "Lực đẩy" },
								{ value: "grid", label: "Lưới" },
								{ value: "random", label: "Ngẫu nhiên" },
							],
						},
					],
				},
			];
		case VisualizationType.TABLE:
			return [
				{
					name: "columns",
					type: "array",
					label: "Cột bảng",
					arrayItemLabel: "cột",
					fields: [
						{
							name: "field",
							type: "text",
							required: true,
							label: "Trường dữ liệu",
							placeholder: "Nhập trường dữ liệu cho cột",
						},
						{
							name: "header",
							type: "text",
							required: true,
							label: "Tiêu đề cột",
							placeholder: "Nhập tiêu đề hiển thị cho cột",
						},
						{
							name: "sortable",
							type: "switch",
							label: "Có thể sắp xếp",
						},
						{
							name: "filterable",
							type: "switch",
							label: "Có thể lọc",
						},
					],
				},
			];
		case VisualizationType.CHART:
			return [
				{
					name: "chart_type",
					type: "select",
					label: "Loại biểu đồ",
					options: [
						{ value: "bar", label: "Biểu đồ cột" },
						{ value: "line", label: "Biểu đồ đường" },
						{ value: "pie", label: "Biểu đồ tròn" },
						{ value: "scatter", label: "Biểu đồ phân tán" },
						{ value: "area", label: "Biểu đồ vùng" },
					],
				},
				{
					name: "axes",
					type: "object",
					label: "Trục biểu đồ",
					fields: [
						{
							name: "x_field",
							type: "text",
							label: "Trường trục X",
							placeholder: "Nhập trường dữ liệu cho trục X",
						},
						{
							name: "y_field",
							type: "text",
							label: "Trường trục Y (nếu có)",
							placeholder: "Nhập trường dữ liệu cho trục Y (nếu có)",
						},
					],
				},
			];
		case VisualizationType.TREE:
			return [
				{
					name: "node_config",
					type: "object",
					label: "Cấu hình nút cây",
					fields: [
						{
							name: "color",
							type: "text",
							label: "Màu sắc nút",
							placeholder: "Nhập màu sắc cho nút cây",
						},
						{
							name: "size",
							type: "number",
							label: "Kích thước nút",
							placeholder: "Nhập kích thước nút cây",
						},
					],
				},
				{
					name: "edge_config",
					type: "object",
					label: "Cấu hình cạnh cây",
					fields: [
						{
							name: "color",
							type: "text",
							label: "Màu sắc cạnh",
							placeholder: "Nhập màu sắc cho cạnh cây",
						},
						{
							name: "width",
							type: "number",
							label: "Độ rộng cạnh",
							placeholder: "Nhập độ rộng cạnh cây",
						},
					],
				},
				{
					name: "orientation",
					type: "select",
					label: "Hướng hiển thị cây",
					options: [
						{ value: "vertical", label: "Dọc" },
						{ value: "horizontal", label: "Ngang" },
					],
				},
				{
					name: "alignment",
					type: "select",
					label: "Căn chỉnh nhãn nút",
					options: [
						{ value: "center", label: "Giữa" },
						{ value: "left", label: "Trái" },
						{ value: "right", label: "Phải" },
					],
				},
				{
					name: "node_separation",
					type: "number",
					label: "Khoảng cách giữa các nút (px)",
				},
				{
					name: "level_separation",
					type: "number",
					label: "Khoảng cách giữa các cấp (px)",
				},
				{
					name: "show_labels",
					type: "checkbox",
					label: "Hiển thị nhãn nút",
				},
				{
					name: "show_tooltips",
					type: "checkbox",
					label: "Hiển thị tooltip khi di chuột",
				},
			];
		default:
			throw new Error("Unsupported visualization type");
	}
};
