export interface Node {
  id: string;
  type: string;
  label: string;
  properties: Record<string, unknown>;
  metadata: {
    source: string;
    confidence: number;
    createdAt: Date;
    updatedAt: Date;
    createdBy: string;
    updatedBy: string;
  };
}

export interface Edge {
  id: string;
  type: string;
  label: string;
  source: string;
  target: string;
  properties: Record<string, unknown>;
  metadata: {
    source: string;
    confidence: number;
    createdAt: Date;
    updatedAt: Date;
    createdBy: string;
    updatedBy: string;
  };
}

export interface Graph {
  nodes: Node[];
  edges: Edge[];
}

export type CypherQuery = {
  query: string;
  parameters?: Record<string, unknown>;
};
