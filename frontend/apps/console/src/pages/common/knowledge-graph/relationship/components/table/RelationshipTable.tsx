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
import { Relationship } from "@vbkg/types";
import {
	ArrowRight,
	CheckCircle,
	Clock,
	Edit3,
	Eye,
	Plus,
	Trash2,
} from "lucide-react";
import { useState } from "react";
import CreateRelationshipDialog from "../dialogs/CreateRelationshipDialog";
import ViewRelationshipDialog from "../dialogs/ViewRelationshipDialog";

interface RelationshipTableProps {
	relationships?: Relationship[];
}

type TValue = string | number | boolean | undefined;

export default function RelationshipTable({
	relationships,
}: RelationshipTableProps) {
	const [showCreateDialog, setShowCreateDialog] = useState(false);
	const [showDetailsDialog, setShowDetailsDialog] = useState(false);
	const [mode, setMode] = useState<"create" | "edit">("create");
	const [selectedRelationship, setSelectedRelationship] = useState<
		Relationship | undefined
	>();
	const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

	const relationshipColumns: SimpleColumnDef<Relationship, TValue>[] = [
		{
			header: "Loại quan hệ",
			enableFiltering: true,
			cell: (rel) => (
				<Badge variant="outline" className="font-medium uppercase">
					{rel?.relationship_type}
				</Badge>
			),
		},
		{
			header: "Nguồn → Đích",
			cell: (rel: any) => (
				<div className="space-y-1">
					<div className="flex items-center gap-2">
						<div className="font-medium">{rel.source_entity.entity_text}</div>
						<ArrowRight size={14} className="text-muted-foreground" />
						<div className="font-medium">{rel.target_entity.entity_text}</div>
					</div>
					<div className="flex items-center gap-2 text-xs text-muted-foreground">
						<Badge variant="secondary" className="text-xs">
							{rel.source_entity.entity_type}
						</Badge>
						<ArrowRight size={10} />
						<Badge variant="secondary" className="text-xs">
							{rel.target_entity.entity_type}
						</Badge>
					</div>
				</div>
			),
		},
		{
			header: "Thuộc tính",
			cell: (rel: any) => (
				<div className="space-y-1 max-w-xs">
					{Object.entries(rel.properties || {})
						.slice(0, 2)
						.map(([key, value]) => (
							<div key={key} className="text-sm">
								<span className="text-muted-foreground">{key}:</span>{" "}
								{String(value)}
							</div>
						))}
					{Object.keys(rel.properties || {}).length > 2 && (
						<span className="text-xs text-muted-foreground">
							+{Object.keys(rel.properties || {}).length - 2} more
						</span>
					)}
				</div>
			),
		},
		{
			header: "Độ tin cậy",
			cell: (rel: any) => (
				<div className="flex items-center gap-2">
					<div className="w-16 bg-muted rounded-full h-2">
						<div
							className="bg-green-500 h-2 rounded-full"
							style={{ width: `${rel.confidence * 100}%` }}
						/>
					</div>
					<span className="text-sm">{Math.round(rel.confidence * 100)}%</span>
				</div>
			),
		},
		{
			header: "Trạng thái",
			enableFiltering: true,
			cell: (rel: any) =>
				rel.is_verified ? (
					<Badge variant="default" className="bg-green-500">
						<CheckCircle size={12} className="mr-1" />
						Verified
					</Badge>
				) : (
					<Badge variant="secondary">
						<Clock size={12} className="mr-1" />
						Pending
					</Badge>
				),
		},
		{
			header: "Actions",
			cell: (rel) => (
				<div className="flex gap-1">
					<Button
						variant={"outline"}
						size="sm"
						onClick={() => {
							setSelectedRelationship(rel);
							setShowDetailsDialog(true);
						}}
					>
						<Eye size={16} />
					</Button>
					<Button
						variant={"outline"}
						onClick={() => {
							setSelectedRelationship(rel);
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
							setSelectedRelationship(rel);
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
							<CardTitle>Mối quan hệ ({relationships?.length})</CardTitle>
							<CardDescription>
								Danh sách các mối quan hệ trong Knowledge Graph của bạn. Bạn có
								thể tìm kiếm, xem chi tiết, chỉnh sửa hoặc xóa các mối quan hệ
								này.
							</CardDescription>
						</div>
						<div className="flex gap-2">
							<Button onClick={() => setShowCreateDialog(true)}>
								<Plus size={16} className="mr-2" />
								Thêm mối quan hệ
							</Button>
						</div>
					</div>
				</CardHeader>
				<CardContent>
					<DataTable data={relationships} columns={relationshipColumns} />
				</CardContent>
			</Card>

			<CreateRelationshipDialog
				showCreateDialog={showCreateDialog}
				setShowCreateDialog={() => setShowCreateDialog(false)}
				selectedRelationship={selectedRelationship}
				mode={mode}
			/>
			<ViewRelationshipDialog
				showDetailsDialog={showDetailsDialog}
				setShowDetailsDialog={setShowDetailsDialog}
				selectedRelationship={selectedRelationship}
			/>
			<Dialog
				open={showDeleteConfirmation}
				onOpenChange={setShowDeleteConfirmation}
				showFooter
				title="Delete Entity"
				size="sm"
				onPrimaryAction={async () => {
					if (!selectedRelationship) {
						console.error("No entity selected for deletion");
						return;
					}

					setShowDeleteConfirmation(false);
				}}
				onClose={() => setShowDeleteConfirmation(false)}
			>
				<p className="text-sm text-muted-foreground">
					Deleting this relationship will remove it from the knowledge graph.
				</p>
				<p className="text-sm text-red-500 mt-2">
					Are you sure you want to delete{" "}
					<span className="font-medium">
						{selectedRelationship?.relationship_type}
					</span>
					?
				</p>
			</Dialog>
		</>
	);
}
