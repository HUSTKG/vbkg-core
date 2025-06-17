import { BarChart3, TreePine } from "lucide-react";
import { D3GraphVisualization } from "./D3GraphVisualization";
import {
	ChartVisualizationConfig,
	GraphVisualizationConfig,
	Visualization,
	VisualizationData,
	VisualizationType,
} from "@vbkg/types";

export const VisualizationPreview = ({
	visualization,
	data,
}: {
	visualization: Visualization;
	data: VisualizationData;
}) => {
	const renderVisualization = () => {
		switch (visualization.visualization_type) {
			case VisualizationType.GRAPH:
				return (
					<D3GraphVisualization
						data={data}
						config={visualization.config as GraphVisualizationConfig}
						width={325}
						height={300}
					/>
				);

			case VisualizationType.TABLE:
				return (
					<div className="border rounded-lg p-4 bg-white">
						<table className="w-full text-sm">
							<thead className="border-b">
								<tr>
									<th className="p-2 text-left">Entity</th>
									<th className="p-2 text-left">Type</th>
									<th className="p-2 text-left">Properties</th>
								</tr>
							</thead>
							<tbody>
								{data.rows?.slice(0, 5).map((row, idx) => (
									<tr key={idx} className="border-b">
										<td className="p-2">{row.name}</td>
										<td className="p-2">{row.type}</td>
										<td className="p-2">
											{Object.keys(row.properties || {}).length}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				);

			case VisualizationType.CHART:
				return (
					<div className="border rounded-lg p-4 bg-white h-64 flex items-center justify-center">
						<div className="text-center">
							<BarChart3 size={48} className="mx-auto text-gray-400 mb-2" />
							<p className="text-sm text-gray-500">Chart Visualization</p>
							<p className="text-xs text-gray-400">
								Type:{" "}
								{(visualization.config as ChartVisualizationConfig)
									?.chart_type || "bar"}
							</p>
						</div>
					</div>
				);

			case VisualizationType.TREE:
				return (
					<div className="border rounded-lg p-4 bg-white h-64 flex items-center justify-center">
						<div className="text-center">
							<TreePine size={48} className="mx-auto text-gray-400 mb-2" />
							<p className="text-sm text-gray-500">Tree Visualization</p>
							<p className="text-xs text-gray-400">Hierarchical Layout</p>
						</div>
					</div>
				);

			default:
				return (
					<div className="border rounded-lg p-4 bg-gray-50 h-64 flex items-center justify-center">
						<p className="text-gray-500">Preview not available</p>
					</div>
				);
		}
	};

	return (
		<div className="space-y-2">
			<div className="flex items-center justify-between">
				<h4 className="text-sm font-medium">Preview</h4>
				<div className="flex items-center space-x-1">
					<span
						className={`inline-block w-2 h-2 rounded-full ${
							visualization.is_public ? "bg-green-500" : "bg-yellow-500"
						}`}
					/>
					<span className="text-xs text-gray-500">
						{visualization.is_public ? "Public" : "Private"}
					</span>
				</div>
			</div>
			{renderVisualization()}
		</div>
	);
};
