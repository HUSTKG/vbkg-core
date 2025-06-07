export const StatusBadge = ({ status }: any) => {
	const statusConfig: any = {
		detected: {
			label: "Phát hiện",
			color:
				"bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
		},
		under_review: {
			label: "Đang xem xét",
			color: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
		},
		resolved_manual: {
			label: "Đã giải quyết",
			color:
				"bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
		},
		resolved_auto: {
			label: "Tự động giải quyết",
			color:
				"bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
		},
		rejected: {
			label: "Từ chối",
			color: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
		},
		escalated: {
			label: "Báo cáo",
			color: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
		},
	};

	const config = statusConfig[status] || statusConfig.detected;

	return (
		<span
			className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}
		>
			{config.label}
		</span>
	);
};
