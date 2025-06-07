import React, { useState, useEffect, useMemo } from "react";
import {
	useSearchEntities,
	useFindSimilarEntities,
	useGraphSearch,
	useGenerateEmbeddings,
} from "@vbkg/api-client";
import {
	Search,
	TrendingUp,
	Database,
	GitBranch,
	AlertCircle,
	ExternalLink,
	Download,
	RefreshCw,
	Eye,
	Loader2,
	Network,
} from "lucide-react";
import {
	AppForm,
	DataTable,
	FieldConfig,
	ResultCard,
	StatisticCard,
} from "@/components";
import z from "zod";
import { SearchType } from "@vbkg/types";

// Main Component
const KnowledgeSearchPage = () => {
	const [searchParams, setSearchParams] = useState({
		query: "",
		entity_types: [],
		search_type: SearchType.HYBRID,
		limit: 20,
		similarity_threshold: 0.5,
		include_relationships: true,
		include_similar_entities: false,
	});
	const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
	const [currentView, setCurrentView] = useState("overview");
	const [selectedResults, setSelectedResults] = useState([]);

	// Hooks
	const searchEntities = useSearchEntities(
		{ ...searchParams },
		{
			enabled: !!searchParams.query,
		},
	);

	const findSimilarEntities = useFindSimilarEntities(
		{ entity_id: selectedEntity!, limit: 10 },
		{ enabled: !!selectedEntity },
	);

	const graphSearch = useGraphSearch(
		{
			start_entity_text: searchParams.query,
			relationship_path: ["RELATED_TO"],
			max_depth: 2,
			limit: 20,
		},
		{ enabled: !!searchParams.query && currentView === "graph" },
	);

	const generateEmbeddings = useGenerateEmbeddings({
		onSuccess: (data) => {
			console.log("Generated embedding:", data);
		},
		onError: (error) => {
			console.error("Failed to generate embedding:", error);
		},
	});

	// Form fields
	const searchFormFields = [
		{
			name: "query",
			type: "text",
			label: "Search Query",
			placeholder: "Enter search terms...",
			required: true,
			description: "Search across entities and relationships",
		},
		{
			name: "search_type",
			type: "select",
			label: "Search Type",
			placeholder: "Select search type",
			options: [
				{ value: "exact", label: "Exact Match" },
				{ value: "fuzzy", label: "Fuzzy Search" },
				{ value: "semantic", label: "Semantic Search" },
				{ value: "hybrid", label: "Hybrid Search" },
			],
		},
		{
			name: "entity_types",
			type: "select",
			label: "Entity Types",
			placeholder: "Select entity types",
			options: [
				{ value: "Company", label: "Company" },
				{ value: "Person", label: "Person" },
				{ value: "Product", label: "Product" },
				{ value: "Location", label: "Location" },
			],
			description: "Hold Ctrl/Cmd to select multiple types",
		},
		{
			name: "similarity_threshold",
			type: "number",
			label: "Similarity Threshold",
			placeholder: "0.5",
			description: "Minimum similarity score (0-1)",
		},
		{
			name: "limit",
			type: "number",
			label: "Result Limit",
			placeholder: "20",
			description: "Maximum number of results",
		},
		{
			name: "include_relationships",
			type: "switch",
			label: "Include relationships",
		},
		{
			name: "include_similar_entities",
			type: "switch",
			label: "Find similar entities",
		},
	] satisfies FieldConfig[];

	// Entity table columns
	const entityColumns = [
		{
			header: "Entity",
			accessorKey: "text",
			cell: (row) => (
				<div>
					<div className="font-medium">{row.text}</div>
					<div className="text-sm text-gray-500">{row.type}</div>
				</div>
			),
		},
		{
			header: "Score",
			accessorKey: "score",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<div className="w-16 bg-gray-200 rounded-full h-2">
						<div
							className="bg-blue-500 h-2 rounded-full"
							style={{ width: `${row.score * 100}%` }}
						/>
					</div>
					<span className="text-sm">{(row.score * 100).toFixed(1)}%</span>
				</div>
			),
		},
		{
			header: "Properties",
			accessorKey: "properties",
			cell: (row) => (
				<div className="text-sm text-gray-600">
					{Object.keys(row.properties || {}).length} properties
				</div>
			),
		},
		{
			header: "Relationships",
			accessorKey: "relationships",
			cell: (row) => (
				<div className="text-sm text-gray-600">
					{(row.relationships || []).length} relations
				</div>
			),
		},
		{
			header: "Actions",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<button
						onClick={() => setSelectedEntity(row.id)}
						className="p-1 hover:bg-gray-100 rounded"
						title="Find similar"
					>
						<Network size={16} />
					</button>
					<button className="p-1 hover:bg-gray-100 rounded">
						<Eye size={16} />
					</button>
					<button className="p-1 hover:bg-gray-100 rounded">
						<ExternalLink size={16} />
					</button>
				</div>
			),
		},
	];

	// Handle search
	const handleSearch = (searchData: any) => {
		setSearchParams({
			...searchData,
			entity_types: [searchData.entity_types],
			limit: Number(searchData.limit) || 20,
			similarity_threshold: Number(searchData.similarity_threshold),
		});
	};

	// Handle generate embeddings
	const handleGenerateEmbeddings = async () => {
		if (searchParams.query) {
			await generateEmbeddings.mutateAsync({
				text: searchParams.query,
				model: "sentence-transformers/all-MiniLM-L6-v2",
			});
		}
	};

	// Statistics
	const stats = useMemo(() => {
		const results = searchEntities.data?.data.results || [];
		return {
			totalEntities: results.length,
			totalRelationships: results.reduce(
				(sum, entity) => sum + (entity.relationships?.length || 0),
				0,
			),
			avgScore:
				results.length > 0
					? (
							results.reduce((sum, e) => sum + e.score, 0) / results.length
						).toFixed(2)
					: 0,
			executionTime: searchEntities.data?.execution_time_ms || 0,
		};
	}, [searchEntities.data]);

	return (
		<div className="min-h-screen bg-gray-50 p-6">
			<div className="max-w-7xl mx-auto space-y-6">
				{/* Header */}
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">
							Knowledge Graph Search
						</h1>
						<p className="text-gray-600 mt-1">
							Search and explore entities and relationships using advanced AI
						</p>
					</div>
					<div className="flex items-center space-x-3">
						<button
							onClick={handleGenerateEmbeddings}
							disabled={!searchParams.query || generateEmbeddings.isLoading}
							className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
						>
							{generateEmbeddings.isLoading ? (
								<Loader2 className="mr-2 h-4 w-4 animate-spin" />
							) : null}
							Generate Embeddings
						</button>
						<button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
							<Download size={16} className="mr-2" />
							Export Results
						</button>
					</div>
				</div>

				{/* Statistics */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatisticCard
						title="Found Entities"
						value={stats.totalEntities}
						icon={<Database size={20} />}
						color="blue"
						onClick={() => setCurrentView("entities")}
					/>
					<StatisticCard
						title="Relationships"
						value={stats.totalRelationships}
						icon={<GitBranch size={20} />}
						color="green"
						onClick={() => setCurrentView("relationships")}
					/>
					<StatisticCard
						title="Avg Score"
						value={`${(Number(stats.avgScore) * 100).toFixed(0)}%`}
						icon={<TrendingUp size={20} />}
						color="purple"
					/>
					<StatisticCard
						title="Execution Time"
						value={`${stats.executionTime}ms`}
						icon={<RefreshCw size={20} />}
						color="yellow"
					/>
				</div>

				{/* Search Form */}
				<div className="bg-white rounded-lg border shadow-sm p-6">
					<div className="flex items-center space-x-2 mb-4">
						<Search size={20} className="text-gray-400" />
						<h2 className="text-lg font-semibold">Search Knowledge Graph</h2>
					</div>

					<AppForm
						fields={searchFormFields}
						onSubmit={handleSearch}
						schema={z.object({
							query: z.string().min(1, "Query is required"),
							entity_types: z.string().optional(),
							search_type: z.nativeEnum(SearchType).optional(),
							limit: z.string().optional(),
							similarity_threshold: z.string().optional(),
							include_relationships: z.boolean().optional(),
							include_similar_entities: z.boolean().optional(),
						})}
						submitButtonText={
							searchEntities.isLoading ? "Searching..." : "Search"
						}
						isLoading={searchEntities.isLoading}
					/>
				</div>

				{/* View Toggle */}
				{searchEntities.data && (
					<div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
						<button
							onClick={() => setCurrentView("overview")}
							className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
								currentView === "overview"
									? "bg-blue-100 text-blue-700"
									: "text-gray-600 hover:text-gray-900"
							}`}
						>
							Overview
						</button>
						<button
							onClick={() => setCurrentView("entities")}
							className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
								currentView === "entities"
									? "bg-blue-100 text-blue-700"
									: "text-gray-600 hover:text-gray-900"
							}`}
						>
							Entities ({stats.totalEntities})
						</button>
						<button
							onClick={() => setCurrentView("graph")}
							className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
								currentView === "graph"
									? "bg-blue-100 text-blue-700"
									: "text-gray-600 hover:text-gray-900"
							}`}
						>
							Graph View
						</button>
					</div>
				)}

				{/* Similar Entities */}
				{selectedEntity && findSimilarEntities.data && (
					<div className="bg-white rounded-lg border shadow-sm p-6">
						<div className="flex items-center justify-between mb-4">
							<h2 className="text-lg font-semibold">Similar Entities</h2>
							<button
								onClick={() => setSelectedEntity(null)}
								className="text-gray-400 hover:text-gray-600"
							>
								✕
							</button>
						</div>
						<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
							{findSimilarEntities.data.map((entity) => (
								<div key={entity.id} className="border rounded-lg p-4">
									<div className="flex items-center justify-between mb-2">
										<span className="font-medium">{entity.text}</span>
										<span className="text-sm text-gray-500">
											{(entity.similarity * 100).toFixed(1)}%
										</span>
									</div>
									<span className="text-sm text-gray-600">{entity.type}</span>
								</div>
							))}
						</div>
					</div>
				)}

				{/* Search Results */}
				{currentView === "overview" && searchEntities.data && (
					<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
						{searchEntities.data.data.results.map((entity) => (
							<ResultCard
								key={entity.id}
								id={entity.id}
								type={entity.type}
								name={entity.text}
								properties={entity.properties}
								score={entity.score}
								relationships={entity.relationships || []}
								onViewDetails={(id) => console.log("View details:", id)}
								onViewSimilar={(id) => setSelectedEntity(id)}
								highlightTerms={searchParams.query ? [searchParams.query] : []}
							/>
						))}
					</div>
				)}

				{currentView === "entities" && searchEntities.data && (
					<div className="bg-white rounded-lg border shadow-sm">
						<div className="p-6 border-b">
							<div className="flex items-center justify-between">
								<h2 className="text-lg font-semibold">Entity Results</h2>
								<span className="text-sm text-gray-500">
									{searchEntities.data.data.results.length} entities found
								</span>
							</div>
						</div>
						<div className="p-6">
							<DataTable
								data={searchEntities.data.data.results}
								columns={entityColumns}
								showGlobalFilter={true}
								onRowSelectionChange={setSelectedResults}
							/>
						</div>
					</div>
				)}

				{currentView === "graph" && (
					<div className="bg-white rounded-lg border shadow-sm p-6">
						<div className="flex items-center justify-between mb-4">
							<h2 className="text-lg font-semibold">Graph Search Results</h2>
							{graphSearch.isLoading && (
								<Loader2 className="h-5 w-5 animate-spin" />
							)}
						</div>

						{graphSearch.data && (
							<div className="space-y-4">
								{graphSearch.data.paths.map((path, index) => (
									<div key={index} className="border rounded-lg p-4">
										<div className="flex items-center space-x-2 text-sm">
											{path.path.map((node, nodeIndex) => (
												<React.Fragment key={nodeIndex}>
													<span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
														{node}
													</span>
													{nodeIndex < path.path.length - 1 && (
														<span className="text-gray-400">→</span>
													)}
												</React.Fragment>
											))}
										</div>
									</div>
								))}
							</div>
						)}
					</div>
				)}

				{/* Loading State */}
				{searchEntities.isLoading && (
					<div className="text-center py-12">
						<div className="inline-flex items-center space-x-2">
							<Loader2 size={20} className="animate-spin" />
							<span>Searching knowledge graph...</span>
						</div>
					</div>
				)}

				{/* Error State */}
				{searchEntities.error && (
					<div className="text-center py-12">
						<AlertCircle size={48} className="mx-auto text-red-400 mb-4" />
						<h3 className="text-lg font-medium text-gray-900 mb-2">
							Search Error
						</h3>
						<p className="text-gray-600">
							{searchEntities.error.message ||
								"An error occurred while searching"}
						</p>
					</div>
				)}

				{/* Empty State */}
				{!searchEntities.isLoading &&
					!searchEntities.error &&
					searchEntities.data &&
					searchEntities.data.data.results.length === 0 && (
						<div className="text-center py-12">
							<Search size={48} className="mx-auto text-gray-400 mb-4" />
							<h3 className="text-lg font-medium text-gray-900 mb-2">
								No results found
							</h3>
							<p className="text-gray-600">
								Try adjusting your search terms or search type to find what
								you're looking for.
							</p>
						</div>
					)}
			</div>
		</div>
	);
};

export default KnowledgeSearchPage;
