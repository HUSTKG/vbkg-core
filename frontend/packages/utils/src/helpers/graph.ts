import { Graph, Node, Edge } from "@vbkg/types";
import { cloneDeep } from "lodash";

export const findConnectedNodes = (graph: Graph, nodeId: string): Node[] => {
  const connectedEdges = graph.edges.filter(
    (edge) => edge.source === nodeId || edge.target === nodeId,
  );

  const connectedNodeIds = new Set(
    connectedEdges.flatMap((edge) => [edge.source, edge.target]),
  );

  return graph.nodes.filter((node) => connectedNodeIds.has(node.id));
};

export const findShortestPath = (): Edge[] => {
  // Implement shortest path algorithm (e.g., Dijkstra's)
  return [];
};

export const mergeGraphs = (graphs: Graph[]): Graph => {
  const mergedGraph: Graph = {
    nodes: [],
    edges: [],
  };

  for (const graph of graphs) {
    const clonedGraph = cloneDeep(graph);
    mergedGraph.nodes.push(...clonedGraph.nodes);
    mergedGraph.edges.push(...clonedGraph.edges);
  }

  return mergedGraph;
};
