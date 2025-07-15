import { GitBranch } from "lucide-react";
import { stepDisplayMap } from "../configs/stepDisplayMap";

export const isStepIncrementalCapable = (stepType: string): boolean => {
	const incrementalCapableTypes = new Set([
		"file_ingestion",
		"api_ingestion",
		"database_ingestion",
		"knowledge_extractor",
		"knowledge_mapping",
		"entity_resolution",
		"kg_writer",
		"quality_monitoring",
	]);
	return incrementalCapableTypes.has(stepType);
};

export const getDifficultyColor = (difficulty?: string) => {
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

export const getStepIcon = (stepName: string) => {
	const stepInfo = stepDisplayMap[stepName];
	return stepInfo?.icon || <GitBranch size={14} />;
};

export const getStepDisplayName = (stepName: string) => {
	const stepInfo = stepDisplayMap[stepName];
	return stepInfo?.name || stepName;
};

export const getStepDescription = (stepName: string) => {
	const stepInfo = stepDisplayMap[stepName];
	return stepInfo?.description || "Bước xử lý";
};

export const getStepCategory = (_stepName: string) => {
	return "Xử lý";
};
