import React from "react";
import { Search, GitBranch, Clock, Star } from "lucide-react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	Input,
	ScrollArea,
	Badge,
	Button,
} from "@/components";
import { PipelineTemplate } from "./types/pipeline";
import { getDifficultyColor } from "./utils/pipelineUtils";

interface BrowseStepProps {
	templates: PipelineTemplate[];
	searchQuery: string;
	onSearchChange: (query: string) => void;
	onTemplateSelect: (template: PipelineTemplate) => void;
}

export const BrowseStep: React.FC<BrowseStepProps> = ({
	templates,
	searchQuery,
	onSearchChange,
	onTemplateSelect,
}) => {
	return (
		<div className="space-y-6">
			<div className="space-y-4">
				<div className="flex gap-4">
					<div className="flex-1 relative">
						<Search
							className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground"
							size={16}
						/>
						<Input
							placeholder="Tìm kiếm mẫu..."
							value={searchQuery}
							onChange={(e) => onSearchChange(e.target.value)}
							className="pl-10"
						/>
					</div>
				</div>

				<ScrollArea className="h-96">
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4 pr-4">
						{templates?.map((template) => (
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
										{template.tags?.slice(0, 3).map((tag) => (
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
										onClick={() => onTemplateSelect(template)}
									>
										Sử dụng mẫu
									</Button>
								</CardContent>
							</Card>
						))}
					</div>
				</ScrollArea>

				{templates?.length === 0 && (
					<div className="text-center py-8">
						<GitBranch className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
						<h3 className="text-lg font-medium mb-2">Không tìm thấy mẫu</h3>
						<p className="text-muted-foreground">
							Thử điều chỉnh tiêu chí tìm kiếm hoặc bộ lọc
						</p>
					</div>
				)}
			</div>
		</div>
	);
};
