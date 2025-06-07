import { ResolutionMethodBadge } from "@/pages/common/quality-management/conflicts/components/ResolutionMethodBadge";
import { AlertTriangle, Check, ChevronDown, ChevronUp, Lightbulb, RefreshCw } from "lucide-react";
import { useState } from "react";

export const AISuggestionCard = ({ suggestion, index, onApply, isApplying }: any) => {
	const [isExpanded, setIsExpanded] = useState(false);

	return (
		<div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20">
			<div className="flex justify-between items-start mb-3">
				<div className="flex items-center space-x-2">
					<ResolutionMethodBadge method={suggestion.resolution_method} />
					<span className="text-sm font-medium text-gray-700 dark:text-gray-300">
						Gợi ý #{index + 1}
					</span>
				</div>
				<div className="flex items-center space-x-2">
					<span className="text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 rounded-full">
						{Math.round((suggestion.confidence_score || 0) * 100)}%
					</span>
					<button
						onClick={() => setIsExpanded(!isExpanded)}
						className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					>
						{isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
					</button>
				</div>
			</div>

			<p className="text-sm text-black dark:text-white mb-3">
				{suggestion.reasoning}
			</p>

			{isExpanded && (
				<div className="space-y-3 mb-4">
					{suggestion.potential_risks && (
						<div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-md border border-yellow-200 dark:border-yellow-800">
							<h5 className="text-xs font-medium text-yellow-800 dark:text-yellow-400 mb-1 flex items-center">
								<AlertTriangle size={12} className="mr-1" />
								RỦI RO TIỀM ẨN:
							</h5>
							<p className="text-xs text-yellow-700 dark:text-yellow-300">
								{suggestion.potential_risks}
							</p>
						</div>
					)}

					{suggestion.specific_actions && (
						<div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-200 dark:border-blue-800">
							<h5 className="text-xs font-medium text-blue-800 dark:text-blue-400 mb-2 flex items-center">
								<Lightbulb size={12} className="mr-1" />
								HÀNH ĐỘNG CỤ THỂ:
							</h5>
							<ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
								{suggestion.specific_actions.map(
									(action: string, idx: number) => (
										<li key={idx} className="flex items-start">
											<span className="inline-block w-1 h-1 bg-blue-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
											<span>{action}</span>
										</li>
									),
								)}
							</ul>
						</div>
					)}
				</div>
			)}

			<div className="flex justify-end">
				<button
					onClick={() => onApply(suggestion)}
					disabled={isApplying}
					className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
				>
					{isApplying ? (
						<>
							<RefreshCw size={12} className="mr-1 animate-spin" />
							Đang áp dụng...
						</>
					) : (
						<>
							<Check size={12} className="mr-1" />
							Áp dụng gợi ý
						</>
					)}
				</button>
			</div>
		</div>
	);
};
