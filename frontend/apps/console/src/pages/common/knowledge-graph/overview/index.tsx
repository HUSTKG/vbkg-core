import { useKGStats } from "@vbkg/api-client";
import {
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	StatisticCard,
} from "@/components";
import { Database, GitBranch, Layers, Network, RefreshCw } from "lucide-react";

export default function KnowledgeGraphOverview() {
	const {
		data: _stats,
		isFetching: loading,
		refetch: refetchStats,
	} = useKGStats();

	const stats = _stats?.data || {};

	const entityTypes = stats?.entity_types?.sort((a, b) => b.count - a.count);
	const relationshipTypes = stats?.relationship_types?.sort(
		(a, b) => b.count - a.count,
	);
	return (
		<div className="p-6 space-y-6">
			{/* Header */}
			<div className="flex justify-between items-center">
				<div className="space-y-1">
					<h1 className="text-3xl font-bold">📊 Knowledge Graph Overview</h1>
					<p className="text-muted-foreground text-sm">
						{" "}
						Cập nhật lúc {new Date(stats?.last_updated || "").toLocaleString()}
					</p>
				</div>{" "}
				<div className="flex gap-2">
					<Button onClick={() => refetchStats()}>
						<RefreshCw size={16} className="mr-2" />
						Làm mới
					</Button>
				</div>
			</div>

			{/* Quick Stats */}
			<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
				<StatisticCard
					title="Tổng số thực thể"
					value={loading ? "..." : stats?.total_entities?.toLocaleString() || 0}
					icon={<Database size={20} />}
					color="blue"
					description="Thực thể"
					loading={loading}
				/>
				<StatisticCard
					title="Tổng số mối quan hệ"
					value={
						loading ? "..." : stats?.total_relationships?.toLocaleString() || 0
					}
					icon={<Network size={20} />}
					color="green"
					description="Mối quan hệ"
					loading={loading}
				/>
				<StatisticCard
					title="Trung bình"
					value={
						loading
							? "..."
							: stats?.avg_relationships_per_entity?.toLocaleString() || 0
					}
					icon={<Database size={20} />}
					color="blue"
					description="Mối quan hệ mỗi thực thể"
					loading={loading}
				/>
				<StatisticCard
					title="Thực thể mới"
					value={
						loading
							? "..."
							: stats?.recent_entities_count?.toLocaleString() || 0
					}
					icon={<Database size={20} />}
					color="blue"
					description="Thực thể mới được thêm gần đây"
					loading={loading}
				/>
			</div>

			{/* Main Content Grid */}
			<div className="grid grid-cols-2 gap-6">
				{/* Entity Types Distribution */}
				<Card className="lg:col-span-1 px-0 overflow-y-auto space-y-0 max-h-max">
					<CardHeader className="sticky px-6 top-0 bg-white/95">
						<CardTitle className="flex items-center gap-2">
							<Layers size={20} />
							Loại thực thể
						</CardTitle>
						<CardDescription>Phân bố theo loại thực thể</CardDescription>
					</CardHeader>
					<CardContent>
						{loading ? (
							<div className="space-y-3">
								{[1, 2, 3, 4, 5].map((i) => (
									<div key={i} className="flex justify-between items-center">
										<div className="h-4 bg-muted rounded w-24 animate-pulse" />
										<div className="h-4 bg-muted rounded w-12 animate-pulse" />
									</div>
								))}
							</div>
						) : (
							<div className="space-y-4">
								{entityTypes?.map((type, i) => (
									<div key={String(i)} className="space-y-2">
										<div className="flex justify-between items-center">
											<Badge variant="outline">{type.entity_type}</Badge>
											<span className="font-medium">
												{type.count.toLocaleString()}
											</span>
										</div>
										<div className="w-full bg-muted rounded-full h-2">
											<div
												className="bg-blue-500 h-2 rounded-full"
												style={{
													width: `${(type.count / Number(stats?.total_entities)) * 100}%`,
												}}
											/>
										</div>
									</div>
								))}
							</div>
						)}
					</CardContent>
				</Card>

				{/* Relationship Types Distribution */}
				<Card className="lg:col-span-1 px-0 overflow-y-auto space-y-0 max-h-max">
					<CardHeader className="sticky px-6 top-0 bg-white/95">
						<CardTitle className="flex items-center gap-2">
							<GitBranch size={20} />
							Loại mối quan hệ
						</CardTitle>
						<CardDescription>Phân bố theo loại mối quan hệ</CardDescription>
					</CardHeader>
					<CardContent>
						{loading ? (
							<div className="space-y-3">
								{[1, 2, 3, 4, 5].map((i) => (
									<div key={i} className="flex justify-between items-center">
										<div className="h-4 bg-muted rounded w-28 animate-pulse" />
										<div className="h-4 bg-muted rounded w-12 animate-pulse" />
									</div>
								))}
							</div>
						) : (
							<div className="space-y-4">
								{relationshipTypes?.map((type, i) => (
									<div key={String(i)} className="space-y-2">
										<div className="flex justify-between items-center">
											<Badge variant="secondary">
												{type.relationship_type}
											</Badge>
											<span className="font-medium">
												{type.count.toLocaleString()}
											</span>
										</div>
										<div className="w-full bg-muted rounded-full h-2">
											<div
												className="bg-green-500 h-2 rounded-full"
												style={{
													width: `${(type.count / stats.total_relationships) * 100}%`,
												}}
											/>
										</div>
									</div>
								))}
							</div>
						)}
					</CardContent>
				</Card>
			</div>
		</div>
	);
}
