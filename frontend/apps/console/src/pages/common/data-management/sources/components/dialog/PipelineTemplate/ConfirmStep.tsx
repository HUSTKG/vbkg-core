import React from 'react';
import { CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Label, Badge } from '@/components';
import { PipelineTemplate } from './types/pipeline';
import { getStepDisplayName, getStepIcon } from './utils/pipelineUtils';

interface ConfirmStepProps {
	selectedTemplate: PipelineTemplate;
	pipelineConfig: any;
	dataSourceId: string;
	stepConfigs: Record<string, Record<string, any>>;
	incrementalConfigs: Record<string, Record<string, any>>;
}

export const ConfirmStep: React.FC<ConfirmStepProps> = ({
	selectedTemplate,
	pipelineConfig,
	dataSourceId,
	stepConfigs,
	incrementalConfigs
}) => {
	return (
		<div className="space-y-6">
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<CheckCircle className="text-green-500" size={20} />
						Pipeline sẵn sàng tạo
					</CardTitle>
					<CardDescription>
						Xem lại cấu hình pipeline của bạn trước khi tạo
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
								Mẫu
							</Label>
							<p className="font-medium">{selectedTemplate.name}</p>
						</div>
						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Nguồn dữ liệu
							</Label>
							<p className="font-medium">{dataSourceId}</p>
						</div>
						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Thời gian ước tính
							</Label>
							<p className="font-medium">
								{selectedTemplate.estimated_duration}
							</p>
						</div>
					</div>

					<div>
						<Label className="text-sm font-medium text-muted-foreground">
							Mô tả
						</Label>
						<p className="text-sm">{pipelineConfig.description}</p>
					</div>

					<div className="flex gap-4">
						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Lập lịch
							</Label>
							<p className="text-sm">
								{pipelineConfig.schedule_enabled
									? `Đã bật (${pipelineConfig.schedule_cron})`
									: "Đã tắt"}
							</p>
						</div>
						<div>
							<Label className="text-sm font-medium text-muted-foreground">
								Tự động thử lại
							</Label>
							<p className="text-sm">
								{pipelineConfig.auto_retry
									? `Đã bật (tối đa ${pipelineConfig.max_retries} lần)`
									: "Đã tắt"}
							</p>
						</div>
					</div>

					{/* Step Configurations Summary */}
					<div>
						<Label className="text-sm font-medium text-muted-foreground">
							Các bước đã cấu hình
						</Label>
						<div className="space-y-2 mt-2">
							{selectedTemplate.steps.map((stepName, index) => {
								const stepKey = `${stepName}_${index}`;
								const config = stepConfigs[stepKey] || {};
								const incrementalConfig = incrementalConfigs[stepKey] || {};
								const hasCustomConfig = Object.keys(config).length > 0;
								const hasIncrementalConfig = Object.keys(incrementalConfig).length > 0 && incrementalConfig.enabled;

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
													Cấu hình tùy chỉnh
												</Badge>
											)}
											{hasIncrementalConfig && (
												<Badge variant={"outline"} className="text-xs bg-green-50 text-green-700">
													Tăng dần
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
