import { useDomains } from "@vbkg/api-client";

// Step configuration schemas
export interface StepConfigField {
	key: string;
	label: string;
	type: "text" | "number" | "select" | "boolean" | "textarea" | "array";
	options?: { value: string; label: string }[];
	defaultValue?: any;
	description?: string;
	required?: boolean;
}

export const useStepConfigSchema = (stepType: string): StepConfigField[] => {
	const { data: domains } = useDomains({});
	if (stepType in stepConfigSchemas) {
		if (stepType === "llm_entity_extractor") {
			// Add domain options for LLM entity extractor
			const domainOptions = domains?.data.map((d) => ({
				value: d.name,
				label: d.display_name,
			}));
			stepConfigSchemas.llm_entity_extractor[1].options = domainOptions;
		}
		return stepConfigSchemas[stepType];
	}
	return [];
};

export const stepConfigSchemas: Record<string, StepConfigField[]> = {
	file_reader: [ ],
	api_fetcher: [
		{
			key: "method",
			label: "HTTP Method",
			type: "select",
			options: [
				{ value: "GET", label: "GET" },
				{ value: "POST", label: "POST" },
				{ value: "PUT", label: "PUT" },
			],
			defaultValue: "GET",
		},
		{
			key: "data_format",
			label: "Định dạng dữ liệu",
			type: "select",
			options: [
				{ value: "json", label: "JSON" },
				{ value: "xml", label: "XML" },
				{ value: "csv", label: "CSV" },
			],
			defaultValue: "json",
		},
		{
			key: "headers",
			label: "Custom Headers",
			type: "textarea",
			description: "JSON object with custom headers",
			defaultValue: "{}",
		},
	],
	database_extractor: [
		{
			key: "query",
			label: "SQL Query",
			type: "textarea",
			defaultValue: "SELECT * FROM your_table",
			description: "SQL truy vấn để trích xuất dữ liệu",
			required: true,
		},
		{
			key: "batch_size",
			label: "Batch Size",
			type: "number",
			defaultValue: 1000,
			description: "Số lượng bản ghi để truy xuất trong mỗi lô",
		},
	],
	text_extractor: [
		{
			key: "input_format",
			label: "Định dạng đầu vào",
			type: "select",
			options: [
				{ value: "auto", label: "Auto-detect" },
				{ value: "pdf", label: "PDF" },
				{ value: "docx", label: "Word Document" },
				{ value: "html", label: "HTML" },
				{ value: "txt", label: "Plain Text" },
			],
			defaultValue: "auto",
		},
		{
			key: "extract_tables",
			label: "Trích xuất bảng",
			type: "boolean",
			defaultValue: true,
			description: "Trích xuất bảng từ tài liệu",
		},
		{
			key: "extract_metadata",
			label: "Extract Metadata",
			type: "boolean",
			defaultValue: true,
			description: "Trích xuất metadata từ tài liệu",
		},
		{
			key: "chunk_size",
			label: "Chunk Size",
			type: "number",
			defaultValue: 1000,
			description: "Kích thước của mỗi đoạn văn bản (số ký tự)",
		},
	],
	llm_entity_extractor: [
		{
			key: "llm_model",
			label: "Mô hình LLM",
			type: "select",
			options: [
				{ value: "gpt-4o-mini", label: "GPT-4o Mini" },
				{ value: "gpt-4o", label: "GPT-4o" },
				{ value: "claude-3-haiku", label: "Claude 3 Haiku" },
				{ value: "claude-3-sonnet", label: "Claude 3 Sonnet" },
			],
			defaultValue: "gpt-4o-mini",
		},
		{
			key: "domain",
			label: "Domain",
			type: "select",
			options: [],
			description: "Miền để trích xuất thực thể (cách dấu phẩy)",
		},
		{
			key: "extract_relationships",
			label: "Trích xuất mối quan hệ",
			type: "boolean",
			defaultValue: true,
			description: "Trích xuất mối quan hệ giữa các thực thể",
		},
		{
			key: "temperature",
			label: "Temperature",
			type: "number",
			defaultValue: 0.2,
			description: "Model temperature (0.0 - 1.0)",
		},
	],
	data_validation: [
		{
			key: "quality_threshold",
			label: "Quality Threshold",
			type: "number",
			defaultValue: 0.8,
			description: "Minimum data quality score (0.0 - 1.0)",
		},
		{
			key: "validation_rules",
			label: "Validation Rules",
			type: "textarea",
			defaultValue: "[]",
			description: "JSON array of validation rules",
		},
	],
	entity_resolution: [
		{
			key: "similarity_threshold",
			label: "Similarity Threshold",
			type: "number",
			defaultValue: 0.8,
			description: "Minimum similarity for entity matching (0.0 - 1.0)",
		},
		{
			key: "resolution_strategy",
			label: "Resolution Strategy",
			type: "select",
			options: [
				{ value: "fuzzy_match", label: "Fuzzy Matching" },
				{ value: "exact_match", label: "Exact Matching" },
				{ value: "semantic_match", label: "Semantic Matching" },
			],
			defaultValue: "fuzzy_match",
		},
	],
	fibo_mapper: [
		{
			key: "mapping_confidence_threshold",
			label: "Mapping Confidence Threshold",
			type: "number",
			defaultValue: 0.7,
			description: "Minimum confidence for FIBO mapping (0.0 - 1.0)",
		},
		{
			key: "fibo_domains",
			label: "FIBO Domains",
			type: "array",
			defaultValue: [],
			description: "Specific FIBO domains to map to (comma-separated)",
		},
	],
	knowledge_graph_writer: [
		{
			key: "batch_size",
			label: "Batch Size",
			type: "number",
			defaultValue: 100,
			description: "Number of entities to write in each batch",
		},
		{
			key: "track_provenance",
			label: "Track Provenance",
			type: "boolean",
			defaultValue: true,
			description: "Track data lineage and provenance",
		},
	],
	data_profiling: [
		{
			key: "profile_columns",
			label: "Profile All Columns",
			type: "boolean",
			defaultValue: true,
			description: "Generate profiles for all columns",
		},
		{
			key: "sample_size",
			label: "Sample Size",
			type: "number",
			defaultValue: 10000,
			description: "Number of rows to sample for profiling",
		},
	],
};
