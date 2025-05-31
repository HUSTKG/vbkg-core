export type Status = "pending" | "active" | "inactive" | "error" | "completed";
export type DateRange = { start: Date; end: Date };
export type SortDirection = "asc" | "desc";
export type PaginationParams = { page: number; limit: number };
