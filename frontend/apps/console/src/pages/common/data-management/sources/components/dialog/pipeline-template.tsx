import React, { useState } from "react";
import {
	Plus,
	GitBranch,
	Play,
	Clock,
	CheckCircle,
	Search,
	Star,
	Settings,
	ChevronDown,
	ChevronRight,
	Edit3,
} from "lucide-react";
import {
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	Dialog,
	Input,
	Label,
	ScrollArea,
	Select,
	SelectContent,
	Badge,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Separator,
	Switch,
	Textarea,
	toast,
	Collapsible,
	CollapsibleContent,
	CollapsibleTrigger,
} from "@/components";
import {
	useCreatePipelineFromTemplate,
	useDomains,
	usePipelineTemplates,
} from "@vbkg/api-client";
import { StepConfigField, stepConfigSchemas } from "../../configs/stepConfigSchema";
import { stepDisplayMap } from "../../configs/stepDisplayMap";

// Types for pipeline templates (updated to match actual schema)
interface PipelineTemplate {
	id: string;
	name: string;
	description: string;
	steps: string[];
	estimated_duration: string;
	// Additional metadata for UI
	category?:
		| "data_processing"
		| "etl"
		| "ml_prep"
		| "knowledge_graph"
		| "analytics";
	source_types?: string[];
	difficulty?: "beginner" | "intermediate" | "advanced";
	tags?: string[];
	is_popular?: boolean;
	usage_count?: number;
	rating?: number;
	created_by?: string;
	created_at?: string;
}


interface PipelineTemplateDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	dataSourceId: string;
	sourceType: string;
	onCreatePipeline?: (templateId: string, config: any) => void;
}

const PipelineTemplateDialog: React.FC<PipelineTemplateDialogProps> = ({
	open,
	onOpenChange,
	dataSourceId,
	sourceType,
	onCreatePipeline,
}) => {
	const [selectedTemplate, setSelectedTemplate] =
		useState<PipelineTemplate | null>(null);
	const [searchQuery, setSearchQuery] = useState("");
	const [showOnlyRecommended, setShowOnlyRecommended] = useState(false);
	const [step, setStep] = useState<"browse" | "configure" | "confirm">(
		"browse",
	);
	const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

	const [stepConfigs, setStepConfigs] = useState<Record<string, Record<string, any>>>({});

	const {data: domains} = useDomains({})

	const { data: templates = [] } = usePipelineTemplates({
		datasource_id: dataSourceId,
	});
	const { mutate: createPipeline } = useCreatePipelineFromTemplate({
		onSuccess: () => {
			toast("Pipeline created successfully");
		},
		onError: (error) => {
			toast("Failed to create pipeline: " + error.message);
		},
	});

	const [pipelineConfig, setPipelineConfig] = useState({
		name: "",
		description: "",
		schedule_enabled: false,
		schedule_cron: "0 0 * * *",
		auto_retry: true,
		max_retries: 3,
	});

	// Initialize step configurations when template is selected
	const initializeStepConfigs = (template: PipelineTemplate) => {
		const configs: Record<string, Record<string, any>> = {};
		template.steps.forEach((stepName, index) => {
			let schema = stepConfigSchemas[stepName] || [];
		if (stepName === "llm_entity_extractor") {
			// Add domain options for LLM entity extractor
			const domainOptions = domains?.data.map((d) => ({
				value: String(d.id),
				label: d.display_name,
			}));

			schema[1].options = domainOptions;
		}
			const config: Record<string, any> = {};
			schema.forEach((field) => {
				config[field.key] = field.defaultValue;
			});
			configs[`${stepName}_${index}`] = config;
		});
		setStepConfigs(configs);
	};

	// Filter templates based on source type, category, search, etc.
	const filteredTemplates = (templates as any)?.data?.filter(
		(template: any) => {
			// Filter by source type compatibility
			if (template.source_types && !template.source_types.includes(sourceType))
				return false;

			// Filter by search query
			if (
				searchQuery &&
				!template.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
				!template.description
					.toLowerCase()
					.includes(searchQuery.toLowerCase()) &&
				(!template.tags ||
					!template.tags.some((tag: any) =>
						tag.toLowerCase().includes(searchQuery.toLowerCase()),
					))
			) {
				return false;
			}

			return true;
		},
	);

	const getDifficultyColor = (difficulty?: string) => {
		switch (difficulty) {
			case "beginner":
				return "bg-green-100 text-green-800";
			case "intermediate":
				return "bg-yellow-100 text-yellow-800";
			case "advanced":
				return "bg-red-100 text-red-800";
			default:
				return "bg-gray-100 text-gray-800";
		}
	};

	const getStepIcon = (stepName: string) => {
		const stepInfo = stepDisplayMap[stepName];
		return stepInfo?.icon || <GitBranch size={14} />;
	};

	const getStepDisplayName = (stepName: string) => {
		const stepInfo = stepDisplayMap[stepName];
		return stepInfo?.name || stepName;
	};

	const getStepDescription = (stepName: string) => {
		const stepInfo = stepDisplayMap[stepName];
		return stepInfo?.description || "Processing step";
	};

	const getStepType = (stepName: string) => {
		const stepInfo = stepDisplayMap[stepName];
		return stepInfo?.type || "process";
	};

	const handleTemplateSelect = (template: PipelineTemplate) => {
		setSelectedTemplate(template);
		setPipelineConfig({
			...pipelineConfig,
			name: `${template.name} - ${new Date().toLocaleDateString()}`,
			description: template.description,
		});
		initializeStepConfigs(template);
		setStep("configure");
	};

	const handleStepConfigChange = (stepKey: string, fieldKey: string, value: any) => {
		setStepConfigs(prev => ({
			...prev,
			[stepKey]: {
				...prev[stepKey],
				[fieldKey]: value,
			},
		}));
	};

	const toggleStepExpanded = (stepKey: string) => {
		setExpandedSteps(prev => ({
			...prev,
			[stepKey]: !prev[stepKey],
		}));
	};

	const renderConfigField = (field: StepConfigField, stepKey: string, value: any) => {
		const fieldId = `${stepKey}_${field.key}`;
		
		switch (field.type) {
			case "text":
				return (
					<Input
						id={fieldId}
						value={value || ""}
						onChange={(e) => handleStepConfigChange(stepKey, field.key, e.target.value)}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
					/>
				);
			
			case "number":
				return (
					<Input
						id={fieldId}
						type="number"
						value={value || ""}
						onChange={(e) => handleStepConfigChange(stepKey, field.key, parseFloat(e.target.value) || 0)}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
					/>
				);
			
			case "select":
				return (
					<Select
						value={value || field.defaultValue}
						onValueChange={(val) => handleStepConfigChange(stepKey, field.key, val)}
					>
						<SelectTrigger>
							<SelectValue placeholder="Select" />
						</SelectTrigger>
						<SelectContent>
							{field.options?.map((option) => (
								<SelectItem key={option.value} value={option.value}>
									{option.label}
								</SelectItem>
							))}
						</SelectContent>
					</Select>
				);
			
			case "boolean":
				return (
					<Switch
						id={fieldId}
						checked={value !== undefined ? value : field.defaultValue}
						onCheckedChange={(checked) => handleStepConfigChange(stepKey, field.key, checked)}
					/>
				);
			
			case "textarea":
				return (
					<Textarea
						id={fieldId}
						value={value || ""}
						onChange={(e) => handleStepConfigChange(stepKey, field.key, e.target.value)}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
						rows={3}
					/>
				);
			
			case "array":
				return (
					<Input
						id={fieldId}
						value={Array.isArray(value) ? value.join(", ") : (value || "")}
						onChange={(e) => {
							const arrayValue = e.target.value.split(",").map(item => item.trim()).filter(Boolean);
							handleStepConfigChange(stepKey, field.key, arrayValue);
						}}
						placeholder="Enter values separated by commas..."
					/>
				);
			
			default:
				return null;
		}
	};

	const handleCreatePipeline = () => {
		if (selectedTemplate) {
			// Prepare the custom options with step configurations
			const customOptions = {
				...pipelineConfig,
				steps: stepConfigs,
			};

			createPipeline({
				template_name: selectedTemplate.name,
				datasource_id: dataSourceId,
				custom_options: customOptions,
			});
			
			onCreatePipeline?.(selectedTemplate.id, {
				...customOptions,
				template: selectedTemplate,
				datasource_id: dataSourceId,
			});
		}
		onOpenChange(false);
		// Reset state
		setStep("browse");
		setSelectedTemplate(null);
		setStepConfigs({});
		setExpandedSteps({});
		setPipelineConfig({
			name: "",
			description: "",
			schedule_enabled: false,
			schedule_cron: "0 0 * * *",
			auto_retry: true,
			max_retries: 3,
		});
	};

	const renderBrowseStep = () => (
		<div className="space-y-6">
			<div className="space-y-4">
				<div className="flex gap-4">
					<div className="flex-1 relative">
						<Search
							className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
							size={16}
						/>
						<Input
							placeholder="Search templates..."
							value={searchQuery}
							onChange={(e) => setSearchQuery(e.target.value)}
							className="pl-10"
						/>
					</div>
					<div className="flex items-center space-x-2">
						<Switch
							id="recommended"
							checked={showOnlyRecommended}
							onCheckedChange={setShowOnlyRecommended}
						/>
						<Label htmlFor="recommended" className="text-sm">
							Recommended only
						</Label>
					</div>
				</div>

				{/* Templates Grid */}
				<ScrollArea className="h-96">
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
						{filteredTemplates?.map((template: any) => (
							<Card
								key={template.id}
								className="cursor-pointer hover:shadow-md transition-shadow"
							>
								<CardHeader className="pb-3">
									<div className="flex justify-between items-start">
										<div className="flex items-center gap-2">
											<CardTitle className="text-base">
												{template.name}
											</CardTitle>
											{template.is_popular && (
												<Badge variant={"outline"} className="text-xs">
													<Star size={10} className="mr-1" />
													Popular
												</Badge>
											)}
										</div>
									</div>
									<CardDescription className="text-sm">
										{template.description}
									</CardDescription>
								</CardHeader>
								<CardContent className="pt-0 space-y-3">
									<div className="flex flex-wrap gap-2">
										{template.tags?.slice(0, 3).map((tag: any) => (
											<Badge variant={"outline"} key={tag} className="text-xs">
												{tag}
											</Badge>
										)) || []}
										{template.tags && template.tags?.length > 3 && (
											<Badge variant={"outline"} className="text-xs">
												+{template.tags?.length - 3}
											</Badge>
										)}
									</div>

									<div className="flex justify-between items-center text-sm text-muted-foreground">
										<div className="flex items-center gap-2">
											{template.difficulty && (
												<Badge
													variant={"outline"}
													className={getDifficultyColor(template.difficulty)}
												>
													{template.difficulty}
												</Badge>
											)}
											<span className="flex items-center gap-1">
												<Clock size={12} />
												{template.estimated_duration}
											</span>
										</div>
										{template.rating && template.usage_count && (
											<div className="flex items-center gap-1">
												<Star
													size={12}
													className="fill-current text-yellow-400"
												/>
												<span>{template.rating}</span>
												<span>({template.usage_count})</span>
											</div>
										)}
									</div>

									<Button
										className="w-full"
										variant="outline"
										onClick={() => handleTemplateSelect(template)}
									>
										Use Template
									</Button>
								</CardContent>
							</Card>
						))}
					</div>
				</ScrollArea>

				{filteredTemplates?.length === 0 && (
					<div className="text-center py-8">
						<GitBranch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
						<h3 className="text-lg font-medium mb-2">No templates found</h3>
						<p className="text-muted-foreground">
							Try adjusting your search criteria or filters
						</p>
					</div>
				)}
			</div>
		</div>
	);

	const renderConfigureStep = () => {
		if (!selectedTemplate) return null;

		return (
			<div className="space-y-6">
				{/* Template Overview */}
				<Card>
					<CardHeader className="pb-3">
						<div className="flex justify-between items-start">
							<div>
								<CardTitle className="flex items-center gap-2">
									{selectedTemplate.name}
									{selectedTemplate.difficulty && (
										<Badge
											variant={"outline"}
											className={getDifficultyColor(
												selectedTemplate.difficulty,
											)}
										>
											{selectedTemplate.difficulty}
										</Badge>
									)}
								</CardTitle>
								<CardDescription>
									{selectedTemplate.description}
								</CardDescription>
							</div>
							{selectedTemplate.rating && (
								<div className="flex items-center gap-1 text-sm text-muted-foreground">
									<Star size={12} className="fill-current text-yellow-400" />
									<span>{selectedTemplate.rating}</span>
								</div>
							)}
						</div>
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							<div>
								<Label className="text-sm font-medium">
									Pipeline Steps ({selectedTemplate.steps?.length})
								</Label>
								<div className="grid grid-cols-1 gap-2 mt-2">
									{selectedTemplate.steps?.map((stepName, index) => {
										const stepKey = `${stepName}_${index}`;
										const stepType = getStepType(stepName);
										const isExpanded = expandedSteps[stepKey];
										const configSchema = stepConfigSchemas[stepName] || [];
										const hasConfig = configSchema.length > 0;

										return (
											<Card key={stepKey} className="p-0">
												<Collapsible 
													open={isExpanded} 
													onOpenChange={() => toggleStepExpanded(stepKey)}
												>
													<CollapsibleTrigger asChild>
														<div className="flex items-center gap-2 p-3 border rounded cursor-pointer hover:bg-gray-50">
															<div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs">
																{index + 1}
															</div>
															<div className="flex-1">
																<div className="flex items-center gap-2">
																	{getStepIcon(stepName)}
																	<span className="font-medium text-sm">
																		{getStepDisplayName(stepName)}
																	</span>
																	<Badge variant={"outline"} className="text-xs">
																		{stepType}
																	</Badge>
																	{hasConfig && (
																		<Badge variant={"secondary"} className="text-xs">
																			<Settings size={10} className="mr-1" />
																			Configurable
																		</Badge>
																	)}
																</div>
																<p className="text-xs text-muted-foreground">
																	{getStepDescription(stepName)}
																</p>
															</div>
															{hasConfig && (
																<div className="flex items-center gap-2">
																	<Edit3 size={14} className="text-muted-foreground" />
																	{isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
																</div>
															)}
														</div>
													</CollapsibleTrigger>
													
													{hasConfig && (
														<CollapsibleContent>
															<div className="px-3 pb-3 pt-0 border-t bg-gray-50/50">
																<div className="space-y-3 pt-3">
																	<div className="flex items-center gap-2 text-sm font-medium text-gray-700">
																		<Settings size={14} />
																		Step Configuration
																	</div>
																	<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
																		{configSchema.map((field) => (
																			<div key={field.key} className="space-y-1">
																				<Label htmlFor={`${stepKey}_${field.key}`} className="text-xs font-medium">
																					{field.label}
																					{field.required && <span className="text-red-500 ml-1">*</span>}
																				</Label>
																				{renderConfigField(field, stepKey, stepConfigs[stepKey]?.[field.key])}
																				{field.description && (
																					<p className="text-xs text-muted-foreground">
																						{field.description}
																					</p>
																				)}
																			</div>
																		))}
																	</div>
																</div>
															</div>
														</CollapsibleContent>
													)}
												</Collapsible>
											</Card>
										);
									})}
								</div>
							</div>
						</div>
					</CardContent>
				</Card>

				{/* Pipeline Configuration */}
				<Card>
					<CardHeader>
						<CardTitle>Pipeline Configuration</CardTitle>
						<CardDescription>Configure your pipeline settings</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<Label htmlFor="pipeline-name">Pipeline Name</Label>
								<Input
									id="pipeline-name"
									value={pipelineConfig.name}
									onChange={(e) =>
										setPipelineConfig({
											...pipelineConfig,
											name: e.target.value,
										})
									}
									placeholder="Enter pipeline name..."
								/>
							</div>
							<div>
								<Label htmlFor="datasource">Data Source</Label>
								<Input
									id="datasource"
									value={dataSourceId}
									disabled
									className="bg-muted"
								/>
							</div>
						</div>

						<div>
							<Label htmlFor="pipeline-description">Description</Label>
							<Textarea
								id="pipeline-description"
								value={pipelineConfig.description}
								onChange={(e) =>
									setPipelineConfig({
										...pipelineConfig,
										description: e.target.value,
									})
								}
								placeholder="Enter pipeline description..."
								rows={3}
							/>
						</div>

						<Separator />

						<div className="space-y-4">
							<div className="flex items-center justify-between">
								<div>
									<Label htmlFor="schedule-enabled">Enable Scheduling</Label>
									<p className="text-sm text-muted-foreground">
										Run pipeline automatically on schedule
									</p>
								</div>
								<Switch
									id="schedule-enabled"
									checked={pipelineConfig.schedule_enabled}
									onCheckedChange={(checked) =>
										setPipelineConfig({
											...pipelineConfig,
											schedule_enabled: checked,
										})
									}
								/>
							</div>

							{pipelineConfig.schedule_enabled && (
								<div>
									<Label htmlFor="schedule-cron">
										Schedule (Cron Expression)
									</Label>
									<Select
										value={pipelineConfig.schedule_cron}
										onValueChange={(value) =>
											setPipelineConfig({
												...pipelineConfig,
												schedule_cron: value,
											})
										}
									>
										<SelectTrigger>
											<SelectValue />
										</SelectTrigger>
										<SelectContent>
											<SelectItem value="0 0 * * *">
												Daily at midnight
											</SelectItem>
											<SelectItem value="0 0 * * 0">
												Weekly on Sunday
											</SelectItem>
											<SelectItem value="0 0 1 * *">Monthly on 1st</SelectItem>
											<SelectItem value="0 */6 * * *">Every 6 hours</SelectItem>
											<SelectItem value="*/30 * * * *">
												Every 30 minutes
											</SelectItem>
										</SelectContent>
									</Select>
								</div>
							)}

							<div className="flex items-center justify-between">
								<div>
									<Label htmlFor="auto-retry">Auto Retry on Failure</Label>
									<p className="text-sm text-muted-foreground">
										Automatically retry failed pipeline runs
									</p>
								</div>
								<Switch
									id="auto-retry"
									checked={pipelineConfig.auto_retry}
									onCheckedChange={(checked) =>
										setPipelineConfig({
											...pipelineConfig,
											auto_retry: checked,
										})
									}
								/>
							</div>

							{pipelineConfig.auto_retry && (
								<div>
									<Label htmlFor="max-retries">Maximum Retries</Label>
									<Select
										value={pipelineConfig.max_retries.toString()}
										onValueChange={(value) =>
											setPipelineConfig({
												...pipelineConfig,
												max_retries: parseInt(value),
											})
										}
									>
										<SelectTrigger>
											<SelectValue />
										</SelectTrigger>
										<SelectContent>
											<SelectItem value="1">1 retry</SelectItem>
											<SelectItem value="2">2 retries</SelectItem>
											<SelectItem value="3">3 retries</SelectItem>
											<SelectItem value="5">5 retries</SelectItem>
										</SelectContent>
									</Select>
								</div>
							)}
						</div>
					</CardContent>
				</Card>
			</div>
		);
	};

	const renderConfirmStep = () => {
		if (!selectedTemplate) return null;

		return (
			<div className="space-y-6">
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<CheckCircle className="text-green-500" size={20} />
							Pipeline Ready to Create
						</CardTitle>
						<CardDescription>
							Review your pipeline configuration before creating
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Pipeline Name
								</Label>
								<p className="font-medium">{pipelineConfig.name}</p>
							</div>
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Template
								</Label>
								<p className="font-medium">{selectedTemplate.name}</p>
							</div>
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Data Source
								</Label>
								<p className="font-medium">{dataSourceId}</p>
							</div>
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Estimated Duration
								</Label>
								<p className="font-medium">
									{selectedTemplate.estimated_duration}
								</p>
							</div>
						</div>

						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Description
							</Label>
							<p className="text-sm">{pipelineConfig.description}</p>
						</div>

						<div className="flex gap-4">
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Scheduling
								</Label>
								<p className="text-sm">
									{pipelineConfig.schedule_enabled
										? `Enabled (${pipelineConfig.schedule_cron})`
										: "Disabled"}
								</p>
							</div>
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Auto Retry
								</Label>
								<p className="text-sm">
									{pipelineConfig.auto_retry
										? `Enabled (${pipelineConfig.max_retries} max)`
										: "Disabled"}
								</p>
							</div>
						</div>

						{/* Step Configurations Summary */}
						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Configured Steps
							</Label>
							<div className="space-y-2 mt-2">
								{selectedTemplate.steps.map((stepName, index) => {
									const stepKey = `${stepName}_${index}`;
									const config = stepConfigs[stepKey] || {};
									const hasCustomConfig = Object.keys(config).length > 0;

									return (
										<div key={stepKey} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
											<div className="flex items-center gap-2">
												{getStepIcon(stepName)}
												<span>{getStepDisplayName(stepName)}</span>
											</div>
											{hasCustomConfig && (
												<Badge variant={"outline"} className="text-xs">
													Custom config
												</Badge>
											)}
										</div>
									);
								})}
							</div>
						</div>
					</CardContent>
				</Card>
			</div>
		);
	};

	return (
		<Dialog
			title="Create Pipeline from Template"
			description="Choose a template and configure your data pipeline"
			size={"3xl"}
			open={open}
			onOpenChange={onOpenChange}
		>
			<div className="flex-1 overflow-hidden">
				{step === "browse" && renderBrowseStep()}
				{step === "configure" && renderConfigureStep()}
				{step === "confirm" && renderConfirmStep()}
			</div>

			<div className="flex justify-between items-center pt-4 border-t">
				<div className="flex items-center gap-2">
					{step !== "browse" && (
						<Button
							variant="outline"
							onClick={() => {
								if (step === "configure") setStep("browse");
								if (step === "confirm") setStep("configure");
							}}
						>
							Back
						</Button>
					)}
				</div>

				<div className="flex items-center gap-2">
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Cancel
					</Button>

					{step === "browse" && (
						<Button
							variant="outline"
							disabled={filteredTemplates?.length === 0}
						>
							Select Template
						</Button>
					)}

					{step === "configure" && (
						<Button
							onClick={() => setStep("confirm")}
							disabled={!pipelineConfig.name.trim()}
						>
							Review & Create
						</Button>
					)}

					{step === "confirm" && (
						<Button onClick={handleCreatePipeline}>
							<Play size={16} className="mr-2" />
							Create Pipeline
						</Button>
					)}
				</div>
			</div>
		</Dialog>
	);
};

// Integration with DataSource Detail Page
const DataSourcePipelineSection: React.FC<{
	dataSourceId: string;
	sourceType: string;
}> = ({ dataSourceId, sourceType }) => {
	const [showTemplateDialog, setShowTemplateDialog] = useState(false);
	const [pipelines, setPipelines] = useState<any>([
		{
			id: "pipeline-1",
			name: "CSV to Knowledge Graph - 2024-01-15",
			status: "active",
			last_run: "2024-01-15T10:30:00Z",
			next_run: "2024-01-16T10:30:00Z",
			template: "CSV to Knowledge Graph",
		},
	]);

	const handleCreatePipeline = (templateId: string, config: any) => {
		console.log("Creating pipeline:", { templateId, config });
		// Add API call here to create pipeline
		const newPipeline = {
			id: `pipeline-${Date.now()}`,
			name: config.name,
			status: "creating",
			last_run: null,
			next_run: config.schedule_enabled ? new Date().toISOString() : null,
			template: config.template.name,
		};
		setPipelines([...pipelines, newPipeline]);
	};

	return (
		<div className="space-y-4">
			<div className="flex justify-between items-center">
				<h3 className="text-lg font-medium">Pipelines</h3>
				<Button onClick={() => setShowTemplateDialog(true)}>
					<Plus size={16} className="mr-2" />
					Create Pipeline
				</Button>
			</div>

			{pipelines?.length > 0 ? (
				<div className="space-y-2">
					{pipelines.map((pipeline: any) => (
						<Card key={pipeline.id}>
							<CardContent className="p-4">
								<div className="flex justify-between items-center">
									<div>
										<h4 className="font-medium">{pipeline.name}</h4>
										<p className="text-sm text-muted-foreground">
											Template: {pipeline.template}
										</p>
									</div>
									<div className="flex items-center gap-2">
										<Badge variant={"outline"}>{pipeline.status}</Badge>
										<Button size="sm">
											<Play size={14} />
										</Button>
									</div>
								</div>
							</CardContent>
						</Card>
					))}
				</div>
			) : (
				<div className="text-center py-8">
					<GitBranch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
					<h3 className="text-lg font-medium mb-2">No pipelines yet</h3>
					<p className="text-muted-foreground mb-4">
						Create your first pipeline from a template
					</p>
					<Button onClick={() => setShowTemplateDialog(true)}>
						<Plus size={16} className="mr-2" />
						Create Pipeline
					</Button>
				</div>
			)}

			<PipelineTemplateDialog
				open={showTemplateDialog}
				onOpenChange={setShowTemplateDialog}
				dataSourceId={dataSourceId}
				sourceType={sourceType}
				onCreatePipeline={handleCreatePipeline}
			/>
		</div>
	);
};

export { PipelineTemplateDialog, DataSourcePipelineSection };
