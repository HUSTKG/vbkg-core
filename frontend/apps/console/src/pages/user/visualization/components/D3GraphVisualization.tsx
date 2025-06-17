import { GraphVisualizationConfig, VisualizationData } from "@vbkg/types";
import * as d3 from "d3";
import { useEffect, useRef, useState, useCallback } from "react";

export const D3GraphVisualization = ({
	data,
	config,
	width = 800,
	height = 600,
}: {
	data: VisualizationData;
	config: GraphVisualizationConfig;
	width?: number;
	height?: number;
}) => {
	const svgRef = useRef(null);
	const tooltipRef = useRef(null);
	const containerRef = useRef(null);
	const [selectedNode, setSelectedNode] = useState(null);
	const [isFullscreen, setIsFullscreen] = useState(false);
	const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
	const [dimensions, setDimensions] = useState({ width, height });

	// Zoom behavior
	const zoom = useRef(null);

	// Update dimensions when fullscreen changes
	useEffect(() => {
		if (isFullscreen) {
			setDimensions({ width: window.innerWidth, height: window.innerHeight });
		} else {
			setDimensions({ width, height });
		}
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
	const exportAsImage = useCallback((format: 'png' | 'svg' = 'png') => {
		const svg = svgRef.current;
		if (!svg) return;

		if (format === 'svg') {
			// Export as SVG
			const svgData = new XMLSerializer().serializeToString(svg);
			const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
			const url = URL.createObjectURL(svgBlob);
			
			const link = document.createElement('a');
			link.href = url;
			link.download = `graph-visualization.svg`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			URL.revokeObjectURL(url);
		} else {
			// Export as PNG
			const canvas = document.createElement('canvas');
			const context = canvas.getContext('2d');
			canvas.width = dimensions.width;
			canvas.height = dimensions.height;

			const data = new XMLSerializer().serializeToString(svg);
			const img = new Image();
			const svgBlob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' });
			const url = URL.createObjectURL(svgBlob);

			img.onload = () => {
				context.fillStyle = 'white';
				context.fillRect(0, 0, canvas.width, canvas.height);
				context.drawImage(img, 0, 0);
				
				canvas.toBlob((blob) => {
					const link = document.createElement('a');
					link.href = URL.createObjectURL(blob);
					link.download = `graph-visualization.png`;
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
					URL.revokeObjectURL(link.href);
				});
				
				URL.revokeObjectURL(url);
			};
			img.src = url;
		}
	}, [dimensions]);

	// Reset zoom
	const resetZoom = useCallback(() => {
		if (zoom.current && svgRef.current) {
			const svg = d3.select(svgRef.current);
			svg.transition().duration(750).call(
				zoom.current.transform,
				d3.zoomIdentity
			);
		}
	}, []);

	// Fit to view
	const fitToView = useCallback(() => {
		if (!data.nodes || !zoom.current || !svgRef.current) return;

		const svg = d3.select(svgRef.current);
		const bounds = svg.node().getBBox();
		const fullWidth = dimensions.width;
		const fullHeight = dimensions.height;
		const width = bounds.width;
		const height = bounds.height;
		const midX = bounds.x + width / 2;
		const midY = bounds.y + height / 2;

		if (width == 0 || height == 0) return;

		const scale = Math.min(fullWidth / width, fullHeight / height) * 0.8;
		const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];

		svg.transition().duration(750).call(
			zoom.current.transform,
			d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
		);
	}, [data.nodes, dimensions]);

	useEffect(() => {
		if (!data.nodes || !data.edges) return;

		const svg = d3.select(svgRef.current);
		svg.selectAll("*").remove();

		// Create main group for zoom/pan
		const g = svg.append("g").attr("class", "main-group");

		// Create tooltip
		const tooltip = d3.select(tooltipRef.current);

		// Setup zoom behavior
		zoom.current = d3.zoom()
			.scaleExtent([0.1, 10])
			.on("zoom", (event) => {
				g.attr("transform", event.transform);
				setTransform(event.transform);
			});

		svg.call(zoom.current);

		const simulation = d3
			.forceSimulation(data.nodes)
			.force(
				"link",
				d3
					.forceLink(data.edges)
					.id((d: any) => d.id)
					.distance(150),
			)
			.force("charge", d3.forceManyBody().strength(-400))
			.force("center", d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
			.force("collision", d3.forceCollide().radius(30));

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
			.attr("stroke", config?.edge_config?.default_color || "#999")
			.attr("stroke-opacity", 0.6)
			.attr("stroke-width", (d: any) => {
				return d.properties && Object.keys(d.properties).length > 0 ? 3 : 2;
			})
			.attr("marker-end", "url(#arrowhead)");

		// Add arrow markers
		svg.append("defs").selectAll("marker")
			.data(["arrowhead"])
			.enter().append("marker")
			.attr("id", d => d)
			.attr("viewBox", "0 -5 10 10")
			.attr("refX", 20)
			.attr("refY", 0)
			.attr("markerWidth", 6)
			.attr("markerHeight", 6)
			.attr("orient", "auto")
			.append("path")
			.attr("d", "M0,-5L10,0L0,5")
			.attr("fill", "#999");

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
			.call(
				d3
					.drag()
					.on("start", dragstarted)
					.on("drag", dragged)
					.on("end", dragended),
			);

		// Add circles for nodes
		const node = nodeGroup
			.append("circle")
			.attr("r", (d: any) => {
				const baseSize = config?.node_config?.size_range?.[0] || 12;
				const propertiesCount = d.properties ? Object.keys(d.properties).length : 0;
				return Math.max(baseSize, baseSize + propertiesCount * 2);
			})
			.attr("fill", (d: any) => {
				return (
					config?.node_config?.color_mapping?.[d.type] ||
					config?.node_config?.default_color ||
					getNodeColor(d.type)
				);
			})
			.attr("stroke", "#fff")
			.attr("stroke-width", 2)
			.on("mouseover", function(event, d: any) {
				const tooltipContent = createTooltipContent(d);
				tooltip
					.style("opacity", 1)
					.style("left", (event.pageX + 10) + "px")
					.style("top", (event.pageY - 10) + "px")
					.html(tooltipContent);
				
				highlightConnected(d, link, nodeGroup);
			})
			.on("mouseout", function() {
				tooltip.style("opacity", 0);
				link.attr("stroke-opacity", 0.6).attr("stroke-width", (d: any) => 
					d.properties && Object.keys(d.properties).length > 0 ? 3 : 2
				);
				nodeGroup.select("circle").attr("opacity", 1);
				edgeLabel.attr("opacity", 1);
			})
			.on("click", function(event, d: any) {
				setSelectedNode(d);
			});

		// Add main labels (node.text)
		const mainLabel = nodeGroup
			.append("text")
			.attr("class", "main-label")
			.text((d: any) => {
				return d.text || d.name || d.label || d.id;
			})
			.attr("font-size", 12)
			.attr("font-weight", "bold")
			.attr("text-anchor", "middle")
			.attr("dy", -15)
			.attr("fill", "#333");

		// Add type labels
		const typeLabel = nodeGroup
			.append("text")
			.attr("class", "type-label")
			.text((d: any) => d.type || "Unknown")
			.attr("font-size", 10)
			.attr("text-anchor", "middle")
			.attr("dy", 25)
			.attr("fill", "#666")
			.attr("font-style", "italic");

		// Add properties indicator
		const propertiesIndicator = nodeGroup
			.filter((d: any) => d.properties && Object.keys(d.properties).length > 0)
			.append("text")
			.attr("class", "properties-indicator")
			.text((d: any) => `[${Object.keys(d.properties).length} props]`)
			.attr("font-size", 8)
			.attr("text-anchor", "middle")
			.attr("dy", 35)
			.attr("fill", "#999");

		simulation.on("tick", () => {
			link
				.attr("x1", (d: any) => d.source.x)
				.attr("y1", (d: any) => d.source.y)
				.attr("x2", (d: any) => d.target.x)
				.attr("y2", (d: any) => d.target.y);

			nodeGroup.attr("transform", (d: any) => `translate(${d.x},${d.y})`);

			edgeLabel
				.attr("x", (d: any) => (d.source.x + d.target.x) / 2)
				.attr("y", (d: any) => (d.source.y + d.target.y) / 2 - 5);
		});

		function dragstarted(event: any, d: any) {
			if (!event.active) simulation.alphaTarget(0.3).restart();
			d.fx = d.x;
			d.fy = d.y;
		}

		function dragged(event: any, d: any) {
			d.fx = event.x;
			d.fy = event.y;
		}

		function dragended(event: any, d: any) {
			if (!event.active) simulation.alphaTarget(0);
			d.fx = null;
			d.fy = null;
		}

		function highlightConnected(targetNode: any, links: any, nodes: any) {
			const connectedIds = new Set();
			
			links.each(function(d: any) {
				if (d.source.id === targetNode.id) {
					connectedIds.add(d.target.id);
				}
				if (d.target.id === targetNode.id) {
					connectedIds.add(d.source.id);
				}
			});
			
			links
				.attr("stroke-opacity", (d: any) => 
					d.source.id === targetNode.id || d.target.id === targetNode.id ? 1 : 0.1
				)
				.attr("stroke-width", (d: any) => 
					d.source.id === targetNode.id || d.target.id === targetNode.id ? 4 : 2
				);
			
			nodes.select("circle")
				.attr("opacity", (d: any) => 
					d.id === targetNode.id || connectedIds.has(d.id) ? 1 : 0.3
				);
			
			edgeLabel
				.attr("opacity", (d: any) => 
					d.source.id === targetNode.id || d.target.id === targetNode.id ? 1 : 0.2
				);
		}

		return () => {
			simulation.stop();
		};
	}, [data, config, dimensions]);

	function getNodeColor(type: string): string {
		const colorMap: { [key: string]: string } = {
			'BANK': '#2563eb',
			'BRANCH': '#059669',
			'ACCOUNT': '#dc2626',
			'CUSTOMER': '#7c3aed',
			'PRODUCT': '#ea580c',
			'SERVICE': '#0891b2',
			'TRANSACTION': '#be123c',
			'REGULATION': '#4338ca',
			'CARD': '#9333ea',
			'LOAN': '#c2410c'
		};
		return colorMap[type?.toUpperCase()] || '#64748b';
	}

	function createTooltipContent(node: any): string {
		let content = `
			<div style="background: white; border: 1px solid #ccc; border-radius: 8px; padding: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); min-width: 200px;">
				<div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1f2937;">
					${node.text || node.name || node.label || node.id}
				</div>
				<div style="font-size: 12px; color: #6b7280; margin-bottom: 8px;">
					<strong>Loại:</strong> ${node.type || 'Unknown'}
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
			
			Object.entries(node.properties).forEach(([key, value]) => {
				content += `
					<div style="margin: 2px 0;">
						<span style="font-weight: 500; color: #4b5563;">${key}:</span> 
						<span style="color: #6b7280;">${value}</span>
					</div>
				`;
			});
			
			content += `
					</div>
				</div>
			`;
		}

		content += `</div>`;
		return content;
	}

	function formatPropertiesForPanel(properties: any): string {
		if (!properties || Object.keys(properties).length === 0) {
			return '<p style="color: #6b7280; font-style: italic;">Không có thuộc tính</p>';
		}

		let formatted = '<div style="space-y: 8px;">';
		Object.entries(properties).forEach(([key, value]) => {
			formatted += `
				<div style="padding: 8px; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 8px;">
					<div style="font-weight: 600; color: #374151; margin-bottom: 4px;">${key}</div>
					<div style="color: #6b7280; font-size: 14px;">${JSON.stringify(value, null, 2)}</div>
				</div>
			`;
		});
		formatted += '</div>';
		return formatted;
	}

	const controlButtonStyle = {
		background: 'white',
		border: '1px solid #d1d5db',
		borderRadius: '6px',
		padding: '8px 12px',
		margin: '2px',
		cursor: 'pointer',
		fontSize: '14px',
		display: 'flex',
		alignItems: 'center',
		gap: '6px',
		boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
		transition: 'all 0.2s'
	};

	return (
		<div 
			ref={containerRef}
			style={{ 
				position: 'relative',
				width: isFullscreen ? '100vw' : '100%',
				height: isFullscreen ? '100vh' : 'auto',
				background: isFullscreen ? 'white' : 'transparent'
			}}
		>
			{/* Control Panel */}
			<div 
				style={{
					position: 'absolute',
					top: 10,
					left: 10,
					display: 'flex',
					flexDirection: 'column',
					gap: '8px',
					zIndex: 200,
					background: 'rgba(255, 255, 255, 0.95)',
					padding: '12px',
					borderRadius: '8px',
					border: '1px solid #d1d5db',
					boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
				}}
			>
				<div style={{ fontWeight: 'bold', fontSize: '14px', color: '#374151', marginBottom: '4px' }}>
					Điều khiển
				</div>
				
				{/* Zoom Controls */}
				<div style={{ display: 'flex', gap: '4px' }}>
					<button
						style={controlButtonStyle}
						onClick={() => {
							if (zoom.current && svgRef.current) {
								const svg = d3.select(svgRef.current);
								svg.transition().duration(200).call(
									zoom.current.scaleBy, 1.5
								);
							}
						}}
						title="Phóng to"
					>
						🔍+
					</button>
					<button
						style={controlButtonStyle}
						onClick={() => {
							if (zoom.current && svgRef.current) {
								const svg = d3.select(svgRef.current);
								svg.transition().duration(200).call(
									zoom.current.scaleBy, 0.67
								);
							}
						}}
						title="Thu nhỏ"
					>
						🔍-
					</button>
					<button
						style={controlButtonStyle}
						onClick={resetZoom}
						title="Reset zoom"
					>
						🏠
					</button>
					<button
						style={controlButtonStyle}
						onClick={fitToView}
						title="Vừa màn hình"
					>
						📐
					</button>
				</div>

				{/* View Controls */}
				<div style={{ display: 'flex', gap: '4px' }}>
					<button
						style={controlButtonStyle}
						onClick={toggleFullscreen}
						title={isFullscreen ? "Thoát toàn màn hình" : "Toàn màn hình"}
					>
						{isFullscreen ? "🔳" : "⛶"}
					</button>
				</div>

				{/* Export Controls */}
				<div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
					<button
						style={controlButtonStyle}
						onClick={() => exportAsImage('png')}
						title="Xuất ảnh PNG"
					>
						📷 PNG
					</button>
					<button
						style={controlButtonStyle}
						onClick={() => exportAsImage('svg')}
						title="Xuất ảnh SVG"
					>
						🎨 SVG
					</button>
				</div>

				{/* Zoom Level Display */}
				<div style={{ 
					fontSize: '12px', 
					color: '#6b7280', 
					textAlign: 'center',
					padding: '4px',
					background: '#f9fafb',
					borderRadius: '4px'
				}}>
					Zoom: {(transform.k * 100).toFixed(0)}%
				</div>
			</div>

			{/* Navigation Hint */}
			<div 
				style={{
					position: 'absolute',
					top: 10,
					left: '50%',
					transform: 'translateX(-50%)',
					background: 'rgba(59, 130, 246, 0.1)',
					border: '1px solid rgba(59, 130, 246, 0.3)',
					borderRadius: '6px',
					padding: '8px 16px',
					fontSize: '12px',
					color: '#1e40af',
					zIndex: 150
				}}
			>
				💡 Kéo để di chuyển • Scroll để zoom • Click node để xem chi tiết
			</div>

			{/* Main SVG */}
			<svg
				ref={svgRef}
				width={dimensions.width}
				height={dimensions.height}
				className="border rounded-lg bg-white"
				style={{ display: 'block' }}
			/>
			
			{/* Tooltip */}
			<div
				ref={tooltipRef}
				style={{
					position: 'absolute',
					opacity: 0,
					pointerEvents: 'none',
					zIndex: 1000,
					transition: 'opacity 0.3s'
				}}
			/>

			{/* Selected Node Panel */}
			{selectedNode && (
				<div 
					style={{
						position: 'absolute',
						top: 10,
						right: 10,
						width: 300,
						maxHeight: dimensions.height - 20,
						overflow: 'auto',
						background: 'white',
						border: '1px solid #d1d5db',
						borderRadius: '8px',
						padding: '16px',
						boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
						zIndex: 100
					}}
				>
					<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
						<h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold', color: '#1f2937' }}>
							Chi tiết Node
						</h3>
						<button
							onClick={() => setSelectedNode(null)}
							style={{
								background: 'none',
								border: 'none',
								fontSize: '18px',
								cursor: 'pointer',
								color: '#6b7280'
							}}
						>
							×
						</button>
					</div>
					
					<div style={{ marginBottom: '16px' }}>
						<div style={{ marginBottom: '8px' }}>
							<strong style={{ color: '#374151' }}>Text:</strong>
							<div style={{ marginTop: '4px', padding: '8px', background: '#f9fafb', borderRadius: '4px', fontSize: '14px' }}>
								{selectedNode.text || selectedNode.name || selectedNode.label || 'N/A'}
							</div>
						</div>
						
						<div style={{ marginBottom: '8px' }}>
							<strong style={{ color: '#374151' }}>Type:</strong>
							<div style={{ marginTop: '4px', padding: '8px', background: '#f9fafb', borderRadius: '4px', fontSize: '14px' }}>
								{selectedNode.type || 'Unknown'}
							</div>
						</div>
						
						<div style={{ marginBottom: '8px' }}>
							<strong style={{ color: '#374151' }}>ID:</strong>
							<div style={{ marginTop: '4px', padding: '8px', background: '#f9fafb', borderRadius: '4px', fontSize: '14px', fontFamily: 'monospace' }}>
								{selectedNode.id}
							</div>
						</div>
					</div>
					
					<div>
						<strong style={{ color: '#374151' }}>Properties:</strong>
						<div 
							style={{ marginTop: '8px' }}
							dangerouslySetInnerHTML={{ 
								__html: formatPropertiesForPanel(selectedNode.properties) 
							}}
						/>
					</div>
				</div>
			)}

			{/* Legend */}
			<div 
				style={{
					position: 'absolute',
					bottom: 10,
					left: 10,
					background: 'rgba(255, 255, 255, 0.9)',
					border: '1px solid #d1d5db',
					borderRadius: '6px',
					padding: '12px',
					fontSize: '12px',
					maxWidth: '200px'
				}}
			>
				<div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#374151' }}>Hướng dẫn:</div>
				<div style={{ color: '#6b7280', lineHeight: '1.4' }}>
					• Di chuột qua node để xem thông tin<br/>
					• Click node để xem chi tiết<br/>
					• Kéo thả để di chuyển node<br/>
					• Scroll để zoom in/out<br/>
					• Số trong [...] là số lượng properties
				</div>
			</div>
		</div>
	);
};
