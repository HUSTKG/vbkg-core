import { useState, useMemo } from "react";
import {
	BarChart3,
	Network,
	Table,
	TreePine,
	Plus,
	Edit,
	Copy,
	Maximize2,
	Minimize2,
	Grid,
	List,
	Globe,
	Lock,
} from "lucide-react";
import { StatisticCard } from "@/components";
import { D3GraphVisualization } from "./components/D3GraphVisualization";
import { VisualizationPreview } from "./components/VisualizationPreview";
import { Visualization, VisualizationType } from "@vbkg/types";
import { VisualizationTemplates } from "./components/VisualizationTemplates";
import CreateVisualizationDialog from "./components/CreateVisualizationModal";
import TableVisualization from "./components/TableVisualization";
import { useVisualizationData, useVisualizations } from "@vbkg/api-client";

// Main Visualization Management Component
const VisualizationManagementPage = () => {
	const [selectedVisualization, setSelectedVisualization] =
		useState<Visualization | null>(null);
	const { data: _visualizations } = useVisualizations({});
	const visualizations = _visualizations?.data || [];


	const { data: _visualizationData } = useVisualizationData(
		{
			id: selectedVisualization?.id || "",
		},
		{
			enabled: !!selectedVisualization?.id,
		},
	);

	const visualizationData = _visualizationData?.data

	const [currentView, setCurrentView] = useState("gallery"); // 'gallery', 'table', 'templates'
	const [showCreateModal, setShowCreateModal] = useState(false);
	const [showEditModal, setShowEditModal] = useState(false);
	const [editingVisualization, setEditingVisualization] =
		useState<Visualization | null>(null);
	const [selectedRows, setSelectedRows] = useState<string[]>([]);
	const [isFullscreen, setIsFullscreen] = useState(false);

	// Statistics
	const stats = useMemo(
		() => ({
			total: visualizations.length,
			public: visualizations.filter((v) => v.is_public).length,
			private: visualizations.filter((v) => !v.is_public).length,
			byType: {
				GRAPH: visualizations.filter(
					(v) => v.visualization_type === VisualizationType.GRAPH,
				).length,
				TABLE: visualizations.filter(
					(v) => v.visualization_type === VisualizationType.TABLE,
				).length,
				CHART: visualizations.filter(
					(v) => v.visualization_type === VisualizationType.CHART,
				).length,
				TREE: visualizations.filter(
					(v) => v.visualization_type === VisualizationType.TREE,
				).length,
			},
		}),
		[visualizations],
	);

	// Handle editing visualization
	const handleEditVisualization = (visualization: Visualization) => {
		setEditingVisualization(visualization);
		setShowEditModal(true);
	};

	// Handle duplicate visualization
	const handleDuplicateVisualization = (visualization: Visualization) => {
		const duplicated = {
			...visualization,
			id: Date.now().toString(),
			name: `${visualization.name} (Copy)`,
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString(),
		};
	};

	// Handle delete visualization
	const handleDeleteVisualization = (id: string) => {
		if (window.confirm("Are you sure you want to delete this visualization?")) {
			if (selectedVisualization?.id === id) {
				setSelectedVisualization(null);
			}
		}
	};

	// Handle template selection
	const handleSelectTemplate = (template: any) => {
		setShowCreateModal(true);
		// Pre-fill form with template data
		setTimeout(() => {
			const nameInput = document.querySelector('input[name="name"]');
			const typeSelect = document.querySelector('select[name="config.type"]');
			if (nameInput) nameInput.nodeValue = template.name;
			if (typeSelect) typeSelect.nodeValue = template.type;
		}, 100);
	};

	// Handle bulk actions
	const handleBulkDelete = () => {
		if (selectedRows.length === 0) return;
		if (
			window.confirm(`Delete ${selectedRows.length} selected visualizations?`)
		) {
			setSelectedRows([]);
		}
	};

	const handleBulkExport = () => {
		const selectedVizs = visualizations.filter((viz) =>
			selectedRows.includes(viz.id),
		);
		const exportData = {
			visualizations: selectedVizs,
			exported_at: new Date().toISOString(),
		};

		const blob = new Blob([JSON.stringify(exportData, null, 2)], {
			type: "application/json",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `visualizations-export-${Date.now()}.json`;
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
							Visualization Management
						</h1>
						<p className="text-gray-600 mt-1">
							Create, manage, and share data visualizations
						</p>
					</div>
					<div className="flex items-center space-x-3">
						<button
							onClick={() =>
								setCurrentView(currentView === "gallery" ? "table" : "gallery")
							}
							className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
							title={currentView === "gallery" ? "Table View" : "Gallery View"}
						>
							{currentView === "gallery" ? (
								<List size={20} />
							) : (
								<Grid size={20} />
							)}
						</button>
						<button
							onClick={() => setShowCreateModal(true)}
							className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
						>
							<Plus size={16} />
							<span>Create Visualization</span>
						</button>
					</div>
				</div>
			</div>

			<div className="p-6 space-y-6">
				{/* Statistics Dashboard */}
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
					<StatisticCard
						title="Total Visualizations"
						value={stats.total}
						icon={<BarChart3 size={20} />}
						trend={{ value: 12, isPositive: true }}
						color="blue"
					/>
					<StatisticCard
						title="Public Visualizations"
						value={stats.public}
						icon={<Globe size={20} />}
						color="green"
					/>
					<StatisticCard
						title="Graph Networks"
						value={stats.byType.GRAPH}
						icon={<Network size={20} />}
						color="purple"
					/>
					<StatisticCard
						title="Data Tables"
						value={stats.byType.TABLE}
						icon={<Table size={20} />}
						color="yellow"
					/>
				</div>

				{/* View Selector */}
				<div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
					<button
						onClick={() => setCurrentView("gallery")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "gallery"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						Gallery View
					</button>
					<button
						onClick={() => setCurrentView("table")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "table"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						Table View
					</button>
					<button
						onClick={() => setCurrentView("templates")}
						className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
							currentView === "templates"
								? "bg-blue-100 text-blue-700"
								: "text-gray-600 hover:text-gray-900"
						}`}
					>
						Templates
					</button>
				</div>

				{/* Bulk Actions */}
				{selectedRows.length > 0 && (
					<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
						<div className="flex items-center justify-between">
							<span className="text-sm font-medium text-blue-800">
								{selectedRows.length} visualizations selected
							</span>
							<div className="flex items-center space-x-2">
								<button
									onClick={handleBulkExport}
									className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
								>
									Export Selected
								</button>
								<button
									onClick={handleBulkDelete}
									className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
								>
									Delete Selected
								</button>
							</div>
						</div>
					</div>
				)}

				{/* Main Content */}
				{currentView === "gallery" && (
					<div className="flex gap-6">
						{/* Visualization Gallery */}
						<div className="grow">
							<div className="bg-white rounded-lg border shadow-sm">
								<div className="p-6 border-b">
									<h2 className="text-lg font-semibold">Visualizations</h2>
								</div>
								<div className="p-6">
									<div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
										{visualizations.map((viz) => (
											<div
												key={viz.id}
												className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
													selectedVisualization?.id === viz.id
														? "ring-2 ring-blue-500 bg-blue-50"
														: ""
												}`}
												onClick={() => setSelectedVisualization(viz)}
											>
												<div className="flex items-start justify-between mb-3">
													<div className="flex items-center space-x-2">
														<div className="p-2 bg-blue-100 rounded-lg text-blue-600">
															{viz.visualization_type ===
																VisualizationType.GRAPH && (
																<Network size={16} />
															)}
															{viz.visualization_type ===
																VisualizationType.TABLE && <Table size={16} />}
															{viz.visualization_type ===
																VisualizationType.CHART && (
																<BarChart3 size={16} />
															)}
															{viz.visualization_type ===
																VisualizationType.TREE && (
																<TreePine size={16} />
															)}
														</div>
														<div>
															<h3 className="font-medium text-sm">
																{viz.name}
															</h3>
															<p className="text-xs text-gray-500">
																{viz.visualization_type}
															</p>
														</div>
													</div>
													<div className="flex items-center space-x-1">
														{viz.is_public ? (
															<Globe size={14} className="text-green-500" />
														) : (
															<Lock size={14} className="text-gray-400" />
														)}
													</div>
												</div>

												<p className="text-xs text-gray-600 mb-3 line-clamp-2">
													{viz.description}
												</p>

												<div className="flex items-center justify-between">
													<time className="text-xs text-gray-400">
														{new Date(viz.updated_at).toLocaleDateString()}
													</time>
													<div className="flex items-center space-x-1">
														<button
															onClick={(e) => {
																e.stopPropagation();
																handleEditVisualization(viz);
															}}
															className="p-1 hover:bg-gray-100 rounded"
														>
															<Edit size={12} />
														</button>
														<button
															onClick={(e) => {
																e.stopPropagation();
																handleDuplicateVisualization(viz);
															}}
															className="p-1 hover:bg-gray-100 rounded"
														>
															<Copy size={12} />
														</button>
													</div>
												</div>
											</div>
										))}
									</div>
								</div>
							</div>
						</div>

						{/* Visualization Preview */}
						<div className="min-w-max shrink-0">
							<div className="bg-white rounded-lg border shadow-sm">
								<div className="p-6 border-b">
									<div className="flex items-center justify-between">
										<h2 className="text-lg font-semibold">Preview</h2>
										{selectedVisualization && (
											<button
												onClick={() => setIsFullscreen(true)}
												className="p-2 hover:bg-gray-100 rounded"
												title="Fullscreen"
											>
												<Maximize2 size={16} />
											</button>
										)}
									</div>
								</div>
								<div className="p-6">
									{selectedVisualization && visualizationData ? (
										<VisualizationPreview
											visualization={selectedVisualization}
											data={visualizationData}
										/>
									) : (
										<div className="text-center py-8 text-gray-500">
											<Network size={48} className="mx-auto mb-4 opacity-50" />
											<p>Select a visualization to preview</p>
										</div>
									)}
								</div>
							</div>
						</div>
					</div>
				)}

				{currentView === "table" && (
					<TableVisualization
						visualizations={visualizations}
						setSelectedVisualization={setSelectedVisualization}
						handleDuplicateVisualization={handleDuplicateVisualization}
						handleEditVisualization={handleEditVisualization}
						handleDeleteVisualization={handleDeleteVisualization}
					/>
				)}

				{currentView === "templates" && (
					<div className="bg-white rounded-lg border shadow-sm">
						<div className="p-6 border-b">
							<h2 className="text-lg font-semibold">Visualization Templates</h2>
							<p className="text-sm text-gray-600 mt-1">
								Quick start with pre-configured visualization templates
							</p>
						</div>
						<div className="p-6">
							<VisualizationTemplates onSelectTemplate={handleSelectTemplate} />
						</div>
					</div>
				)}
			</div>

			<CreateVisualizationDialog
				open={showCreateModal}
				onOpenChange={setShowCreateModal}
				mode="create"
			/>

			<CreateVisualizationDialog
				open={showEditModal}
				onOpenChange={setShowEditModal}
				setEditingVisualization={setEditingVisualization}
				editingVisualization={editingVisualization}
				mode="edit"
			/>

			{/* Fullscreen Visualization Modal */}
			{isFullscreen && selectedVisualization && (
				<div className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center z-50">
					<div className="w-full h-full p-8 flex flex-col">
						<div className="flex items-center justify-between mb-4">
							<h2 className="text-white text-xl font-semibold">
								{selectedVisualization.name}
							</h2>
							<button
								onClick={() => setIsFullscreen(false)}
								className="text-white p-2 hover:bg-white hover:bg-opacity-20 rounded"
							>
								<Minimize2 size={20} />
							</button>
						</div>
						<div className="flex-1 flex items-center justify-center">
							{selectedVisualization.visualization_type ===
							VisualizationType.GRAPH ? (
								<D3GraphVisualization
									data={[]}
									config={selectedVisualization.config}
									width={Math.min(window.innerWidth - 100, 1200)}
									height={Math.min(window.innerHeight - 200, 800)}
								/>
							) : (
								<div className="bg-white rounded-lg p-8">
									<VisualizationPreview
										visualization={selectedVisualization}
										data={[]}
									/>
								</div>
							)}
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default VisualizationManagementPage;
