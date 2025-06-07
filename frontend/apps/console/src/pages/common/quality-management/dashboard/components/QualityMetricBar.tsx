interface QualityMetricBarProps {
	label: string;
	score: number;
}

export default function QualityMetricBar({
	label,
	score = 0.0, // Default to 0 if score is not provided
}: QualityMetricBarProps) {
	const percentage = Math.round(score * 100);
	const getColor = (score: any) => {
		if (score >= 0.9) return { bg: "bg-emerald-500", text: "text-emerald-600" };
		if (score >= 0.7) return { bg: "bg-blue-500", text: "text-blue-600" };
		if (score >= 0.5) return { bg: "bg-yellow-500", text: "text-yellow-600" };
		return { bg: "bg-red-500", text: "text-red-600" };
	};

	const colors = getColor(score);

	return (
		<div className="mb-6">
			<div className="flex justify-between items-center mb-3">
				<span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
					{label}
				</span>
				<span
					className={`text-sm font-bold ${colors.text} bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full`}
				>
					{percentage}%
				</span>
			</div>
			<div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
				<div
					className={`${colors.bg} h-3 rounded-full transition-all duration-1000 ease-out relative overflow-hidden`}
					style={{ width: `${percentage}%` }}
				>
					<div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-20 animate-pulse" />
				</div>
			</div>
		</div>
	);
};
