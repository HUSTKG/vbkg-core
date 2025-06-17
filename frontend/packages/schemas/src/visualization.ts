import { z } from "zod";
import { ChartType, GraphLayoutType, VisualizationType } from "@vbkg/types";
import { CypherQuerySchema } from "./common";

// Base configuration schemas for different visualization types
const NodeDisplayConfigSchema = z.object({
	color_field: z.string().optional(),
	color_mapping: z.record(z.string(), z.string()).optional(),
	default_color: z.string().default("#1f77b4"),
	size_field: z.string().optional(),
	size_range: z.array(z.number()).length(2).default([30, 80]),
	label_field: z.string().default("text"),
	icon_field: z.string().optional(),
	icon_mapping: z.record(z.string(), z.string()).optional(),
	group_by_field: z.string().optional(),
});

const EdgeDisplayConfigSchema = z.object({
	color_field: z.string().optional(),
	color_mapping: z.record(z.string(), z.string()).optional(),
	default_color: z.string().default("#aaa"),
	width_field: z.string().optional(),
	width_range: z.array(z.number()).length(2).default([1, 5]),
	label_field: z.string().default("type"),
	style_field: z.string().optional(),
	style_mapping: z.record(z.string(), z.string()).optional(),
});

const GraphLayoutConfigSchema = z.object({
	type: z.nativeEnum(GraphLayoutType).default(GraphLayoutType.FORCE),
	params: z.record(z.string(), z.any()).default({}),
});

// Base visualization details schema (like ConnectionDetailsSchema in datasource)
const VisualizationDetailsSchema = z.object({
	name: z.string().min(1),
	description: z.string().optional(),
	entity_id: z.string().uuid().optional(),
	query_id: z.string().uuid().optional(),
	cypher_query: CypherQuerySchema.optional(),
	entity_type: z.string().optional(),
	is_public: z.boolean().default(false),
});

// Graph visualization schema
const _GraphVisualizationSchema = z
	.object({
		visualization_type: z.literal(VisualizationType.GRAPH),
		config: z.object({
			node_config: NodeDisplayConfigSchema.default({}),
			edge_config: EdgeDisplayConfigSchema.default({}),
			layout: GraphLayoutConfigSchema.default({}),
			show_labels: z.boolean().default(true),
			show_tooltips: z.boolean().default(true),
			zoom_enabled: z.boolean().default(true),
			pan_enabled: z.boolean().default(true),
			clustering_enabled: z.boolean().default(false),
			physics_enabled: z.boolean().default(true),
			interactive: z.boolean().default(true),
			max_nodes: z.number().min(1).max(2000).default(500),
			height: z.number().min(300).max(2000).default(600),
			width: z.number().optional(),
		}),
	})
	.extend(VisualizationDetailsSchema.shape);

// Tree visualization schema
const _TreeVisualizationSchema = z
	.object({
		visualization_type: z.literal(VisualizationType.TREE),
		config: z.object({
			node_config: NodeDisplayConfigSchema.default({}),
			edge_config: EdgeDisplayConfigSchema.default({}),
			orientation: z.enum(["vertical", "horizontal"]).default("vertical"),
			alignment: z.enum(["center", "left", "right"]).default("center"),
			node_separation: z.number().default(150),
			level_separation: z.number().default(200),
			show_labels: z.boolean().default(true),
			show_tooltips: z.boolean().default(true),
			interactive: z.boolean().default(true),
			height: z.number().min(300).max(2000).default(600),
			width: z.number().optional(),
		}),
	})
	.extend(VisualizationDetailsSchema.shape);

// Table visualization schema
const TableColumnSchema = z.object({
	field: z.string(),
	header: z.string(),
	sortable: z.boolean().default(true),
	filterable: z.boolean().default(true),
	width: z.number().optional(),
	render_template: z.string().optional(),
});

const _TableVisualizationSchema = z
	.object({
		visualization_type: z.literal(VisualizationType.TABLE),
		config: z.object({
			columns: z.array(TableColumnSchema),
			pagination: z.boolean().default(true),
			page_size: z.number().min(1).max(100).default(10),
			sortable: z.boolean().default(true),
			filterable: z.boolean().default(true),
			height: z.number().optional(),
			width: z.number().optional(),
		}),
	})
	.extend(VisualizationDetailsSchema.shape);

// Chart visualization schema
const ChartAxesSchema = z.object({
	x_field: z.string(),
	y_field: z.string().optional(),
	z_field: z.string().optional(),
	color_field: z.string().optional(),
	size_field: z.string().optional(),
	group_by_field: z.string().optional(),
});

const _ChartVisualizationSchema = z
	.object({
		visualization_type: z.literal(VisualizationType.CHART),
		config: z.object({
			chart_type: z.nativeEnum(ChartType),
			axes: ChartAxesSchema,
			color_scheme: z.array(z.string()).optional(),
			title: z.string().optional(),
			legend: z.boolean().default(true),
			grid: z.boolean().default(true),
			stacked: z.boolean().default(false),
			normalized: z.boolean().default(false),
			annotations: z.array(z.record(z.string(), z.any())).optional(),
			height: z.number().min(200).max(1000).default(400),
			width: z.number().optional(),
		}),
	})
	.extend(VisualizationDetailsSchema.shape);

// Schema for creating a visualization using discriminated union
export const CreateVisualizationSchema = z
	.discriminatedUnion("visualization_type", [
		_GraphVisualizationSchema,
		_TreeVisualizationSchema,
		_TableVisualizationSchema,
		_ChartVisualizationSchema,
	])
	.refine(
		(data) => {
			// Ensure at least one of query_id ,cypher_query or entity_id is provided
			return data.query_id || data.cypher_query || data.entity_id;
		},
		{
			message:
				"Một trong các trường query_id, cypher_query hoặc entity_id phải được cung cấp.",
			path: ["query_id", "cypher_query", "entity_id"],
		},
	);

// Schema for retrieving visualizations with optional filters
export const ReadVisualizationsSchema = z.object({
	type: z.string().optional(),
	is_public: z.boolean().optional(),
	limit: z.number().min(1).max(1000).default(100),
	skip: z.number().min(0).default(0),
});

// Schema for retrieving a specific visualization by ID
export const ReadVisualizationByIdSchema = z.object({
	visualization_id: z.string().uuid(),
});

// Schema for updating a visualization
export const UpdateVisualizationSchema = CreateVisualizationSchema;

// Schema for deleting a visualization
export const DeleteVisualizationSchema = z.object({
	visualization_id: z.string().uuid(),
});

// Schema for retrieving data for a visualization
export const GetVisualizationDataSchema = z.object({
	visualization_id: z.string().uuid(),
	params: z.record(z.string(), z.string()).optional(),
});

// Schema for creating a default visualization
export const CreateDefaultVisualizationSchema = z.object({
	title: z.string().optional(),
	description: z.string().optional(),
	entity_id: z.string().optional(),
	is_public: z.boolean().default(false),
	visualization_type: z.enum(["GRAPH", "TREE", "TABLE", "CHART"]),
});

// Schema for retrieving visualization templates
export const GetVisualizationTemplatesSchema = z.object({});
