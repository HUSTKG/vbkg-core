import { ConflictSeverity } from "@vbkg/types";

interface SeverityBadgeProps {
	severity: ConflictSeverity
}

export const SeverityBadge = ({ severity }: SeverityBadgeProps) => {
	const severityConfig: Record<string, any> = {
		low: {
			label: "Thấp",
			color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
		},
		medium: {
			label: "Trung bình",
			color:
				"bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
		},
		high: {
			label: "Cao",
			color:
				"bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
		},
		critical: {
			label: "Nghiêm trọng",
			color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
		},
	};

	const config = severityConfig[severity] || severityConfig.medium;

	return (
		<span
			className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
		>
			{config.label}
		</span>
	);
};
