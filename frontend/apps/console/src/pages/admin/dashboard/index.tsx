import { useState } from "react";
import {
	Users,
	Activity,
	RefreshCw,
	Server,
	Key,
	Shield,
	UserCheck,
	UserX,
	Edit,
	Trash2,
	Plus,
	AlertCircle,
	Play,
	Pause,
	Cpu,
	HardDrive,
	Zap,
} from "lucide-react";
import { Button, RecentActivityItem, StatisticCard } from "@/components";
import {
	useSystemStats,
	useUsers,
	useMyActivity,
	useCeleryDashboard,
} from "@vbkg/api-client";
import { PERMISSIONS } from "@vbkg/utils";
import { usePermissionUtils } from "../../../hooks/permission";
import { useNavigate } from "react-router";

const AdminDashboard = () => {
	const [refreshTime, setRefreshTime] = useState(new Date());
	const navigate = useNavigate();
	const { isAdmin, hasPermission } = usePermissionUtils();

	// Real data from API
	const {
		data: systemStats,
		isLoading: isStatsLoading,
		refetch: refetchStats,
	} = useSystemStats({
		enabled: isAdmin,
	});

	const { data: usersData, isLoading: isUsersLoading } = useUsers(
		{
			limit: 5,
		},
		{
			enabled: hasPermission(PERMISSIONS.USER_MANAGEMENT),
		},
	);

	const { data: recentActivity, isLoading: isActivityLoading } = useMyActivity({
		limit: 10,
	});

	const { data: celeryData } = useCeleryDashboard();

	const handleRefresh = async () => {
		await refetchStats();
		setRefreshTime(new Date());
	};

	const stats = systemStats?.data;
	const users = usersData?.data || [];
	const activities = recentActivity?.data || [];

	const { data: celeryWorker } = useCeleryDashboard();

	const workers = celeryWorker?.data?.workers || [];

	return (
		<div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
			{/* Header */}
			<div className="mb-8">
				<div className="flex justify-between items-center">
					<div>
						<h1 className="text-3xl font-bold text-gray-900 dark:text-white">
						Tổng quan
						</h1>
						<p className="text-gray-600 dark:text-gray-400 mt-1">
							Cập nhật lần cuối:{" "}
							{refreshTime.toLocaleTimeString()}
						</p>
					</div>
					<Button
						onClick={handleRefresh}
						disabled={isStatsLoading}
					>
						<RefreshCw
							size={16}
							className={isStatsLoading ? "animate-spin" : ""}
						/>
						Làm mới
					</Button>
				</div>
			</div>

			{/* Statistics Overview */}
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-6 gap-4 mb-8">
				<StatisticCard
					title="Tổng người dùng"
					value={stats?.total_users || 0}
					icon={<Users size={18} />}
					color="blue"
					description="Người dùng hệ thống"
					loading={isStatsLoading}
				/>
				<StatisticCard
					title="Admin"
					value={stats?.user_counts_by_role?.admin || 0}
					icon={<Shield size={18} />}
					color="purple"
					description="Quản trị viên"
					loading={isStatsLoading}
				/>
				<StatisticCard
					title="Chuyên gia"
					value={stats?.user_counts_by_role?.expert || 0}
					icon={<UserCheck size={18} />}
					color="green"
					description="Chuyên gia"
					loading={isStatsLoading}
				/>
				<StatisticCard
					title="API Keys"
					value={stats?.active_api_keys || 0}
					icon={<Key size={18} />}
					color="yellow"
					description="API Keys hoạt động"
					loading={isStatsLoading}
				/>
				<StatisticCard
					title="Celery Workers"
					value={
						celeryData?.data?.worker_stats
							? `${celeryData.data.worker_stats.online}/${celeryData.data.worker_stats.total}`
							: "0/0"
					}
					icon={<Server size={18} />}
					color="indigo"
					description="Online"
				/>
				<StatisticCard
					title="Hoạt động"
					value={stats?.recent_activity_count || 0}
					icon={<Activity size={18} />}
					color="red"
					description="Tuần qua"
					loading={isStatsLoading}
				/>
			</div>

			<div className="mb-8">
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow">
					<div className="p-4 border-b border-gray-200 dark:border-gray-700">
						<div className="flex justify-between items-center">
							<h3 className="text-lg font-semibold text-gray-900 dark:text-white">
								Celery Workers
							</h3>
						</div>
					</div>

					<div className="p-4">
						<div className="flex flex-wrap gap-4">
							{workers.map((worker) => (
								<div
									key={worker.name}
									className={`border rounded-lg min-w-[350px] flex-grow shrink-0 p-4 ${
										worker.status === "online"
											? "border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-900/20"
											: "border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-900/20"
									}`}
								>
									<div className="flex justify-between items-start mb-3">
										<div className="flex items-center gap-2">
											<div
												className={`w-3 animate-pulse h-3 rounded-full ${
													worker.status === "online"
														? "bg-green-500"
														: "bg-red-500"
												}`}
											/>
											<h4 className="font-medium text-gray-900 dark:text-white text-sm">
												{worker.name}
											</h4>
										</div>
										<div className="flex items-center gap-2">
											<span
												className={`px-2 py-1 text-xs rounded-full ${
													worker.status === "online"
														? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
														: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
												}`}
											>
												{worker.status}
											</span>
											{worker.status === "online" ? (
												<Play size={12} className="text-green-600" />
											) : (
												<Pause size={12} className="text-red-600" />
											)}
										</div>
									</div>

									{worker.status === "online" ? (
										<>
											{/* Task Info */}
											<div className="grid grid-cols-2 gap-4 mb-3">
												<div className="text-center p-2 bg-white dark:bg-gray-700 rounded border">
													<div className="text-lg font-semibold text-blue-600 dark:text-blue-400">
														{worker.active_tasks}
													</div>
													<div className="text-xs text-gray-600 dark:text-gray-400">
														Active Tasks
													</div>
												</div>
												<div className="text-center p-2 bg-white dark:bg-gray-700 rounded border">
													<div className="text-lg font-semibold text-green-600 dark:text-green-400">
														{worker.processed_tasks}
													</div>
													<div className="text-xs text-gray-600 dark:text-gray-400">
														Processed
													</div>
												</div>
											</div>

											{/* System Metrics */}
											<div className="space-y-2">
												<div className="flex items-center justify-between text-sm">
													<div className="flex items-center gap-2">
														<Cpu
															size={14}
															className="text-gray-600 dark:text-gray-400"
														/>
														<span className="text-gray-700 dark:text-gray-300">
															CPU
														</span>
													</div>
													<div className="flex items-center gap-2">
														<div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
															<div
																className="bg-blue-500 h-2 rounded-full"
																style={{
																	width: `${worker.system_info.cpu_usage}%`,
																}}
															></div>
														</div>
														<span className="text-xs w-12 text-right text-gray-600 dark:text-gray-400">
															{worker.system_info.cpu_usage}%
														</span>
													</div>
												</div>

												<div className="flex items-center justify-between text-sm">
													<div className="flex items-center gap-2">
														<HardDrive
															size={14}
															className="text-gray-600 dark:text-gray-400"
														/>
														<span className="text-gray-700 dark:text-gray-300">
															Memory
														</span>
													</div>
													<div className="flex items-center gap-2">
														<div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
															<div
																className="bg-green-500 h-2 rounded-full"
																style={{
																	width: `${worker.system_info.memory_usage}%`,
																}}
															></div>
														</div>
														<span className="text-xs w-12 text-right text-gray-600 dark:text-gray-400">
															{worker.system_info.memory_usage}%
														</span>
													</div>
												</div>

												<div className="flex items-center justify-between text-sm">
													<div className="flex items-center gap-2">
														<Zap
															size={14}
															className="text-gray-600 dark:text-gray-400"
														/>
														<span className="text-gray-700 dark:text-gray-300">
															Disk
														</span>
													</div>
													<div className="flex items-center gap-2">
														<div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
															<div
																className="bg-yellow-500 h-2 rounded-full"
																style={{
																	width: `${worker.system_info.disk_usage}%`,
																}}
															></div>
														</div>
														<span className="text-xs w-12 text-right text-gray-600 dark:text-gray-400">
															{worker.system_info.disk_usage}%
														</span>
													</div>
												</div>
											</div>

											{/* Additional Info */}
											<div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
												<div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
													<span>Load Avg: {worker.load_avg.join(", ")}</span>
													<span>Uptime: {worker.system_info.uptime}</span>
												</div>
												<div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
													Last heartbeat:{" "}
													{worker.heartbeat
														? Math.floor(
																(Date.now() -
																	new Date(worker.heartbeat)?.getTime()) /
																	1000,
															)
														: "N/A"}{" "}
													s ago
												</div>
											</div>
										</>
									) : (
										<div className="flex items-center justify-center py-8">
											<div className="text-center">
												<AlertCircle
													size={32}
													className="text-red-500 mx-auto mb-2"
												/>
												<p className="text-sm text-gray-600 dark:text-gray-400">
													Worker is offline
												</p>
												<p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
													Last seen:{" "}
													{worker.heartbeat
														? Math.floor(
																(Date.now() -
																	new Date(worker.heartbeat).getTime()) /
																	60000,
															)
														: "N/A"}{" "}
													m ago
												</p>
											</div>
										</div>
									)}
								</div>
							))}
						</div>
					</div>
				</div>
			</div>

			{/* Main Content Grid */}
			<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
				{/* Recent Users */}
				{hasPermission(PERMISSIONS.USER_MANAGEMENT) && (
					<div className="bg-white dark:bg-gray-800 rounded-lg shadow">
						<div className="p-4 border-b border-gray-200 dark:border-gray-700">
							<div className="flex justify-between items-center">
								<h3 className="text-lg font-semibold text-gray-900 dark:text-white">
									Recent Users
								</h3>
								<Button
									variant="outline"
									onClick={() => navigate("/admin/users")}
								>
									Xem tất cả
								</Button>
							</div>
						</div>
						<div className="p-4 overflow-y-auto">
							{isUsersLoading ? (
								<div className="space-y-3">
									{[...Array(5)].map((_, i) => (
										<div key={i} className="flex items-center space-x-3 p-2">
											<div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse"></div>
											<div className="flex-1">
												<div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
												<div className="h-3 bg-gray-200 rounded animate-pulse w-2/3"></div>
											</div>
										</div>
									))}
								</div>
							) : (
								<div className="space-y-3">
									{users.map((user) => (
										<div
											key={user.id}
											className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded"
										>
											<div className="flex items-center space-x-3">
												<div
													className={`w-2 h-2 rounded-full ${
														user.is_active ? "bg-green-500" : "bg-red-500"
													}`}
												/>
												<div>
													<p className="font-medium text-sm text-gray-900 dark:text-white">
														{user.full_name || user.email}
													</p>
													<p className="text-xs text-gray-500">
														{user.roles.join(", ")} •{" "}
														{user.department || "No department"}
													</p>
												</div>
											</div>
										</div>
									))}
								</div>
							)}
						</div>
					</div>
				)}

				{/* Recent Activity */}
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow">
					<div className="p-4 border-b border-gray-200 dark:border-gray-700">
						<h3 className="text-lg font-semibold text-gray-900 dark:text-white">
							My Recent Activity
						</h3>
					</div>
					<div className="p-4 max-h-80 overflow-y-auto overflow-x-hidden">
						{isActivityLoading ? (
							<div className="space-y-3">
								{[...Array(5)].map((_, i) => (
									<div key={i} className="flex items-start space-x-3 p-2">
										<div className="w-6 h-6 bg-gray-200 rounded-full animate-pulse"></div>
										<div className="flex-1">
											<div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
											<div className="h-3 bg-gray-200 rounded animate-pulse w-3/4"></div>
										</div>
									</div>
								))}
							</div>
						) : (
							<div className="space-y-3">
								{activities.map((activity) => {
									const getActivityIcon = () => {
										switch (activity.action) {
											case "create_entity":
											case "create_relationship":
												return <Plus size={12} />;
											case "update_entity":
											case "update_relationship":
												return <Edit size={12} />;
											case "delete_entity":
											case "delete_relationship":
												return <Trash2 size={12} />;
											case "login":
												return <UserCheck size={12} />;
											case "logout":
												return <UserX size={12} />;
											default:
												return <Activity size={12} />;
										}
									};

									const getActivityStatus = () => {
										if (activity.action.includes("delete")) return "error";
										if (activity.action.includes("create")) return "success";
										return "info";
									};

									return (
										<RecentActivityItem
											key={activity.id}
											title={activity.action.replace("_", " ").toUpperCase()}
											description={
												activity.resource_type
													? `${activity.resource_type} - ${activity.details ? JSON.stringify(activity.details).slice(0, 100) + "..." : "No details"}`
													: "System activity"
											}
											time={new Date(activity.created_at).toLocaleTimeString()}
											status={getActivityStatus()}
											icon={getActivityIcon()}
										/>
									);
								})}
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
};

export default AdminDashboard;
