export interface StepConfigField {
	key: string;
	label: string;
	type: 'text' | 'number' | 'select' | 'boolean' | 'textarea' | 'array' | 'json';
	required?: boolean;
	defaultValue?: any;
	description?: string;
	options?: { label: string; value: string }[];
	dependsOn?: string;
	category?: 'basic';
}

export interface PipelineTemplate {
	id: string;
	name: string;
	description: string;
	steps: string[];
	estimated_duration: string;
	category?: string;
	source_types?: string[];
	difficulty?: 'beginner' | 'intermediate' | 'advanced';
	tags?: string[];
	is_popular?: boolean;
	usage_count?: number;
	rating?: number;
}

export interface PipelineTemplateDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	dataSourceId: string;
	sourceType: string;
	dataSource?: any;
	onCreatePipeline?: (templateId: string, config: any) => void;
}

