import type { SimpleColumnDef } from "@/components";
import {
	useCreateEntity,
	useEntityTypes,
	useKGEntitiesSearch,
} from "@vbkg/api-client";
import { CreateEntitySchema } from "@vbkg/schemas";
import type { Entity } from "@vbkg/types";
import {
	AppForm,
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	DataTable,
	Dialog,
	Input,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Switch,
} from "@/components";
import {
	CheckCircle,
	Circle,
	Clock,
	Edit3,
	ExternalLink,
	Eye,
	Plus,
	Search,
	Trash2,
} from "lucide-react";
import { useState } from "react";

type TValue = string | number | boolean | undefined;

export default function KnowledgeGraphEntities() {
	const [searchQuery, setSearchQuery] = useState("");
	const [selectedType, setSelectedType] = useState("all");
	const [showCreateDialog, setShowCreateDialog] = useState(false);
	const [confidenceThreshold, setConfidenceThreshold] = useState<number>();
	const [semanticSearchEnabled, setSemanticSearchEnabled] = useState(false);
	const [selectedEntity, setSelectedEntity] = useState<Entity | undefined>(
		undefined,
	);
	const { data: entityTypes } = useEntityTypes({});
	const [showDetailsDialog, setShowDetailsDialog] = useState(false);

	const { mutate: createKGEntity } = useCreateEntity({
		onSuccess: () => {
			setShowCreateDialog(false);
		},
		onError: (error) => {
			console.error("Failed to create entity:", error);
		},
	});

	const { entities } =
		useKGEntitiesSearch({
			limit: 100000,
		}).data || {};

	const entityColumns: SimpleColumnDef<Entity & {relationship_count: number}, TValue>[] = [
		{
			header: "Entity",
			accessorKey: "entity_text" as const,
			cell: (entity) => (
				<div>
					<div className="font-medium">{entity?.entity_text}</div>
					<Badge variant="outline" className="mt-1">
						{entity?.entity_type}
					</Badge>
				</div>
			),
		},
		{
			header: "Properties",
			cell: (entity) => (
				<div className="space-y-1 max-w-xs line-clamp-2">
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
			header: "Confidence",
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
			header: "Status",
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
			header: "Relations",
			cell: (entity) => (
				<span className="text-muted-foreground">
					{entity?.relationship_count}
				</span>
			),
		},
		{
			header: "Actions",
			cell: (entity) => (
				<div className="flex gap-1">
					<Button
						size="sm"
						onClick={() => {
							setSelectedEntity(entity);
							setShowDetailsDialog(true);
						}}
					>
						<Eye size={16} />
					</Button>
					<Button size="sm">
						<Edit3 size={16} />
					</Button>
					<Button size="sm">
						<Trash2 size={16} />
					</Button>
				</div>
			),
		},
	];

	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div>
					<h1 className="text-3xl font-bold">🏢 Entities Management</h1>
					<p className="text-muted-foreground mt-2">
						Manage all entities in your knowledge graph
					</p>
				</div>
			</div>

			{/* Search and Filters */}
			<Card>
				<CardContent className="p-6">
					<div className="flex flex-col sm:flex-row gap-4">
						<div className="flex-1">
							<div className="relative">
								<Search
									className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
									size={16}
								/>
								<Input
									placeholder="Search entities by name, type, or properties..."
									value={searchQuery}
									onChange={(e) => setSearchQuery(e.target.value)}
									className="pl-10"
								/>
							</div>
						</div>
						<div className="flex items-center gap-2">
							<Switch
								id="semantic-search"
								checked={semanticSearchEnabled}
								onCheckedChange={(val) => setSemanticSearchEnabled(val)}
							/>
							<label htmlFor="semantic-search" className="text-sm">
								Semantic Search
							</label>
						</div>
						<Input
							placeholder="Confidence threshold..."
							value={confidenceThreshold}
							className="w-48"
							onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
						/>
						<Select value={selectedType} onValueChange={setSelectedType}>
							<SelectTrigger className="w-[180px]">
								<SelectValue placeholder="Entity Type" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="all">All Types</SelectItem>
								{entityTypes?.data?.map((type) => (
									<SelectItem key={type.id} value={String(type.id)}>
										<Circle size={16} className="mr-2" color={type.color} />
										{type.display_name}
									</SelectItem>
								))}
								<SelectItem value="custom">Custom Types</SelectItem>
							</SelectContent>
						</Select>
					</div>
				</CardContent>
			</Card>

			{/* Entities Table */}
			<Card>
				<CardHeader>
					<div className="flex justify-between items-center">
						<div>
							<CardTitle>
								Entities ({entities ? entities?.length : 0})
							</CardTitle>
							<CardDescription>
								Complete list of knowledge graph entities
							</CardDescription>
						</div>
						<div className="flex gap-2">
							<Button onClick={() => setShowCreateDialog(true)}>
								<Plus size={16} className="mr-2" />
								Add Entity
							</Button>
						</div>
					</div>
				</CardHeader>
				<CardContent>
					<DataTable data={entities} columns={entityColumns} />
				</CardContent>
			</Card>

			{/* Create Entity Dialog */}
			<Dialog
				title="Create New Entity"
				description="Add a new entity to the knowledge graph"
				open={showCreateDialog}
				size="2xl"
				onOpenChange={setShowCreateDialog}
			>
				<AppForm
					schema={CreateEntitySchema}
					onSubmit={() => {
						createKGEntity({
							entity_text: "New Entity",
							entity_type: "ORGANIZATION",
							properties: {},
							is_verified: false,
							confidence: 0.8,
						});
					}}
					fields={[
						{
							name: "entity_text",
							label: "Entity Text",
							type: "text",
							required: true,
						},
						{
							name: "entity_type",
							label: "Entity Type",
							type: "select",
							options: [
								{ value: "ORGANIZATION", label: "Organization" },
								{ value: "PERSON", label: "Person" },
								{ value: "LOCATION", label: "Location" },
								{ value: "PRODUCT", label: "Product" },
								{ value: "CONCEPT", label: "Concept" },
							],
							required: true,
						},
						{
							name: "properties",
							label: "Properties (JSON)",
							type: "textarea",
							placeholder: '{"industry": "Technology", "founded": "1976"}',
						},
						{
							name: "is_verified",
							label: "Mark as verified",
							type: "switch",
						},
					]}
				/>
			</Dialog>

			{/* Entity Details Dialog */}
			<Dialog
				title="Entity Details"
				description="Detailed information about the selected entity"
				open={showDetailsDialog}
				size="2xl"
				onOpenChange={setShowDetailsDialog}
			>
				{selectedEntity && (
					<div className="space-y-6">
						{/* Basic Info */}
						<div className="grid grid-cols-2 gap-4">
							<div>
								<span className="text-sm font-medium text-muted-foreground">
									Entity Text
								</span>
								<p className="font-medium">{selectedEntity.entity_text}</p>
							</div>
							<div>
								<span className="text-sm font-medium text-muted-foreground">
									Entity Type
								</span>
								<Badge variant="outline" className="mt-1">
									{selectedEntity.entity_type}
								</Badge>
							</div>
							<div>
								<span className="text-sm font-medium text-muted-foreground">
									Confidence
								</span>
								<div className="flex items-center gap-2 mt-1">
									<div className="w-24 bg-muted rounded-full h-2">
										<div
											className="bg-blue-500 h-2 rounded-full"
											style={{ width: `${Number(selectedEntity?.confidence) * 100}%` }}
										/>
									</div>
									<span className="text-sm">
										{Math.round(Number(selectedEntity.confidence) * 100)}%
									</span>
								</div>
							</div>
							<div>
								{/* biome-ignore lint/a11y/noLabelWithoutControl: <explanation> */}
								<label className="text-sm font-medium text-muted-foreground">
									Status
								</label>
								<div className="mt-1">
									{selectedEntity.is_verified ? (
										<Badge variant="default" className="bg-green-500">
											Verified
										</Badge>
									) : (
										<Badge variant="secondary">Pending</Badge>
									)}
								</div>
							</div>
						</div>

						{/* Properties */}
						<div>
							{/* biome-ignore lint/a11y/noLabelWithoutControl: <explanation> */}
							<label className="text-sm font-medium text-muted-foreground">
								Properties
							</label>
							<div className="mt-2 p-4 bg-muted rounded-lg">
								<pre className="text-sm">
									{JSON.stringify(selectedEntity.properties, null, 2)}
								</pre>
							</div>
						</div>

						{/* Actions */}
						<div className="flex justify-end gap-2">
							<Button>
								<Edit3 size={16} className="mr-2" />
								Edit
							</Button>
							<Button>
								<ExternalLink size={16} className="mr-2" />
								View in Graph
							</Button>
							<Button>
								<Trash2 size={16} className="mr-2" />
								Delete
							</Button>
						</div>
					</div>
				)}
			</Dialog>
		</div>
	);
}
