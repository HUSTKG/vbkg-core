import { useState } from "react";
import { AlertTriangle, Eye, Zap, Search, Activity, Clock, CheckCircle, ArrowUp } from "lucide-react";
import {
	useAutoResolveConflict,
	useConflicts,
	useDetectConflicts,
	useResolveConflict,
} from "@vbkg/api-client";
import { Conflict, ConflictStatus, ConflictType } from "@vbkg/types";
import {
	Input,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	StatisticCard,
	toast,
} from "@/components";
import { ConflictTypeIcon } from "./components/ConflictTypeIcon";
import { StatusBadge } from "@/components/StatusBadge";
import { SeverityBadge } from "@/components/SeverityBadge";
import ConflictDetailsDialog from "./components/ConflictDetailsDialog";
import ManualResolutionDialog from "./components/ManualResolutionDialog";

const ConflictsPage = () => {
	const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(
		null,
	);
	const [showDetails, setShowDetails] = useState(false);

	// Filters
	const [statusFilter, setStatusFilter] = useState("all");
	const [severityFilter, setSeverityFilter] = useState("all");
	const [typeFilter, setTypeFilter] = useState("all");
	const [searchTerm, setSearchTerm] = useState("");
	const [showManualResolution, setShowManualResolution] = useState(false);

	const { data: conflictsResponse } = useConflicts({
		limit: 50,
		severity: severityFilter !== "all" ? (severityFilter as string) : undefined,
		status:
			statusFilter !== "all" ? (statusFilter as ConflictStatus) : undefined,
		conflict_type:
			typeFilter !== "all" ? (typeFilter as ConflictType) : undefined,
	});

	const conflicts = conflictsResponse?.data;

	const { mutate: detectConflict, isPending: isDetecting } =
		useDetectConflicts();
	const { mutate: resolveConflict } = useResolveConflict();
	const { mutate: autoResolveConflict } = useAutoResolveConflict();

	const handleDetectConflicts = async () => {
		detectConflict({});
	};

	const handleManualResolve = (conflictId: string) => {
		const conflict = conflicts?.find((c) => c.id === conflictId);
		setSelectedConflict(conflict);
		setShowManualResolution(true);
	};

	const handleViewDetails = (conflict: Conflict) => {
		setSelectedConflict(conflict);
		setShowDetails(true);
	};

	const handleAutoResolve = async (conflictId: any) => {
		autoResolveConflict({ conflict_id: conflictId, confidence_threshold: 0.8 });
		setShowDetails(false);
	};

	const handleApplySuggestion = async (conflictId: string, suggestion: any) => {
		// Apply specific AI suggestion
		try {
			resolveConflict({
				conflict_id: conflictId,
				resolution_method: suggestion.resolution_method,
				reasoning: suggestion.reasoning || "auto resolution",
				confidence_score: suggestion.confidence_score,
				resolution_data: {sugesstions: suggestion.specific_actions},
			});
			setShowDetails(false);
			toast.success("Đã áp dụng gợi ý AI thành công!");
		} catch (error) {
			toast.error("Có lỗi xảy ra khi áp dụng gợi ý AI");
		}
	};

	const getStatusStats = () => {
		const resolved = conflicts?.filter((c) => c.status.includes("resolved")).length || 0;
		const stats = {
			total: conflictsResponse?.meta.total || 0,
			detected: conflicts?.filter((c) => c.status === "detected").length || 0,
			under_review:
				conflicts?.filter((c) => c.status === "under_review").length || 0,
			resolved: resolved,
			escalated: conflicts?.filter((c) => c.status === "escalated").length || 0,
		};
		return stats;
	};

	const getSeverityStats = () => {
		return {
			critical: conflicts?.filter((c) => c.severity === "critical").length || 0,
			high: conflicts?.filter((c) => c.severity === "high").length || 0,
			medium: conflicts?.filter((c) => c.severity === "medium").length || 0,
			low: conflicts?.filter((c) => c.severity === "low").length || 0,
		};
	};

	const stats = getStatusStats();
	const severityStats = getSeverityStats();

	// Filter conflicts based on search term
	const filteredConflicts = conflicts?.filter((conflict) => {
		if (!searchTerm) return true;
		const searchLower = searchTerm.toLowerCase();
		return (
			conflict.id.toLowerCase().includes(searchLower) ||
			conflict.description.toLowerCase().includes(searchLower) ||
			conflict.context_data?.entity1_text
				?.toLowerCase()
				.includes(searchLower) ||
			conflict.context_data?.entity2_text?.toLowerCase().includes(searchLower)
		);
	});

	// Calculate resolution rate
	const resolutionRate = stats.total > 0 ? Math.round((stats.resolved / stats.total) * 100) : 0;

	return (
		<div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
			<div className="max-w-7xl mx-auto">
				{/* Header */}
				<div className="mb-8">
					<div className="flex justify-between items-start">
						<div>
							<h1 className="text-3xl font-bold text-gray-900 dark:text-white">
								Quản lý xung đột
							</h1>
							<p className="text-gray-600 dark:text-gray-400 mt-2">
								Phát hiện và giải quyết các xung đột trong Knowledge Graph
							</p>
						</div>
						{/* <button */}
						{/* 	onClick={handleDetectConflicts} */}
						{/* 	disabled={isDetecting} */}
						{/* 	className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2" */}
						{/* > */}
						{/* 	<Search size={16} /> */}
						{/* 	<span>{isDetecting ? "Đang phát hiện..." : "Phát hiện xung đột"}</span> */}
						{/* </button> */}
					</div>
				</div>

				{/* Statistics Cards */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
					<StatisticCard
						title="Tổng số xung đột"
						value={stats.total}
						icon={<Activity size={20} />}
						color="blue"
						description="Tổng số xung đột trong hệ thống"
						onClick={() => setStatusFilter("all")}
					/>
					
					<StatisticCard
						title="Cần xử lý"
						value={stats.detected}
						icon={<AlertTriangle size={20} />}
						color="yellow"
						description="Xung đột mới phát hiện"
						onClick={() => setStatusFilter("detected")}
					/>
					
					<StatisticCard
						title="Đang xem xét"
						value={stats.under_review}
						icon={<Clock size={20} />}
						color="orange"
						description="Đang được xem xét và phân tích"
						onClick={() => setStatusFilter("under_review")}
					/>
					
					<StatisticCard
						title="Đã giải quyết"
						value={stats.resolved}
						icon={<CheckCircle size={20} />}
						color="green"
						trend={{
							value: resolutionRate,
							isPositive: resolutionRate > 80
						}}
						description={`Tỷ lệ giải quyết: ${resolutionRate}%`}
						onClick={() => setStatusFilter("resolved_manual")}
					/>
				</div>

				{/* Severity Statistics */}
				<div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
					<StatisticCard
						title="Nghiêm trọng"
						value={severityStats.critical}
						icon={<ArrowUp size={20} />}
						color="red"
						description="Cần xử lý ngay lập tức"
						onClick={() => setSeverityFilter("critical")}
					/>
					
					<StatisticCard
						title="Mức cao"
						value={severityStats.high}
						icon={<ArrowUp size={20} />}
						color="orange"
						description="Ưu tiên cao"
						onClick={() => setSeverityFilter("high")}
					/>
					
					<StatisticCard
						title="Mức trung bình"
						value={severityStats.medium}
						icon={<ArrowUp size={20} />}
						color="yellow"
						description="Ưu tiên trung bình"
						onClick={() => setSeverityFilter("medium")}
					/>
					
					<StatisticCard
						title="Mức thấp"
						value={severityStats.low}
						icon={<ArrowUp size={20} />}
						color="teal"
						description="Có thể xử lý sau"
						onClick={() => setSeverityFilter("low")}
					/>
				</div>

				{/* Filters */}
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
					<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
						<div>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Tìm kiếm
							</label>
							<div className="relative">
								<Input
									type="text"
									placeholder="Tìm theo ID, mô tả hoặc entity..."
									value={searchTerm}
									onChange={(e) => setSearchTerm(e.target.value)}
									className="pl-10 w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white"
								/>
								<Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
							</div>
						</div>
						<div>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Trạng thái
							</label>
							<Select
								value={statusFilter}
								onValueChange={(value: string) => setStatusFilter(value)}
							>
								<SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
									{statusFilter === "all" ? "Tất cả trạng thái" : 
									 statusFilter === "detected" ? "Phát hiện" :
									 statusFilter === "under_review" ? "Đang xem xét" :
									 statusFilter === "resolved_manual" ? "Đã giải quyết" :
									 statusFilter === "escalated" ? "Đã báo cáo" : "Chọn trạng thái"}
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Tất cả trạng thái</SelectItem>
									<SelectItem value="detected">Phát hiện</SelectItem>
									<SelectItem value="under_review">Đang xem xét</SelectItem>
									<SelectItem value="resolved_manual">Đã giải quyết</SelectItem>
									<SelectItem value="escalated">Đã báo cáo</SelectItem>
								</SelectContent>
							</Select>
						</div>
						<div>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Độ nghiêm trọng
							</label>
							<Select
								value={severityFilter}
								onValueChange={(value) => setSeverityFilter(value)}
							>
								<SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
									{severityFilter === "all" ? "Tất cả mức độ" :
									 severityFilter === "critical" ? "Nghiêm trọng" :
									 severityFilter === "high" ? "Cao" :
									 severityFilter === "medium" ? "Trung bình" :
									 severityFilter === "low" ? "Thấp" : "Chọn độ nghiêm trọng"}
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Tất cả mức độ</SelectItem>
									<SelectItem value="critical">Nghiêm trọng</SelectItem>
									<SelectItem value="high">Cao</SelectItem>
									<SelectItem value="medium">Trung bình</SelectItem>
									<SelectItem value="low">Thấp</SelectItem>
								</SelectContent>
							</Select>
						</div>
						<div>
							<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Loại xung đột
							</label>
							<Select
								value={typeFilter}
								onValueChange={(e) => setTypeFilter(e)}
							>
								<SelectTrigger className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 text-gray-900 dark:text-white">
									{typeFilter === "all" ? "Tất cả loại" : "Chọn loại xung đột"}
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">Tất cả</SelectItem>
									<SelectItem value="duplicate_entity">
										Entity trùng lặp
									</SelectItem>
									<SelectItem value="attribute_mismatch">
										Thuộc tính không khớp
									</SelectItem>
									<SelectItem value="contradictory_relationship">
										Quan hệ mâu thuẫn
									</SelectItem>
									<SelectItem value="temporal_conflict">
										Xung đột về thời gian
									</SelectItem>
								</SelectContent>
							</Select>
						</div>
					</div>
				</div>

				{/* Conflicts List */}
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
					<div className="p-6 border-b border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-medium text-gray-900 dark:text-white">
							Danh sách xung đột ({filteredConflicts?.length || 0})
						</h3>
					</div>

					{!filteredConflicts || filteredConflicts.length === 0 ? (
						<div className="p-12 text-center">
							<AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
							<h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
								Không có xung đột nào
							</h3>
							<p className="text-gray-500 dark:text-gray-400">
								{searchTerm ||
								statusFilter !== "all" ||
								severityFilter !== "all" ||
								typeFilter !== "all"
									? "Không tìm thấy xung đột nào phù hợp với bộ lọc."
									: "Chưa phát hiện xung đột nào trong hệ thống."}
							</p>
						</div>
					) : (
						<div className="divide-y divide-gray-200 dark:divide-gray-700">
							{filteredConflicts?.map((conflict) => (
								<div
									key={conflict.id}
									className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50"
								>
									<div className="flex items-start justify-between">
										<div className="flex-1">
											<div className="flex items-center space-x-3 mb-2">
												<ConflictTypeIcon type={conflict.conflict_type} />
												<h4 className="text-sm font-medium text-gray-900 dark:text-white">
													{conflict.description}
												</h4>
												<StatusBadge status={conflict.status} />
												<SeverityBadge severity={conflict.severity} />
											</div>

											{/* Entity information */}
											{conflict.context_data && (
												<div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400 mb-2">
													<span className="bg-blue-100 dark:bg-blue-900/30 px-2 py-1 rounded">
														{conflict.context_data.entity1_text}
													</span>
													<span>vs</span>
													<span className="bg-orange-100 dark:bg-orange-900/30 px-2 py-1 rounded">
														{conflict.context_data.entity2_text}
													</span>
												</div>
											)}

											<div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
												<span>ID: {conflict.id.slice(0, 8)}...</span>
												<span>
													Độ tin cậy:{" "}
													{Math.round(conflict.confidence_score * 100)}%
												</span>
												<span>
													Phát hiện:{" "}
													{new Date(conflict.detected_at).toLocaleDateString()}
												</span>
												{conflict.assigned_to && (
													<span>Được giao cho: {conflict.assigned_to}</span>
												)}
												{conflict.auto_resolution_suggestions && (
													<span className="text-blue-600 dark:text-blue-400">
														{conflict.auto_resolution_suggestions.length} gợi ý
														AI
													</span>
												)}
											</div>
										</div>

										<div className="flex items-center space-x-2 ml-4">
											<button
												onClick={() => handleViewDetails(conflict)}
												className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-600"
												title="Xem chi tiết"
											>
												<Eye size={16} />
											</button>
											{conflict.status === "detected" && (
												<button
													onClick={() => handleAutoResolve(conflict.id)}
													className="p-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30"
													title="Tự động giải quyết"
												>
													<Zap size={16} />
												</button>
											)}
										</div>
									</div>
								</div>
							))}
						</div>
					)}
				</div>

				{/* Details Modal */}
				<ConflictDetailsDialog
					conflict={selectedConflict}
					isOpen={showDetails}
					onOpenChange={() => setShowDetails(false)}
					onResolve={handleManualResolve}
					onAutoResolve={handleAutoResolve}
					onApplySuggestion={handleApplySuggestion}
				/>
				{/* Manual Resolution Dialog */}
				<ManualResolutionDialog
					conflict={selectedConflict}
					isOpen={showManualResolution}
					onOpenChange={() => setShowManualResolution(false)}
				/>
			</div>
		</div>
	);
};

export default ConflictsPage;
