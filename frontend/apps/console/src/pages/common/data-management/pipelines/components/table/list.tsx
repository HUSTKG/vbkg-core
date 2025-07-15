import {
	useDeletePipeline,
	usePipelines,
	useRunPipeline,
} from "@vbkg/api-client";
import { Pipeline, PipelineType } from "@vbkg/types";
import {
	Badge,
	ConfirmDialog,
	DataTable,
	SimpleColumnDef,
	toast,
} from "@/components";
import { Eye, Play, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

// Component badge loại pipeline
const TypeBadge = ({ type }: { type?: PipelineType }) => {
	switch (type) {
		case PipelineType.EXTRACTION:
			return (
				<Badge
					variant="outline"
					className="bg-blue-50 text-blue-700 border-blue-200"
				>
					Trích xuất
				</Badge>
			);
		case PipelineType.TRANSFORMATION:
			return (
				<Badge
					variant="outline"
					className="bg-purple-50 text-purple-700 border-purple-200"
				>
					Chuyển đổi
				</Badge>
			);
		case PipelineType.LOADING:
			return (
				<Badge
					variant="outline"
					className="bg-amber-50 text-amber-700 border-amber-200"
				>
					Tải dữ liệu
				</Badge>
			);
		case PipelineType.COMPLETE:
			return (
				<Badge
					variant="outline"
					className="bg-emerald-50 text-emerald-700 border-emerald-200"
				>
					Hoàn thiện
				</Badge>
			);
		default:
			return <Badge variant="outline">Chưa xác định</Badge>;
	}
};

export default function DataPipelineTable() {
	const { data: pipelines } = usePipelines({});
	const navigate = useNavigate();
	const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(
		null,
	);
	const [showDeleteDialog, setShowDeleteDialog] = useState(false);

	const columns: SimpleColumnDef<Pipeline, any>[] = [
		{
			header: "Tên",
			accessorKey: "name",
			cell: (row) => <div className="font-medium">{row?.name}</div>,
		},
		{
			header: "Mô tả",
			accessorKey: "description",
			cell: (row) => (
				<div className="text-sm text-muted-foreground max-w-md truncate">
					{row?.description || "Không có mô tả"}
				</div>
			),
		},
		{
			header: "Loại",
			accessorKey: "pipeline_type",
			cell: (row) => <TypeBadge type={row?.pipeline_type} />,
		},
		{
			header: "Cập nhật lúc",
			accessorKey: "updated_at",
			cell: (row) => (
				<div className="text-sm">
					{row?.updated_at
						? new Date(row.updated_at).toLocaleDateString("vi-VN")
						: "Chưa có"}
				</div>
			),
		},
	];

	const { mutate: deletePipeline } = useDeletePipeline({
		onSuccess: () => {
			toast.success("Xóa thành công pipeline.");
			setShowDeleteDialog(false);
			setSelectedPipeline(null);
		},
		onError: () => {
			toast.error("Không thể xóa pipeline. Vui lòng thử lại.");
		},
	});

	const { mutate: runPipeline } = useRunPipeline({
		onSuccess: () => {
			toast.success("Pipeline đã được khởi chạy thành công.");
		},
		onError: () => {
			toast.error("Không thể khởi chạy pipeline. Vui lòng thử lại.");
		},
	});

	const confirmDeletePipeline = async () => {
		if (!selectedPipeline) return;
		deletePipeline({ id: selectedPipeline.id });
	};

	const handleRunPipeline = async (pipeline?: Pipeline) => {
		if (!pipeline) return;
		runPipeline({ id: pipeline.id });
	};

	const handleDeletePipeline = (pipeline: Pipeline) => {
		setSelectedPipeline(pipeline);
		setShowDeleteDialog(true);
	};

	const handleViewPipeline = (pipeline: Pipeline) => {
		navigate(`./${pipeline.id}`);
	};

	return (
		<>
			<DataTable<Pipeline, any>
				data={pipelines?.data}
				columns={columns}
				showGlobalFilter={true}
				showColumnFilters={true}
				showPagination={true}
				actionsOptions={{
					show: true,
					position: "end",
					actions: [
						{
							label: "Xem chi tiết",
							icon: <Eye className="h-4 w-4" />,
							onClick: handleViewPipeline,
							variant: "ghost",
						},
						{
							label: "Chạy Pipeline",
							icon: <Play className="h-4 w-4" />,
							onClick: handleRunPipeline,
							variant: "outline",
							className: "text-green-600 hover:text-green-700",
						},
						{
							label: "Xóa",
							icon: <Trash2 className="h-4 w-4" />,
							onClick: handleDeletePipeline,
							variant: "outline",
							className: "text-red-600 hover:text-red-700",
						},
					],
					showInDropdown: true,
					dropdownLabel: "Hành động",
				}}
			/>
			{selectedPipeline && (
				<ConfirmDialog
					isOpen={showDeleteDialog}
					type="delete"
					onCancel={() => setShowDeleteDialog(false)}
					onConfirm={confirmDeletePipeline}
					message={`Bạn có chắc chắn muốn xóa pipeline "${selectedPipeline.name}" không? Hành động này không thể hoàn tác.`}
					title={`Xóa Pipeline "${selectedPipeline.name}"`}
				/>
			)}
		</>
	);
}
