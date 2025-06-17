import { ResolutionMethod } from "@vbkg/types";

interface ResolutionMethodBadgeProps {
	method: ResolutionMethod
}

export const ResolutionMethodBadge = ({ method }: ResolutionMethodBadgeProps) => {
	const colors: any = {
		merge_entities:
			"bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400",
		keep_both:
			"bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400",
		keep_source:
			"bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400",
		keep_target:
			"bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400",
		create_new:
			"bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400",
	};

	const methodLabels: any = {
		merge_entities: "Hợp nhất",
		keep_both: "Giữ cả hai",
		keep_source: "Giữ nguồn",
		keep_target: "Giữ đích",
		create_new: "Tạo mới",
	};

	return (
		<span
			className={`px-2 py-1 text-xs font-medium rounded-full ${colors[method] || "bg-gray-100 text-gray-800"}`}
		>
			{methodLabels[method] || method}
		</span>
	);
};
