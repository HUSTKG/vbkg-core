// packages/ui/src/ontology-graph/index.tsx
import React, { useEffect, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, RotateCw, Download, Maximize2, Minimize2 } from 'lucide-react';
import { cn } from '../../lib/utils';

// Define types for the OntologyGraph component
export interface OntologyClass {
  id: string | number;
  name: string;
  description?: string;
  properties?: Array<{
    name: string;
    type: string;
    required: boolean;
    description?: string;
  }>;
}

export interface OntologyRelation {
  id: string | number;
  name: string;
  source: string | number; // ID of source class
  target: string | number; // ID of target class
  description?: string;
}

export interface OntologyGraphProps {
  classes: OntologyClass[];
  relations: OntologyRelation[];
  onSelectNode?: (type: 'class' | 'relation', id: string | number) => void;
  selectedNodeId?: string | number;
  height?: string | number;
  className?: string;
  isLoading?: boolean;
  renderMode?: 'simple' | 'detailed';
  showControls?: boolean;
  isDraggable?: boolean;
  isZoomable?: boolean;
}

const OntologyGraph: React.FC<OntologyGraphProps> = ({
  classes,
  relations,
  onSelectNode,
  selectedNodeId,
  height = 500,
  className,
  isLoading = false,
  renderMode = 'detailed',
  showControls = true,
  isDraggable = true,
  isZoomable = true,
}) => {
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<SVGSVGElement>(null);

  // In a real implementation, we would use a library like D3.js, Cytoscape.js, or react-force-graph
  // For this mockup, we'll create a simple visualization to demonstrate the component structure

  const handleZoomIn = () => {
    if (zoom < 2) setZoom(prev => prev + 0.1);
  };

  const handleZoomOut = () => {
    if (zoom > 0.5) setZoom(prev => prev - 0.1);
  };

  const handleReset = () => {
    setZoom(1);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    
    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const downloadAsSVG = () => {
    if (!graphRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(graphRef.current);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const svgUrl = URL.createObjectURL(svgBlob);
    
    const downloadLink = document.createElement('a');
    downloadLink.href = svgUrl;
    downloadLink.download = 'ontology-graph.svg';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(svgUrl);
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // Generate mock positions for the classes in a circle layout
  const nodePositions = classes.map((cls, index) => {
    const angle = (index / classes.length) * 2 * Math.PI;
    const radius = 150;
    const x = 250 + radius * Math.cos(angle);
    const y = 200 + radius * Math.sin(angle);
    return { id: cls.id, x, y };
  });

  return (
    <div 
      ref={containerRef}
      className={cn(
        "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden relative",
        isFullscreen ? "fixed inset-0 z-50" : "",
        className
      )}
      style={{ height: isFullscreen ? '100vh' : height }}
    >
      {isLoading ? (
        <div className="w-full h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {showControls && (
            <div className="absolute top-2 right-2 flex space-x-1 z-10">
              <button 
                onClick={handleZoomIn} 
                disabled={!isZoomable || zoom >= 2}
                className="p-1.5 bg-white dark:bg-gray-700 rounded-md shadow hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50"
                aria-label="Zoom in"
              >
                <ZoomIn size={16} />
              </button>
              <button 
                onClick={handleZoomOut} 
                disabled={!isZoomable || zoom <= 0.5}
                className="p-1.5 bg-white dark:bg-gray-700 rounded-md shadow hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50"
                aria-label="Zoom out"
              >
                <ZoomOut size={16} />
              </button>
              <button 
                onClick={handleReset} 
                className="p-1.5 bg-white dark:bg-gray-700 rounded-md shadow hover:bg-gray-100 dark:hover:bg-gray-600"
                aria-label="Reset view"
              >
                <RotateCw size={16} />
              </button>
              <button 
                onClick={downloadAsSVG} 
                className="p-1.5 bg-white dark:bg-gray-700 rounded-md shadow hover:bg-gray-100 dark:hover:bg-gray-600"
                aria-label="Download as SVG"
              >
                <Download size={16} />
              </button>
              <button 
                onClick={toggleFullscreen} 
                className="p-1.5 bg-white dark:bg-gray-700 rounded-md shadow hover:bg-gray-100 dark:hover:bg-gray-600"
                aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
              >
                {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
            </div>
          )}

          <div 
            className="w-full h-full overflow-hidden"
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center center' }}
          >
            <svg 
              ref={graphRef}
              width="100%" 
              height="100%" 
              viewBox="0 0 500 400"
              className="ontology-graph"
            >
              {/* Draw relation lines */}
              {relations.map(relation => {
                const sourcePos = nodePositions.find(p => p.id === relation.source);
                const targetPos = nodePositions.find(p => p.id === relation.target);

                if (!sourcePos || !targetPos) return null;

                return (
                  <g key={`relation-${relation.id}`}>
                    <line 
                      x1={sourcePos.x} 
                      y1={sourcePos.y} 
                      x2={targetPos.x} 
                      y2={targetPos.y} 
                      stroke={relation.id === selectedNodeId ? "#3b82f6" : "#9ca3af"}
                      strokeWidth="2"
                      markerEnd="url(#arrow)"
                    />
                    {renderMode === 'detailed' && (
                      <text 
                        x={(sourcePos.x + targetPos.x) / 2} 
                        y={(sourcePos.y + targetPos.y) / 2 - 5}
                        textAnchor="middle"
                        fontSize="12"
                        fill="#6b7280"
                        className="text-xs"
                      >
                        {relation.name}
                      </text>
                    )}
                  </g>
                );
              })}

              {/* Arrow marker definition */}
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="5"
                  refY="5"
                  markerWidth="5"
                  markerHeight="5"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#9ca3af" />
                </marker>
              </defs>

              {/* Draw class nodes */}
              {classes.map((cls, index) => {
                const pos = nodePositions[index];
                const isSelected = cls.id === selectedNodeId;
                
                return (
                  <g 
                    key={`class-${cls.id}`}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={() => onSelectNode && onSelectNode('class', cls.id)}
                    className="cursor-pointer"
                    style={{ cursor: onSelectNode ? 'pointer' : 'default' }}
                  >
                    <circle 
                      r="30" 
                      fill={isSelected ? "#3b82f6" : "#f3f4f6"} 
                      stroke={isSelected ? "#2563eb" : "#d1d5db"}
                      strokeWidth="2"
                      className={isSelected ? "dark:fill-blue-900" : "dark:fill-gray-700"}
                    />
                    <text 
                      textAnchor="middle" 
                      dy="5"
                      fontSize="12"
                      fontWeight={isSelected ? "bold" : "normal"}
                      fill={isSelected ? "white" : "#374151"}
                      className={isSelected ? "dark:fill-white" : "dark:fill-gray-300"}
                    >
                      {cls.name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </>
      )}

      {classes.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full p-4 text-center">
          <p className="text-gray-500 dark:text-gray-400 mb-2">Không có dữ liệu Ontology</p>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Thêm classes và relations để bắt đầu xây dựng cấu trúc Ontology
          </p>
        </div>
      )}
    </div>
  );
};

export default OntologyGraph;
