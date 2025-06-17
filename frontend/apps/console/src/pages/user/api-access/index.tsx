import { useState, useMemo } from "react";
import {
	Activity,
	Users,
	Clock,
	TrendingUp,
	Database,
	Download,
	Plus,
	Key,
	Code,
	BarChart3,
	CheckCircle,
	X,
} from "lucide-react";
import { Button, StatisticCard } from "@/components";
import { APIKey, UserActivity } from "@vbkg/types";
import { ActivityTimeline } from "./components/ActivityTimeline";
import ActivityTable from "./components/ActivityTable";
import {
	getActivityColor,
	getActivityIcon,
	getActivityLabel,
} from "./components/utils";
import { useUserActivity, useUserAPIKeys } from "@vbkg/api-client";
import { ApiKeyCard } from "./components/APIKeyCard";
import CreateApiKeyDialog from "./components/CreateApiKeyDialog";

// User Activities Page Component
const UserActivitiesPage = () => {
	const { data: _activities } = useUserActivity({});
	const activities = _activities?.data || [];
	const [selectedActivity, setSelectedActivity] = useState<UserActivity | null>(
		null,
	);
	const [filters, setFilters] = useState({
		user: "",
		type: "",
		dateFrom: "",
		dateTo: "",
	});
	const [currentView, setCurrentView] = useState("timeline"); // 'timeline', 'table'

	// Statistics
	const stats = useMemo(() => {
		const now = new Date();
		const today = activities.filter((a) => {
			const activityDate = new Date(a.created_at);
			return activityDate.toDateString() === now.toDateString();
		}).length;

		const uniqueUsers = new Set(activities.map((a) => a.user_id)).size;
		const apiCalls = activities.filter((a) => a.action === "api_call").length;
		const entityOperations = activities.filter((a) =>
			["entity_create", "entity_update", "entity_delete"].includes(a.action),
		).length;

		return {
			todayActivities: today,
			uniqueUsers,
			apiCalls,
			entityOperations,
		};
	}, [activities]);

	// Handle export
	const handleExportActivities = () => {
		const exportData = {
			activities: activities,
			exported_at: new Date().toISOString(),
			total_count: activities.length,
		};

		const blob = new Blob([JSON.stringify(exportData, null, 2)], {
			type: "application/json",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `user-activities-${Date.now()}.json`;
		a.click();
		URL.revokeObjectURL(url);
	};

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<div className="bg-white border-b border-gray-200 p-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">
							User Activities
						</h1>
						<p className="text-gray-600 mt-1">
							Monitor and track user actions across the platform
						</p>
					</div>
					<div className="flex items-center space-x-3">
						<button
							onClick={() =>
								setCurrentView(
									currentView === "timeline" ? "table" : "timeline",
								)
							}
							className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
							title={
								currentView === "timeline" ? "Table View" : "Timeline View"
							}
						>
							{currentView === "timeline" ? (
								<BarChart3 size={20} />
							) : (
								<Activity size={20} />
							)}
						</button>
						<button
							onClick={handleExportActivities}
							className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
						>
							<Download size={16} />
							<span>Export</span>
						</button>
					</div>
				</div>
			</div>

			<div className="p-6 space-y-6">
				{/* Statistics Dashboard */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatisticCard
						title="Today's Activities"
						value={stats.todayActivities}
						icon={<Activity size={20} />}
						trend={{ value: 15, isPositive: true }}
						color="blue"
					/>
					<StatisticCard
						title="Active Users"
						value={stats.uniqueUsers}
						icon={<Users size={20} />}
						color="green"
					/>
					<StatisticCard
						title="API Calls"
						value={stats.apiCalls}
						icon={<Code size={20} />}
						trend={{ value: 8, isPositive: true }}
						color="orange"
					/>
					<StatisticCard
						title="Entity Operations"
						value={stats.entityOperations}
						icon={<Database size={20} />}
						color="purple"
					/>
				</div>

				{/* Filters */}
				<div className="bg-white rounded-lg border shadow-sm p-6">
					<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
						<div>
							<label className="block text-sm font-medium mb-2">User</label>
							<input
								type="text"
								placeholder="Filter by user..."
								value={filters.user}
								onChange={(e) =>
									setFilters((prev) => ({ ...prev, user: e.target.value }))
								}
								className="w-full h-10 px-3 border rounded-lg"
							/>
						</div>
						<div>
							<label className="block text-sm font-medium mb-2">
								Activity Type
							</label>
							<select
								value={filters.type}
								onChange={(e) =>
									setFilters((prev) => ({ ...prev, type: e.target.value }))
								}
								className="w-full h-10 px-3 border rounded-lg"
							>
								<option value="">All Types</option>
								<option value="user_login">User Login</option>
								<option value="entity_create">Entity Create</option>
								<option value="search_query">Search Query</option>
								<option value="api_call">API Call</option>
							</select>
						</div>
						<div>
							<label className="block text-sm font-medium mb-2">
								From Date
							</label>
							<input
								type="date"
								value={filters.dateFrom}
								onChange={(e) =>
									setFilters((prev) => ({ ...prev, dateFrom: e.target.value }))
								}
								className="w-full h-10 px-3 border rounded-lg"
							/>
						</div>
						<div>
							<label className="block text-sm font-medium mb-2">To Date</label>
							<input
								type="date"
								value={filters.dateTo}
								onChange={(e) =>
									setFilters((prev) => ({ ...prev, dateTo: e.target.value }))
								}
								className="w-full h-10 px-3 border rounded-lg"
							/>
						</div>
					</div>
				</div>

				{/* Activities Display */}
				{currentView === "timeline" ? (
					<div className="bg-white rounded-lg border shadow-sm">
						<div className="p-6 border-b">
							<h2 className="text-lg font-semibold">Activity Timeline</h2>
						</div>
						<div className="p-6">
							<ActivityTimeline
								activities={activities}
								onActivityClick={setSelectedActivity}
							/>
						</div>
					</div>
				) : (
					<ActivityTable />
				)}
			</div>

			{/* Activity Detail Modal */}
			{selectedActivity && (
				<div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
					<div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
						<div className="p-6 border-b border-gray-200">
							<div className="flex items-center justify-between">
								<h2 className="text-lg font-semibold">Activity Details</h2>
								<button
									onClick={() => setSelectedActivity(null)}
									className="p-1 hover:bg-gray-100 rounded"
								>
									<X size={20} />
								</button>
							</div>
						</div>
						<div className="p-6 space-y-4">
							<div className="flex items-center space-x-3">
								<div
									className={`p-3 rounded-full ${getActivityColor(selectedActivity.action)}`}
								>
									{getActivityIcon(selectedActivity.action)}
								</div>
								<div>
									<h3 className="font-medium">
										{getActivityLabel(selectedActivity.action)}
									</h3>
									{/* <p className="text-sm text-gray-600"> */}
									{/* 	{selectedActivity.description} */}
									{/* </p> */}
								</div>
							</div>

							<div className="grid grid-cols-2 gap-4">
								{/* <div> */}
								{/* 	<label className="text-sm font-medium text-gray-500"> */}
								{/* 		User */}
								{/* 	</label> */}
								{/* 	<p className="mt-1">{selectedActivity.user}</p> */}
								{/* </div> */}
								<div>
									<label className="text-sm font-medium text-gray-500">
										Timestamp
									</label>
									<p className="mt-1">
										{new Date(selectedActivity.created_at).toLocaleString()}
									</p>
								</div>
								<div>
									<label className="text-sm font-medium text-gray-500">
										IP Address
									</label>
									<p className="mt-1 font-mono text-sm">
										{selectedActivity.ip_address}
									</p>
								</div>
								<div>
									<label className="text-sm font-medium text-gray-500">
										User Agent
									</label>
									<p className="mt-1 text-sm">{selectedActivity.user_agent}</p>
								</div>
							</div>

							{selectedActivity.details && (
								<div>
									<label className="text-sm font-medium text-gray-500">
										Additional Information
									</label>
									<div className="mt-2 p-4 bg-gray-50 rounded-lg">
										{Object.entries(selectedActivity.details).map(
											([key, value]) => (
												<div key={key} className="flex justify-between py-1">
													<span className="font-medium text-sm">{key}:</span>
													<span className="text-sm">{String(value)}</span>
												</div>
											),
										)}
									</div>
								</div>
							)}
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

const ApiAccessPage = () => {
	const { data: _apiKeys } = useUserAPIKeys();
	const apiKeys = _apiKeys?.data || [];
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [newApiKey, setNewApiKey] = useState<APIKey | null>(null);
	const [currentView, setCurrentView] = useState("keys"); // 'keys', 'docs', 'logs', 'analytics'

	// API key form fields

	// Statistics
	const stats = useMemo(() => {
		const totalKeys = apiKeys.length;
		const activeKeys = apiKeys.filter((k) => k.is_active).length;
		const totalRequests = apiKeys.reduce(
			(sum, k) => sum + (k.usage_count || 0),
			0,
		);
		const avgRequestsPerKey =
			totalKeys > 0 ? Math.round(totalRequests / totalKeys) : 0;

		return {
			totalKeys,
			activeKeys,
			totalRequests,
			avgRequestsPerKey,
		};
	}, [apiKeys]);

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<div className="bg-white border-b border-gray-200 p-6">
				<div className="flex items-center justify-between">
					<div>
						<h1 className="text-3xl font-bold text-gray-900">
							API Access Management
						</h1>
						<p className="text-gray-600 mt-1">
							Manage API keys, monitor usage, and configure access permissions
						</p>
					</div>
					<div className="flex items-center space-x-3">
						<Button
							onClick={() => setShowCreateModal(true)}
							className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
						>
							<Plus size={16} />
							<span>Tạo API Key</span>
						</Button>
					</div>
				</div>
			</div>

			<div className="p-6 space-y-6">
				{/* Statistics Dashboard */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatisticCard
						title="Total API Keys"
						value={stats.totalKeys}
						icon={<Key size={20} />}
						color="blue"
					/>
					<StatisticCard
						title="Active Keys"
						value={stats.activeKeys}
						icon={<CheckCircle size={20} />}
						trend={{ value: 12, isPositive: true }}
						color="green"
					/>
					<StatisticCard
						title="Total Requests"
						value={stats.totalRequests.toLocaleString()}
						icon={<BarChart3 size={20} />}
						trend={{ value: 25, isPositive: true }}
						color="purple"
					/>
					<StatisticCard
						title="Avg Requests/Key"
						value={stats.avgRequestsPerKey}
						icon={<TrendingUp size={20} />}
						color="orange"
					/>
				</div>

				{/* View Selector */}
				<div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
					<button
						onClick={() => setCurrentView("keys")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "keys"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						API Keys
					</button>
					<button
						onClick={() => setCurrentView("docs")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "docs"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						Documentation
					</button>
					<button
						onClick={() => setCurrentView("logs")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "logs"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						API Logs
					</button>
					<button
						onClick={() => setCurrentView("analytics")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "analytics"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						Analytics
					</button>
				</div>

				{/* Main Content */}
				{currentView === "keys" && (
					<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
						{newApiKey && <ApiKeyCard key={newApiKey.id} apiKey={newApiKey} />}
						{apiKeys.map((apiKey) => (
							<ApiKeyCard key={apiKey.id} apiKey={apiKey} />
						))}
					</div>
				)}

				{currentView === "docs" && (
					<div className="bg-white rounded-lg border shadow-sm">
						<div className="p-6 border-b">
							<h2 className="text-lg font-semibold">API Documentation</h2>
						</div>
						<div className="p-6 space-y-6">
							<div>
								<h3 className="text-md font-medium mb-3">Authentication</h3>
								<p className="text-sm text-gray-600 mb-3">
									Include your API key in the Authorization header:
								</p>
								<div className="bg-gray-50 p-4 rounded-lg">
									<code className="text-sm">
										Authorization: Bearer YOUR_API_KEY
									</code>
								</div>
							</div>

							<div>
								<h3 className="text-md font-medium mb-3">Base URL</h3>
								<div className="bg-gray-50 p-4 rounded-lg">
									<code className="text-sm">
										https://api.knowledgegraph.com/v1
									</code>
								</div>
							</div>

							<div>
								<h3 className="text-md font-medium mb-3">Endpoints</h3>
								<div className="space-y-4">
									<div className="border rounded-lg p-4">
										<div className="flex items-center space-x-2 mb-2">
											<span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
												GET
											</span>
											<code className="text-sm">/api/v1/entities</code>
										</div>
										<p className="text-sm text-gray-600">
											Retrieve entities from the knowledge graph
										</p>
									</div>

									<div className="border rounded-lg p-4">
										<div className="flex items-center space-x-2 mb-2">
											<span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
												POST
											</span>
											<code className="text-sm">/api/v1/entities</code>
										</div>
										<p className="text-sm text-gray-600">
											Create a new entity in the knowledge graph
										</p>
									</div>

									<div className="border rounded-lg p-4">
										<div className="flex items-center space-x-2 mb-2">
											<span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
												GET
											</span>
											<code className="text-sm">/api/v1/relationships</code>
										</div>
										<p className="text-sm text-gray-600">
											Retrieve relationships between entities
										</p>
									</div>

									<div className="border rounded-lg p-4">
										<div className="flex items-center space-x-2 mb-2">
											<span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
												GET
											</span>
											<code className="text-sm">/api/v1/search</code>
										</div>
										<p className="text-sm text-gray-600">
											Search entities and relationships
										</p>
									</div>
								</div>
							</div>
						</div>
					</div>
				)}

				{currentView === "logs" && (
					<div className="bg-white rounded-lg border shadow-sm">
						<div className="p-6 border-b">
							<h2 className="text-lg font-semibold">API Request Logs</h2>
						</div>
						<div className="p-6">
							<div className="space-y-3">
								{[
									{
										method: "GET",
										endpoint: "/api/v1/entities",
										status: 200,
										time: "2024-01-25T15:30:00Z",
										ip: "192.168.1.100",
									},
									{
										method: "POST",
										endpoint: "/api/v1/entities",
										status: 201,
										time: "2024-01-25T15:25:00Z",
										ip: "10.0.0.50",
									},
									{
										method: "GET",
										endpoint: "/api/v1/search",
										status: 200,
										time: "2024-01-25T15:20:00Z",
										ip: "172.16.0.25",
									},
									{
										method: "GET",
										endpoint: "/api/v1/relationships",
										status: 404,
										time: "2024-01-25T15:15:00Z",
										ip: "203.0.113.10",
									},
								].map((log, index) => (
									<div
										key={index}
										className="flex items-center justify-between p-3 border rounded hover:bg-gray-50"
									>
										<div className="flex items-center space-x-4">
											<span
												className={`px-2 py-1 text-xs rounded ${
													log.method === "GET"
														? "bg-green-100 text-green-800"
														: log.method === "POST"
															? "bg-blue-100 text-blue-800"
															: "bg-gray-100 text-gray-800"
												}`}
											>
												{log.method}
											</span>
											<code className="text-sm">{log.endpoint}</code>
											<span
												className={`px-2 py-1 text-xs rounded ${
													log.status < 300
														? "bg-green-100 text-green-800"
														: log.status < 400
															? "bg-yellow-100 text-yellow-800"
															: "bg-red-100 text-red-800"
												}`}
											>
												{log.status}
											</span>
										</div>
										<div className="flex items-center space-x-4 text-sm text-gray-500">
											<span>{log.ip}</span>
											<span>{new Date(log.time).toLocaleString()}</span>
										</div>
									</div>
								))}
							</div>
						</div>
					</div>
				)}

				{currentView === "analytics" && (
					<div className="space-y-6">
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
							<div className="bg-white rounded-lg border shadow-sm p-6">
								<h3 className="text-lg font-semibold mb-4">Request Volume</h3>
								<div className="h-64 flex items-center justify-center text-gray-500">
									<div className="text-center">
										<BarChart3 size={48} className="mx-auto mb-2" />
										<p>Request volume chart would go here</p>
									</div>
								</div>
							</div>

							<div className="bg-white rounded-lg border shadow-sm p-6">
								<h3 className="text-lg font-semibold mb-4">Response Times</h3>
								<div className="h-64 flex items-center justify-center text-gray-500">
									<div className="text-center">
										<Clock size={48} className="mx-auto mb-2" />
										<p>Response time metrics would go here</p>
									</div>
								</div>
							</div>
						</div>

						<div className="bg-white rounded-lg border shadow-sm p-6">
							<h3 className="text-lg font-semibold mb-4">Top Endpoints</h3>
							<div className="space-y-3">
								{[
									{
										endpoint: "/api/v1/entities",
										requests: 1250,
										percentage: 45,
									},
									{ endpoint: "/api/v1/search", requests: 892, percentage: 32 },
									{
										endpoint: "/api/v1/relationships",
										requests: 456,
										percentage: 16,
									},
									{
										endpoint: "/api/v1/visualizations",
										requests: 189,
										percentage: 7,
									},
								].map((item, index) => (
									<div
										key={index}
										className="flex items-center justify-between"
									>
										<div className="flex items-center space-x-3">
											<code className="text-sm">{item.endpoint}</code>
											<span className="text-sm text-gray-500">
												{item.requests} requests
											</span>
										</div>
										<div className="flex items-center space-x-2">
											<div className="w-24 bg-gray-200 rounded-full h-2">
												<div
													className="bg-blue-500 h-2 rounded-full"
													style={{ width: `${item.percentage}%` }}
												/>
											</div>
											<span className="text-sm text-gray-500 w-8">
												{item.percentage}%
											</span>
										</div>
									</div>
								))}
							</div>
						</div>
					</div>
				)}
			</div>

			{/* Create API Key Modal */}
			{showCreateModal && (
				<CreateApiKeyDialog
					open={showCreateModal}
					onOpenChange={setShowCreateModal}
					onApiKeyCreated={setNewApiKey}
				/>
			)}
		</div>
	);
};

// Main Component that combines both pages
const UserActivitiesAndApiAccess = () => {
	const [activePage, setActivePage] = useState("activities"); // 'activities' or 'api'

	return (
		<div>
			{/* Page Navigation */}
			<div className="bg-white border-b border-gray-200">
				<div className="px-6 py-3">
					<div className="flex space-x-1">
						<button
							onClick={() => setActivePage("activities")}
							className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
								activePage === "activities"
									? "bg-blue-100 text-blue-700"
									: "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
							}`}
						>
							User Activities
						</button>
						<button
							onClick={() => setActivePage("api")}
							className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
								activePage === "api"
									? "bg-blue-100 text-blue-700"
									: "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
							}`}
						>
							API Access
						</button>
					</div>
				</div>
			</div>

			{/* Page Content */}
			{activePage === "activities" ? <UserActivitiesPage /> : <ApiAccessPage />}
		</div>
	);
};

export default UserActivitiesAndApiAccess;
