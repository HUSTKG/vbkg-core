import { DataTable, SimpleColumnDef } from "@/components";
import {
	BarChart3,
	Copy,
	Edit,
	Eye,
	Globe,
	LockIcon,
	Network,
	Table,
	Trash2,
	TreePine,
} from "lucide-react";
import { useMemo } from "react";

interface TableVisualizationProps {
	visualizations: any[];
	setSelectedVisualization: (visualization: any) => void;
	handleEditVisualization: (row: any) => void;
	handleDuplicateVisualization: (row: any) => void;
	handleDeleteVisualization: (row: any) => void;
}

export default function TableVisualization({
	visualizations,
	setSelectedVisualization,
	handleDuplicateVisualization,
	handleEditVisualization,
	handleDeleteVisualization,
}: TableVisualizationProps) {
	const visualizationColumns = useMemo<SimpleColumnDef<any, any>[]>(
		() => [
			{
				header: "Visualization",
				accessorKey: "name",
				cell: (row) => (
					<div className="flex items-center space-x-3">
						<div className="p-2 bg-blue-100 rounded-lg text-blue-600">
							{row.config.type === "GRAPH" && <Network size={16} />}
							{row.config.type === "TABLE" && <Table size={16} />}
							{row.config.type === "CHART" && <BarChart3 size={16} />}
							{row.config.type === "TREE" && <TreePine size={16} />}
						</div>
						<div>
							<div className="font-medium">{row.name}</div>
							<div className="text-sm text-gray-500">{row.description}</div>
						</div>
					</div>
				),
			},
			{
				header: "Type",
				accessorKey: "config.type",
				cell: (row) => (
					<span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded">
						{row.config.type}
					</span>
				),
			},
			{
				header: "Status",
				accessorKey: "is_public",
				cell: (row) => (
					<div className="flex items-center space-x-1">
						{row.is_public ? (
							<>
								<Globe size={14} className="text-green-500" />
								<span className="text-sm text-green-700">Public</span>
							</>
						) : (
							<>
								<LockIcon size={14} className="text-gray-500" />
								<span className="text-sm text-gray-700">Private</span>
							</>
						)}
					</div>
				),
			},
			{
				header: "Created",
				accessorKey: "created_at",
				cell: (row) => (
					<div className="text-sm text-gray-500">
						{new Date(row.created_at).toLocaleDateString()}
					</div>
				),
			},
			{
				header: "Actions",
				cell: (row) => (
					<div className="flex items-center space-x-2">
						<button
							onClick={() => setSelectedVisualization(row)}
							className="p-1 hover:bg-gray-100 rounded"
							title="View"
						>
							<Eye size={16} />
						</button>
						<button
							onClick={() => handleEditVisualization(row)}
							className="p-1 hover:bg-gray-100 rounded"
							title="Edit"
						>
							<Edit size={16} />
						</button>
						<button
							onClick={() => handleDuplicateVisualization(row)}
							className="p-1 hover:bg-gray-100 rounded"
							title="Duplicate"
						>
							<Copy size={16} />
						</button>
						<button
							onClick={() => handleDeleteVisualization(row.id)}
							className="p-1 hover:bg-gray-100 rounded text-red-500"
							title="Delete"
						>
							<Trash2 size={16} />
						</button>
					</div>
				),
			},
		],
		[],
	);

	return (
		<div className="bg-white rounded-lg border shadow-sm">
			<div className="p-6 border-b">
				<h2 className="text-lg font-semibold">All Visualizations</h2>
			</div>
			<div className="p-6">
				<DataTable
					data={visualizations}
					columns={visualizationColumns}
					showGlobalFilter={true}
				/>
			</div>
		</div>
	);
}
