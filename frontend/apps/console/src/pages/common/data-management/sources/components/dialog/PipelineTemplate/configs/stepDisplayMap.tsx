import React from "react";
import {
	Database,
	FileText,
	Globe,
	Zap,
	CheckCircle,
	ArrowRight,
	Settings,
} from "lucide-react";

export const stepDisplayMap: Record<
	string,
	{ name: string; description: string; icon: React.ReactNode; type: string }
> = {
	file_reader: {
		name: "File Reader",
		description: "Read and parse files from various formats",
		icon: <FileText size={14} />,
		type: "extract",
	},
	text_extractor: {
		name: "Text Extractor",
		description: "Extract text content from documents",
		icon: <Database size={14} />,
		type: "extract",
	},
	llm_entity_extractor: {
		name: "LLM Entity Extractor",
		description: "Extract entities using large language models",
		icon: <Zap size={14} />,
		type: "enrich",
	},
	knowledge_graph_writer: {
		name: "Knowledge Graph Writer",
		description: "Store entities and relationships in knowledge graph",
		icon: <ArrowRight size={14} />,
		type: "load",
	},
	api_fetcher: {
		name: "API Fetcher",
		description: "Fetch data from REST APIs",
		icon: <Globe size={14} />,
		type: "extract",
	},
	database_extractor: {
		name: "Database Extractor",
		description: "Extract data from database sources",
		icon: <Database size={14} />,
		type: "extract",
	},
	data_validation: {
		name: "Data Validation",
		description: "Validate data quality and completeness",
		icon: <CheckCircle size={14} />,
		type: "validate",
	},
	entity_resolution: {
		name: "Entity Resolution",
		description: "Resolve and deduplicate entities",
		icon: <Settings size={14} />,
		type: "transform",
	},
	fibo_mapper: {
		name: "FIBO Mapper",
		description: "Map entities to FIBO ontology",
		icon: <ArrowRight size={14} />,
		type: "enrich",
	},
	data_profiling: {
		name: "Data Profiling",
		description: "Profile and analyze data structure",
		icon: <Settings size={14} />,
		type: "analyze",
	},
};
