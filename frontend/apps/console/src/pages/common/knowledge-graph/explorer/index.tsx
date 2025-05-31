import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@vbkg/ui";
import {
  ArrowRight,
  Database,
  Download,
  ExternalLink,
  Layers,
  Link,
  Maximize,
  Network,
  RefreshCw,
  RotateCcw,
  Search,
  Settings,
  Upload,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useKGSubgraph } from "@vbkg/api-client";

export default function KnowledgeGraphExplorer() {
  const [selectedEntityId, setSelectedEntityId] = useState("1");
  const [radius, setRadius] = useState(2);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: graphData, isFetching: loading } =
    useKGSubgraph({
      entity_id: selectedEntityId,
      radius: radius,
    }) || {};

  const GraphVisualization = () => {
    if (loading) {
      return (
        <div className="h-96 flex items-center justify-center bg-muted rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p>Loading graph...</p>
          </div>
        </div>
      );
    }

    if (!graphData) {
      return (
        <div className="h-96 flex items-center justify-center bg-muted rounded-lg">
          <p className="text-muted-foreground">
            Select an entity to explore the graph
          </p>
        </div>
      );
    }

    return (
      <div className="h-96 bg-muted rounded-lg p-4 relative">
        {/* Simple graph visualization mockup */}
        <svg width="100%" height="100%" viewBox="0 0 800 400">
          {/* Draw edges first */}
          {graphData.edges.map((edge: any) => {
            const sourceNode = graphData.nodes.find(
              (n: any) => n.id === edge.source,
            );
            const targetNode = graphData.nodes.find(
              (n: any) => n.id === edge.target,
            );
            if (!sourceNode || !targetNode) return null;

            // Calculate positions in a circle layout
            const sourceIndex = graphData.nodes.findIndex(
              (n: any) => n.id === edge.source,
            );
            const targetIndex = graphData.nodes.findIndex(
              (n: any) => n.id === edge.target,
            );

            const centerX = 400;
            const centerY = 200;
            const radiusOffset = 120;

            const sourceAngle =
              (sourceIndex / graphData.nodes.length) * 2 * Math.PI;
            const targetAngle =
              (targetIndex / graphData.nodes.length) * 2 * Math.PI;

            const x1 = centerX + radiusOffset * Math.cos(sourceAngle);
            const y1 = centerY + radiusOffset * Math.sin(sourceAngle);
            const x2 = centerX + radiusOffset * Math.cos(targetAngle);
            const y2 = centerY + radiusOffset * Math.sin(targetAngle);

            return (
              <g key={edge.id}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke="#94a3b8"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
                <text
                  x={(x1 + x2) / 2}
                  y={(y1 + y2) / 2 - 10}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#64748b"
                  className="pointer-events-none"
                >
                  {edge.type}
                </text>
              </g>
            );
          })}

          {/* Define arrowhead marker */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="10"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
            </marker>
          </defs>

          {/* Draw nodes */}
          {graphData.nodes.map((node: any, i: any) => {
            const centerX = 400;
            const centerY = 200;
            const radiusOffset = 120;
            const angle = (i / graphData.nodes.length) * 2 * Math.PI;
            const x = centerX + radiusOffset * Math.cos(angle);
            const y = centerY + radiusOffset * Math.sin(angle);
            const isCenter = node.is_center;

            return (
              <g key={node.id}>
                <circle
                  cx={x}
                  cy={y}
                  r={isCenter ? 40 : 30}
                  fill={isCenter ? "#3b82f6" : "#f1f5f9"}
                  stroke={isCenter ? "#2563eb" : "#cbd5e1"}
                  strokeWidth="2"
                  className="cursor-pointer hover:opacity-80"
                  onClick={() => setSelectedEntityId(node.id)}
                />
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={isCenter ? "bold" : "normal"}
                  fill={isCenter ? "white" : "#334155"}
                  className="cursor-pointer pointer-events-none"
                >
                  {node.label.length > 10
                    ? node.label.substring(0, 10) + "..."
                    : node.label}
                </text>
                <text
                  x={x}
                  y={y + 15}
                  textAnchor="middle"
                  fontSize="9"
                  fill={isCenter ? "#e2e8f0" : "#64748b"}
                  className="pointer-events-none"
                >
                  {node.type}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Graph controls */}
        <div className="absolute top-4 right-4 flex gap-2">
          <Button size="sm">
            <ZoomIn size={16} />
          </Button>
          <Button size="sm">
            <ZoomOut size={16} />
          </Button>
          <Button size="sm">
            <RotateCcw size={16} />
          </Button>
          <Button size="sm">
            <Maximize size={16} />
          </Button>
          <Button size="sm">
            <Download size={16} />
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">🔍 Knowledge Graph Explorer</h1>
        </div>
      </div>

      {/* Search and Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Graph Explorer Controls</CardTitle>
          <CardDescription>
            Configure your graph exploration parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium">Search Entity</label>
              <div className="relative mt-1">
                <Search
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search entities..."
                  className="pl-10"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Center Entity ID</label>
              <Input
                value={selectedEntityId}
                onChange={(e) => setSelectedEntityId(e.target.value)}
                placeholder="Enter entity ID..."
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Exploration Radius</label>
              <Select
                value={radius.toString()}
                onValueChange={(val) => setRadius(parseInt(val))}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 hop</SelectItem>
                  <SelectItem value="2">2 hops</SelectItem>
                  <SelectItem value="3">3 hops</SelectItem>
                  <SelectItem value="4">4 hops</SelectItem>
                  <SelectItem value="5">5 hops</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={() => {}} className="w-full">
                <RefreshCw size={16} className="mr-2" />
                Explore
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Graph Visualization */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Network size={20} />
                Knowledge Graph Visualization
              </CardTitle>
              {graphData && (
                <CardDescription>
                  Showing {graphData.node_count} nodes and{" "}
                  {graphData.edge_count} edges
                </CardDescription>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <GraphVisualization />
        </CardContent>
      </Card>

      {/* Graph Information */}
      {graphData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Nodes Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database size={20} />
                Nodes ({graphData.node_count})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {graphData.nodes.map((node: any) => (
                  <div
                    key={node.id}
                    className={`flex items-center justify-between p-3 rounded border cursor-pointer hover:bg-muted/50 ${
                      node.is_center ? "border-blue-500 bg-blue-50" : ""
                    }`}
                    onClick={() => setSelectedEntityId(node.id)}
                  >
                    <div>
                      <div className="font-medium">{node.label}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {node.type}
                        </Badge>
                        {node.is_center && (
                          <Badge variant="default" className="text-xs">
                            Center
                          </Badge>
                        )}
                      </div>
                    </div>
                    <Button size="sm">
                      <ExternalLink size={14} />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Edges Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link size={20} />
                Relationships ({graphData.edge_count})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {graphData.edges.map((edge: any) => (
                  <div
                    key={edge.id}
                    className="p-3 rounded border hover:bg-muted/50"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary" className="text-xs">
                        {edge.type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium">
                        {
                          graphData.nodes.find((n: any) => n.id === edge.source)
                            ?.label
                        }
                      </span>
                      <ArrowRight size={14} className="text-muted-foreground" />
                      <span className="font-medium">
                        {
                          graphData.nodes.find((n: any) => n.id === edge.target)
                            ?.label
                        }
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
