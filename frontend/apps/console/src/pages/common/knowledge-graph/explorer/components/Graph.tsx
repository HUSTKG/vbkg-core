import React, {
	useState,
	useEffect,
	useRef,
	useCallback,
	ReactNode,
} from "react";
import { Button } from "@/components/ui/button";
import { Download, RotateCcw, ZoomIn, ZoomOut, Move, Info } from "lucide-react";
import { IEdge, INode, ISubgraphResponse } from "@vbkg/types";

interface GraphVisualizationProps {
	loading?: boolean;
	graphData?: ISubgraphResponse;
}

// Enhanced Graph Visualization with simplified node dragging
export default function GraphVisualization({
	loading,
	graphData,
}: GraphVisualizationProps) {
	const svgRef = useRef<SVGSVGElement>(null);
	const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
	const [isDragging, setIsDragging] = useState(false);
	const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
	const [hoveredNode, setHoveredNode] = useState<string | null>(null);
	const [selectedNode, setSelectedNode] = useState<string | null>(null);
	const [tooltip, setTooltip] = useState<{
		x: number;
		y: number;
		content: ReactNode;
	} | null>(null);
	const [layout, setLayout] = useState<"circle" | "force">("force");
	const [nodePositions, setNodePositions] = useState<
		Record<string, { x: number; y: number }>
	>({});

	// Node dragging states
	const [isDraggingNode, setIsDraggingNode] = useState(false);
	const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);

	// Calculate force-directed layout
	const calculateForceLayout = useCallback((nodes: INode[], edges: IEdge[]) => {
		const positions: Record<string, { x: number; y: number }> = {};
		const width = 800;
		const height = 400;

		// Initialize random positions
		nodes.forEach((node) => {
			positions[node.id] = {
				x: Math.random() * (width - 100) + 50,
				y: Math.random() * (height - 100) + 50,
			};
		});

		// Simple force simulation
		for (let iteration = 0; iteration < 100; iteration++) {
			const forces: Record<string, { x: number; y: number }> = {};

			// Initialize forces
			nodes.forEach((node) => {
				forces[node.id] = { x: 0, y: 0 };
			});

			// Repulsion between all nodes
			nodes.forEach((nodeA) => {
				nodes.forEach((nodeB) => {
					if (nodeA.id !== nodeB.id) {
						const dx = positions[nodeA.id].x - positions[nodeB.id].x;
						const dy = positions[nodeA.id].y - positions[nodeB.id].y;
						const distance = Math.sqrt(dx * dx + dy * dy) || 1;
						const force = 500 / (distance * distance);

						forces[nodeA.id].x += (dx / distance) * force;
						forces[nodeA.id].y += (dy / distance) * force;
					}
				});
			});

			// Attraction along edges
			edges.forEach((edge) => {
				const dx = positions[edge.target].x - positions[edge.source].x;
				const dy = positions[edge.target].y - positions[edge.source].y;
				const distance = Math.sqrt(dx * dx + dy * dy) || 1;
				const force = distance * 0.01;

				forces[edge.source].x += (dx / distance) * force;
				forces[edge.source].y += (dy / distance) * force;
				forces[edge.target].x -= (dx / distance) * force;
				forces[edge.target].y -= (dy / distance) * force;
			});

			// Apply forces
			nodes.forEach((node) => {
				positions[node.id].x += forces[node.id].x * 0.1;
				positions[node.id].y += forces[node.id].y * 0.1;

				// Keep nodes within bounds
				positions[node.id].x = Math.max(
					50,
					Math.min(width - 50, positions[node.id].x),
				);
				positions[node.id].y = Math.max(
					50,
					Math.min(height - 50, positions[node.id].y),
				);
			});
		}

		return positions;
	}, []);

	// Calculate circle layout
	const calculateCircleLayout = useCallback((nodes: INode[]) => {
		const positions: Record<string, { x: number; y: number }> = {};
		const centerX = 400;
		const centerY = 200;
		const radius = 120;

		nodes.forEach((node, i) => {
			const angle = (i / nodes.length) * 2 * Math.PI;
			positions[node.id] = {
				x: centerX + radius * Math.cos(angle),
				y: centerY + radius * Math.sin(angle),
			};
		});

		return positions;
	}, []);

	// Update node positions when layout changes
	useEffect(() => {
		if (!graphData) return;

		let newPositions: Record<string, { x: number; y: number }>;

		switch (layout) {
			case "force":
				newPositions = calculateForceLayout(graphData.nodes, graphData.edges);
				break;
			case "circle":
				newPositions = calculateCircleLayout(graphData.nodes);
				break;
			default:
				newPositions = calculateCircleLayout(graphData.nodes);
		}

		setNodePositions(newPositions);
	}, [graphData, layout, calculateForceLayout, calculateCircleLayout]);

	// Convert screen coordinates to SVG coordinates
	const screenToSVGCoords = useCallback(
		(screenX: number, screenY: number) => {
			if (!svgRef.current) return { x: 0, y: 0 };

			const rect = svgRef.current.getBoundingClientRect();
			const x = (screenX - rect.left - transform.x) / transform.scale;
			const y = (screenY - rect.top - transform.y) / transform.scale;

			return { x, y };
		},
		[transform],
	);

	// Handle mouse events for pan and zoom
	const handleMouseDown = (e: React.MouseEvent) => {
		if (!isDraggingNode) {
			setIsDragging(true);
			setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
		}
	};

	const handleMouseMove = (e: React.MouseEvent) => {
		if (isDraggingNode && draggedNodeId) {
			// Update dragged node position
			const svgCoords = screenToSVGCoords(e.clientX, e.clientY);

			setNodePositions((prev) => ({
				...prev,
				[draggedNodeId]: {
					x: Math.max(50, Math.min(750, svgCoords.x)),
					y: Math.max(50, Math.min(350, svgCoords.y)),
				},
			}));
		} else if (isDragging && !isDraggingNode) {
			// Pan the canvas
			setTransform((prev) => ({
				...prev,
				x: e.clientX - dragStart.x,
				y: e.clientY - dragStart.y,
			}));
		}
	};

	const handleMouseUp = () => {
		setIsDragging(false);
		setIsDraggingNode(false);
		setDraggedNodeId(null);
	};

	// Node-specific event handlers
	const handleNodeMouseDown = (e: React.MouseEvent, nodeId: string) => {
		e.stopPropagation(); // Prevent canvas pan
		setIsDraggingNode(true);
		setDraggedNodeId(nodeId);
	};

	const handleWheel = (e: React.WheelEvent) => {
		e.preventDefault();
		const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
		setTransform((prev) => ({
			...prev,
			scale: Math.max(0.5, Math.min(3, prev.scale * scaleFactor)),
		}));
	};

	// Control functions
	const handleZoomIn = () => {
		setTransform((prev) => ({ ...prev, scale: Math.min(3, prev.scale * 1.2) }));
	};

	const handleZoomOut = () => {
		setTransform((prev) => ({
			...prev,
			scale: Math.max(0.5, prev.scale / 1.2),
		}));
	};

	const handleReset = () => {
		setTransform({ x: 0, y: 0, scale: 1 });
		setSelectedNode(null);
		setHoveredNode(null);
		// Regenerate positions based on current layout
		if (graphData) {
			let newPositions: Record<string, { x: number; y: number }>;
			switch (layout) {
				case "force":
					newPositions = calculateForceLayout(graphData.nodes, graphData.edges);
					break;
				case "circle":
					newPositions = calculateCircleLayout(graphData.nodes);
					break;
				default:
					newPositions = calculateCircleLayout(graphData.nodes);
			}
			setNodePositions(newPositions);
		}
	};

	const handleDownload = () => {
		if (!svgRef.current) return;

		const svgData = new XMLSerializer().serializeToString(svgRef.current);
		const canvas = document.createElement("canvas");
		const ctx = canvas.getContext("2d");
		const img = new Image();

		canvas.width = 800;
		canvas.height = 400;

		img.onload = () => {
			ctx?.drawImage(img, 0, 0);
			const link = document.createElement("a");
			link.download = "knowledge-graph.png";
			link.href = canvas.toDataURL();
			link.click();
		};

		img.src = "data:image/svg+xml;base64," + btoa(svgData);
	};

	const handleNodeHover = (node: INode, e: React.MouseEvent) => {
		setHoveredNode(node.id);
		setTooltip({
			x: e.clientX,
			y: e.clientY,
			content: (
				<div className="text-sm">
					<strong>{node.label}</strong> ({node.type})
					{node.properties && (
						<pre className="mt-1 text-sm font-bold text-gray-300">{JSON.stringify(node.properties)}</pre>
					)}
				</div>
			),
		});
	};

	const handleNodeLeave = () => {
		setHoveredNode(null);
		setTooltip(null);
	};

	const handleNodeClick = (node: INode) => {
		setSelectedNode(node.id);
		// Trigger search params update
		window.dispatchEvent(
			new CustomEvent("node-selected", { detail: { entity_id: node.id } }),
		);
	};

	if (loading) {
		return (
			<div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
					<p className="text-gray-600">Đang tải đồ thị...</p>
				</div>
			</div>
		);
	}

	if (!graphData || graphData.nodes.length === 0) {
		return (
			<div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
				<div className="text-center">
					<Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
					<p className="text-gray-500">
						Chọn một thực thể để xem đồ thị kiến thức hoặc tải lên dữ liệu
					</p>
					<p className="text-sm text-gray-400 mt-2">
						Không có dữ liệu đồ thị hiện tại. Vui lòng chọn một thực thể hoặc tải
						lên dữ liệu mới.
					</p>
				</div>
			</div>
		);
	}

	return (
		<div className="relative bg-white rounded-lg border shadow-sm">
			{/* Header with layout controls */}
			<div className="flex items-center justify-between p-4 border-b bg-gray-50">
				<div className="flex items-center gap-4">
					<h3 className="font-semibold text-gray-900">Đồ thị</h3>
					<div className="flex items-center gap-2">
						<span className="text-sm text-gray-600">Bố cục:</span>
						<select
							value={layout}
							onChange={(e) => setLayout(e.target.value as any)}
							className="text-sm border rounded px-2 py-1"
						>
							<option value="force">Force-directed</option>
							<option value="circle">Circle</option>
						</select>
					</div>
				</div>

				<div className="flex items-center gap-1">
					<Button
						size="sm"
						variant="outline"
						onClick={handleZoomIn}
						className="h-8 w-8 p-0"
						title="Phóng to"
					>
						<ZoomIn size={14} />
					</Button>
					<Button
						size="sm"
						variant="outline"
						onClick={handleZoomOut}
						className="h-8 w-8 p-0"
						title="Thu nhỏ"
					>
						<ZoomOut size={14} />
					</Button>
					<Button
						size="sm"
						variant="outline"
						onClick={handleReset}
						className="h-8 w-8 p-0"
						title="Đặt lại"
					>
						<RotateCcw size={14} />
					</Button>
					<Button
						size="sm"
						variant="outline"
						onClick={handleDownload}
						className="h-8 w-8 p-0"
						title="Tải hình ảnh"
					>
						<Download size={14} />
					</Button>
				</div>
			</div>

			{/* Graph container */}
			<div
				className={`relative h-96 overflow-hidden ${isDraggingNode ? "cursor-grabbing" : "cursor-move"
					}`}
				onMouseDown={handleMouseDown}
				onMouseMove={handleMouseMove}
				onMouseUp={handleMouseUp}
				onMouseLeave={handleMouseUp}
				onWheel={handleWheel}
			>
				<svg
					ref={svgRef}
					width="100%"
					height="100%"
					viewBox="0 0 800 400"
					className="bg-gradient-to-br from-blue-50 to-indigo-50"
				>
					{/* Background grid */}
					<defs>
						<pattern
							id="grid"
							width="40"
							height="40"
							patternUnits="userSpaceOnUse"
						>
							<path
								d="M 40 0 L 0 0 0 40"
								fill="none"
								stroke="#e5e7eb"
								strokeWidth="1"
								opacity="0.5"
							/>
						</pattern>

						{/* Arrow marker */}
						<marker
							id="arrowhead"
							markerWidth="10"
							markerHeight="7"
							refX="10"
							refY="3.5"
							orient="auto"
						>
							<polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
						</marker>

						{/* Glow effect */}
						<filter id="glow">
							<feGaussianBlur stdDeviation="3" result="coloredBlur" />
							<feMerge>
								<feMergeNode in="coloredBlur" />
								<feMergeNode in="SourceGraphic" />
							</feMerge>
						</filter>

						{/* Gradients for center nodes */}
						<linearGradient
							id="centerGradient"
							x1="0%"
							y1="0%"
							x2="100%"
							y2="100%"
						>
							<stop offset="0%" stopColor="#3b82f6" />
							<stop offset="100%" stopColor="#1d4ed8" />
						</linearGradient>
					</defs>

					<rect width="100%" height="100%" fill="url(#grid)" />

					<g
						transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}
					>
						{/* Draw edges */}
						{graphData.edges.map((edge) => {
							const sourcePos = nodePositions[edge.source];
							const targetPos = nodePositions[edge.target];

							if (!sourcePos || !targetPos) return null;

							const isHighlighted =
								hoveredNode === edge.source || hoveredNode === edge.target;

							return (
								<g key={edge.id}>
									<line
										x1={sourcePos.x}
										y1={sourcePos.y}
										x2={targetPos.x}
										y2={targetPos.y}
										stroke={isHighlighted ? "#3b82f6" : "#6b7280"}
										strokeWidth={isHighlighted ? "3" : "2"}
										markerEnd="url(#arrowhead)"
										opacity={isHighlighted ? 1 : 0.6}
										className="transition-all duration-200"
									/>
									<text
										x={(sourcePos.x + targetPos.x) / 2}
										y={(sourcePos.y + targetPos.y) / 2 - 10}
										textAnchor="middle"
										fontSize="10"
										fill={isHighlighted ? "#1d4ed8" : "#6b7280"}
										className="pointer-events-none font-medium"
									>
										{edge.type}
									</text>
								</g>
							);
						})}

						{/* Draw nodes */}
						{graphData.nodes.map((node) => {
							const position = nodePositions[node.id];
							if (!position) return null;

							const isCenter = node.is_center;
							const isHovered = hoveredNode === node.id;
							const isSelected = selectedNode === node.id;
							const nodeRadius = isCenter ? 35 : 25;

							return (
								<g key={node.id}>
									{/* Node shadow */}
									<circle
										cx={position.x + 2}
										cy={position.y + 2}
										r={nodeRadius}
										fill="rgba(0,0,0,0.1)"
										className="pointer-events-none"
									/>

									{/* Main node */}
									<circle
										cx={position.x}
										cy={position.y}
										r={nodeRadius + (isHovered ? 3 : 0)}
										fill={
											isCenter
												? "url(#centerGradient)"
												: isSelected
													? "#10b981"
													: isHovered
														? "#60a5fa"
														: "#f8fafc"
										}
										stroke={
											isCenter
												? "#1d4ed8"
												: isSelected
													? "#059669"
													: isHovered
														? "#3b82f6"
														: "#cbd5e1"
										}
										strokeWidth={isHovered || isSelected ? "3" : "2"}
										className="cursor-grab hover:cursor-grab active:cursor-grabbing transition-all duration-200"
										filter={isCenter ? "url(#glow)" : "none"}
										onMouseEnter={(e) => handleNodeHover(node, e)}
										onMouseLeave={handleNodeLeave}
										onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
										onClick={() => !isDraggingNode && handleNodeClick(node)}
									/>

									{/* Node label */}
									<text
										x={position.x}
										y={position.y - 2}
										textAnchor="middle"
										fontSize={isCenter ? "12" : "11"}
										fontWeight={isCenter ? "bold" : "normal"}
										fill={isCenter ? "white" : "#1f2937"}
										className="pointer-events-none font-medium select-none"
									>
										{node.label.length > 12
											? node.label.substring(0, 12) + "..."
											: node.label}
									</text>

									{/* Node type */}
									<text
										x={position.x}
										y={position.y + 12}
										textAnchor="middle"
										fontSize="9"
										fill={isCenter ? "#e2e8f0" : "#6b7280"}
										className="pointer-events-none select-none"
									>
										{node.type}
									</text>
								</g>
							);
						})}
					</g>
				</svg>

				{/* Stats overlay */}
				<div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-2 text-sm border">
					<div className="flex items-center gap-4">
						<span>
							<strong>{graphData.nodes.length}</strong> đỉnh
						</span>
						<span>
							<strong>{graphData.edges.length}</strong> cạnh
						</span>
						<span>
							Tỉ lệ: <strong>{Math.round(transform.scale * 100)}%</strong>
						</span>
					</div>
				</div>
			</div>

			{/* Tooltip */}
			{tooltip && (
				<div
					className="fixed z-50 bg-gray-900 text-white text-sm rounded-lg px-3 py-2 pointer-events-none shadow-lg"
					style={{
						left: tooltip.x + 10,
						top: tooltip.y - 30,
					}}
				>
					{tooltip.content}
				</div>
			)}

			{/* Legend */}
			<div className="p-4 bg-gray-50 border-t">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-6 text-sm">
						<div className="flex items-center gap-2">
							<div className="w-4 h-4 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 border"></div>
							<span>Trung tâm</span>
						</div>
						<div className="flex items-center gap-2">
							<div className="w-4 h-4 rounded-full bg-white border-2 border-gray-300"></div>
							<span>Đỉnh</span>
						</div>
						<div className="flex items-center gap-2">
							<div className="w-4 h-1 bg-gray-500"></div>
							<span>Cạnh</span>
						</div>
					</div>

					<div className="text-xs text-gray-500">
						<Move className="inline w-3 h-3 mr-1" />
						Kéo để di chuyển, <ZoomIn className="inline w-3 h-3 mr-1" />
						<ZoomOut className="inline w-3 h-3 mr-1" />
						Phóng to/Thu nhỏ, <RotateCcw className="inline w-3 h-3 mr-1" />
						Đặt lại, <Download className="inline w-3 h-3 mr-1" />
						Tải hình ảnh
					</div>
				</div>
			</div>
		</div>
	);
}
