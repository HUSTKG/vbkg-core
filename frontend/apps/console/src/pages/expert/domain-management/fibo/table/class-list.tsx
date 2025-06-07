import { FIBOClass } from "@vbkg/types";
import { ActionButton, Badge, DataTable, SimpleColumnDef, toast } from "@/components";
import { Edit, ExternalLink, Eye, Trash2 } from "lucide-react";
import { useState } from "react";
import EditFiboClassDialog from "../dialog/edit-class";
import ViewFiboClassDialog from "../dialog/view-class";
import { useDeleteFiboClass } from "@vbkg/api-client";

interface ClassListTableProps {
	classes: FIBOClass[];
	getClassById: (id: number) => FIBOClass | undefined;
}
export default function ClassListTable({
	classes,
	getClassById,
}: ClassListTableProps) {
	const [selectedClass, setSelectedClass] = useState<FIBOClass | null>(null);
	const [isEditClassModalOpen, setIsEditClassModalOpen] = useState(false);
	const [isViewClassModalOpen, setIsViewClassModalOpen] = useState(false);
	const { mutate: deleteClass } = useDeleteFiboClass({
		onSuccess: () => {
			toast("Xóa lớp thành công");
		},
		onError: (error) => {
			toast("Xóa lớp thất bại: " + error.message);
		},
	});

	// Table columns for FIBO Classes
	const classColumns: SimpleColumnDef<FIBOClass, any>[] = [
		{
			accessorKey: "label",
			header: "Label",
			cell: (row) => (
				<div>
					<div className="font-medium uppercase">
						{row?.label || "No Label"}
					</div>
					<div className="text-xs text-gray-500 font-mono truncate max-w-xs">
						{row?.uri}
					</div>
				</div>
			),
		},
		{
			accessorKey: "domain",
			header: "Domain",
			cell: (row) => (
				<Badge variant={row?.domain ? "default" : "secondary"}>
					{row?.domain || "No Domain"}
				</Badge>
			),
		},
		{
			accessorKey: "parent_class_id",
			header: "Parent Class",
			cell: (row) => {
				const parent = row?.parent_class_id
					? getClassById(row.parent_class_id)
					: null;
				return parent ? (
					<span className="text-sm">{parent.label || parent.uri}</span>
				) : (
					<span className="text-gray-400 text-sm">No parent</span>
				);
			},
		},
		{
			accessorKey: "is_custom",
			header: "Type",
			cell: (row) => (
				<Badge variant={row?.is_custom ? "outline" : "default"}>
					{row?.is_custom ? "Custom" : "FIBO"}
				</Badge>
			),
		},
		{
			accessorKey: "updated_at",
			header: "Updated",
			cell: (row) =>
				new Date(row?.updated_at || "").toLocaleDateString("vi-VN"),
		},
	];
	// Action buttons
	const classActionButtons: ActionButton<FIBOClass>[] = [
		{
			label: "Xem",
			icon: <Eye size={16} />,
			onClick: (cls) => {
				setSelectedClass(cls);
				setIsViewClassModalOpen(true);
			},
			variant: "ghost",
		},
		{
			label: "Sửa",
			icon: <Edit size={16} />,
			onClick: (cls) => {
				setSelectedClass(cls);
				setIsEditClassModalOpen(true);
			},
			variant: "ghost",
		},
		{
			label: "URI",
			icon: <ExternalLink size={16} />,
			onClick: (cls) => {
				window.open(cls.uri, "_blank");
			},
			variant: "ghost",
		},
		{
			label: "Xóa",
			icon: <Trash2 size={16} />,
			onClick: (row) => {
				deleteClass({
					id: String(row.id) 
				});
			},
			variant: "ghost",
			className: "text-red-600 hover:text-red-800",
		},
	];
	return (
		<>
			<DataTable
				data={classes}
				columns={classColumns}
				actionsOptions={{
					show: true,
					actions: classActionButtons,
					showInDropdown: true,
					dropdownLabel: "Actions",
				}}
				showGlobalFilter={false}
				showColumnFilters={true}
				showPagination={true}
			/>
			<EditFiboClassDialog
				isEditClassModalOpen={isEditClassModalOpen}
				setIsEditClassModalOpen={setIsEditClassModalOpen}
				getClassById={getClassById}
				fiboClasses={classes}
				selectedClass={selectedClass}
			/>
			<ViewFiboClassDialog
				isViewClassModalOpen={isViewClassModalOpen}
				setIsViewClassModalOpen={setIsViewClassModalOpen}
				selectedClass={selectedClass}
				getClassById={getClassById}
			/>
		</>
	);
}
