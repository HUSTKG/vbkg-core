import React, { useState } from "react";
import {
	Plus,
	GitBranch,
	Play,
	Clock,
	CheckCircle,
	Search,
	Star,
	ChevronDown,
	ChevronRight,
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
	usePipelineTemplates,
} from "@vbkg/api-client";
import {
	stepConfigSchemas,
	stepDisplayMap,
} from "../../components/dialog/PipelineTemplate/configs/stepConfigSchema";
import {
	PipelineTemplate,
	PipelineTemplateDialogProps,
	StepConfigField,
} from "../../components/dialog/PipelineTemplate/types/pipeline";

const PipelineTemplateDialog: React.FC<PipelineTemplateDialogProps> = ({
	open,
	onOpenChange,
	dataSourceId,
	sourceType,
	dataSource,
	onCreatePipeline,
}) => {
	const [selectedTemplate, setSelectedTemplate] =
		useState<PipelineTemplate | null>(null);
	const [searchQuery, setSearchQuery] = useState("");
	const [step, setStep] = useState<"browse" | "configure" | "confirm">(
		"browse",
	);
	const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>(
		{},
	);
	const [configCategory, setConfigCategory] = useState<
		"basic" | "advanced" | "incremental"
	>("basic");

	// Enhanced step configurations with incremental support
	const [stepConfigs, setStepConfigs] = useState<
		Record<string, Record<string, any>>
	>({});

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
	});

	// Initialize configurations based on backend logic
	const initializeStepConfigs = (template: PipelineTemplate) => {
		const configs: Record<string, Record<string, any>> = {};

		template.steps.forEach((stepName, index) => {
			const stepKey = `${stepName}_${index}`;
			const schema = stepConfigSchemas[stepName] || [];

			// Initialize basic config
			const config: Record<string, any> = {};
			schema.forEach((field) => {
				config[field.key] = field.defaultValue;
			});

			// Add datasource-specific defaults based on backend logic
			config.datasource_id = dataSourceId;
			config.trust_score = dataSource?.trust_score || 0.5;
			config.metadata_tracking = true;

			configs[stepKey] = config;

			setStepConfigs(configs);
		});
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

	const getStepCategory = (stepName: string) => {
		const stepInfo = stepDisplayMap[stepName];
		return stepInfo?.category || "Processing";
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

	const handleStepConfigChange = (
		stepKey: string,
		fieldKey: string,
		value: any,
	) => {
		setStepConfigs((prev) => ({
			...prev,
			[stepKey]: {
				...prev[stepKey],
				[fieldKey]: value,
			},
		}));
	};

	const toggleStepExpanded = (stepKey: string) => {
		setExpandedSteps((prev) => ({
			...prev,
			[stepKey]: !prev[stepKey],
		}));
	};

	const renderConfigField = (
		field: StepConfigField,
		stepKey: string,
		value: any,
	) => {
		const fieldId = `${stepKey}_${field.key}`;

		// Skip dependent fields if their dependency is not met
		if (field.dependsOn) {
			const dependsOnValue = stepConfigs[stepKey]?.[field.dependsOn];
			if (!dependsOnValue) return null;
		}

		switch (field.type) {
			case "text":
				return (
					<Input
						id={fieldId}
						value={value || ""}
						onChange={(e) =>
							handleStepConfigChange(stepKey, field.key, e.target.value)
						}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
					/>
				);

			case "number":
				return (
					<Input
						id={fieldId}
						type="number"
						value={value || ""}
						onChange={(e) =>
							handleStepConfigChange(
								stepKey,
								field.key,
								parseFloat(e.target.value) || 0,
							)
						}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
					/>
				);

			case "select":
				return (
					<Select
						value={value || field.defaultValue}
						onValueChange={(val) =>
							handleStepConfigChange(stepKey, field.key, val)
						}
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
						onCheckedChange={(checked) =>
							handleStepConfigChange(stepKey, field.key, checked)
						}
					/>
				);

			case "textarea":
				return (
					<Textarea
						id={fieldId}
						value={value || ""}
						onChange={(e) =>
							handleStepConfigChange(stepKey, field.key, e.target.value)
						}
						placeholder={`Enter ${field.label.toLowerCase()}...`}
						rows={3}
					/>
				);

			case "array":
				return (
					<Input
						id={fieldId}
						value={Array.isArray(value) ? value.join(", ") : value || ""}
						onChange={(e) => {
							const arrayValue = e.target.value
								.split(",")
								.map((item) => item.trim())
								.filter(Boolean);
							handleStepConfigChange(stepKey, field.key, arrayValue);
						}}
						placeholder="Enter values separated by commas..."
					/>
				);

			case "json":
				return (
					<Textarea
						id={fieldId}
						value={
							typeof value === "object"
								? JSON.stringify(value, null, 2)
								: value || "{}"
						}
						onChange={(e) => {
							try {
								const jsonValue = JSON.parse(e.target.value);
								handleStepConfigChange(stepKey, field.key, jsonValue);
							} catch {
								// Keep the raw string if JSON is malformed
								handleStepConfigChange(stepKey, field.key, e.target.value);
							}
						}}
						placeholder="Enter JSON object..."
						rows={4}
					/>
				);

			default:
				return null;
		}
	};

	const handleCreatePipeline = () => {
		if (selectedTemplate) {
			// Prepare the custom options matching backend expectations
			const customOptions = {
				...pipelineConfig,
				steps: stepConfigs, // This matches the backend's expected structure
				datasource_id: dataSourceId,
				trust_score: dataSource?.trust_score || 0.5,
			};

			createPipeline({
				template_name: selectedTemplate.name,
				datasource_id: dataSourceId,
				custom_options: customOptions,
			});

			onCreatePipeline?.(selectedTemplate.id, {
				...customOptions,
				template: selectedTemplate,
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
						<div className="grid grid-cols-1 gap-2 mt-2">
							{selectedTemplate.steps?.map((stepName, index) => {
								const stepKey = `${stepName}_${index}`;
								const stepCategory = getStepCategory(stepName);
								const isExpanded = expandedSteps[stepKey];
								const configSchema = stepConfigSchemas[stepName] || [];

								// Filter fields by category
								const fieldsToShow = configSchema.filter(
									(field) =>
										field.category === configCategory ||
										(!field.category && configCategory === "basic"),
								);

								const hasConfig = fieldsToShow.length > 0;

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
																{stepCategory}
															</Badge>
														</div>
														<p className="text-xs text-muted-foreground">
															{getStepDescription(stepName)}
														</p>
													</div>
													{hasConfig && (
														<div className="flex items-center gap-2">
															{isExpanded ? (
																<ChevronDown size={14} />
															) : (
																<ChevronRight size={14} />
															)}
														</div>
													)}
												</div>
											</CollapsibleTrigger>

											{hasConfig && (
												<CollapsibleContent>
													<div className="px-3 pb-3 pt-0 border-t bg-gray-50/50">
														<div className="space-y-3 pt-3">
															<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
																{fieldsToShow.map((field) => {
																	const currentValue =
																		stepConfigs[stepKey]?.[field.key];

																	return (
																		<div key={field.key} className="space-y-1">
																			<Label
																				htmlFor={`${stepKey}_${field.key}`}
																				className="text-xs font-medium"
																			>
																				{field.label}
																				{field.required && (
																					<span className="text-red-500 ml-1">
																						*
																					</span>
																				)}
																			</Label>
																			{renderConfigField(
																				field,
																				stepKey,
																				currentValue,
																			)}
																			{field.description && (
																				<p className="text-xs text-muted-foreground">
																					{field.description}
																				</p>
																			)}
																		</div>
																	);
																})}
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
							<div className="space-y-2">
								<Label htmlFor="pipeline-name">Tên</Label>
								<Input
									id="pipeline-name"
									value={pipelineConfig.name}
									onChange={(e) =>
										setPipelineConfig({
											...pipelineConfig,
											name: e.target.value,
										})
									}
									placeholder="Nhập tên..."
								/>
							</div>
							<div className="space-y-2">
								<Label htmlFor="datasource">Nguồn</Label>
								<Input
									id="datasource"
									value={dataSourceId}
									disabled
									className="bg-muted"
								/>
							</div>
						</div>

						<div className="space-y-2">
							<Label htmlFor="pipeline-description">Mô tả</Label>
							<Textarea
								id="pipeline-description"
								value={pipelineConfig.description}
								onChange={(e) =>
									setPipelineConfig({
										...pipelineConfig,
										description: e.target.value,
									})
								}
								placeholder="Nhập mô tả..."
								rows={3}
							/>
						</div>

						<Separator />
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
							Xác nhận cấu hình
						</CardTitle>
						<CardDescription>
							Xem lại cấu hình của bạn trước khi tạo pipeline mới.
						</CardDescription>
					</CardHeader>
					<CardContent className="space-y-4">
						<div className="grid grid-cols-2 gap-4">
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Tên Pipeline
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
									Nguồn
								</Label>
								<p className="font-medium">{dataSourceId}</p>
							</div>
							<div>
								<Label className="text-sm font-medium text-muted-foreground">
									Dự kiến hoàn thành
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
										<div
											key={stepKey}
											className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
										>
											<div className="flex items-center gap-2">
												{getStepIcon(stepName)}
												<span>{getStepDisplayName(stepName)}</span>
											</div>
											<div className="flex gap-1">
												{hasCustomConfig && (
													<Badge variant={"outline"} className="text-xs">
														Custom config
													</Badge>
												)}
											</div>
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
			title="Tạo Pipeline từ Template"
			description="Chọn một template để bắt đầu cấu hình pipeline của bạn."
			size={"3xl"}
			open={open}
			onOpenChange={onOpenChange}
		>
			<div className="flex-1 overflow-hidden">
				{step === "browse" && renderBrowseStep()}
				{step === "configure" && renderConfigureStep()}
				{step === "confirm" && renderConfirmStep()}
			</div>

			<div className="flex justify-between items-center mt-4 pt-4 border-t">
				<div className="flex items-center gap-2">
					{step !== "browse" && (
						<Button
							variant="outline"
							onClick={() => {
								if (step === "configure") setStep("browse");
								if (step === "confirm") setStep("configure");
							}}
						>
							Quay lại
						</Button>
					)}
				</div>

				<div className="flex items-center gap-2">
					<Button variant="outline" onClick={() => onOpenChange(false)}>
						Hủy
					</Button>

					{step === "configure" && (
						<Button
							onClick={() => setStep("confirm")}
							disabled={!pipelineConfig.name.trim()}
						>
							Xem lại và xác nhận
						</Button>
					)}

					{step === "confirm" && (
						<Button onClick={handleCreatePipeline}>
							<Play size={16} className="mr-2" />
							Tạo Pipeline
						</Button>
					)}
				</div>
			</div>
		</Dialog>
	);
};

// Integration with DataSource Detail Page (unchanged)
const DataSourcePipelineSection: React.FC<{
	dataSourceId: string;
	sourceType: string;
	dataSource?: any;
}> = ({ dataSourceId, sourceType, dataSource }) => {
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
					<h3 className="text-lg font-medium mb-2">No Pipelines Yet</h3>
					<p className="text-muted-foreground mb-4">
						Create a new pipeline to start processing data from this source.
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
				dataSource={dataSource}
				onCreatePipeline={handleCreatePipeline}
			/>
		</div>
	);
};

export { PipelineTemplateDialog, DataSourcePipelineSection };
