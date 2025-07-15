import { useState } from "react";
import {
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	Input,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components";
import {
	ArrowRight,
	Database,
	ExternalLink,
	Link,
	Network,
	SearchCheck,
} from "lucide-react";
import { useKGEntitiesSearch, useKGSubgraph } from "@vbkg/api-client";
import { useSearchParams } from "react-router";
import SearchSelect, { Option } from "@/components/search-select";
import { D3GraphVisualization } from "@/pages/user/visualization/components/D3GraphVisualization";
import { GraphLayoutType } from "@vbkg/types";

export default function KnowledgeGraphExplorer() {
	const [searchParams, setSearchParams] = useSearchParams();
	const entityId = searchParams.get("entity_id") || "";
	const selectedRadius = searchParams.get("radius") || "2";
	const [radius, setRadius] = useState(selectedRadius);
	const [searchQuery, setSearchQuery] = useState<string>("");
	const [searchOptions, setSearchOptions] = useState<Option[]>([]);
	const { data: entities, isFetching: loadEntities } = useKGEntitiesSearch({
		limit: 10,
		query: searchQuery,
	});

	const { data: graphData, isFetching: loading } =
		useKGSubgraph({
			entity_id: entityId,
			radius: selectedRadius ? parseInt(selectedRadius) : 2,
		}) || {};

	const setEntityId = (id: string) => {
		if (id) {
			setSearchParams({
				entity_id: id,
				radius: radius.toString(),
			});
		}
	};

	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div>
					<h1 className="text-3xl font-bold">🔍 Knowledge Graph Explorer</h1>
				</div>
			</div>

			{/* Search and Controls */}
			<Card className="overflow-visible">
				<CardHeader>
					<CardTitle>
						<Network size={20} className="inline-block mr-2" />
						Khám Phá Knowledge Graph
					</CardTitle>
					<CardDescription>
						Sử dụng công cụ này để khám phá các thực thể và mối quan hệ trong
						Knowledge Graph của bạn. Bạn có thể tìm kiếm thực thể, đặt bán kính
						khám phá và xem trực quan hóa đồ thị.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="flex flex-wrap items-end gap-4">
						<div className="grow">
							<label className="text-sm font-medium">Tìm kiếm Thực thể</label>
							<div className="relative mt-1">
								<SearchSelect
									value={searchOptions}
									onSearchChange={(term) => setSearchQuery(term)}
									searchTerm={searchQuery}
									loading={loadEntities}
									onChange={(value) => {
										setSearchOptions(value as Option[]);
										setEntityId((value as Option).value);
									}}
									options={entities?.data?.map((e) => ({
										label: e.entity_text,
										value: e.id,
									}))}
								/>
							</div>
						</div>
						<div className="grow">
							<label className="text-sm font-medium">
								ID Thực thể trung tâm
							</label>
							<Input
								value={entityId}
								onChange={(e) => setEntityId(e.target.value)}
								placeholder="ID thực thể..."
								className="mt-1"
							/>
						</div>
						<div className="shrink-0">
							<label className="text-sm font-medium">Phạm vi</label>
							<Select
								value={radius.toString()}
								onValueChange={(val) => setRadius(val)}
							>
								<SelectTrigger className="mt-1">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="1">1 hop </SelectItem>
									<SelectItem value="2">2 hops</SelectItem>
									<SelectItem value="3">3 hops</SelectItem>
									<SelectItem value="4">4 hops</SelectItem>
									<SelectItem value="5">5 hops</SelectItem>
								</SelectContent>
							</Select>
						</div>
						<div className="flex items-end shrink-0 grow-0 w-40 ml-auto">
							<Button
								onClick={() =>
									setSearchParams({
										entity_id: entityId,
										radius: radius.toString(),
									})
								}
								className="w-full"
							>
								<SearchCheck size={16} className="mr-2" />
								Khám phá
							</Button>
						</div>
					</div>
				</CardContent>
			</Card>

			{loading && (
				<div className="flex items-center justify-center h-64">
					<p className="text-muted-foreground">Đang tải dữ liệu...</p>
				</div>
			)}
			{!entityId && !loading && (
				<div className="flex items-center justify-center h-64">
					<p className="text-muted-foreground">
						Vui lòng chọn một thực thể để xem đồ thị.
					</p>
				</div>
			)}
			{!loading && graphData && (
				<Card>
					<CardHeader>
						<div className="flex items-center justify-between">
							<div>
								<CardTitle className="flex items-center gap-2">
									<Network size={20} />
									Đồ thị trực quan
								</CardTitle>
								{graphData && (
									<CardDescription>
										Hiển thị {graphData.node_count} đỉnh and{" "}
										{graphData.edge_count} cạnh
									</CardDescription>
								)}
							</div>
						</div>
					</CardHeader>
					<CardContent>
						<D3GraphVisualization
							data={{
								nodes: graphData?.nodes || [],
								edges: graphData?.edges || [],
							}}
							centralNodeId={entityId}
							width={1150}
							height={700}
							config={{
								zoom_enabled: true,
								pan_enabled: true,
								clustering_enabled: true,
								physics_enabled: true,
								interactive: true,
								max_nodes: 10,
								height: 500,

								node_config: {
									default_color: "#4f46e5",
									size_range: [5, 15],
									label_field: "entity_text",
								},
								edge_config: {
									default_color: "#9ca3af",
									width_range: [0.1, 0.3],
									label_field: "relationship_type",
								},
								layout: {
									type: GraphLayoutType.FORCE,
									params: {
										gravity: 0.1,
										charge: -100,
										link_distance: 50,
										link_strength: 0.1,
									},
								},
								show_labels: true,
								show_tooltips: true,
							}}
							editable
						/>
					</CardContent>
				</Card>
			)}

			{/* Graph Information */}
			{graphData && (
				<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
					{/* Nodes Panel */}
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center gap-2">
								<Database size={20} />
								Thực thể ({graphData.node_count})
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="space-y-3 max-h-80 overflow-y-auto">
								{graphData.nodes.map((node: any) => (
									<div
										key={node.id}
										className={`flex items-center justify-between p-3 rounded border cursor-pointer hover:bg-muted/50 ${
											node.is_center ? "border-blue-500 bg-blue-50" : ""
										}`}
										onClick={() => setEntityId(node.id)}
									>
										<div>
											<div className="font-medium">{node.label}</div>
											<div className="flex items-center gap-2 mt-1">
												<Badge variant="outline" className="text-xs">
													{node.type}
												</Badge>
												{node.is_center && (
													<Badge variant="default" className="text-xs">
														Trung tâm
													</Badge>
												)}
											</div>
										</div>
										<Button size="sm">
											<ExternalLink size={14} />
										</Button>
									</div>
								))}
							</div>
						</CardContent>
					</Card>

					{/* Edges Panel */}
					<Card>
						<CardHeader>
							<CardTitle className="flex items-center gap-2">
								<Link size={20} />
								Mối quan hệ ({graphData.edge_count})
							</CardTitle>
						</CardHeader>
						<CardContent>
							<div className="space-y-3 max-h-80 overflow-y-auto">
								{graphData?.edges.map((edge: any) => (
									<div
										key={edge.id}
										className="p-3 rounded border hover:bg-muted/50"
									>
										<div className="flex items-center gap-2 mb-2">
											<Badge variant="secondary" className="text-xs">
												{edge.type}
											</Badge>
										</div>
										<div className="flex items-center gap-2 text-sm">
											<span className="font-medium">
												{edge.source_entity_text}
											</span>
											<ArrowRight
												size={14}
												className="text-muted-foreground shrink-0"
											/>
											<span className="font-medium">
												{edge.target_entity_text}
											</span>
										</div>
									</div>
								))}
							</div>
						</CardContent>
					</Card>
				</div>
			)}
		</div>
	);
}
