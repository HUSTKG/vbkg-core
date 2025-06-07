import {
	ActionButton,
	Badge,
	Button,
	Card,
	CardContent,
	CardHeader,
	CardTitle,
	DataTable,
	Dialog,
	Progress,
	SimpleColumnDef,
	StatisticCard,
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
} from "@/components";
import {
	useEntityMappings,
	useEntityTypes,
	useRelationshipMappings,
	useRelationshipTypes,
} from "@vbkg/api-client";
import { EntityMapping, RelationshipMapping } from "@vbkg/types";
import {
	AlertTriangle,
	CheckCircle,
	Database,
	Eye,
	Lightbulb,
	Link2,
	Plus,
	RefreshCw,
	Trash2,
	Upload,
	X,
} from "lucide-react";
import { useState } from "react";
import EntityMappingWizard from "./components/EntityMappingWizard";
import RelationshipMappingWizard from "./components/RelationshipMappingWizard";

const FIBOMappingManagementPage = () => {
	const {
		data: entityMappingResponse,
		isLoading: entityMappingsLoading,
		error: entityMappingsError,
		refetch: refetchEntityMappings,
	} = useEntityMappings({ limit: 200 });

	const {
		data: relationshipMappingResponse,
		isLoading: relationshipMappingsLoading,
		error: relationshipMappingsError,
		refetch: refetchRelationshipMappings,
	} = useRelationshipMappings({ limit: 200 });

	// Local state
	const [selectedMapping, setSelectedMapping] = useState<
		EntityMapping | RelationshipMapping | null
	>(null);
	const [isEntityMappingWizardOpen, setIsEntityMappingWizardOpen] =
		useState(false);
	const [isRelationshipMappingWizardOpen, setIsRelationshipMappingWizardOpen] =
		useState(false);
	const [isViewModalOpen, setIsViewModalOpen] = useState(false);

	const { data: entityTypesResponse } = useEntityTypes({});
	const entityTypes = entityTypesResponse?.data || [];

	const { data: relationshipTypesResponse } = useRelationshipTypes({});
	const relationshipTypes = relationshipTypesResponse?.data || [];

	const entityMappings = entityMappingResponse?.data || [];
	const relationshipMappings = relationshipMappingResponse?.data || [];

	const relationshipMappingColumns: SimpleColumnDef<
		RelationshipMapping,
		any
	>[] = [
		{
			accessorKey: "relationship_type",
			header: "Relationship Type",
			cell: (row) => {
				const relationshipType = relationshipTypes.find(
					(et) => et.name === row?.relationship_type,
				);
				return (
					<div className="flex items-center space-x-2">
						<div
							className="w-3 h-3 rounded-full"
							style={{ backgroundColor: relationshipType?.color || "#6366F1" }}
						/>
						<span className="font-medium">
							{relationshipType?.display_name || row?.relationship_type}
						</span>
					</div>
				);
			},
		},
		{
			id: "fibo_class",
			header: "FIBO Class",
			cell: (row) => (
				<div>
					<div className="font-medium text-sm">
						{row?.fibo_property?.label || "Unknown"}
					</div>
					<div className="text-xs text-gray-500 truncate max-w-xs">
						{row?.fibo_property_uri}
					</div>
				</div>
			),
		},
		{
			accessorKey: "confidence",
			header: "Confidence",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<Progress value={(row?.confidence || 0) * 100} className="w-16 h-2" />
					<span className="text-sm">
						{((row?.confidence || 0) * 100).toFixed(0)}%
					</span>
				</div>
			),
		},
		{
			accessorKey: "mapping_status",
			header: "Status",
			cell: (row) => {
				const statusColors = {
					pending: "bg-yellow-100 text-yellow-800",
					mapped: "bg-green-100 text-green-800",
					rejected: "bg-red-100 text-red-800",
					needs_review: "bg-orange-100 text-orange-800",
				};
				return (
					<Badge className={statusColors[row?.mapping_status || "pending"]}>
						{row?.mapping_status || "pending"}
					</Badge>
				);
			},
		},
		{
			accessorKey: "is_verified",
			header: "Verified",
			cell: (row) =>
				row?.is_verified ? (
					<CheckCircle size={16} className="text-green-500" />
				) : (
					<X size={16} className="text-gray-400" />
				),
		},
	];
	// Table columns
	const entityMappingColumns: SimpleColumnDef<EntityMapping, any>[] = [
		{
			accessorKey: "entity_type",
			header: "Entity Type",
			cell: (row) => {
				const entityType = entityTypes.find(
					(et) => et.name === row?.entity_type,
				);
				return (
					<div className="flex items-center space-x-2">
						<div
							className="w-3 h-3 rounded-full"
							style={{ backgroundColor: entityType?.color || "#6366F1" }}
						/>
						<span className="font-medium">
							{entityType?.display_name || row?.entity_type}
						</span>
					</div>
				);
			},
		},
		{
			id: "fibo_class",
			header: "FIBO Class",
			cell: (row) => (
				<div>
					<div className="text-xs text-gray-500 truncate max-w-xs">
						{row?.fibo_class_uri}
					</div>
				</div>
			),
		},
		{
			accessorKey: "confidence",
			header: "Confidence",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<Progress value={(row?.confidence || 0) * 100} className="w-16 h-2" />
					<span className="text-sm">
						{((row?.confidence || 0) * 100).toFixed(0)}%
					</span>
				</div>
			),
		},
		{
			accessorKey: "mapping_status",
			header: "Status",
			cell: (row) => {
				const statusColors = {
					pending: "bg-yellow-100 text-yellow-800",
					mapped: "bg-green-100 text-green-800",
					rejected: "bg-red-100 text-red-800",
					needs_review: "bg-orange-100 text-orange-800",
				};
				return (
					<Badge className={statusColors[row?.mapping_status || "pending"]}>
						{row?.mapping_status || "pending"}
					</Badge>
				);
			},
		},
		{
			accessorKey: "is_verified",
			header: "Verified",
			cell: (row) =>
				row?.is_verified ? (
					<CheckCircle size={16} className="text-green-500" />
				) : (
					<X size={16} className="text-gray-400" />
				),
		},
	];
	const propertyActionButtons: ActionButton<RelationshipMapping>[] = [
		{
			label: "View",
			icon: <Eye size={16} />,
			onClick: (mapping) => {
				setSelectedMapping(mapping);
				setIsViewModalOpen(true);
			},
			variant: "ghost",
		},
		{
			label: "Delete",
			icon: <Trash2 size={16} />,
			onClick: () => {
				if (confirm("Are you sure you want to delete this mapping?")) {
					// Handle delete
				}
			},
			variant: "ghost",
			className: "text-red-600 hover:text-red-800",
		},
	];

	// Action buttons
	const actionButtons: ActionButton<EntityMapping>[] = [
		{
			label: "View",
			icon: <Eye size={16} />,
			onClick: (mapping) => {
				setSelectedMapping(mapping);
				setIsViewModalOpen(true);
			},
			variant: "ghost",
		},
		{
			label: "Delete",
			icon: <Trash2 size={16} />,
			onClick: () => {
				if (confirm("Are you sure you want to delete this mapping?")) {
					// Handle delete
				}
			},
			variant: "ghost",
			className: "text-red-600 hover:text-red-800",
		},
	];

	// Statistics
	const stats = {
		totalEntityMappings: entityMappings.length,
		verifiedEntityMappings: entityMappings.filter((m) => m.is_verified).length,
		totalRelationshipMappings: relationshipMappings.length,
		verifiedRelationshipMappings: relationshipMappings.filter(
			(m) => m.is_verified,
		).length,
		pendingMappings: [...entityMappings, ...relationshipMappings].filter(
			(m) => m.mapping_status === "pending",
		).length,
		autoMappings: [...entityMappings, ...relationshipMappings].filter(
			(m) => m.auto_mapped,
		).length,
	};

	// Loading and error states
	if (entityMappingsLoading || relationshipMappingsLoading) {
		return (
			<div className="p-6 flex items-center justify-center">
				<RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
				<span className="ml-2">Loading mappings...</span>
			</div>
		);
	}

	if (entityMappingsError || relationshipMappingsError) {
		return (
			<div className="p-6 flex items-center justify-center text-red-600">
				<AlertTriangle className="h-6 w-6 mr-2" />
				<span>Error loading mappings. Please try again.</span>
			</div>
		);
	}

	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div>
					<h1 className="text-2xl font-bold text-gray-900">
						FIBO Mapping Management
					</h1>
					<p className="text-gray-600 mt-1">
						Create and manage mappings between your types and FIBO ontology with
						AI-powered suggestions
					</p>
				</div>
				<div className="flex space-x-2">
					<Button
						variant="outline"
						onClick={() => setIsEntityMappingWizardOpen(true)}
					>
						<Plus size={16} className="mr-2" />
						Add Entity Mapping
					</Button>
					<Button
						variant="outline"
						onClick={() => setIsRelationshipMappingWizardOpen(true)}
					>
						<Plus size={16} className="mr-2" />
						Add Relationship Mapping
					</Button>
				</div>
			</div>

			{/* Statistics */}
			<div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6 gap-4">
				<StatisticCard
					title="Entity Mappings"
					value={stats.totalEntityMappings}
					icon={<Database size={20} />}
					color="blue"
				/>
				<StatisticCard
					title="Verified Entities"
					value={stats.verifiedEntityMappings}
					icon={<CheckCircle size={20} />}
					color="green"
				/>
				<StatisticCard
					title="Relationship Mappings"
					value={stats.totalRelationshipMappings}
					icon={<Link2 size={20} />}
					color="purple"
				/>
				<StatisticCard
					title="Verified Relationships"
					value={stats.verifiedRelationshipMappings}
					icon={<CheckCircle size={20} />}
					color="green"
				/>
				<StatisticCard
					title="Pending Review"
					value={stats.pendingMappings}
					icon={<X size={20} />}
					color="yellow"
				/>
				<StatisticCard
					title="Auto Mapped"
					value={stats.autoMappings}
					icon={<Upload size={20} />}
					color="indigo"
				/>
			</div>

			{/* Main Content */}
			<Tabs defaultValue="entity-mappings" className="space-y-4">
				<TabsList>
					<TabsTrigger value="entity-mappings">Entity Mappings</TabsTrigger>
					<TabsTrigger value="relationship-mappings">
						Relationship Mappings
					</TabsTrigger>
					<TabsTrigger value="bulk-operations">Bulk Operations</TabsTrigger>
				</TabsList>

				<TabsContent value="entity-mappings" className="space-y-4">
					<Card>
						<CardHeader>
							<CardTitle>
								Entity Type Mappings ({entityMappings.length})
							</CardTitle>
						</CardHeader>
						<CardContent>
							<DataTable
								data={entityMappings}
								columns={entityMappingColumns}
								actionsOptions={{
									show: true,
									actions: actionButtons,
									showInDropdown: true,
									dropdownLabel: "Actions",
								}}
								showGlobalFilter={true}
								showColumnFilters={true}
								showPagination={true}
							/>
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="relationship-mappings" className="space-y-4">
					<Card>
						<CardHeader>
							<CardTitle>
								Relationship Type Mappings ({relationshipMappings.length})
							</CardTitle>
						</CardHeader>
						<CardContent>
							<p className="text-gray-500">
								<DataTable<RelationshipMapping, any>
									data={relationshipMappings}
									columns={relationshipMappingColumns}
									actionsOptions={{
										show: true,
										actions: propertyActionButtons,
										showInDropdown: true,
										dropdownLabel: "Actions",
									}}
									showGlobalFilter={true}
									showColumnFilters={true}
									showPagination={true}
								/>
							</p>
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="bulk-operations" className="space-y-4">
					<Card>
						<CardHeader>
							<CardTitle>Bulk Mapping Operations</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
								<div className="space-y-4">
									<h3 className="font-medium">Auto-Mapping</h3>
									<p className="text-sm text-gray-600">
										Automatically create mappings for unmapped entity and
										relationship types using AI suggestions.
									</p>
									<Button className="w-full">
										<Lightbulb size={16} className="mr-2" />
										Run Auto-Mapping
									</Button>
								</div>

								<div className="space-y-4">
									<h3 className="font-medium">Bulk Verification</h3>
									<p className="text-sm text-gray-600">
										Verify all pending mappings with high confidence scores.
									</p>
									<Button className="w-full">
										<CheckCircle size={16} className="mr-2" />
										Bulk Verify (80%+ confidence)
									</Button>
								</div>
							</div>
						</CardContent>
					</Card>
				</TabsContent>
			</Tabs>

			{/* Modals */}
			<Dialog
				title="View Mapping Details"
				description="Detailed information about the selected mapping"
				open={isViewModalOpen}
				onOpenChange={setIsViewModalOpen}
			>
				{selectedMapping && (
					<div className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div>
								<label className="text-sm font-medium text-gray-500">
									{"entity_type" in selectedMapping
										? "Entity Type"
										: "Relationship Type"}
								</label>
								<p className="mt-1 font-medium">
									{"entity_type" in selectedMapping
										? selectedMapping.entity_type
										: selectedMapping.relationship_type}
								</p>
							</div>
							<div>
								<label className="text-sm font-medium text-gray-500">
									{"entity_type" in selectedMapping
										? "FIBO Class"
										: "FIBO Property"}
								</label>
								<p className="mt-1">
									{"entity_type" in selectedMapping
										? selectedMapping.fibo_class_uri?.label || "Unknown"
										: selectedMapping.fibo_property?.label || "Unknown"}
								</p>
							</div>
						</div>
					</div>
				)}
			</Dialog>

			<Dialog
				title="Create Entity Mapping"
				size="2xl"
				description="Map your entity types to FIBO classes"
				open={isEntityMappingWizardOpen}
				onOpenChange={setIsEntityMappingWizardOpen}
			>
				<EntityMappingWizard
					setIsEntityMappingWizardOpen={setIsEntityMappingWizardOpen}
					refetchEntityMappings={refetchEntityMappings}
				/>
			</Dialog>

			<Dialog
				title="Create Relationship Mapping"
				size="2xl"
				description="Map your relationship types to FIBO properties"
				open={isRelationshipMappingWizardOpen}
				onOpenChange={setIsRelationshipMappingWizardOpen}
			>
				<RelationshipMappingWizard
					setIsRelationshipMappingWizardOpen={
						setIsRelationshipMappingWizardOpen
					}
					refetchRelationshipMappings={refetchRelationshipMappings}
				/>
			</Dialog>
		</div>
	);
};

export default FIBOMappingManagementPage;
