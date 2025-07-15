import React from "react";
import { Star } from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	Button,
	Badge,
	Label,
	Input,
	Textarea,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Switch,
	Separator,
} from "@/components";
import { PipelineTemplate, StepConfigField } from "./types/pipeline";
import { getDifficultyColor } from "./utils/pipelineUtils";

interface ConfigureStepProps {
	selectedTemplate: PipelineTemplate;
	configCategory: "basic" | "advanced" | "incremental";
	onConfigCategoryChange: (
		category: "basic" | "advanced" | "incremental",
	) => void;
	expandedSteps: Record<string, boolean>;
	onToggleStepExpanded: (stepKey: string) => void;
	stepConfigs: Record<string, Record<string, any>>;
	incrementalConfigs: Record<string, Record<string, any>>;
	onStepConfigChange: (
		stepKey: string,
		fieldKey: string,
		value: any,
		isIncremental?: boolean,
	) => void;
	pipelineConfig: any;
	onPipelineConfigChange: (config: any) => void;
	dataSourceId: string;
}

export const ConfigureStep: React.FC<ConfigureStepProps> = ({
	selectedTemplate,
	configCategory,
	onConfigCategoryChange,
	expandedSteps,
	onToggleStepExpanded,
	stepConfigs,
	incrementalConfigs,
	onStepConfigChange,
	pipelineConfig,
	onPipelineConfigChange,
	dataSourceId,
}) => {
	const renderConfigField = (
		field: StepConfigField,
		stepKey: string,
		value: any,
		isIncremental: boolean = false,
	) => {
		const fieldId = `${stepKey}_${field.key}`;

		// Skip dependent fields if their dependency is not met
		if (field.dependsOn) {
			const dependsOnValue = isIncremental
				? incrementalConfigs[stepKey]?.[field.dependsOn]
				: stepConfigs[stepKey]?.[field.dependsOn];
			if (!dependsOnValue) return null;
		}

		switch (field.type) {
			case "text":
				return (
					<Input
						id={fieldId}
						value={value || ""}
						onChange={(e) =>
							onStepConfigChange(
								stepKey,
								field.key,
								e.target.value,
								isIncremental,
							)
						}
						placeholder={`Nhập ${field.label.toLowerCase()}...`}
					/>
				);

			case "number":
				return (
					<Input
						id={fieldId}
						type="number"
						value={value || ""}
						onChange={(e) =>
							onStepConfigChange(
								stepKey,
								field.key,
								parseFloat(e.target.value) || 0,
								isIncremental,
							)
						}
						placeholder={`Nhập ${field.label.toLowerCase()}...`}
					/>
				);

			case "select":
				return (
					<Select
						value={value || field.defaultValue}
						onValueChange={(val) =>
							onStepConfigChange(stepKey, field.key, val, isIncremental)
						}
					>
						<SelectTrigger>
							<SelectValue placeholder="Chọn" />
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
							onStepConfigChange(stepKey, field.key, checked, isIncremental)
						}
					/>
				);

			case "textarea":
				return (
					<Textarea
						id={fieldId}
						value={value || ""}
						onChange={(e) =>
							onStepConfigChange(
								stepKey,
								field.key,
								e.target.value,
								isIncremental,
							)
						}
						placeholder={`Nhập ${field.label.toLowerCase()}...`}
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
							onStepConfigChange(stepKey, field.key, arrayValue, isIncremental);
						}}
						placeholder="Nhập các giá trị cách nhau bằng dấu phẩy..."
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
								onStepConfigChange(
									stepKey,
									field.key,
									jsonValue,
									isIncremental,
								);
							} catch {
								onStepConfigChange(
									stepKey,
									field.key,
									e.target.value,
									isIncremental,
								);
							}
						}}
						placeholder="Nhập đối tượng JSON..."
						rows={4}
					/>
				);

			default:
				return null;
		}
	};

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
										className={getDifficultyColor(selectedTemplate.difficulty)}
									>
										{selectedTemplate.difficulty}
									</Badge>
								)}
							</CardTitle>
							<CardDescription>{selectedTemplate.description}</CardDescription>
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
						{/* Configuration Category Tabs */}
						<div className="flex gap-2">
							<Button
								variant={configCategory === "basic" ? "default" : "outline"}
								size="sm"
								onClick={() => onConfigCategoryChange("basic")}
							>
								Cơ bản
							</Button>
							<Button
								variant={configCategory === "advanced" ? "default" : "outline"}
								size="sm"
								onClick={() => onConfigCategoryChange("advanced")}
							>
								Nâng cao
							</Button>
							<Button
								variant={
									configCategory === "incremental" ? "default" : "outline"
								}
								size="sm"
								onClick={() => onConfigCategoryChange("incremental")}
							>
								Tăng dần
							</Button>
						</div>

						<div>
							<Label className="text-sm font-medium">
								Bước pipeline ({selectedTemplate.steps?.length})
							</Label>
							{renderConfigField(
								field,
								stepKey,
								currentValue,
								configCategory === "incremental",
							)}
							{field.description && (
								<p className="text-xs text-muted-foreground">
									{field.description}
								</p>
							)}
						</div>
					</div>
				</CardContent>
			</Card>

			{/* Pipeline Configuration */}
			<Card>
				<CardHeader>
					<CardTitle>Cấu hình Pipeline</CardTitle>
					<CardDescription>
						Cấu hình các thiết lập pipeline của bạn
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<Label htmlFor="pipeline-name">Tên Pipeline</Label>
							<Input
								id="pipeline-name"
								value={pipelineConfig.name}
								onChange={(e) =>
									onPipelineConfigChange({
										...pipelineConfig,
										name: e.target.value,
									})
								}
								placeholder="Nhập tên pipeline..."
							/>
						</div>
						<div>
							<Label htmlFor="datasource">Nguồn dữ liệu</Label>
							<Input
								id="datasource"
								value={dataSourceId}
								disabled
								className="bg-muted"
							/>
						</div>
					</div>

					<div>
						<Label htmlFor="pipeline-description">Mô tả</Label>
						<Textarea
							id="pipeline-description"
							value={pipelineConfig.description}
							onChange={(e) =>
								onPipelineConfigChange({
									...pipelineConfig,
									description: e.target.value,
								})
							}
							placeholder="Nhập mô tả pipeline..."
							rows={3}
						/>
					</div>

					<Separator />

					<div className="space-y-4">
						<div className="flex items-center justify-between">
							<div>
								<Label htmlFor="schedule-enabled">Bật lập lịch</Label>
								<p className="text-sm text-muted-foreground">
									Chạy pipeline tự động theo lịch
								</p>
							</div>
							<Switch
								id="schedule-enabled"
								checked={pipelineConfig.schedule_enabled}
								onCheckedChange={(checked) =>
									onPipelineConfigChange({
										...pipelineConfig,
										schedule_enabled: checked,
									})
								}
							/>
						</div>

						{pipelineConfig.schedule_enabled && (
							<div>
								<Label htmlFor="schedule-cron">
									Lịch trình (Biểu thức Cron)
								</Label>
								<Select
									value={pipelineConfig.schedule_cron}
									onValueChange={(value) =>
										onPipelineConfigChange({
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
											Hàng ngày lúc 00:00
										</SelectItem>
										<SelectItem value="0 0 * * 0">
											Hàng tuần vào Chủ nhật
										</SelectItem>
										<SelectItem value="0 0 1 * *">
											Hàng tháng vào ngày 1
										</SelectItem>
										<SelectItem value="0 */6 * * *">Mỗi 6 giờ</SelectItem>
										<SelectItem value="*/30 * * * *">Mỗi 30 phút</SelectItem>
									</SelectContent>
								</Select>
							</div>
						)}

						<div className="flex items-center justify-between">
							<div>
								<Label htmlFor="auto-retry">Tự động thử lại</Label>
								<p className="text-sm text-muted-foreground">
									Tự động thử lại các bước thất bại
								</p>
							</div>
							<Switch
								id="auto-retry"
								checked={pipelineConfig.auto_retry}
								onCheckedChange={(checked) =>
									onPipelineConfigChange({
										...pipelineConfig,
										auto_retry: checked,
									})
								}
							/>
						</div>

						{pipelineConfig.auto_retry && (
							<div>
								<Label htmlFor="max-retries">Số lần thử lại tối đa</Label>
								<Select
									value={pipelineConfig.max_retries.toString()}
									onValueChange={(value) =>
										onPipelineConfigChange({
											...pipelineConfig,
											max_retries: parseInt(value),
										})
									}
								>
									<SelectTrigger>
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="1">1 lần thử lại</SelectItem>
										<SelectItem value="2">2 lần thử lại</SelectItem>
										<SelectItem value="3">3 lần thử lại</SelectItem>
										<SelectItem value="5">5 lần thử lại</SelectItem>
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
