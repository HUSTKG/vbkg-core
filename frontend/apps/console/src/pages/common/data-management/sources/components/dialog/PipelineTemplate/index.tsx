import React, { useState } from "react";
import { Play } from "lucide-react";
import { Dialog, Button, toast } from "@/components";
import {
	useCreatePipelineFromTemplate,
	usePipelineTemplates,
} from "@vbkg/api-client";
import { BrowseStep } from "./BrowseStep";
import { ConfigureStep } from "./ConfigureStep";
import { ConfirmStep } from "./ConfirmStep";
import {
	PipelineTemplate,
	PipelineTemplateDialogProps,
} from "./types/pipeline";
import { stepConfigSchemas, incrementalConfigSchema } from "./configs/stepConfigSchema";
import { isStepIncrementalCapable } from "./utils/pipelineUtils";

export const PipelineTemplateDialog: React.FC<PipelineTemplateDialogProps> = ({
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

	const [stepConfigs, setStepConfigs] = useState<
		Record<string, Record<string, any>>
	>({});
	const [incrementalConfigs, setIncrementalConfigs] = useState<
		Record<string, Record<string, any>>
	>({});

	const { data: templates = [] } = usePipelineTemplates({
		datasource_id: dataSourceId,
	});

	const { mutate: createPipeline } = useCreatePipelineFromTemplate({
		onSuccess: () => {
			toast("Tạo pipeline thành công");
		},
		onError: (error) => {
			toast("Tạo pipeline thất bại: " + error.message);
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

	const initializeStepConfigs = (template: PipelineTemplate) => {
		const configs: Record<string, Record<string, any>> = {};
		const incrementalConfigs: Record<string, Record<string, any>> = {};

		template.steps.forEach((stepName, index) => {
			const stepKey = `${stepName}_${index}`;
			const schema = stepConfigSchemas[stepName] || [];

			const config: Record<string, any> = {};
			schema.forEach((field) => {
				if (field.category !== "incremental") {
					config[field.key] = field.defaultValue;
				}
			});

			config.datasource_id = dataSourceId;
			config.trust_score = dataSource?.trust_score || 0.5;
			config.metadata_tracking = true;

			configs[stepKey] = config;

			if (isStepIncrementalCapable(stepName)) {
				const incrementalConfig: Record<string, any> = {};
				incrementalConfigSchema.forEach((field) => {
					incrementalConfig[field.key] = field.defaultValue;
				});
				incrementalConfigs[stepKey] = incrementalConfig;
			}
		});

		setStepConfigs(configs);
		setIncrementalConfigs(incrementalConfigs);
	};

	const filteredTemplates = (templates as any)?.data?.filter(
		(template: any) => {
			if (template.source_types && !template.source_types.includes(sourceType))
				return false;

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
		isIncremental: boolean = false,
	) => {
		if (isIncremental) {
			setIncrementalConfigs((prev) => ({
				...prev,
				[stepKey]: {
					...prev[stepKey],
					[fieldKey]: value,
				},
			}));
		} else {
			setStepConfigs((prev) => ({
				...prev,
				[stepKey]: {
					...prev[stepKey],
					[fieldKey]: value,
				},
			}));
		}
	};

	const handleCreatePipeline = () => {
		if (selectedTemplate) {
			const customOptions = {
				...pipelineConfig,
				steps: stepConfigs,
				incremental_configs: incrementalConfigs,
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
		setIncrementalConfigs({});
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

	return (
		<Dialog
			title="Tạo Pipeline từ Mẫu"
			description="Chọn một mẫu để tạo pipeline mới"
			size={"3xl"}
			open={open}
			onOpenChange={onOpenChange}
		>
			<div className="flex-1 overflow-hidden">
				{step === "browse" && (
					<BrowseStep
						templates={filteredTemplates}
						searchQuery={searchQuery}
						onSearchChange={setSearchQuery}
						onTemplateSelect={handleTemplateSelect}
					/>
				)}
				{step === "configure" && selectedTemplate && (
					<ConfigureStep
						selectedTemplate={selectedTemplate}
						configCategory={configCategory}
						onConfigCategoryChange={setConfigCategory}
						expandedSteps={expandedSteps}
						onToggleStepExpanded={(stepKey) =>
							setExpandedSteps((prev) => ({
								...prev,
								[stepKey]: !prev[stepKey],
							}))
						}
						stepConfigs={stepConfigs}
						incrementalConfigs={incrementalConfigs}
						onStepConfigChange={handleStepConfigChange}
						pipelineConfig={pipelineConfig}
						onPipelineConfigChange={setPipelineConfig}
						dataSourceId={dataSourceId}
					/>
				)}
				{step === "confirm" && selectedTemplate && (
					<ConfirmStep
						selectedTemplate={selectedTemplate}
						pipelineConfig={pipelineConfig}
						dataSourceId={dataSourceId}
						stepConfigs={stepConfigs}
						incrementalConfigs={incrementalConfigs}
					/>
				)}
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
							Xem lại & Xác nhận
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
