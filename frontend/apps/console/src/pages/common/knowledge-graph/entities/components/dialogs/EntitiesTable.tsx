import {
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	DataTable,
	Dialog,
	SimpleColumnDef,
} from "@/components";
import { Entity } from "@vbkg/types";
import { CheckCircle, Clock, Edit3, Eye, Plus, Trash2 } from "lucide-react";
import { useDeleteEntity } from "@vbkg/api-client";
import { useState } from "react";
import ViewEntityDialog from "./ViewEntityDialog";
import CreateEntityDialog from "./CreateEntityDialog";

type TValue = string | number | boolean | undefined;

interface EntitesTableProps {
	entities: Entity[] | undefined;
}
export default function EntitiesTable({ entities }: EntitesTableProps) {
	const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
	const [showCreateDialog, setShowCreateDialog] = useState(false);
	const [showDetailsDialog, setShowDetailsDialog] = useState(false);
	const [mode, setMode] = useState<"create" | "edit">("create");
	const [selectedEntity, setSelectedEntity] = useState<Entity | undefined>();
	const { mutateAsync: deleteEntity } = useDeleteEntity({
		onSuccess: () => {
			setShowDeleteConfirmation(false);
		},
		onError: (error) => {
			console.error("Failed to delete entity:", error);
		},
	});

	const entityColumns: SimpleColumnDef<
		Entity & { relationship_count: number; similarity_score?: number },
		TValue
	>[] = [
		{
			header: "Tên thực thể",
			accessorKey: "entity_text" as const,
			cell: (entity) => (
				<div>
					<div className="font-medium flex items-center gap-2">
						{entity?.entity_text}
						{entity?.similarity_score && (
							<Badge
								variant="secondary"
								className="text-xs text-green-700 font-bold"
							>
								~ {Math.round(entity.similarity_score * 100)}%
							</Badge>
						)}
					</div>
					<Badge variant="outline" className="mt-1 uppercase">
						{entity?.entity_type}
					</Badge>
				</div>
			),
		},
		{
			header: "Thuộc tính",
			id: "properties",
			cell: (entity) => (
				<div className="space-y-1 max-w-xs">
					{Object.entries(entity?.properties || {})
						.slice(0, 2)
						.map(([key, value]) => (
							<div key={key} className="text-sm">
								<span className="text-muted-foreground">{key}:</span>{" "}
								{String(value)}
							</div>
						))}
					{Object.keys(entity?.properties || {}).length > 2 && (
						<span className="text-xs text-muted-foreground">
							+{Object.keys(entity?.properties || {}).length - 2} more
						</span>
					)}
				</div>
			),
		},
		{
			header: "Độ tin cậy",
			enableSorting: true,
			id: "confidence",
			cell: (entity) => (
				<div className="flex items-center gap-2">
					<div className="w-16 bg-muted rounded-full h-2">
						<div
							className="bg-blue-500 h-2 rounded-full"
							style={{ width: `${Number(entity?.confidence) * 100}%` }}
						/>
					</div>
					<span className="text-sm">
						{Math.round(Number(entity?.confidence) * 100)}%
					</span>
				</div>
			),
		},
		{
			header: "Trạng thái",
			id: "status",
			cell: (entity) => (
				<div className="flex items-center gap-2">
					{entity?.is_verified ? (
						<Badge variant="default" className="bg-green-500">
							<CheckCircle size={12} className="mr-1" />
							Verified
						</Badge>
					) : (
						<Badge variant="secondary">
							<Clock size={12} className="mr-1" />
							Pending
						</Badge>
					)}
				</div>
			),
		},
		{
			header: "Quan hệ",
			id: "relationship_count",
			cell: (entity) => (
				<span className="text-muted-foreground">
					{entity?.relationship_count}
				</span>
			),
		},
		{
			header: "Hành động",
			id: "actions",
			cell: (entity) => (
				<div className="flex gap-1">
					<Button
						size="sm"
						variant={"outline"}
						onClick={() => {
							setSelectedEntity(entity);
							setShowDetailsDialog(true);
						}}
					>
						<Eye size={16} />
					</Button>
					<Button
						variant={"outline"}
						onClick={() => {
							setSelectedEntity(entity);
							setShowCreateDialog(true);
							setMode("edit");
						}}
						size="sm"
					>
						<Edit3 size={16} />
					</Button>
					<Button
						variant={"outline"}
						onClick={() => {
							setSelectedEntity(entity);
							setShowDeleteConfirmation(true);
						}}
						size="sm"
					>
						<Trash2 size={16} />
					</Button>
				</div>
			),
		},
	];
	return (
		<>
			<Card>
				<CardHeader>
					<div className="flex justify-between items-center">
						<div>
							<CardTitle>
								Thực thể ({entities ? entities?.length : 0})
							</CardTitle>
							<CardDescription>
								Danh sách các thực thể trong Knowledge Graph của bạn. Bạn có thể
								tìm kiếm, xem chi tiết, chỉnh sửa hoặc xóa các thực thể này.
							</CardDescription>
						</div>
						<div className="flex gap-2">
							<Button
								onClick={() => {
									setShowCreateDialog(true);
									setMode("create");
								}}
							>
								<Plus size={16} className="mr-2" />
								Thêm thực thể
							</Button>
						</div>
					</div>
				</CardHeader>
				<CardContent>
					<DataTable data={entities} columns={entityColumns as any} />
				</CardContent>
			</Card>
			<Dialog
				open={showDeleteConfirmation}
				onOpenChange={setShowDeleteConfirmation}
				showFooter
				title="Delete Entity"
				size="sm"
				onPrimaryAction={async () => {
					if (!selectedEntity) {
						console.error("No entity selected for deletion");
						return;
					}
					await deleteEntity({
						id: selectedEntity?.id || "",
					});

					setShowDeleteConfirmation(false);
				}}
				onClose={() => setShowDeleteConfirmation(false)}
			>
				<p className="text-sm text-muted-foreground">
					Deleting this entity will remove it from the knowledge graph and all
					its associated relationships.
				</p>
				<p className="text-sm text-red-500 mt-2">
					Are you sure you want to delete{" "}
					<span className="font-medium">{selectedEntity?.entity_text}</span>?
				</p>
			</Dialog>
			{/* Create Entity Dialog */}
			<CreateEntityDialog
				showCreateDialog={showCreateDialog}
				setShowCreateDialog={setShowCreateDialog}
				selectedEntity={selectedEntity}
				mode={mode}
			/>

			{/* Entity Details Dialog */}
			<ViewEntityDialog
				showDetailsDialog={showDetailsDialog}
				setShowDetailsDialog={setShowDetailsDialog}
				selectedEntity={selectedEntity || null}
			/>
		</>
	);
}
