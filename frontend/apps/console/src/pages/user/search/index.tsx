// pages/search/ai-search.tsx - Simple AI Search Page with Real Hooks
import React, { useState, useMemo } from "react";
import {
	Search,
	TrendingUp,
	Database,
	GitBranch,
	Loader2,
	Network,
	Brain,
	Sparkles,
	AlertCircle,
	Download,
	RefreshCw,
} from "lucide-react";
import {
	AppForm,
	DataTable,
	FieldConfig,
	ResultCard,
	StatisticCard,
} from "@/components";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import z from "zod";

// Import real hooks
import {
	useAISearchMutation,
	useQuickAISearch,
	useSearchSuggestions,
	useAISearchStats,
	useExplainAISearch,
	useAISubgraph,
} from "@vbkg/api-client";

// Import types
import { AISearchRequest, SearchType } from "@vbkg/types";
import { D3GraphVisualization } from "../visualization/components/D3GraphVisualization";

const SimpleAISearchPage = () => {
	const [query, setQuery] = useState("");
	const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
	const [currentView, setCurrentView] = useState("search");
	const [searchHistory, setSearchHistory] = useState<string[]>([]);
	const [entityTypes, setEntityTypes] = useState<string[]>([]);

	// Real AI Search Hooks
	const aiSearchMutation = useAISearchMutation({
		onSuccess: (data) => {
			setCurrentView("results");
			// Add to search history
			if (!searchHistory.includes(query)) {
				setSearchHistory((prev) => [query, ...prev.slice(0, 9)]);
			}
		},
		onError: (error) => {
			console.error("AI Search failed:", error);
		},
	});

	// Search suggestions hook
	const { data: suggestions, isLoading: suggestionsLoading } =
		useSearchSuggestions(
			{ partial_query: query, limit: 5 },
			{ enabled: query.length >= 2 },
		);

	// AI Search stats
	const { data: searchStats } = useAISearchStats();

	// Explain search results
	const explainSearch = useExplainAISearch(
		{
			query,
			generate_answer: true,
			top_k_entities: 10,
		},
		{ enabled: false },
	);

	// Subgraph data
	const subgraphData = useAISubgraph(
		{
			query,
			top_k_entities: 10,
			subgraph_radius: 2,
		},
		{ enabled: false },
	);

	// Handle AI Search
	const handleAISearch = async () => {
		if (!query.trim()) return;

		const searchRequest: AISearchRequest = {
			query: query.trim(),
			entity_types: entityTypes.length > 0 ? entityTypes : undefined,
			generate_answer: true,
			top_k_entities: 10,
			similarity_threshold: 0.3,
			max_candidates: 50,
		};

		await aiSearchMutation.mutateAsync(searchRequest);
	};

	// Handle Enter key
	const handleKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") {
			handleAISearch();
		}
	};

	// Handle suggestion click
	const handleSuggestionClick = (suggestion: string) => {
		setQuery(suggestion);
		setTimeout(() => {
			const searchRequest: AISearchRequest = {
				query: suggestion,
				entity_types: entityTypes.length > 0 ? entityTypes : undefined,
				generate_answer: true,
				top_k_entities: 10,
			};
			aiSearchMutation.mutateAsync(searchRequest);
		}, 100);
	};

	// Handle entity type filter
	const handleEntityTypeChange = (type: string) => {
		if (entityTypes.includes(type)) {
			setEntityTypes((prev) => prev.filter((t) => t !== type));
		} else {
			setEntityTypes((prev) => [...prev, type]);
		}
	};

	// Handle explain results
	const handleExplainResults = () => {
		explainSearch.refetch();
		setCurrentView("explain");
	};

	// Handle view subgraph
	const handleViewSubgraph = () => {
		subgraphData.refetch();
		setCurrentView("graph");
	};

	// Statistics
	const stats = useMemo(() => {
		const results = aiSearchMutation.data?.data.entities || [];
		return {
			totalEntities: results.length,
			totalRelationships: results.reduce(
				(sum, entity) => sum + (entity.relationships?.length || 0),
				0,
			),
			avgScore:
				results.length > 0
					? (
							results.reduce((sum, e) => sum + e.final_score, 0) /
							results.length
						).toFixed(2)
					: 0,
			executionTime: aiSearchMutation.data?.data.execution_time_ms || 0,
			confidence: aiSearchMutation.data?.data.confidence_score
				? (aiSearchMutation.data.data.confidence_score * 100).toFixed(0)
				: 0,
		};
	}, [aiSearchMutation.data]);

	// Entity table columns
	const entityColumns = [
		{
			header: "Entity",
			accessorKey: "entity_text",
			cell: (row) => (
				<div>
					<div className="font-medium">{row?.entity_text}</div>
					<div className="text-sm text-gray-500">{row.entity_type}</div>
				</div>
			),
		},
		{
			header: "Final Score",
			accessorKey: "final_score",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<div className="w-16 bg-gray-200 rounded-full h-2">
						<div
							className="bg-blue-500 h-2 rounded-full"
							style={{ width: `${row.final_score * 100}%` }}
						/>
					</div>
					<span className="text-sm">{(row.final_score * 100).toFixed(1)}%</span>
				</div>
			),
		},
		{
			header: "Similarity",
			accessorKey: "similarity_score",
			cell: (row) => (
				<span className="text-sm">
					{(row.similarity_score * 100).toFixed(1)}%
				</span>
			),
		},
		{
			header: "PersonRank",
			accessorKey: "personrank_score",
			cell: (row) => (
				<span className="text-sm">
					{(row.personrank_score * 100).toFixed(1)}%
				</span>
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
			header: "Actions",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<button
						onClick={() => setSelectedEntity(row.entity_id)}
						className="p-1 hover:bg-gray-100 rounded"
						title="View details"
					>
						<Network size={16} />
					</button>
				</div>
			),
		},
	];

	return (
		<div className="min-h-screen bg-gray-50 p-6">
			<div className="max-w-7xl mx-auto space-y-6">
				{/* Header */}
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
							<Brain className="h-8 w-8 text-blue-600" />
							<span>AI Search</span>
						</h1>
						<p className="text-gray-600 mt-1">
							Tìm kiếm thông minh sử dụng AI và phân tích đồ thị tri thức.
						</p>
					</div>
					<div className="flex items-center space-x-3">
						{aiSearchMutation.data && (
							<>
								<Button
									variant="outline"
									onClick={handleExplainResults}
									disabled={explainSearch.isLoading}
								>
									{explainSearch.isLoading ? (
										<Loader2 className="h-4 w-4 animate-spin mr-2" />
									) : null}
									Explain Results
								</Button>
								<Button
									variant="outline"
									onClick={handleViewSubgraph}
									disabled={subgraphData.isLoading}
								>
									{subgraphData.isLoading ? (
										<Loader2 className="h-4 w-4 animate-spin mr-2" />
									) : null}
									View Graph
								</Button>
							</>
						)}
					</div>
				</div>

				{/* AI Search Bar */}
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center space-x-2">
							<Sparkles className="h-5 w-5 text-purple-600" />
							<span>AI Knowledge Search</span>
							{searchStats?.data?.ai_search_available && (
								<Badge
									variant="secondary"
									className="bg-green-100 text-green-700"
								>
									AI Ready
								</Badge>
							)}
						</CardTitle>
					</CardHeader>
					<CardContent className="space-y-4">
						{/* Search Input */}
						<div className="flex space-x-4">
							<div className="flex-1 relative">
								<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
								<Input
									value={query}
									onChange={(e) => setQuery(e.target.value)}
									onKeyDown={handleKeyDown}
									disabled={aiSearchMutation.isPending}
									placeholder="Hỏi bất cứ điều gì về đồ thị tri thức của bạn..."
									className="pl-10 text-base py-6"
								/>
							</div>
							<Button
								onClick={handleAISearch}
								disabled={!query.trim() || aiSearchMutation.isPending}
								size="lg"
								className="bg-gradient-to-r h-12 from-blue-600 to-purple-600"
							>
								{aiSearchMutation.isPending ? (
									<Loader2 className="h-5 w-5 animate-spin" />
								) : (
									<Sparkles className="h-5 w-5" />
								)}
							</Button>
						</div>

						{/* Entity Type Filters */}
						<div className="space-y-2">
							<p className="text-sm text-gray-600">Lọc theo loại thực thể:</p>
							<div className="flex flex-wrap gap-2">
								{[
									"Company",
									"Person",
									"Product",
									"Location",
									"Technology",
									"Organization",
								].map((type) => (
									<Badge
										key={type}
										variant={
											entityTypes.includes(type) ? "default" : "secondary"
										}
										className="cursor-pointer"
										onClick={() => handleEntityTypeChange(type)}
									>
										{type}
									</Badge>
								))}
							</div>
						</div>

						{/* Search Suggestions */}
						{suggestions?.data?.suggestions &&
							suggestions.data.suggestions.length > 0 && (
								<div className="space-y-2">
									<p className="text-sm text-gray-600">Gợi ý tìm kiếm:</p>
									<div className="flex flex-wrap gap-2">
										{suggestions.data.suggestions.map((suggestion, index) => (
											<Badge
												key={index}
												variant="outline"
												className="cursor-pointer hover:bg-blue-50"
												onClick={() => handleSuggestionClick(suggestion)}
											>
												{suggestion}
											</Badge>
										))}
									</div>
								</div>
							)}

						{/* Example queries */}
						<div className="space-y-2">
							<p className="text-sm text-gray-600">Thử các câu hỏi mẫu:</p>
							<div className="flex flex-wrap gap-2">
								{[
									"Những công ty nào liên quan đến công nghệ AI?",
									"Mối quan hệ giữa các tổ chức và con người",
									"Phân tích mạng lưới đầu tư",
									"Các thực thể trong lĩnh vực tài chính",
								].map((example) => (
									<Badge
										key={example}
										variant="secondary"
										className="cursor-pointer hover:bg-blue-100"
										onClick={() => setQuery(example)}
									>
										{example}
									</Badge>
								))}
							</div>
						</div>
					</CardContent>
				</Card>

				{/* Error Display */}
				{aiSearchMutation.error && (
					<Alert variant="destructive">
						<AlertCircle className="h-4 w-4" />
						<AlertDescription>
							{aiSearchMutation.error?.message ||
								"Đã xảy ra lỗi khi tìm kiếm. Vui lòng thử lại."}
						</AlertDescription>
					</Alert>
				)}

				{/* Statistics */}
				{aiSearchMutation.data && (
					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
						<StatisticCard
							title="Found Entities"
							value={stats.totalEntities}
							icon={<Database size={20} />}
							color="blue"
						/>
						<StatisticCard
							title="Relationships"
							value={stats.totalRelationships}
							icon={<GitBranch size={20} />}
							color="green"
						/>
						<StatisticCard
							title="Avg Score"
							value={`${(Number(stats.avgScore) * 100).toFixed(0)}%`}
							icon={<TrendingUp size={20} />}
							color="purple"
						/>
						<StatisticCard
							title="Confidence"
							value={`${stats.confidence}%`}
							icon={<Brain size={20} />}
							color="yellow"
						/>
						<StatisticCard
							title="Execution Time"
							value={`${stats.executionTime}ms`}
							icon={<Loader2 size={20} />}
							color="gray"
						/>
					</div>
				)}

				{/* AI Answer */}
				{aiSearchMutation.data?.data.answer && (
					<Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
						<CardHeader>
							<CardTitle className="flex items-center space-x-2">
								<Brain className="h-5 w-5 text-blue-600" />
								<span>AI Answer</span>
								<Badge variant="secondary">
									Confidence: {stats.confidence}%
								</Badge>
							</CardTitle>
						</CardHeader>
						<CardContent>
							<p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
								{aiSearchMutation.data.data.answer}
							</p>
						</CardContent>
					</Card>
				)}

				{/* Tabs for different views */}
				{aiSearchMutation.data && (
					<Tabs
						value={currentView}
						onValueChange={setCurrentView}
						className="w-full"
					>
						<TabsList className="grid w-full grid-cols-4">
							<TabsTrigger value="results">Results</TabsTrigger>
							<TabsTrigger value="overview">Overview</TabsTrigger>
							<TabsTrigger value="entities">
								Entities ({stats.totalEntities})
							</TabsTrigger>
							<TabsTrigger value="explain" disabled={!explainSearch.data}>
								Analysis
							</TabsTrigger>
						</TabsList>

						<TabsContent value="results" className="space-y-4">
							<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
								{aiSearchMutation.data.data.entities
									.slice(0, 6)
									.map((entity) => (
										<Card
											key={entity.entity_id}
											className="hover:shadow-md transition-shadow"
										>
											<CardContent className="p-4">
												<div className="flex items-start justify-between mb-2">
													<div>
														<h3 className="font-semibold text-gray-900">
															{entity.entity_text}
														</h3>
														<Badge variant="outline" className="mt-1">
															{entity.entity_type}
														</Badge>
													</div>
													<div className="text-right">
														<div className="text-lg font-bold text-blue-600">
															{(entity.final_score * 100).toFixed(0)}%
														</div>
														<div className="text-xs text-gray-500">
															Final Score
														</div>
													</div>
												</div>

												<div className="grid grid-cols-2 gap-2 text-xs text-gray-600 mb-3">
													<div>
														Similarity:{" "}
														{(entity.similarity_score * 100).toFixed(0)}%
													</div>
													<div>
														PersonRank:{" "}
														{(entity.personrank_score * 100).toFixed(0)}%
													</div>
												</div>

												{Object.keys(entity.properties).length > 0 && (
													<div className="text-sm text-gray-600">
														{Object.entries(entity.properties)
															.slice(0, 2)
															.map(([key, value]) => (
																<div key={key}>
																	<span className="font-medium">{key}:</span>{" "}
																	{String(value).slice(0, 50)}
																	{String(value).length > 50 && "..."}
																</div>
															))}
													</div>
												)}
											</CardContent>
										</Card>
									))}
							</div>
						</TabsContent>

						<TabsContent value="overview">
							<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
								{aiSearchMutation.data.data.entities.map((entity) => (
									<ResultCard
										key={entity.entity_id}
										id={entity.entity_id}
										type={entity.entity_type}
										name={entity.entity_text}
										properties={entity.properties}
										score={entity.final_score}
										relationships={[]}
										onViewDetails={(id) => console.log("View details:", id)}
										onViewSimilar={(id) => setSelectedEntity(id)}
										highlightTerms={query ? [query] : []}
									/>
								))}
							</div>
						</TabsContent>

						<TabsContent value="entities">
							<div className="bg-white rounded-lg border shadow-sm">
								<div className="p-6 border-b">
									<div className="flex items-center justify-between">
										<h2 className="text-lg font-semibold">Entity Results</h2>
										<span className="text-sm text-gray-500">
											{aiSearchMutation.data.data.entities.length} entities
											found
										</span>
									</div>
								</div>
								<div className="p-6">
									<DataTable
										data={aiSearchMutation.data.data.entities}
										columns={entityColumns}
										showGlobalFilter={true}
									/>
								</div>
							</div>
						</TabsContent>

						<TabsContent value="explain">
							{explainSearch.data ? (
								<div className="space-y-6">
									<Card>
										<CardHeader>
											<CardTitle>Algorithm Explanation</CardTitle>
										</CardHeader>
										<CardContent>
											<div className="space-y-4">
												{explainSearch.data.data.algorithm_steps.map(
													(step, index) => (
														<div
															key={index}
															className="flex items-start space-x-3"
														>
															<Badge variant="secondary">{index + 1}</Badge>
															<p className="text-sm text-gray-700">{step}</p>
														</div>
													),
												)}
											</div>
										</CardContent>
									</Card>

									<Card>
										<CardHeader>
											<CardTitle>Scoring Breakdown</CardTitle>
										</CardHeader>
										<CardContent>
											<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
												<div className="p-3 bg-blue-50 rounded-lg">
													<h4 className="font-medium text-blue-900">
														Similarity Score
													</h4>
													<p className="text-sm text-blue-700">
														{
															explainSearch.data.data.scoring_explanation
																.similarity_score
														}
													</p>
												</div>
												<div className="p-3 bg-purple-50 rounded-lg">
													<h4 className="font-medium text-purple-900">
														PersonRank Score
													</h4>
													<p className="text-sm text-purple-700">
														{
															explainSearch.data.data.scoring_explanation
																.personrank_score
														}
													</p>
												</div>
												<div className="p-3 bg-green-50 rounded-lg">
													<h4 className="font-medium text-green-900">
														Final Score
													</h4>
													<p className="text-sm text-green-700">
														{
															explainSearch.data.data.scoring_explanation
																.final_score
														}
													</p>
												</div>
											</div>
										</CardContent>
									</Card>
								</div>
							) : (
								<div className="text-center py-12">
									<p className="text-gray-500">
										Click "Explain Results" to see algorithm details
									</p>
								</div>
							)}
						</TabsContent>
					</Tabs>
				)}

				{/* Search History */}
				{searchHistory.length > 0 && (
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center space-x-2">
								<RefreshCw className="h-5 w-5 text-gray-600" />
								<span>Recent Searches</span>
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="flex flex-wrap gap-2">
								{searchHistory.map((historyQuery, index) => (
									<Badge
										key={index}
										variant="outline"
										className="cursor-pointer hover:bg-gray-50"
										onClick={() => setQuery(historyQuery)}
									>
										{historyQuery}
									</Badge>
								))}
							</div>
						</CardContent>
					</Card>
				)}

				{/* Subgraph View */}
				{subgraphData.data && currentView === "graph" && (
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center space-x-2">
								<Network className="h-5 w-5 text-purple-600" />
								<span>Knowledge Graph Context</span>
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
								<div className="text-center p-4 bg-purple-50 rounded-lg">
									<div className="text-3xl font-bold text-purple-600">
										{subgraphData.data.data.subgraph_context.node_count}
									</div>
									<div className="text-sm text-gray-600">Nodes in Subgraph</div>
								</div>
								<div className="text-center p-4 bg-blue-50 rounded-lg">
									<div className="text-3xl font-bold text-blue-600">
										{subgraphData.data.data.subgraph_context.edge_count}
									</div>
									<div className="text-sm text-gray-600">Relationships</div>
								</div>
							</div>

							{/* Node List */}
							<div className="space-y-4">
								<h4 className="font-medium text-gray-900">
									Key Entities in Context
								</h4>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
									{subgraphData.data.data.subgraph_context.nodes
										.filter((node) => node.is_top_entity)
										.map((node) => (
											<div
												key={node.id}
												className="p-3 border rounded-lg bg-white"
											>
												<div className="flex items-center justify-between">
													<div>
														<h5 className="font-medium text-gray-900">
															{node.text}
														</h5>
														<p className="text-sm text-gray-600">{node.type}</p>
													</div>
													<Badge variant="secondary">
														{Object.keys(node.properties).length} props
													</Badge>
												</div>
											</div>
										))}
								</div>
							</div>
							<div className="mt-6 mx-auto">
								<D3GraphVisualization
									data={{
										nodes: subgraphData.data.data.subgraph_context.nodes,
										edges: subgraphData.data.data.subgraph_context.edges,
									}}
									width={Math.min(window.innerWidth - 400, 1300)}
									height={Math.min(window.innerHeight - 200, 800)}
								/>
							</div>
						</CardContent>
					</Card>
				)}

				{/* Loading State */}
				{(aiSearchMutation.isPending ||
					explainSearch.isLoading ||
					subgraphData.isLoading) && (
					<div className="text-center py-12">
						<div className="inline-flex items-center space-x-2">
							<Loader2 size={20} className="animate-spin" />
							<span>
								{aiSearchMutation.isPending &&
									"Đang phân tích đồ thị tri thức bằng AI..."}
								{explainSearch.isLoading && "Đang phân tích thuật toán..."}
								{subgraphData.isLoading && "Đang trích xuất đồ thị con..."}
							</span>
						</div>
					</div>
				)}

				{/* Empty State */}
				{!aiSearchMutation.isPending &&
					!aiSearchMutation.error &&
					!aiSearchMutation.data && (
						<div className="text-center py-12">
							<Sparkles size={48} className="mx-auto text-gray-400 mb-4" />
							<h3 className="text-lg font-medium text-gray-900 mb-2">
								Sẵn sàng tìm kiếm với AI
							</h3>
							<p className="text-gray-600">
								Nhập câu hỏi của bạn để bắt đầu phân tích đồ thị tri thức.
							</p>

							{/* Quick tips */}
							<div className="mt-6 max-w-2xl mx-auto">
								<div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
									<div className="p-3 bg-blue-50 rounded-lg">
										<h4 className="font-medium text-blue-900 mb-1">
											💡 Tips for better results
										</h4>
										<p className="text-blue-700">
											Use specific keywords and entity names in your queries
										</p>
									</div>
									<div className="p-3 bg-green-50 rounded-lg">
										<h4 className="font-medium text-green-900 mb-1">
											🔍 Search features
										</h4>
										<p className="text-green-700">
											AI answers, graph analysis, and relationship discovery
										</p>
									</div>
								</div>
							</div>
						</div>
					)}
			</div>
		</div>
	);
};

export default SimpleAISearchPage;
