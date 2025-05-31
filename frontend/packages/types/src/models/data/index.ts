export interface DataReview {
  id: string;
  type: "node" | "edge";
  entityId: string;
  changes: {
    property: string;
    oldValue: unknown;
    newValue: unknown;
    source: string;
  }[];
  status: "pending" | "approved" | "rejected";
  reviewer?: string;
  reviewedAt?: Date;
  comments?: string;
}
