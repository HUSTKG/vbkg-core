import { useState } from "react";
import {
	BarChart3,
	TrendingUp,
	AlertTriangle,
	CheckCircle,
	Database,
	RefreshCw,
	Play,
	Eye,
	Activity,
	Zap,
	Shield,
	Target,
	Clock,
	ArrowUpRight,
	ArrowDownRight,
	Minus,
} from "lucide-react";
import {
	ActivityStatus,
	RecentActivityItem,
	StatisticCard,
	toast,
} from "@/components";
import { useQualityDashboard, useRunQualityMonitoring } from "@vbkg/api-client";
import QualityMetricBar from "./components/QualityMetricBar";


const QualityDashboard = () => {
	const [loading, setLoading] = useState(false);
	const [refreshing, setRefreshing] = useState(false);

	const {
		data: dashboardResponse,
		isLoading,
		error,
		refetch,
	} = useQualityDashboard({});
	const dashboard = dashboardResponse?.data;

	const runQualityMonitoring = useRunQualityMonitoring({
		onSuccess: () => {
			toast.loading("Đã bắt đầu chạy!", {
				duration: 1000,
			});
		},
		onError: (error) => {
			toast.error(`Có lỗi xảy ra khi chạy kiểm tra: ${error.message}`);
		},
	});

	const handleRefresh = async () => {
		setRefreshing(true);
		refetch();
		setRefreshing(false);
	};

	const handleRunMonitoring = async () => {
		setLoading(true);
		runQualityMonitoring.mutate({});
		setLoading(false);
	};

	if (isLoading) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
					<p className="text-gray-600 dark:text-gray-400">
						Đang tải dữ liệu...
					</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
				<div className="text-center">
					<AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
					<p className="text-red-600 dark:text-red-400">
						Có lỗi xảy ra khi tải dữ liệu
					</p>
				</div>
			</div>
		);
	}

	const qualityScore = dashboard?.quality_report?.overall_score || 0;

	const getScoreColor = (score: any) => {
		if (score >= 0.9) return "text-emerald-600 dark:text-emerald-400";
		if (score >= 0.7) return "text-blue-600 dark:text-blue-400";
		if (score >= 0.5) return "text-yellow-600 dark:text-yellow-400";
		return "text-red-600 dark:text-red-400";
	};

	const getTrendIcon = (trend: any) => {
		switch (trend) {
			case "improving":
				return <ArrowUpRight className="h-5 w-5 text-emerald-500" />;
			case "declining":
				return <ArrowDownRight className="h-5 w-5 text-red-500" />;
			default:
				return <Minus className="h-5 w-5 text-gray-500" />;
		}
	};

	const getTrendText = (trend: any) => {
		switch (trend) {
			case "improving":
				return "Đang cải thiện";
			case "declining":
				return "Đang giảm";
			default:
				return "Ổn định";
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
			<div className="max-w-7xl mx-auto p-6">
				{/* Header */}
				<div className="mb-8">
					<div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
						<div>
							<h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
								Quality Dashboard
							</h1>
							<p className="text-gray-600 dark:text-gray-400 mt-2">
								Tổng quan về chất lượng dữ liệu Knowledge Graph
							</p>
						</div>
						<div className="flex flex-col sm:flex-row gap-3">
							<button
								onClick={handleRefresh}
								disabled={refreshing}
								className="flex items-center justify-center px-6 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-all duration-200 hover:shadow-md group"
							>
								<RefreshCw
									className={`h-5 w-5 mr-2 transition-transform duration-300 ${refreshing ? "animate-spin" : "group-hover:rotate-45"}`}
								/>
								{refreshing ? "Đang tải..." : "Làm mới"}
							</button>
							<button
								onClick={handleRunMonitoring}
								disabled={loading}
								className="flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 transition-all duration-200 hover:shadow-lg transform hover:scale-105"
							>
								<Play className="h-5 w-5 mr-2" />
								{loading ? "Đang chạy..." : "Chạy kiểm tra"}
							</button>
						</div>
					</div>
				</div>

				{/* Overall Quality Score */}
				<div className="mb-8">
					<div className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700 p-8 relative overflow-hidden">
						<div className="absolute inset-0 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/10 dark:to-purple-900/10 opacity-50" />
						<div className="relative text-center">
							<h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
								Điểm chất lượng tổng thể
							</h2>
							<div className="flex items-center justify-center space-x-4 mb-4">
								<div
									className={`text-7xl font-bold ${getScoreColor(qualityScore)} transition-all duration-300`}
								>
									{Math.round(qualityScore * 100)}
								</div>
								<div className="text-2xl text-gray-400">/ 100</div>
							</div>
							<div className="flex items-center justify-center space-x-2">
								{getTrendIcon(dashboard?.trending_metrics?.trend)}
								<span className="text-gray-600 dark:text-gray-400 font-medium">
									{getTrendText(dashboard?.trending_metrics?.trend)}
								</span>
							</div>
						</div>
					</div>
				</div>

				{/* Key Statistics */}
				<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
					<StatisticCard
						title="Tổng số Entities"
						value={
							dashboard?.quality_report?.total_entities?.toLocaleString() || "0"
						}
						icon={<Database size={20} />}
						color="blue"
					/>
					<StatisticCard
						title="Tổng số Relationships"
						value={
							dashboard?.quality_report?.total_relationships?.toLocaleString() ||
							"0"
						}
						icon={<BarChart3 size={20} />}
						color="green"
					/>
					<StatisticCard
						title="Xung đột chờ xử lý"
						value={dashboard?.quality_report?.conflicts_pending || 0}
						icon={<AlertTriangle size={20} />}
						color="yellow"
						description="Cần được giải quyết"
					/>
					<StatisticCard
						title="Vấn đề phát hiện"
						value={dashboard?.quality_report?.issues_detected || 0}
						icon={<Eye size={20} />}
						color="red"
						description="Tổng số vấn đề"
					/>
				</div>

				<div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
					{/* Quality Dimensions */}
					<div className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
						<div className="flex items-center space-x-3 mb-8">
							<div className="p-2 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl">
								<Target className="h-6 w-6 text-white" />
							</div>
							<h3 className="text-xl font-semibold text-gray-900 dark:text-white">
								Chất lượng theo tiêu chí 
							</h3>
						</div>
						<div className="space-y-6">
							<QualityMetricBar
								label="Completeness (Tính đầy đủ)"
								score={
									dashboard?.quality_report?.dimension_scores?.completeness || 0
								}
							/>
							<QualityMetricBar
								label="Accuracy (Tính chính xác)"
								score={
									dashboard?.quality_report?.dimension_scores?.accuracy || 0
								}
							/>
							<QualityMetricBar
								label="Consistency (Tính nhất quán)"
								score={
									dashboard?.quality_report?.dimension_scores?.consistency || 0
								}
							/>
							<QualityMetricBar
								label="Validity (Tính hợp lệ)"
								score={
									dashboard?.quality_report?.dimension_scores?.validity || 0
								}
							/>
							<QualityMetricBar
								label="Uniqueness (Tính duy nhất)"
								score={
									dashboard?.quality_report?.dimension_scores?.uniqueness || 0
								}
							/>
							<QualityMetricBar
								label="Timeliness (Tính kịp thời)"
								score={
									dashboard?.quality_report?.dimension_scores?.timeliness || 0
								}
							/>
						</div>
					</div>

					{/* Conflict Statistics */}
					<div className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
						<div className="flex items-center space-x-3 mb-8">
							<div className="p-2 bg-gradient-to-r from-red-500 to-red-600 rounded-xl">
								<Shield className="h-6 w-6 text-white" />
							</div>
							<h3 className="text-xl font-semibold text-gray-900 dark:text-white">
								Thống kê xung đột
							</h3>
						</div>

						<div className="space-y-8">
							<div>
								<h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
									<Activity className="h-4 w-4 mr-2" />
									Theo trạng thái
								</h4>
								<div className="space-y-3">
									{Object.entries(
										dashboard?.conflict_statistics?.by_status || {},
									).map(([status, count]) => (
										<div
											key={status}
											className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
										>
											<span className="text-sm text-gray-600 dark:text-gray-400 capitalize font-medium">
												{status.replace("_", " ")}
											</span>
											<span className="text-sm font-bold text-gray-900 dark:text-white bg-white dark:bg-gray-800 px-3 py-1 rounded-full">
												{count}
											</span>
										</div>
									))}
								</div>
							</div>

							<div>
								<h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center">
									<Zap className="h-4 w-4 mr-2" />
									Theo loại xung đột
								</h4>
								<div className="space-y-3">
									{Object.entries(
										dashboard?.conflict_statistics?.by_type || {},
									).map(([type, count]) => (
										<div
											key={type}
											className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl"
										>
											<span className="text-sm text-gray-600 dark:text-gray-400 capitalize font-medium">
												{type.replace("_", " ")}
											</span>
											<span className="text-sm font-bold text-gray-900 dark:text-white bg-white dark:bg-gray-800 px-3 py-1 rounded-full">
												{count}
											</span>
										</div>
									))}
								</div>
							</div>
						</div>
					</div>
				</div>

				<div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
					{/* Recent Activity */}
					<div className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
						<div className="flex justify-between items-center mb-8">
							<div className="flex items-center space-x-3">
								<div className="p-2 bg-gradient-to-r from-green-500 to-green-600 rounded-xl">
									<Clock className="h-6 w-6 text-white" />
								</div>
								<h3 className="text-xl font-semibold text-gray-900 dark:text-white">
									Hoạt động gần đây
								</h3>
							</div>
							<button className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium">
								Xem tất cả
							</button>
						</div>

						<div className="space-y-2">
							{dashboard?.recent_activity?.map((activity, index) => (
								<RecentActivityItem
									key={index}
									title={activity.description}
									time={activity.timestamp.toLocaleString()}
									description={`Bởi ${activity.user}`}
									status={activity.status as ActivityStatus}
									icon={
										activity.type === "conflict_resolution" ? (
											<CheckCircle size={16} />
										) : activity.type === "quality_monitoring" ? (
											<RefreshCw size={16} />
										) : (
											<Eye size={16} />
										)
									}
								/>
							))}
						</div>
					</div>

					{/* Improvement Recommendations */}
					<div className="bg-white dark:bg-gray-800 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
						<div className="flex items-center space-x-3 mb-8">
							<div className="p-2 bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-xl">
								<TrendingUp className="h-6 w-6 text-white" />
							</div>
							<h3 className="text-xl font-semibold text-gray-900 dark:text-white">
								Đề xuất cải thiện
							</h3>
						</div>

						<div className="space-y-4 mb-8">
							{dashboard?.quality_report?.improvement_recommendations?.map(
								(recommendation, index) => (
									<div
										key={index}
										className="flex items-start space-x-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/30"
									>
										<div className="flex-shrink-0 mt-1">
											<TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
										</div>
										<p className="text-sm text-gray-700 dark:text-gray-300 font-medium leading-relaxed">
											{recommendation}
										</p>
									</div>
								),
							)}
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default QualityDashboard;
