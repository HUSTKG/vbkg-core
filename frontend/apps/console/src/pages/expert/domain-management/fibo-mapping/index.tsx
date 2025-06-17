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
	toast,
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components";
import {
	useEntityMappings,
	useOntologyClasses,
	useOntologyProperties,
	useRelationshipMappings,
	useVerifyEntityMapping,
	useVerifyRelationshipMapping,
	useDeleteEntityMapping,
	useDeleteRelationshipMapping,
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
	Shield,
	ShieldCheck,
	Users,
	Clock,
	AlertCircle,
	TrendingUp,
	Target,
	Zap,
	ThumbsUp,
	ThumbsDown,
	Info,
	ExternalLink,
} from "lucide-react";
import { useState } from "react";

const OntologyMappingManagementPage = () => {
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

	// Mutation hooks for verify operations
	const verifyEntityMappingMutation = useVerifyEntityMapping({
		onSuccess: () => {
			refetchEntityMappings();
			toast.success("Entity mapping đã được verify thành công!");
		},
		onError: (error) => {
			toast.error(`Lỗi khi verify entity mapping: ${error.message}`);
		},
	});

	const verifyRelationshipMappingMutation = useVerifyRelationshipMapping({
		onSuccess: () => {
			refetchRelationshipMappings();
			toast.success("Relationship mapping đã được verify thành công!");
		},
		onError: (error) => {
			toast.error(`Lỗi khi verify relationship mapping: ${error.message}`);
		},
	});

	// Delete mutations
	const deleteEntityMappingMutation = useDeleteEntityMapping({
		onSuccess: () => {
			refetchEntityMappings();
			toast.success("Entity mapping đã được xóa thành công!");
		},
		onError: (error) => {
			toast.error(`Lỗi khi xóa entity mapping: ${error.message}`);
		},
	});

	const deleteRelationshipMappingMutation = useDeleteRelationshipMapping({
		onSuccess: () => {
			refetchRelationshipMappings();
			toast.success("Relationship mapping đã được xóa thành công!");
		},
		onError: (error) => {
			toast.error(`Lỗi khi xóa relationship mapping: ${error.message}`);
		},
	});

	// Local state
	const [selectedMapping, setSelectedMapping] = useState<
		EntityMapping | RelationshipMapping | null
	>(null);
	const [isEntityMappingWizardOpen, setIsEntityMappingWizardOpen] =
		useState(false);
	const [isRelationshipMappingWizardOpen, setIsRelationshipMappingWizardOpen] =
		useState(false);
	const [isViewModalOpen, setIsViewModalOpen] = useState(false);
	const [selectedMappings, setSelectedMappings] = useState<string[]>([]);
	const [isBulkVerifying, setIsBulkVerifying] = useState(false);
	const [showSuggestions, setShowSuggestions] = useState(false);
	const [selectedSuggestion, setSelectedSuggestion] = useState<any>(null);

	const { data: entityTypesResponse } = useOntologyProperties({});
	const entityTypes = entityTypesResponse?.data || [];

	const { data: relationshipTypesResponse } = useOntologyClasses({});
	const relationshipTypes = relationshipTypesResponse?.data || [];

	const entityMappings = entityMappingResponse?.data || [];
	const relationshipMappings = relationshipMappingResponse?.data || [];

	// Helper function to render suggestions
	const renderSuggestions = (
		suggestions: any[],
		type: "entity" | "relationship",
	) => {
		if (!suggestions || suggestions.length === 0) {
			return (
				<div className="text-center py-4 text-gray-500 text-sm">
					<Lightbulb size={16} className="mx-auto mb-2 opacity-50" />
					Không có suggestions
				</div>
			);
		}

		return (
			<div className="space-y-3">
				{suggestions.map((suggestion, index) => (
					<div
						key={index}
						className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
					>
						<div className="flex items-start justify-between">
							<div className="flex-1">
								<div className="flex items-center space-x-2 mb-2">
									<Target size={14} className="text-blue-500" />
									<span className="font-medium text-sm">
										{type === "entity"
											? suggestion.suggested_class
											: suggestion.suggested_property}
									</span>
									<Badge
										className={
											suggestion.confidence >= 0.8
												? "bg-green-100 text-green-800"
												: suggestion.confidence >= 0.6
													? "bg-yellow-100 text-yellow-800"
													: "bg-red-100 text-red-800"
										}
									>
										{(suggestion.confidence * 100).toFixed(0)}%
									</Badge>
									{suggestion.is_new_class || suggestion.is_new_property ? (
										<Badge className="bg-purple-100 text-purple-800">
											<Plus size={10} className="mr-1" />
											New
										</Badge>
									) : null}
								</div>
								<p className="text-sm text-gray-600 mb-3">
									{suggestion.reasoning}
								</p>
								<div className="flex space-x-2">
									<Button
										size="sm"
										onClick={() =>
											applySuggestion(selectedMapping!, suggestion)
										}
										className="bg-green-600 hover:bg-green-700"
									>
										<ThumbsUp size={12} className="mr-1" />
										Áp dụng
									</Button>
									<Button
										size="sm"
										variant="outline"
										onClick={() => {
											// Handle reject suggestion
											toast.info("Suggestion đã được từ chối");
										}}
									>
										<ThumbsDown size={12} className="mr-1" />
										Từ chối
									</Button>
								</div>
							</div>
						</div>
					</div>
				))}
			</div>
		);
	};

	// Verify functions
	const handleVerifyEntityMapping = async (mapping: EntityMapping) => {
		try {
			await verifyEntityMappingMutation.mutateAsync({
				id: mapping.id,
				is_verified: true,
			});
		} catch (error) {
			console.error("Error verifying entity mapping:", error);
		}
	};

	const handleVerifyRelationshipMapping = async (
		mapping: RelationshipMapping,
	) => {
		try {
			await verifyRelationshipMappingMutation.mutateAsync({
				id: mapping.id,
				is_verified: true,
			});
		} catch (error) {
			console.error("Error verifying relationship mapping:", error);
		}
	};

	// Bulk verify function
	const handleBulkVerifyHighConfidence = async (
		confidenceThreshold: number = 0.8,
	) => {
		setIsBulkVerifying(true);
		try {
			// Verify high confidence entity mappings
			const highConfidenceEntityMappings = entityMappings.filter(
				(m) => !m.is_verified && (m.confidence || 0) >= confidenceThreshold,
			);

			const highConfidenceRelationshipMappings = relationshipMappings.filter(
				(m) => !m.is_verified && (m.confidence || 0) >= confidenceThreshold,
			);

			// Verify entity mappings
			const entityPromises = highConfidenceEntityMappings.map((mapping) =>
				verifyEntityMappingMutation.mutateAsync({
					id: mapping.id,
					is_verified: true,
				}),
			);

			// Verify relationship mappings
			const relationshipPromises = highConfidenceRelationshipMappings.map(
				(mapping) =>
					verifyRelationshipMappingMutation.mutateAsync({
						id: mapping.id,
						is_verified: true,
					}),
			);

			await Promise.all([...entityPromises, ...relationshipPromises]);

			toast.success(
				`Đã verify thành công ${entityPromises.length + relationshipPromises.length} mappings với confidence ≥ ${confidenceThreshold * 100}%`,
			);
		} catch (error) {
			toast.error("Có lỗi xảy ra trong quá trình bulk verify");
		} finally {
			setIsBulkVerifying(false);
		}
	};

	// Delete functions
	const handleDeleteEntityMapping = async (mapping: EntityMapping) => {
		if (confirm("Bạn có chắc chắn muốn xóa mapping này không?")) {
			try {
				await deleteEntityMappingMutation.mutateAsync({ id: mapping.id });
			} catch (error) {
				console.error("Error deleting entity mapping:", error);
			}
		}
	};

	const handleDeleteRelationshipMapping = async (
		mapping: RelationshipMapping,
	) => {
		if (confirm("Bạn có chắc chắn muốn xóa mapping này không?")) {
			try {
				await deleteRelationshipMappingMutation.mutateAsync({ id: mapping.id });
			} catch (error) {
				console.error("Error deleting relationship mapping:", error);
			}
		}
	};

	// Table columns for Entity Mappings
	const entityMappingColumns: SimpleColumnDef<EntityMapping, any>[] = [
		{
			accessorKey: "entity_type",
			header: "Entity Type",
			cell: (row) => {
				const entityType = entityTypes.find(
					(et) => et.label === row?.entity_type,
				);
				return (
					<div className="flex items-center space-x-2">
						<div
							className="w-3 h-3 rounded-full"
							style={{ backgroundColor: "#6366F1" }}
						/>
						<span className="font-medium">
							{entityType?.label || row?.entity_type}
						</span>
					</div>
				);
			},
		},
		{
			id: "ontology_class",
			header: "Ontology Class",
			cell: (row) => (
				<div>
					<div className="text-xs text-gray-500 truncate max-w-xs">
						{row?.ontology_property_uri || "Unknown"}
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
			accessorKey: "suggestions",
			header: "Suggestions",
			cell: (row) => {
				const suggestions = row?.suggestions || [];
				const hasSuggestions = suggestions.length > 0;
				const hasHighConfidence = suggestions.some(
					(s: any) => s.confidence >= 0.8,
				);

				return (
					<div className="flex items-center space-x-2">
						{hasSuggestions ? (
							<>
								<Badge
									className={
										hasHighConfidence
											? "bg-green-100 text-green-800"
											: "bg-yellow-100 text-yellow-800"
									}
								>
									{suggestions.length} suggestions
								</Badge>
								{hasHighConfidence && (
									<TrendingUp size={14} className="text-green-500" />
								)}
							</>
						) : (
							<span className="text-xs text-gray-400">No suggestions</span>
						)}
					</div>
				);
			},
		},
		{
			accessorKey: "is_verified",
			header: "Verified",
			cell: (row) => (
				<div className="flex items-center space-x-1">
					{row?.is_verified ? (
						<>
							<ShieldCheck size={16} className="text-green-500" />
							<span className="text-xs text-green-600">Verified</span>
						</>
					) : (
						<>
							<Shield size={16} className="text-gray-400" />
							<span className="text-xs text-gray-500">Pending</span>
						</>
					)}
				</div>
			),
		},
	];

	// Table columns for Relationship Mappings
	const relationshipMappingColumns: SimpleColumnDef<
		RelationshipMapping,
		any
	>[] = [
		{
			accessorKey: "relationship_type",
			header: "Relationship Type",
			cell: (row) => {
				const relationshipType = relationshipTypes.find(
					(et) => et.label === row?.relationship_type,
				);
				return (
					<div className="flex items-center space-x-2">
						<div
							className="w-3 h-3 rounded-full"
							style={{ backgroundColor: "#6366F1" }}
						/>
						<span className="font-medium">
							{relationshipType?.label || row?.relationship_type}
						</span>
					</div>
				);
			},
		},
		{
			id: "ontology_class",
			header: "Ontology Property",
			cell: (row) => (
				<div>
					<div className="text-xs text-gray-500 truncate max-w-xs">
						{row?.ontology_property_uri || "Unknown"}
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
			cell: (row) => (
				<div className="flex items-center space-x-1">
					{row?.is_verified ? (
						<>
							<ShieldCheck size={16} className="text-green-500" />
							<span className="text-xs text-green-600">Verified</span>
						</>
					) : (
						<>
							<Shield size={16} className="text-gray-400" />
							<span className="text-xs text-gray-500">Pending</span>
						</>
					)}
				</div>
			),
		},
	];

	// Action buttons for Entity Mappings
	const entityActionButtons: ActionButton<EntityMapping>[] = [
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
			label: "Suggestions",
			icon: <Lightbulb size={16} />,
			onClick: (mapping) => {
				setSelectedMapping(mapping);
				setShowSuggestions(true);
			},
			variant: "ghost",
			className: "text-blue-600 hover:text-blue-800",
			show: (mapping) => mapping.suggestions && mapping.suggestions.length > 0,
		},
		{
			label: "Verify",
			icon: <ShieldCheck size={16} />,
			onClick: (mapping) => handleVerifyEntityMapping(mapping),
			variant: "ghost",
			className: "text-green-600 hover:text-green-800",
			show: (mapping) => !mapping.is_verified,
		},
		{
			label: "Delete",
			icon: <Trash2 size={16} />,
			onClick: (mapping) => handleDeleteEntityMapping(mapping),
			variant: "ghost",
			className: "text-red-600 hover:text-red-800",
		},
	];

	// Action buttons for Relationship Mappings
	const relationshipActionButtons: ActionButton<RelationshipMapping>[] = [
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
			label: "Suggestions",
			icon: <Lightbulb size={16} />,
			onClick: (mapping) => {
				setSelectedMapping(mapping);
				setShowSuggestions(true);
			},
			variant: "ghost",
			className: "text-blue-600 hover:text-blue-800",
			show: (mapping) => mapping.suggestions && mapping.suggestions.length > 0,
		},
		{
			label: "Verify",
			icon: <ShieldCheck size={16} />,
			onClick: (mapping) => handleVerifyRelationshipMapping(mapping),
			variant: "ghost",
			className: "text-green-600 hover:text-green-800",
			show: (mapping) => !mapping.is_verified,
		},
		{
			label: "Delete",
			icon: <Trash2 size={16} />,
			onClick: (mapping) => handleDeleteRelationshipMapping(mapping),
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
		highConfidencePending: [...entityMappings, ...relationshipMappings].filter(
			(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
		).length,
		needsReview: [...entityMappings, ...relationshipMappings].filter(
			(m) => m.mapping_status === "needs_review",
		).length,
		withSuggestions: [...entityMappings, ...relationshipMappings].filter(
			(m) => m.suggestions && m.suggestions.length > 0,
		).length,
		highConfidenceSuggestions: [
			...entityMappings,
			...relationshipMappings,
		].filter(
			(m) =>
				m.suggestions && m.suggestions.some((s: any) => s.confidence >= 0.8),
		).length,
	};

	// Loading and error states
	if (entityMappingsLoading || relationshipMappingsLoading) {
		return (
			<div className="p-6 flex items-center justify-center">
				<RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
				<span className="ml-2">Đang tải mappings...</span>
			</div>
		);
	}

	if (entityMappingsError || relationshipMappingsError) {
		return (
			<div className="p-6 flex items-center justify-center text-red-600">
				<AlertTriangle className="h-6 w-6 mr-2" />
				<span>Lỗi khi tải mappings. Vui lòng thử lại.</span>
			</div>
		);
	}

	return (
		<>
			<div className="p-6 space-y-6">
				{/* Header */}
				<div className="flex justify-between items-center">
					<div>
						<h1 className="text-2xl font-bold text-gray-900">
							Quản lý Ontology Mapping
						</h1>
						<p className="text-gray-600 mt-1">
							Tạo, quản lý và xác minh các mapping giữa các loại thực thể và
							quan hệ trong ontology của bạn.
						</p>
					</div>

					{/* Quick Actions */}
					<div className="flex space-x-2">
						<Button
							onClick={() => handleBulkVerifyHighConfidence(0.8)}
							disabled={isBulkVerifying || stats.highConfidencePending === 0}
							className="bg-green-600 hover:bg-green-700"
						>
							{isBulkVerifying ? (
								<RefreshCw size={16} className="mr-2 animate-spin" />
							) : (
								<ShieldCheck size={16} className="mr-2" />
							)}
							Verify High Confidence ({stats.highConfidencePending})
						</Button>
						<Button
							onClick={() => {
								refetchEntityMappings();
								refetchRelationshipMappings();
							}}
							variant="outline"
						>
							<RefreshCw size={16} className="mr-2" />
							Refresh
						</Button>
					</div>
				</div>

				{/* Enhanced Statistics */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatisticCard
						title="Entity Mappings"
						value={stats.totalEntityMappings}
						icon={<Database size={20} />}
						color="blue"
					/>
					<StatisticCard
						title="Verified Entities"
						value={stats.verifiedEntityMappings}
						icon={<ShieldCheck size={20} />}
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
						icon={<ShieldCheck size={20} />}
						color="green"
					/>
					<StatisticCard
						title="Pending Review"
						value={stats.pendingMappings}
						icon={<Clock size={20} />}
						color="yellow"
					/>
					<StatisticCard
						title="High Confidence"
						value={stats.highConfidencePending}
						icon={<AlertCircle size={20} />}
						color="orange"
					/>
					<StatisticCard
						title="With Suggestions"
						value={stats.withSuggestions}
						icon={<Lightbulb size={20} />}
						color="cyan"
					/>
					<StatisticCard
						title="High Confidence Suggestions"
						value={stats.highConfidenceSuggestions}
						icon={<TrendingUp size={20} />}
						color="emerald"
					/>
					<StatisticCard
						title="Needs Review"
						value={stats.needsReview}
						icon={<AlertTriangle size={20} />}
						color="red"
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
						<TabsTrigger value="entity-mappings">
							Entity Mappings ({entityMappings.length})
						</TabsTrigger>
						<TabsTrigger value="relationship-mappings">
							Relationship Mappings ({relationshipMappings.length})
						</TabsTrigger>
						<TabsTrigger value="bulk-operations">Bulk Operations</TabsTrigger>
					</TabsList>

					<TabsContent value="entity-mappings" className="space-y-4">
						<Card>
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<CardTitle>
									Entity Type Mappings ({entityMappings.length})
								</CardTitle>
								<div className="flex space-x-2">
									<Button
										size="sm"
										onClick={() => {
											const unverifiedHigh = entityMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											);
											if (unverifiedHigh.length > 0) {
												unverifiedHigh.forEach(handleVerifyEntityMapping);
											}
										}}
										disabled={
											entityMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											).length === 0
										}
										className="bg-green-600 hover:bg-green-700"
									>
										<ShieldCheck size={14} className="mr-1" />
										Verify High Confidence (
										{
											entityMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											).length
										}
										)
									</Button>
								</div>
							</CardHeader>
							<CardContent>
								<DataTable
									data={entityMappings}
									columns={entityMappingColumns}
									actionsOptions={{
										show: true,
										actions: entityActionButtons,
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
							<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
								<CardTitle>
									Relationship Type Mappings ({relationshipMappings.length})
								</CardTitle>
								<div className="flex space-x-2">
									<Button
										size="sm"
										onClick={() => {
											const unverifiedHigh = relationshipMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											);
											if (unverifiedHigh.length > 0) {
												unverifiedHigh.forEach(handleVerifyRelationshipMapping);
											}
										}}
										disabled={
											relationshipMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											).length === 0
										}
										className="bg-green-600 hover:bg-green-700"
									>
										<ShieldCheck size={14} className="mr-1" />
										Verify High Confidence (
										{
											relationshipMappings.filter(
												(m) => !m.is_verified && (m.confidence || 0) >= 0.8,
											).length
										}
										)
									</Button>
								</div>
							</CardHeader>
							<CardContent>
								<DataTable<RelationshipMapping, any>
									data={relationshipMappings}
									columns={relationshipMappingColumns}
									actionsOptions={{
										show: true,
										actions: relationshipActionButtons,
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

					<TabsContent value="bulk-operations" className="space-y-4">
						<Card>
							<CardHeader>
								<CardTitle>Bulk Mapping Operations</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
									{/* Auto-Mapping */}
									<div className="space-y-4">
										<h3 className="font-medium flex items-center">
											<Lightbulb className="mr-2" size={16} />
											Auto-Mapping
										</h3>
										<p className="text-sm text-gray-600">
											Tự động tạo mappings cho các entity và relationship types
											chưa có mapping bằng AI.
										</p>
										<Button className="w-full">
											<Lightbulb size={16} className="mr-2" />
											Chạy Auto-Mapping
										</Button>
									</div>

									{/* Bulk Verification */}
									<div className="space-y-4">
										<h3 className="font-medium flex items-center">
											<ShieldCheck className="mr-2" size={16} />
											Bulk Verification
										</h3>
										<p className="text-sm text-gray-600">
											Verify tất cả mappings có confidence score cao.
										</p>
										<div className="space-y-2">
											<Button
												className="w-full bg-green-600 hover:bg-green-700"
												onClick={() => handleBulkVerifyHighConfidence(0.9)}
												disabled={isBulkVerifying}
											>
												{isBulkVerifying ? (
													<RefreshCw size={16} className="mr-2 animate-spin" />
												) : (
													<ShieldCheck size={16} className="mr-2" />
												)}
												Verify 90%+ confidence
											</Button>
											<Button
												className="w-full bg-green-500 hover:bg-green-600"
												onClick={() => handleBulkVerifyHighConfidence(0.8)}
												disabled={isBulkVerifying}
											>
												{isBulkVerifying ? (
													<RefreshCw size={16} className="mr-2 animate-spin" />
												) : (
													<ShieldCheck size={16} className="mr-2" />
												)}
												Verify 80%+ confidence
											</Button>
										</div>
									</div>

									{/* Review Center */}
									<div className="space-y-4">
										<h3 className="font-medium flex items-center">
											<AlertTriangle className="mr-2" size={16} />
											Review Center
										</h3>
										<p className="text-sm text-gray-600">
											Xem lại các mappings cần review hoặc có confidence thấp.
										</p>
										<div className="space-y-2">
											<Button variant="outline" className="w-full">
												<Eye size={16} className="mr-2" />
												Review Low Confidence
											</Button>
											<Button variant="outline" className="w-full">
												<Users size={16} className="mr-2" />
												Review Conflicts
											</Button>
										</div>
									</div>
								</div>
							</CardContent>
						</Card>
					</TabsContent>
				</Tabs>

				{/* Enhanced View Modal */}
				<Dialog
					title="Chi tiết Mapping"
					description="Thông tin chi tiết về mapping được chọn"
					open={isViewModalOpen}
					onOpenChange={setIsViewModalOpen}
				>
					{selectedMapping && (
						<div className="space-y-6">
							{/* Basic Information */}
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
											? "Ontology Class"
											: "Ontology Property"}
									</label>
									<p className="mt-1 text-sm break-all">
										{"entity_type" in selectedMapping
											? selectedMapping?.ontology_class_uri || "Unknown"
											: selectedMapping?.ontology_property_uri || "Unknown"}
									</p>
								</div>
							</div>

							{/* Verification Status */}
							<div className="grid grid-cols-3 gap-4">
								<div>
									<label className="text-sm font-medium text-gray-500">
										Confidence Score
									</label>
									<div className="mt-1 flex items-center space-x-2">
										<Progress
											value={(selectedMapping.confidence || 0) * 100}
											className="flex-1 h-2"
										/>
										<span className="text-sm font-medium">
											{((selectedMapping.confidence || 0) * 100).toFixed(1)}%
										</span>
									</div>
								</div>
								<div>
									<label className="text-sm font-medium text-gray-500">
										Status
									</label>
									<p className="mt-1">
										<Badge
											className={
												selectedMapping.mapping_status === "mapped"
													? "bg-green-100 text-green-800"
													: selectedMapping.mapping_status === "rejected"
														? "bg-red-100 text-red-800"
														: selectedMapping.mapping_status === "needs_review"
															? "bg-orange-100 text-orange-800"
															: "bg-yellow-100 text-yellow-800"
											}
										>
											{selectedMapping.mapping_status || "pending"}
										</Badge>
									</p>
								</div>
								<div>
									<label className="text-sm font-medium text-gray-500">
										Verification
									</label>
									<div className="mt-1 flex items-center space-x-2">
										{selectedMapping.is_verified ? (
											<>
												<ShieldCheck size={16} className="text-green-500" />
												<span className="text-sm text-green-600">Verified</span>
											</>
										) : (
											<>
												<Shield size={16} className="text-gray-400" />
												<span className="text-sm text-gray-500">
													Not Verified
												</span>
											</>
										)}
									</div>
								</div>
							</div>

							{/* Additional Details */}
							<div className="space-y-4">
								<div>
									<label className="text-sm font-medium text-gray-500">
										Auto Mapped
									</label>
									<p className="mt-1 text-sm">
										{selectedMapping.auto_mapped ? "Yes" : "No"}
									</p>
								</div>

								{selectedMapping.created_at && (
									<div>
										<label className="text-sm font-medium text-gray-500">
											Created At
										</label>
										<p className="mt-1 text-sm">
											{new Date(selectedMapping.created_at).toLocaleString(
												"vi-VN",
											)}
										</p>
									</div>
								)}

								{selectedMapping.updated_at && (
									<div>
										<label className="text-sm font-medium text-gray-500">
											Last Updated
										</label>
										<p className="mt-1 text-sm">
											{new Date(selectedMapping.updated_at).toLocaleString(
												"vi-VN",
											)}
										</p>
									</div>
								)}
							</div>

							{/* Action Buttons in Modal */}
							<div className="flex justify-end space-x-3 pt-4 border-t">
								{!selectedMapping.is_verified && (
									<Button
										onClick={() => {
											if ("entity_type" in selectedMapping) {
												handleVerifyEntityMapping(selectedMapping);
											} else {
												handleVerifyRelationshipMapping(selectedMapping);
											}
											setIsViewModalOpen(false);
										}}
										className="bg-green-600 hover:bg-green-700"
										disabled={
											verifyEntityMappingMutation.isPending ||
											verifyRelationshipMappingMutation.isPending
										}
									>
										{verifyEntityMappingMutation.isPending ||
										verifyRelationshipMappingMutation.isPending ? (
											<RefreshCw size={16} className="mr-2 animate-spin" />
										) : (
											<ShieldCheck size={16} className="mr-2" />
										)}
										Verify Mapping
									</Button>
								)}

								<Button
									variant="outline"
									onClick={() => {
										if ("entity_type" in selectedMapping) {
											handleDeleteEntityMapping(selectedMapping);
										} else {
											handleDeleteRelationshipMapping(selectedMapping);
										}
										setIsViewModalOpen(false);
									}}
									className="text-red-600 hover:text-red-800 hover:bg-red-50"
									disabled={
										deleteEntityMappingMutation.isPending ||
										deleteRelationshipMappingMutation.isPending
									}
								>
									{deleteEntityMappingMutation.isPending ||
									deleteRelationshipMappingMutation.isPending ? (
										<RefreshCw size={16} className="mr-2 animate-spin" />
									) : (
										<Trash2 size={16} className="mr-2" />
									)}
									Delete
								</Button>

								<Button
									variant="outline"
									onClick={() => setIsViewModalOpen(false)}
								>
									Close
								</Button>
							</div>
						</div>
					)}
				</Dialog>

				{/* Loading Overlay */}
				{(verifyEntityMappingMutation.isPending ||
					verifyRelationshipMappingMutation.isPending ||
					deleteEntityMappingMutation.isPending ||
					deleteRelationshipMappingMutation.isPending ||
					isBulkVerifying) && (
					<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
						<div className="bg-white rounded-lg p-6 flex items-center space-x-3">
							<RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
							<span className="text-lg">
								{isBulkVerifying ? "Đang bulk verify..." : "Đang xử lý..."}
							</span>
						</div>
					</div>
				)}
			</div>
			<Dialog
				title="AI Suggestions"
				description="Xem và áp dụng các suggestions từ AI cho mapping này"
				onOpenChange={setShowSuggestions}
				open={showSuggestions}
			>
				{selectedMapping && (
					<div className="space-y-6">
						{/* Mapping Info */}
						<div className="bg-gray-50 rounded-lg p-4">
							<div className="flex items-center space-x-3">
								<div className="w-3 h-3 rounded-full bg-blue-500"></div>
								<div>
									<p className="font-medium">
										{"entity_type" in selectedMapping
											? selectedMapping.entity_type
											: selectedMapping.relationship_type}
									</p>
									<p className="text-sm text-gray-500">
										Current:{" "}
										{"entity_type" in selectedMapping
											? selectedMapping.ontology_class_uri
											: selectedMapping.ontology_property_uri}
									</p>
								</div>
							</div>
						</div>

						{/* Suggestions List */}
						<div>
							<h4 className="font-medium mb-3 flex items-center">
								<Lightbulb size={16} className="mr-2 text-yellow-500" />
								Available Suggestions
							</h4>
							{renderSuggestions(
								selectedMapping.suggestions || [],
								"entity_type" in selectedMapping ? "entity" : "relationship",
							)}
						</div>

						{/* Actions */}
						<div className="flex justify-end space-x-3 pt-4 border-t">
							<Button
								variant="outline"
								onClick={() => setShowSuggestions(false)}
							>
								Close
							</Button>
						</div>
					</div>
				)}
			</Dialog>
		</>
	);
};

export default OntologyMappingManagementPage;
