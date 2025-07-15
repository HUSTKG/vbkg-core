import { GraphVisualizationConfig, VisualizationData } from "@vbkg/types";
import * as d3 from "d3";
import { useEffect, useRef, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import {
	Trash2,
	Edit,
	Plus,
	Save,
	X,
	MoreVertical,
	ZoomIn,
	ZoomOut,
	Home,
	Maximize,
	Download,
	Camera,
	Eye,
	EyeOff,
	Settings,
	ArrowRight,
} from "lucide-react";
import {
	useUpdateEntity,
	useDeleteEntity,
	useCreateRelationship,
	useCreateEntity,
} from "@vbkg/api-client";
import { toast } from "sonner";

// Định nghĩa types
interface Node {
	id: string;
	text?: string;
	name?: string;
	label?: string;
	type: string;
	properties?: Record<string, any>;
	x?: number;
	y?: number;
	fx?: number;
	fy?: number;
}

interface Edge {
	id?: string;
	source: string | Node;
	target: string | Node;
	type?: string;
	properties?: Record<string, any>;
}

interface EditingNode extends Node {
	entity_text: string;
	entity_type: string;
}

interface EditingRelationship {
	id?: string;
	source_entity_id: string;
	target_entity_id: string;
	relationship_type: string;
	properties: Record<string, any>;
}

type LayoutType = "force" | "circle" | "grid" | "hierarchy" | "radial";

export const D3GraphVisualization = ({
	data,
	config,
	width = 800,
	height = 600,
	editable = false,
	centralNodeId = null,
	centralNodes = [],
}: {
	data: VisualizationData;
	config: GraphVisualizationConfig;
	width?: number;
	height?: number;
	editable?: boolean;
	centralNodeId?: string | null;
	centralNodes?: string[];
}) => {
	const svgRef = useRef<SVGSVGElement | null>(null);
	const tooltipRef = useRef<HTMLDivElement | null>(null);
	const containerRef = useRef<HTMLDivElement | null>(null);

	// States
	const [selectedNode, setSelectedNode] = useState<Node | null>(null);
	const [isFullscreen, setIsFullscreen] = useState(false);
	const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
	const [dimensions, setDimensions] = useState({ width, height });
	const [layoutType, setLayoutType] = useState<LayoutType>("force");
	const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);

	// UI states
	const [showControls, setShowControls] = useState(true);
	const [showHints, setShowHints] = useState(true);
	const [showLegend, setShowLegend] = useState(true);

	// Edit states
	const [showEditNodeDialog, setShowEditNodeDialog] = useState(false);
	const [showEditEdgeDialog, setShowEditEdgeDialog] = useState(false);
	const [showCreateNodeDialog, setShowCreateNodeDialog] = useState(false);
	const [showCreateEdgeDialog, setShowCreateEdgeDialog] = useState(false);
	const [editingNode, setEditingNode] = useState<EditingNode | null>(null);
	const [editingEdge, setEditingEdge] = useState<EditingRelationship | null>(
		null,
	);
	const [contextMenuPosition, setContextMenuPosition] = useState<{
		x: number;
		y: number;
	} | null>(null);
	const [contextMenuTarget, setContextMenuTarget] = useState<{
		type: "node" | "edge";
		data: Node | Edge;
	} | null>(null);

	const [deleteNodeId, setDeleteNodeId] = useState<string | null>(null);

	// Create form states
	const [newNodeForm, setNewNodeForm] = useState({
		entity_text: "",
		entity_type: "",
		properties: "{}",
	});
	const [newEdgeForm, setNewEdgeForm] = useState({
		source_entity_id: "",
		target_entity_id: "",
		relationship_type: "",
		properties: "{}",
	});

	// Zoom behavior
	const zoom = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
	const simulation = useRef<d3.Simulation<
		d3.SimulationNodeDatum,
		undefined
	> | null>(null);

	// Helper function to check if node is central
	const isCentralNode = useCallback(
		(nodeId: string): boolean => {
			if (centralNodeId && nodeId === centralNodeId) return true;
			if (centralNodes && centralNodes.includes(nodeId)) return true;
			return false;
		},
		[centralNodeId, centralNodes],
	);

	// Get central nodes for display
	const getCentralNodes = useCallback((): string[] => {
		const result = [];
		if (centralNodeId) result.push(centralNodeId);
		if (centralNodes) result.push(...centralNodes);
		return [...new Set(result)]; // Remove duplicates
	}, [centralNodeId, centralNodes]);

	// Mutation hooks
	const updateEntityMutation = useUpdateEntity({
		onSuccess: () => {
			toast.success("Cập nhật entity thành công!");
			setShowEditNodeDialog(false);
		},
		onError: (error) => {
			toast.error(`Lỗi cập nhật entity: ${error.message}`);
		},
	});

	const deleteEntityMutation = useDeleteEntity({
		onSuccess: () => {
			toast.success("Xóa entity thành công!");
			setSelectedNode(null);
		},
		onError: (error) => {
			toast.error(`Lỗi xóa entity: ${error.message}`);
		},
	});

	const createEntityMutation = useCreateEntity({
		onSuccess: () => {
			toast.success("Tạo entity thành công!");
			setShowCreateNodeDialog(false);
			setNewNodeForm({ entity_text: "", entity_type: "", properties: "{}" });
		},
		onError: (error) => {
			toast.error(`Lỗi tạo entity: ${error.message}`);
		},
	});

	const createRelationshipMutation = useCreateRelationship({
		onSuccess: () => {
			toast.success("Tạo relationship thành công!");
			setShowCreateEdgeDialog(false);
			setNewEdgeForm({
				source_entity_id: "",
				target_entity_id: "",
				relationship_type: "",
				properties: "{}",
			});
		},
		onError: (error) => {
			toast.error(`Lỗi tạo relationship: ${error.message}`);
		},
	});

	// Simple responsive sizing without ResizeObserver
	useEffect(() => {
		if (isFullscreen) {
			setDimensions({
				width: window.innerWidth,
				height: window.innerHeight,
			});
		} else {
			// Use fixed dimensions from props, no dynamic resizing
			setDimensions({ width, height });
		}

		const handleResize = () => {
			if (isFullscreen) {
				setDimensions({
					width: window.innerWidth,
					height: window.innerHeight,
				});
			}
		};

		window.addEventListener("resize", handleResize);
		return () => window.removeEventListener("resize", handleResize);
	}, [isFullscreen, width, height]);

	// Handle fullscreen
	const toggleFullscreen = useCallback(() => {
		if (!document.fullscreenElement) {
			containerRef.current?.requestFullscreen();
			setIsFullscreen(true);
		} else {
			document.exitFullscreen();
			setIsFullscreen(false);
		}
	}, []);

	// Export as image
	const exportAsImage = useCallback(
		(format: "png" | "svg" = "png") => {
			const svg = svgRef.current;
			if (!svg) return;

			if (format === "svg") {
				const svgData = new XMLSerializer().serializeToString(svg);
				const svgBlob = new Blob([svgData], {
					type: "image/svg+xml;charset=utf-8",
				});
				const url = URL.createObjectURL(svgBlob);

				const link = document.createElement("a");
				link.href = url;
				link.download = `graph-visualization.svg`;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				URL.revokeObjectURL(url);
			} else {
				const canvas = document.createElement("canvas");
				const context = canvas.getContext("2d");
				if (!context) return;

				canvas.width = dimensions.width;
				canvas.height = dimensions.height;

				const data = new XMLSerializer().serializeToString(svg);
				const img = new Image();
				const svgBlob = new Blob([data], {
					type: "image/svg+xml;charset=utf-8",
				});
				const url = URL.createObjectURL(svgBlob);

				img.onload = () => {
					context.fillStyle = "white";
					context.fillRect(0, 0, canvas.width, canvas.height);
					context.drawImage(img, 0, 0);

					canvas.toBlob((blob) => {
						if (blob) {
							const link = document.createElement("a");
							link.href = URL.createObjectURL(blob);
							link.download = `graph-visualization.png`;
							document.body.appendChild(link);
							link.click();
							document.body.removeChild(link);
							URL.revokeObjectURL(link.href);
						}
					});

					URL.revokeObjectURL(url);
				};
				img.src = url;
			}
		},
		[dimensions],
	);

	// Reset zoom
	const resetZoom = useCallback(() => {
		if (zoom.current && svgRef.current) {
			const svg = d3.select(svgRef.current);
			svg
				.transition()
				.duration(750)
				.call(zoom.current.transform, d3.zoomIdentity);
		}
	}, []);

	// Fit to view
	const fitToView = useCallback(() => {
		if (!data.nodes || !zoom.current || !svgRef.current) return;

		const svg = d3.select(svgRef.current);
		const mainGroup = svg.select(".main-group");
		if (mainGroup.empty()) return;

		try {
			const bounds = (mainGroup.node() as SVGGElement).getBBox();
			const fullWidth = dimensions.width;
			const fullHeight = dimensions.height;
			const boundsWidth = bounds.width;
			const boundsHeight = bounds.height;
			const midX = bounds.x + boundsWidth / 2;
			const midY = bounds.y + boundsHeight / 2;

			if (boundsWidth === 0 || boundsHeight === 0) return;

			const scale =
				Math.min(fullWidth / boundsWidth, fullHeight / boundsHeight) * 0.8;
			const translate = [
				fullWidth / 2 - scale * midX,
				fullHeight / 2 - scale * midY,
			];

			svg
				.transition()
				.duration(750)
				.call(
					zoom.current.transform,
					d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale),
				);
		} catch (error) {
			console.warn("Error in fitToView:", error);
		}
	}, [data.nodes, dimensions.width, dimensions.height]);

	// Focus on central nodes
	const focusOnCentralNodes = useCallback(() => {
		if (!data.nodes || !zoom.current || !svgRef.current) return;

		const centralNodeIds = getCentralNodes();
		if (centralNodeIds.length === 0) return;

		const centralNodes = (data.nodes as Node[]).filter((node) =>
			centralNodeIds.includes(node.id),
		);
		if (centralNodes.length === 0) return;

		// Wait for simulation to settle before calculating positions
		setTimeout(() => {
			// Calculate bounding box of central nodes
			const xValues = centralNodes.map((node) => node.x || 0);
			const yValues = centralNodes.map((node) => node.y || 0);

			const minX = Math.min(...xValues);
			const maxX = Math.max(...xValues);
			const minY = Math.min(...yValues);
			const maxY = Math.max(...yValues);

			const nodeWidth = Math.max(maxX - minX, 200);
			const nodeHeight = Math.max(maxY - minY, 200);
			const centerX = (minX + maxX) / 2;
			const centerY = (minY + maxY) / 2;

			// Add padding
			const paddedWidth = nodeWidth + 200;
			const paddedHeight = nodeHeight + 200;

			const scale = Math.min(
				dimensions.width / paddedWidth,
				dimensions.height / paddedHeight,
				3, // Max zoom level
			);

			const translate = [
				dimensions.width / 2 - scale * centerX,
				dimensions.height / 2 - scale * centerY,
			];

			if (zoom.current && svgRef.current) {
				const svg = d3.select(svgRef.current);
				svg
					.transition()
					.duration(1000)
					.call(
						zoom.current.transform,
						d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale),
					);
			}
		}, 500);
	}, [data.nodes, getCentralNodes, dimensions.width, dimensions.height]);

	// Apply layout
	const applyLayout = useCallback(
		(nodes: Node[], edges: Edge[], type: LayoutType) => {
			if (!nodes.length) return;

			const centerX = width / 2;
			const centerY = height / 2;

			switch (type) {
				case "circle":
					nodes.forEach((node, i) => {
						const angle = (i / nodes.length) * 2 * Math.PI;
						const radius = Math.min(width, height) / 3;
						node.fx = centerX + radius * Math.cos(angle);
						node.fy = centerY + radius * Math.sin(angle);
					});
					break;

				case "grid":
					const cols = Math.ceil(Math.sqrt(nodes.length));
					const spacing = Math.min(width / (cols + 1), height / (cols + 1));
					nodes.forEach((node, i) => {
						const row = Math.floor(i / cols);
						const col = i % cols;
						node.fx = spacing * (col + 1);
						node.fy = spacing * (row + 1);
					});
					break;

				case "radial":
					nodes.forEach((node, i) => {
						const level = Math.floor(i / 8) + 1;
						const angleStep =
							(2 * Math.PI) / Math.min(8, nodes.length - (level - 1) * 8);
						const angle = angleStep * (i % 8);
						const radius = level * 60;
						node.fx = centerX + radius * Math.cos(angle);
						node.fy = centerY + radius * Math.sin(angle);
					});
					break;

				case "hierarchy":
					// Simple hierarchy layout
					const levels = Math.ceil(Math.sqrt(nodes.length));
					const nodesByLevel = Array.from(
						{ length: levels },
						() => [] as Node[],
					);
					nodes.forEach((node, i) => {
						const level = i % levels;
						nodesByLevel[level].push(node);
					});

					nodesByLevel.forEach((levelNodes, level) => {
						const y = (height / (levels + 1)) * (level + 1);
						levelNodes.forEach((node, i) => {
							const x = (width / (levelNodes.length + 1)) * (i + 1);
							node.fx = x;
							node.fy = y;
						});
					});
					break;

				default: // force
					nodes.forEach((node) => {
						node.fx = undefined;
						node.fy = undefined;
					});
					break;
			}

			if (simulation.current) {
				// Update simulation center
				simulation.current
					.force("center", d3.forceCenter(centerX, centerY))
					.alpha(0.3)
					.restart();
			}
		},
		[width, height],
	); // Use props directly instead of dimensions state

	// Helper function to get relative position
	const getRelativePosition = useCallback((event: MouseEvent) => {
		if (!containerRef.current) return { x: event.clientX, y: event.clientY };

		const containerRect = containerRef.current.getBoundingClientRect();
		return {
			x: event.clientX - containerRect.left,
			y: event.clientY - containerRect.top,
		};
	}, []);

	// Handle context menu
	const handleContextMenu = useCallback(
		(
			event: MouseEvent,
			type: "node" | "edge",
			data: Node | Edge,
			position?: { x: number; y: number },
		) => {
			if (!editable) return;

			event.preventDefault();
			event.stopPropagation();

			// For edges, use the calculated position from the edge center
			// For nodes, calculate relative position
			const menuPosition = position || getRelativePosition(event);

			setContextMenuPosition(menuPosition);
			setContextMenuTarget({ type, data });
		},
		[editable, getRelativePosition],
	);

	// Handle node edit
	const handleEditNode = (node: Node) => {
		setEditingNode({
			...node,
			entity_text: node.text || node.name || node.label || "",
			entity_type: node.type || "",
		});
		setShowEditNodeDialog(true);
		setContextMenuPosition(null);
	};

	// Handle node delete
	const handleDeleteNode = (node: Node) => {
		setShowDeleteConfirmation(true);
		setDeleteNodeId(node.id);
		setContextMenuPosition(null);
	};

	// Handle edge edit
	const handleEditEdge = (edge: Edge) => {
		setEditingEdge({
			id: edge.id,
			source_entity_id:
				typeof edge.source === "string" ? edge.source : edge.source.id,
			target_entity_id:
				typeof edge.target === "string" ? edge.target : edge.target.id,
			relationship_type: edge.type || "",
			properties: edge.properties || {},
		});
		setShowEditEdgeDialog(true);
		setContextMenuPosition(null);
	};

	// Save node changes
	const handleSaveNode = () => {
		if (!editingNode) return;

		updateEntityMutation.mutate({
			id: editingNode.id,
			properties: {
				...editingNode.properties,
				entity_text: editingNode.entity_text,
				entity_type: editingNode.entity_type,
			},
		});
	};

	// Save edge changes
	const handleSaveEdge = () => {
		if (!editingEdge) return;

		createRelationshipMutation.mutate({
			source_entity_id: editingEdge.source_entity_id,
			target_entity_id: editingEdge.target_entity_id,
			relationship_type: editingEdge.relationship_type,
			properties: editingEdge.properties,
		});
	};

	// Create new node
	const handleCreateNode = () => {
		try {
			const properties = JSON.parse(newNodeForm.properties);
			createEntityMutation.mutate({
				entity_text: newNodeForm.entity_text,
				entity_type: newNodeForm.entity_type,
				properties,
			});
		} catch (error) {
			toast.error("Properties phải là JSON hợp lệ");
		}
	};

	// Create new edge
	const handleCreateEdge = () => {
		try {
			const properties = JSON.parse(newEdgeForm.properties);
			createRelationshipMutation.mutate({
				source_entity_id: newEdgeForm.source_entity_id,
				target_entity_id: newEdgeForm.target_entity_id,
				relationship_type: newEdgeForm.relationship_type,
				properties,
			});
		} catch (error) {
			toast.error("Properties phải là JSON hợp lệ");
		}
	};

	// Apply layout when layout type changes
	useEffect(() => {
		if (data.nodes && data.edges && simulation.current) {
			applyLayout(data.nodes as Node[], data.edges as Edge[], layoutType);
		}
	}, [layoutType, applyLayout, data.nodes, data.edges]);

	// Close context menu on click outside
	useEffect(() => {
		const handleClickOutside = () => setContextMenuPosition(null);
		document.addEventListener("click", handleClickOutside);
		return () => document.removeEventListener("click", handleClickOutside);
	}, []);

	useEffect(() => {
		if (!data.nodes || !data.edges || !svgRef.current) return;

		const svg = d3.select(svgRef.current);
		svg.selectAll("*").remove();

		// Create main group for zoom/pan
		const g = svg.append("g").attr("class", "main-group");

		// Create tooltip
		const tooltip = d3.select(tooltipRef.current);

		// Setup zoom behavior
		zoom.current = d3
			.zoom<SVGSVGElement, unknown>()
			.scaleExtent([0.1, 10])
			.on("zoom", (event) => {
				g.attr("transform", event.transform);
				setTransform(event.transform);
			});

		svg.call(zoom.current);

		// Create simulation
		simulation.current = d3
			.forceSimulation(data.nodes as d3.SimulationNodeDatum[])
			.force("charge", d3.forceManyBody().strength(-400))
			.force(
				"center",
				d3.forceCenter(dimensions.width / 2, dimensions.height / 2),
			)
			.force("collision", d3.forceCollide().radius(35));

		// Only add link force for force layout
		if (layoutType === "force") {
			simulation.current.force(
				"link",
				d3
					.forceLink(data.edges)
					.id((d: any) => d.id)
					.distance(150),
			);
		}

		// Apply layout immediately
		applyLayout(data.nodes as Node[], data.edges as Edge[], layoutType);

		// Create arrow markers with better visibility
		const defs = svg.append("defs");

		// Create gradient for central nodes
		const centralGradient = defs
			.append("radialGradient")
			.attr("id", "centralGradient")
			.attr("cx", "50%")
			.attr("cy", "50%")
			.attr("r", "50%");

		centralGradient
			.append("stop")
			.attr("offset", "0%")
			.attr("style", "stop-color:#fbbf24;stop-opacity:0.8");

		centralGradient
			.append("stop")
			.attr("offset", "50%")
			.attr("style", "stop-color:#f59e0b;stop-opacity:0.6");

		centralGradient
			.append("stop")
			.attr("offset", "100%")
			.attr("style", "stop-color:#d97706;stop-opacity:0.4");

		// Create glow filter for central nodes
		const glowFilter = defs
			.append("filter")
			.attr("id", "glow")
			.attr("x", "-50%")
			.attr("y", "-50%")
			.attr("width", "200%")
			.attr("height", "200%");

		glowFilter
			.append("feGaussianBlur")
			.attr("stdDeviation", "4")
			.attr("result", "coloredBlur");

		const feMerge = glowFilter.append("feMerge");
		feMerge.append("feMergeNode").attr("in", "coloredBlur");
		feMerge.append("feMergeNode").attr("in", "SourceGraphic");

		// Create drop shadow filter
		const dropShadowFilter = defs
			.append("filter")
			.attr("id", "dropshadow")
			.attr("x", "-50%")
			.attr("y", "-50%")
			.attr("width", "200%")
			.attr("height", "200%");

		dropShadowFilter
			.append("feDropShadow")
			.attr("dx", "2")
			.attr("dy", "2")
			.attr("stdDeviation", "3")
			.attr("flood-color", "#000")
			.attr("flood-opacity", "0.3");

		// Create arrow marker
		defs
			.append("marker")
			.attr("id", "arrowhead")
			.attr("viewBox", "0 -5 10 10")
			.attr("refX", 25)
			.attr("refY", 0)
			.attr("markerWidth", 4)
			.attr("markerHeight", 4)
			.attr("orient", "auto")
			.append("path")
			.attr("d", "M0,-5L10,0L0,5")
			.attr("fill", "#666")
			.attr("stroke", "#333")
			.attr("stroke-width", 0.5);

		// Create edge labels for properties
		const edgeLabelGroup = g.append("g").attr("class", "edge-labels");

		// Create links
		const link = g
			.append("g")
			.attr("class", "links")
			.selectAll("line")
			.data(data.edges)
			.enter()
			.append("line")
			.attr("stroke", config?.edge_config?.default_color || "#666")
			.attr("stroke-opacity", 0.7)
			.attr("stroke-width", (d: any) => {
				return d.properties && Object.keys(d.properties).length > 0 ? 3 : 2;
			})
			.attr("marker-end", "url(#arrowhead)")
			// .attr("marker-start", "none") // Explicitly no start marker
			.style("cursor", editable ? "pointer" : "default")
			.on("contextmenu", function (event, d: any) {
				if (editable) {
					// Calculate edge center position
					const sourceNode =
						typeof d.source === "object"
							? d.source
							: data.nodes.find((n: any) => n.id === d.source);
					const targetNode =
						typeof d.target === "object"
							? d.target
							: data.nodes.find((n: any) => n.id === d.target);

					if (sourceNode && targetNode) {
						const centerX = (sourceNode.x + targetNode.x) / 2;
						const centerY = (sourceNode.y + targetNode.y) / 2;

						// Convert to screen coordinates
						const currentTransform = d3.zoomTransform(svg.node() as Element);
						const screenX = currentTransform.applyX(centerX);
						const screenY = currentTransform.applyY(centerY);

						// Get container offset
						const containerRect = containerRef.current?.getBoundingClientRect();
						const finalX = screenX + (containerRect?.left || 0);
						const finalY = screenY + (containerRect?.top || 0);

						handleContextMenu(event, "edge", d, { x: finalX, y: finalY });
					}
				}
			})
			.on("mouseover", function (event, d: any) {
				// Highlight edge
				d3.select(this).attr("stroke-width", 4).attr("stroke-opacity", 1);

				// Show tooltip
				const sourceNode =
					typeof d.source === "object"
						? d.source
						: data.nodes.find((n: any) => n.id === d.source);
				const targetNode =
					typeof d.target === "object"
						? d.target
						: data.nodes.find((n: any) => n.id === d.target);

				if (sourceNode && targetNode && tooltipRef.current) {
					const tooltipContent = `
						<div style="background: white; border: 1px solid #ccc; border-radius: 8px; padding: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); min-width: 200px;">
							<div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1f2937;">
								${d.type || "Relationship"}
							</div>
							<div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">
								<strong>Từ:</strong> ${sourceNode.label || sourceNode.name || sourceNode.id}
							</div>
							<div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
								<strong>Đến:</strong> ${targetNode.label || targetNode.name || targetNode.id}
							</div>
							${
								d.properties && Object.keys(d.properties).length > 0
									? `<div style="font-size: 12px; color: #374151;">
									<strong>Properties:</strong> ${Object.keys(d.properties).length} thuộc tính
								</div>`
									: ""
							}
						</div>
					`;

					tooltip
						.style("opacity", 1)
						.style("left", getRelativePosition(event).x + 10 + "px")
						.style("top", getRelativePosition(event).y + 10 + "px")
						.html(tooltipContent);
				}
			})
			.on("mouseout", function () {
				d3.select(this)
					.attr("stroke-width", (d: any) =>
						d.properties && Object.keys(d.properties).length > 0 ? 3 : 2,
					)
					.attr("stroke-opacity", 0.7);
				if (tooltipRef.current) {
					tooltip.style("opacity", 0);
				}
			});

		// Create edge labels
		const edgeLabel = edgeLabelGroup
			.selectAll("text")
			.data(data.edges)
			.enter()
			.append("text")
			.attr("class", "edge-label")
			.attr("font-size", 10)
			.attr("fill", "#666")
			.attr("text-anchor", "middle")
			.attr("background", "white")
			.style("pointer-events", "none")
			.text((d: any) => {
				if (d.type) return d.type;
				if (d.properties && d.properties.type) return d.properties.type;
				return "";
			});

		// Create node groups
		const nodeGroup = g
			.append("g")
			.attr("class", "nodes")
			.selectAll("g")
			.data(data.nodes)
			.enter()
			.append("g")
			.attr("class", "node-group")
			.style("cursor", editable ? "pointer" : "default")
			.call(
				d3
					.drag<SVGGElement, d3.SimulationNodeDatum>()
					.on("start", dragstarted)
					.on("drag", dragged)
					.on("end", dragended),
			);

		// Add circles for nodes
		const node = nodeGroup
			.append("circle")
			.attr("r", (d: any) => {
				const baseSize = config?.node_config?.size_range?.[0] || 15;
				const propertiesCount = d.properties
					? Object.keys(d.properties).length
					: 0;
				const size = Math.max(baseSize, baseSize + propertiesCount * 2);

				// Make central nodes significantly larger
				return isCentralNode(d.id) ? size * 1.5 : size;
			})
			.attr("fill", (d: any) => {
				// Use special gradient for central nodes
				if (isCentralNode(d.id)) {
					return "url(#centralGradient)";
				}

				return (
					config?.node_config?.color_mapping?.[d.type] ||
					config?.node_config?.default_color ||
					getNodeColor(d.type)
				);
			})
			.attr("stroke", (d: any) => {
				// Special stroke for central nodes
				return isCentralNode(d.id) ? "#f59e0b" : "#fff";
			})
			.attr("stroke-width", (d: any) => {
				// Thicker stroke for central nodes
				return isCentralNode(d.id) ? 4 : 3;
			})
			.attr("filter", (d: any) => {
				// Apply glow filter to central nodes
				return isCentralNode(d.id) ? "url(#glow)" : "url(#dropshadow)";
			})
			.style("cursor", editable ? "pointer" : "default")
			.on("mouseover", function (event, d: any) {
				if (tooltipRef.current) {
					const tooltipContent = createTooltipContent(d);
					tooltip
						.style("opacity", 1)
						.style("left", getRelativePosition(event).x + 10 + "px")
						.style("top", getRelativePosition(event).y - 10 + "px")
						.html(tooltipContent);
				}

				highlightConnected(d, link, nodeGroup);
			})
			.on("mouseout", function () {
				if (tooltipRef.current) {
					tooltip.style("opacity", 0);
				}
				link
					.attr("stroke-opacity", 0.7)
					.attr("stroke-width", (d: any) =>
						d.properties && Object.keys(d.properties).length > 0 ? 2 : 1,
					);
				nodeGroup.select("circle").attr("opacity", 1);
				edgeLabel.attr("opacity", 1);
			})
			.on("click", function (event, d: any) {
				setSelectedNode(d);
			})
			.on("contextmenu", function (event, d: any) {
				if (editable) {
					handleContextMenu(event, "node", d);
				}
			});

		// Add pulsing animation for central nodes
		nodeGroup
			.filter((d: any) => isCentralNode(d.id))
			.select("circle")
			.append("animateTransform")
			.attr("attributeName", "transform")
			.attr("attributeType", "XML")
			.attr("type", "scale")
			.attr("values", "1;1.1;1")
			.attr("dur", "2s")
			.attr("repeatCount", "indefinite");

		// Add central node indicator (crown icon)
		nodeGroup
			.filter((d: any) => isCentralNode(d.id))
			.append("text")
			.attr("class", "central-indicator")
			.text("⭐")
			.attr("font-size", 16)
			.attr("text-anchor", "middle")
			.attr("dy", -35)
			.style("pointer-events", "none")
			.style("opacity", 0.9);

		// Add main labels (node.text)
		const mainLabel = nodeGroup
			.append("text")
			.attr("class", "main-label")
			.text((d: any) => {
				const text = d.text || d.name || d.label || d.id;
				return text.length > 15 ? text.substring(0, 12) + "..." : text;
			})
			.attr("font-size", 12)
			.attr("font-weight", "bold")
			.attr("text-anchor", "middle")
			.attr("dy", -20)
			.attr("fill", "#333")
			.style("pointer-events", "none");

		// Add type labels
		const typeLabel = nodeGroup
			.append("text")
			.attr("class", "type-label")
			.text((d: any) => d.type || "Unknown")
			.attr("font-size", 10)
			.attr("text-anchor", "middle")
			.attr("dy", 30)
			.attr("fill", "#666")
			.attr("font-style", "italic")
			.style("pointer-events", "none");

		// Add properties indicator
		const propertiesIndicator = nodeGroup
			.filter((d: any) => d.properties && Object.keys(d.properties).length > 0)
			.append("text")
			.attr("class", "properties-indicator")
			.text((d: any) => `[${Object.keys(d.properties).length}]`)
			.attr("font-size", 8)
			.attr("text-anchor", "middle")
			.attr("dy", 42)
			.attr("fill", "#999")
			.style("pointer-events", "none");

		// Simulation tick function
		function tick() {
			link
				.attr("x1", (d: any) => d.source.x)
				.attr("y1", (d: any) => d.source.y)
				.attr("x2", (d: any) => d.target.x)
				.attr("y2", (d: any) => d.target.y);

			nodeGroup.attr("transform", (d: any) => `translate(${d.x},${d.y})`);

			edgeLabel
				.attr("x", (d: any) => (d.source.x + d.target.x) / 2)
				.attr("y", (d: any) => (d.source.y + d.target.y) / 2 - 8);
		}

		simulation.current.on("tick", tick);

		function dragstarted(event: any, d: any) {
			if (!event.active && simulation.current) {
				simulation.current.alphaTarget(0.3).restart();
			}
			d.fx = d.x;
			d.fy = d.y;
		}

		function dragged(event: any, d: any) {
			d.fx = event.x;
			d.fy = event.y;
		}

		function dragended(event: any, d: any) {
			if (!event.active && simulation.current) {
				simulation.current.alphaTarget(0);
			}
			if (layoutType === "force") {
				d.fx = null;
				d.fy = null;
			}
		}

		function highlightConnected(targetNode: any, links: any, nodes: any) {
			const connectedIds = new Set();

			links.each(function (d: any) {
				if (d.source.id === targetNode.id) {
					connectedIds.add(d.target.id);
				}
				if (d.target.id === targetNode.id) {
					connectedIds.add(d.source.id);
				}
			});

			links
				.attr("stroke-opacity", (d: any) =>
					d.source.id === targetNode.id || d.target.id === targetNode.id
						? 1
						: 0.2,
				)
				.attr("stroke-width", (d: any) =>
					d.source.id === targetNode.id || d.target.id === targetNode.id
						? 4
						: 2,
				);

			nodes
				.select("circle")
				.attr("opacity", (d: any) =>
					d.id === targetNode.id || connectedIds.has(d.id) ? 1 : 0.3,
				);

			edgeLabel.attr("opacity", (d: any) =>
				d.source.id === targetNode.id || d.target.id === targetNode.id
					? 1
					: 0.3,
			);
		}

		return () => {
			if (simulation.current) {
				simulation.current.stop();
			}
		};
	}, [
		data.nodes,
		data.edges,
		config,
		editable,
		layoutType,
		dimensions.width,
		dimensions.height,
	]); // Include specific dimensions

	// Close context menu on click outside
	useEffect(() => {
		const handleClickOutside = () => setContextMenuPosition(null);
		document.addEventListener("click", handleClickOutside);
		return () => document.removeEventListener("click", handleClickOutside);
	}, []);

	// Move functions before useEffect to avoid dependency issues
	const getNodeColor = useCallback((type: string): string => {
		const colorMap: { [key: string]: string } = {
			BANK: "#2563eb",
			BRANCH: "#059669",
			ACCOUNT: "#dc2626",
			CUSTOMER: "#7c3aed",
			PRODUCT: "#ea580c",
			SERVICE: "#0891b2",
			TRANSACTION: "#be123c",
			REGULATION: "#4338ca",
			CARD: "#9333ea",
			LOAN: "#c2410c",
		};
		return colorMap[type?.toUpperCase()] || "#64748b";
	}, []);

	const createTooltipContent = useCallback(
		(node: any): string => {
			const isCentral = isCentralNode(node.id);

			let content = `
			<div style="background: white; border: 1px solid #ccc; border-radius: 8px; padding: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); min-width: 200px;">
				<div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1f2937; display: flex; align-items: center; gap: 6px;">
					${isCentral ? "⭐" : ""}
					${node.text || node.name || node.label || node.id}
					${isCentral ? '<span style="background: #fbbf24; color: #92400e; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600;">CENTRAL</span>' : ""}
				</div>
				<div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
					<strong>Loại:</strong> ${node.type || "Unknown"}
				</div>
				<div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
					<strong>ID:</strong> ${node.id}
				</div>
		`;

			if (node.properties && Object.keys(node.properties).length > 0) {
				content += `
				<div style="font-size: 12px; color: #374151; margin-top: 8px;">
					<strong>Thuộc tính:</strong>
					<div style="margin-top: 4px; padding: 6px; background: #f9fafb; border-radius: 4px;">
			`;

				Object.entries(node.properties)
					.slice(0, 3)
					.forEach(([key, value]) => {
						content += `
					<div style="margin: 2px 0;">
						<span style="font-weight: 500; color: #4b5563;">${key}:</span> 
						<span style="color: #6b7280;">${String(value).length > 20 ? String(value).substring(0, 17) + "..." : value}</span>
					</div>
				`;
					});

				if (Object.keys(node.properties).length > 3) {
					content += `<div style="color: #9ca3af; font-size: 11px;">... và ${Object.keys(node.properties).length - 3} thuộc tính khác</div>`;
				}

				content += `
					</div>
				</div>
			`;
			}

			content += `</div>`;
			return content;
		},
		[isCentralNode],
	);

	const formatPropertiesForPanel = useCallback((properties: any): string => {
		if (!properties || Object.keys(properties).length === 0) {
			return '<p style="color: #6b7280; font-style: italic;">Không có thuộc tính</p>';
		}

		let formatted = '<div style="space-y: 8px;">';
		Object.entries(properties).forEach(([key, value]) => {
			formatted += `
				<div style="padding: 8px; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 8px;">
					<div style="font-weight: 600; color: #374151; margin-bottom: 4px;">${key}</div>
					<div style="color: #6b7280; font-size: 14px; word-break: break-word;">${JSON.stringify(value, null, 2)}</div>
				</div>
			`;
		});
		formatted += "</div>";
		return formatted;
	}, []);

	return (
		<div
			ref={containerRef}
			className={`relative ${isFullscreen ? "w-screen h-screen fixed inset-0 z-50" : "w-full"} ${isFullscreen ? "bg-white" : ""}`}
			style={{
				width: isFullscreen ? "100vw" : `${width}px`,
				height: isFullscreen ? "100vh" : `${height}px`,
				overflow: "hidden",
				boxSizing: "border-box",
			}}
		>
			{/* Control Panel - Top Left */}
			{showControls && (
				<Card className="absolute top-4 left-4 z-30 bg-white/95 backdrop-blur-sm shadow-lg border">
					<CardHeader className="pb-3">
						<div className="flex items-center justify-between">
							<CardTitle className="text-sm font-semibold text-slate-800">
								Điều Khiển
							</CardTitle>
							<Button
								size="sm"
								variant="ghost"
								onClick={() => setShowControls(false)}
								className="h-6 w-6 p-0"
							>
								<EyeOff className="h-4 w-4" />
							</Button>
						</div>
					</CardHeader>
					<CardContent className="space-y-3">
						{/* Layout Selection */}
						<div>
							<Label className="text-xs font-medium text-slate-600 mb-2">
								Layout
							</Label>
							<Select
								value={layoutType}
								onValueChange={(value: LayoutType) => setLayoutType(value)}
							>
								<SelectTrigger className="h-8 text-xs">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="force">Force Directed</SelectItem>
									<SelectItem value="circle">Circle</SelectItem>
									<SelectItem value="grid">Grid</SelectItem>
									<SelectItem value="hierarchy">Hierarchy</SelectItem>
									<SelectItem value="radial">Radial</SelectItem>
								</SelectContent>
							</Select>
						</div>

						{/* Zoom Controls */}
						<div>
							<Label className="text-xs font-medium text-slate-600 mb-2">
								Zoom
							</Label>
							<div className="grid grid-cols-2 gap-1">
								<Button
									size="sm"
									variant="outline"
									onClick={() => {
										if (zoom.current && svgRef.current) {
											const svg = d3.select(svgRef.current);
											svg
												.transition()
												.duration(200)
												.call(zoom.current.scaleBy, 1.5);
										}
									}}
									title="Phóng to"
									className="h-8 p-0"
								>
									<ZoomIn className="h-4 w-4" />
								</Button>
								<Button
									size="sm"
									variant="outline"
									onClick={() => {
										if (zoom.current && svgRef.current) {
											const svg = d3.select(svgRef.current);
											svg
												.transition()
												.duration(200)
												.call(zoom.current.scaleBy, 0.67);
										}
									}}
									title="Thu nhỏ"
									className="h-8 p-0"
								>
									<ZoomOut className="h-4 w-4" />
								</Button>
								<Button
									size="sm"
									variant="outline"
									onClick={resetZoom}
									title="Reset zoom"
									className="h-8 p-0"
								>
									<Home className="h-4 w-4" />
								</Button>
								<Button
									size="sm"
									variant="outline"
									onClick={fitToView}
									title="Vừa toàn bộ graph"
									className="h-8 p-0"
								>
									<Maximize className="h-4 w-4" />
								</Button>
							</div>
						</div>

						{/* View Controls */}
						<div>
							<Label className="text-xs font-medium text-slate-600 mb-2">
								View
							</Label>
							<div className="space-y-1">
								<Button
									size="sm"
									variant="outline"
									onClick={toggleFullscreen}
									title={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}
									className="h-8 w-full text-xs"
								>
									{isFullscreen ? "Thu nhỏ" : "Toàn màn hình"}
								</Button>

								{/* Focus Central Nodes button */}
								{getCentralNodes().length > 0 && (
									<Button
										size="sm"
										variant="outline"
										onClick={focusOnCentralNodes}
										title="Focus vào central nodes"
										className="h-8 w-full text-xs bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100"
									>
										<span className="mr-1">👑</span>
										Focus Central ({getCentralNodes().length})
									</Button>
								)}
							</div>
						</div>

						{/* Export Controls */}
						<div>
							<Label className="text-xs font-medium text-slate-600 mb-2">
								Export
							</Label>
							<div className="flex gap-1">
								<Button
									size="sm"
									variant="outline"
									onClick={() => exportAsImage("png")}
									title="Xuất ảnh PNG"
									className="h-8 flex-1 text-xs"
								>
									<Camera className="h-3 w-3 mr-1" />
									PNG
								</Button>
								<Button
									size="sm"
									variant="outline"
									onClick={() => exportAsImage("svg")}
									title="Xuất ảnh SVG"
									className="h-8 flex-1 text-xs"
								>
									<Download className="h-3 w-3 mr-1" />
									SVG
								</Button>
							</div>
						</div>

						{/* Edit Controls */}
						{editable && (
							<div>
								<Label className="text-xs font-medium text-slate-600 mb-2">
									Edit
								</Label>
								<div className="flex gap-1">
									<Dialog
										open={showCreateNodeDialog}
										onOpenChange={setShowCreateNodeDialog}
									>
										<DialogTrigger asChild>
											<Button
												size="sm"
												variant="default"
												className="h-8 flex-1 text-xs"
											>
												<Plus className="h-3 w-3 mr-1" />
												Node
											</Button>
										</DialogTrigger>
									</Dialog>

									<Dialog
										open={showCreateEdgeDialog}
										onOpenChange={setShowCreateEdgeDialog}
									>
										<DialogTrigger asChild>
											<Button
												size="sm"
												variant="default"
												className="h-8 flex-1 text-xs"
											>
												<Plus className="h-3 w-3 mr-1" />
												Edge
											</Button>
										</DialogTrigger>
									</Dialog>
								</div>
							</div>
						)}

						{/* UI Toggle */}
						<div>
							<Label className="text-xs font-medium text-slate-600 mb-2">
								UI
							</Label>
							<div className="space-y-2">
								<div className="flex items-center justify-between">
									<span className="text-xs">Hướng dẫn</span>
									<Switch checked={showHints} onCheckedChange={setShowHints} />
								</div>
								<div className="flex items-center justify-between">
									<span className="text-xs">Chú thích</span>
									<Switch
										checked={showLegend}
										onCheckedChange={setShowLegend}
									/>
								</div>
							</div>
						</div>

						{/* Zoom Level Display */}
						<div className="text-xs text-slate-600 text-center bg-slate-50 rounded px-2 py-1">
							Zoom: {(transform.k * 100).toFixed(0)}%
						</div>
					</CardContent>
				</Card>
			)}

			{/* Show Controls Button */}
			{!showControls && (
				<Button
					size="sm"
					variant="outline"
					onClick={() => setShowControls(true)}
					className="absolute top-4 left-4 z-30 h-8 w-8 p-0 bg-white/95 backdrop-blur-sm"
					title="Hiện điều khiển"
				>
					<Eye className="h-4 w-4" />
				</Button>
			)}

			{/* Navigation Hint - Top Center */}
			{showHints && (
				<div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-xs text-blue-800 z-20">
					💡 Kéo để di chuyển • Scroll để zoom • Click node để xem chi tiết{" "}
					{editable && "• Chuột phải để chỉnh sửa"}
				</div>
			)}

			{/* Main SVG */}
			<svg
				ref={svgRef}
				width={dimensions.width}
				height={dimensions.height}
				className="border rounded-lg bg-white"
				style={{
					display: "block",
					width: `${dimensions.width}px`,
					height: `${dimensions.height}px`,
				}}
			/>

			{/* Tooltip */}
			<div
				ref={tooltipRef}
				className="absolute opacity-0 pointer-events-none z-40 transition-opacity duration-300"
			/>

			{/* Context Menu */}
			{contextMenuPosition && contextMenuTarget && editable && (
				<Card
					className="absolute z-50 shadow-lg py-1 border bg-white"
					style={{
						left: contextMenuPosition.x,
						top: contextMenuPosition.y,
						transform: "translate(-50%, -100%)",
					}}
				>
					<CardContent className="p-1">
						{contextMenuTarget.type === "node" ? (
							<div className="space-y-1">
								<Button
									size="sm"
									variant="ghost"
									onClick={() => handleEditNode(contextMenuTarget.data as Node)}
									className="w-full justify-start h-8"
								>
									<Edit className="h-4 w-4 mr-2" />
									Chỉnh sửa
								</Button>
								<AlertDialog>
									<AlertDialogTrigger asChild>
										<Button
											size="sm"
											variant="ghost"
											onClick={() =>
												handleDeleteNode(contextMenuTarget.data as Node)
											}
											className="w-full justify-start h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
										>
											<Trash2 className="h-4 w-4 mr-2" />
											Xóa
										</Button>
									</AlertDialogTrigger>
									<AlertDialogContent>
										<AlertDialogHeader>
											<AlertDialogTitle>Xác nhận xóa</AlertDialogTitle>
											<AlertDialogDescription>
												Bạn có chắc chắn muốn xóa node này? Hành động này không
												thể hoàn tác.
											</AlertDialogDescription>
										</AlertDialogHeader>
										<AlertDialogFooter>
											<AlertDialogCancel>Hủy</AlertDialogCancel>
											<AlertDialogAction className="bg-red-600 hover:bg-red-700">
												Xóa
											</AlertDialogAction>
										</AlertDialogFooter>
									</AlertDialogContent>
								</AlertDialog>
							</div>
						) : (
							<div className="space-y-1">
								<Button
									size="sm"
									variant="ghost"
									onClick={() => handleEditEdge(contextMenuTarget.data as Edge)}
									className="w-full justify-start h-8"
								>
									<Edit className="h-4 w-4 mr-2" />
									Chỉnh sửa
								</Button>
							</div>
						)}
					</CardContent>
				</Card>
			)}

			{/* Selected Node Panel - Right */}
			{selectedNode && (
				<Card className="absolute top-4 right-4 w-80 max-h-[calc(100vh-2rem)] z-30 bg-white shadow-lg border">
					<CardHeader className="pb-3">
						<div className="flex justify-between items-center">
							<CardTitle className="text-base font-semibold text-slate-800 flex items-center gap-2">
								{isCentralNode(selectedNode.id) && (
									<span className="text-lg">⭐</span>
								)}
								Chi tiết Node
								{isCentralNode(selectedNode.id) && (
									<Badge
										variant="default"
										className="bg-amber-100 text-amber-800 border-amber-300"
									>
										CENTRAL
									</Badge>
								)}
							</CardTitle>
							<Button
								size="sm"
								variant="ghost"
								onClick={() => setSelectedNode(null)}
								className="h-6 w-6 p-0"
							>
								<X className="h-4 w-4" />
							</Button>
						</div>
					</CardHeader>
					<CardContent className="space-y-4">
						<ScrollArea className="max-h-[60vh]">
							<div className="space-y-4">
								<div>
									<Label className="text-sm font-medium text-slate-700">
										Text
									</Label>
									<div className="mt-1 p-3 bg-slate-50 rounded border text-sm">
										{selectedNode.text ||
											selectedNode.name ||
											selectedNode.label ||
											"N/A"}
									</div>
								</div>

								<div>
									<Label className="text-sm font-medium text-slate-700">
										Type
									</Label>
									<div className="mt-1 p-3 bg-slate-50 rounded border text-sm">
										<Badge variant="outline">
											{selectedNode.type || "Unknown"}
										</Badge>
									</div>
								</div>

								<div>
									<Label className="text-sm font-medium text-slate-700">
										ID
									</Label>
									<div className="mt-1 p-3 bg-slate-50 rounded border text-sm font-mono break-all">
										{selectedNode.id}
									</div>
								</div>

								<div>
									<Label className="text-sm font-medium text-slate-700">
										Properties
									</Label>
									<div
										className="mt-1"
										dangerouslySetInnerHTML={{
											__html: formatPropertiesForPanel(selectedNode.properties),
										}}
									/>
								</div>
							</div>
						</ScrollArea>

						{editable && (
							<div className="pt-3 border-t">
								<Button
									size="sm"
									onClick={() => handleEditNode(selectedNode)}
									className="w-full"
								>
									<Edit className="h-4 w-4 mr-2" />
									Chỉnh sửa Node
								</Button>
							</div>
						)}
					</CardContent>
				</Card>
			)}

			{/* Legend - Bottom Left */}
			{showLegend && (
				<Card className="absolute bottom-4 left-4 max-w-xs bg-white/90 backdrop-blur-sm shadow-lg border z-20">
					<CardContent className="p-3">
						<div className="text-sm font-semibold text-slate-800 mb-2">
							Hướng dẫn:
						</div>
						<div className="text-xs text-slate-600 space-y-1">
							<div>• Di chuột qua node/edge để xem thông tin</div>
							<div>• Click node để xem chi tiết</div>
							<div>• Kéo thả để di chuyển node</div>
							<div>• Scroll để zoom in/out</div>
							{editable && <div>• Chuột phải để chỉnh sửa</div>}
							<div className="flex items-center gap-1">
								<ArrowRight className="h-3 w-3" />
								<span>Hướng relationship</span>
							</div>
							<div>• Số trong [...] là số lượng properties</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Edit Node Dialog */}
			<Dialog open={showEditNodeDialog} onOpenChange={setShowEditNodeDialog}>
				<DialogContent className="max-w-lg z-50">
					<DialogHeader>
						<DialogTitle>Chỉnh sửa Node</DialogTitle>
					</DialogHeader>
					<div className="space-y-4">
						<div>
							<Label htmlFor="entity_text">Text</Label>
							<Input
								id="entity_text"
								value={editingNode?.entity_text || ""}
								onChange={(e) =>
									setEditingNode((prev) =>
										prev ? { ...prev, entity_text: e.target.value } : null,
									)
								}
								placeholder="Nhập text cho entity"
							/>
						</div>

						<div>
							<Label htmlFor="entity_type">Type</Label>
							<Input
								id="entity_type"
								value={editingNode?.entity_type || ""}
								onChange={(e) =>
									setEditingNode((prev) =>
										prev ? { ...prev, entity_type: e.target.value } : null,
									)
								}
								placeholder="Nhập type cho entity"
							/>
						</div>

						<div>
							<Label htmlFor="properties">Properties (JSON)</Label>
							<Textarea
								id="properties"
								value={JSON.stringify(editingNode?.properties || {}, null, 2)}
								onChange={(e) => {
									try {
										const properties = JSON.parse(e.target.value);
										setEditingNode((prev) =>
											prev ? { ...prev, properties } : null,
										);
									} catch (err) {
										// Invalid JSON, keep the text but don't update the object
									}
								}}
								placeholder='{"key": "value"}'
								rows={6}
							/>
						</div>

						<div className="flex justify-end gap-2">
							<Button
								variant="outline"
								onClick={() => setShowEditNodeDialog(false)}
							>
								Hủy
							</Button>
							<Button
								onClick={handleSaveNode}
								disabled={updateEntityMutation.isPending}
							>
								{updateEntityMutation.isPending ? "Đang lưu..." : "Lưu"}
							</Button>
						</div>
					</div>
				</DialogContent>
			</Dialog>

			{/* Edit Edge Dialog */}
			<Dialog open={showEditEdgeDialog} onOpenChange={setShowEditEdgeDialog}>
				<DialogContent className="max-w-lg z-50">
					<DialogHeader>
						<DialogTitle>Chỉnh sửa Edge</DialogTitle>
					</DialogHeader>
					<div className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div>
								<Label htmlFor="source_entity_id">Source Entity ID</Label>
								<Input
									id="source_entity_id"
									value={editingEdge?.source_entity_id || ""}
									onChange={(e) =>
										setEditingEdge((prev) =>
											prev
												? { ...prev, source_entity_id: e.target.value }
												: null,
										)
									}
									placeholder="ID entity nguồn"
								/>
							</div>
							<div>
								<Label htmlFor="target_entity_id">Target Entity ID</Label>
								<Input
									id="target_entity_id"
									value={editingEdge?.target_entity_id || ""}
									onChange={(e) =>
										setEditingEdge((prev) =>
											prev
												? { ...prev, target_entity_id: e.target.value }
												: null,
										)
									}
									placeholder="ID entity đích"
								/>
							</div>
						</div>

						<div>
							<Label htmlFor="relationship_type">Relationship Type</Label>
							<Input
								id="relationship_type"
								value={editingEdge?.relationship_type || ""}
								onChange={(e) =>
									setEditingEdge((prev) =>
										prev
											? { ...prev, relationship_type: e.target.value }
											: null,
									)
								}
								placeholder="Loại relationship"
							/>
						</div>

						<div>
							<Label htmlFor="edge_properties">Properties (JSON)</Label>
							<Textarea
								id="edge_properties"
								value={JSON.stringify(editingEdge?.properties || {}, null, 2)}
								onChange={(e) => {
									try {
										const properties = JSON.parse(e.target.value);
										setEditingEdge((prev) =>
											prev ? { ...prev, properties } : null,
										);
									} catch (err) {
										// Invalid JSON
									}
								}}
								placeholder='{"key": "value"}'
								rows={4}
							/>
						</div>

						<div className="flex justify-end gap-2">
							<Button
								variant="outline"
								onClick={() => setShowEditEdgeDialog(false)}
							>
								Hủy
							</Button>
							<Button
								onClick={handleSaveEdge}
								disabled={createRelationshipMutation.isPending}
							>
								{createRelationshipMutation.isPending ? "Đang lưu..." : "Lưu"}
							</Button>
						</div>
					</div>
				</DialogContent>
			</Dialog>

			{/* Create Node Dialog */}
			<Dialog
				open={showCreateNodeDialog}
				onOpenChange={setShowCreateNodeDialog}
			>
				<DialogContent className="max-w-lg z-50">
					<DialogHeader>
						<DialogTitle>Tạo Node Mới</DialogTitle>
					</DialogHeader>
					<div className="space-y-4">
						<div>
							<Label htmlFor="new_entity_text">Text</Label>
							<Input
								id="new_entity_text"
								value={newNodeForm.entity_text}
								onChange={(e) =>
									setNewNodeForm((prev) => ({
										...prev,
										entity_text: e.target.value,
									}))
								}
								placeholder="Nhập text cho entity mới"
							/>
						</div>

						<div>
							<Label htmlFor="new_entity_type">Type</Label>
							<Input
								id="new_entity_type"
								value={newNodeForm.entity_type}
								onChange={(e) =>
									setNewNodeForm((prev) => ({
										...prev,
										entity_type: e.target.value,
									}))
								}
								placeholder="Nhập type cho entity mới"
							/>
						</div>

						<div>
							<Label htmlFor="new_properties">Properties (JSON)</Label>
							<Textarea
								id="new_properties"
								value={newNodeForm.properties}
								onChange={(e) =>
									setNewNodeForm((prev) => ({
										...prev,
										properties: e.target.value,
									}))
								}
								placeholder='{"key": "value"}'
								rows={4}
							/>
						</div>

						<div className="flex justify-end gap-2">
							<Button
								variant="outline"
								onClick={() => setShowCreateNodeDialog(false)}
							>
								Hủy
							</Button>
							<Button
								onClick={handleCreateNode}
								disabled={createEntityMutation.isPending}
							>
								{createEntityMutation.isPending ? "Đang tạo..." : "Tạo"}
							</Button>
						</div>
					</div>
				</DialogContent>
			</Dialog>

			{/* Create Edge Dialog */}
			<Dialog
				open={showCreateEdgeDialog}
				onOpenChange={setShowCreateEdgeDialog}
			>
				<DialogContent className="max-w-lg z-50">
					<DialogHeader>
						<DialogTitle>Tạo Edge Mới</DialogTitle>
					</DialogHeader>
					<div className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div>
								<Label htmlFor="new_source_entity">Source Entity ID</Label>
								<Input
									id="new_source_entity"
									value={newEdgeForm.source_entity_id}
									onChange={(e) =>
										setNewEdgeForm((prev) => ({
											...prev,
											source_entity_id: e.target.value,
										}))
									}
									placeholder="ID của entity nguồn"
								/>
							</div>
							<div>
								<Label htmlFor="new_target_entity">Target Entity ID</Label>
								<Input
									id="new_target_entity"
									value={newEdgeForm.target_entity_id}
									onChange={(e) =>
										setNewEdgeForm((prev) => ({
											...prev,
											target_entity_id: e.target.value,
										}))
									}
									placeholder="ID của entity đích"
								/>
							</div>
						</div>

						<div>
							<Label htmlFor="new_relationship_type">Relationship Type</Label>
							<Input
								id="new_relationship_type"
								value={newEdgeForm.relationship_type}
								onChange={(e) =>
									setNewEdgeForm((prev) => ({
										...prev,
										relationship_type: e.target.value,
									}))
								}
								placeholder="Loại relationship"
							/>
						</div>

						<div>
							<Label htmlFor="new_edge_properties">Properties (JSON)</Label>
							<Textarea
								id="new_edge_properties"
								value={newEdgeForm.properties}
								onChange={(e) =>
									setNewEdgeForm((prev) => ({
										...prev,
										properties: e.target.value,
									}))
								}
								placeholder='{"key": "value"}'
								rows={4}
							/>
						</div>

						<div className="flex justify-end gap-2">
							<Button
								variant="outline"
								onClick={() => setShowCreateEdgeDialog(false)}
							>
								Hủy
							</Button>
							<Button
								onClick={handleCreateEdge}
								disabled={createRelationshipMutation.isPending}
							>
								{createRelationshipMutation.isPending ? "Đang tạo..." : "Tạo"}
							</Button>
						</div>
					</div>
				</DialogContent>
			</Dialog>
			<AlertDialog
				open={showDeleteConfirmation}
				onOpenChange={setShowDeleteConfirmation}
			>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Xác nhận xóa</AlertDialogTitle>
						<AlertDialogDescription>
							Bạn có chắc chắn muốn xóa node này? Hành động này không thể hoàn
							tác.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Hủy</AlertDialogCancel>
						<AlertDialogAction
							onClick={() => {
								if (deleteNodeId) {
									deleteEntityMutation.mutate({ id: deleteNodeId });
								}
							}}
							className="bg-red-600 hover:bg-red-700"
						>
							Xóa
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	);
};
