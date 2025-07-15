import { format, formatDistance } from "date-fns";
import { vi } from "date-fns/locale";

export const formatDate = (date?: Date | string): string => {
	if (!date) return "";
	const d = typeof date === "string" ? new Date(date) : date;
	return format(d, "PP", {
		locale: vi,
	});
};

export const formatDateTime = (date: Date | string): string => {
	const d = typeof date === "string" ? new Date(date) : date;
	return format(d, "PPpp");
};

export const formatRelativeTime = (date: Date | string): string => {
	const d = typeof date === "string" ? new Date(date) : date;
	return formatDistance(d, new Date(), { addSuffix: true });
};

export const formatTimeAgo = (timestamp: number) => {
	const now = new Date().getTime();
	const past = new Date(timestamp).getTime();
	const diffInMinutes = Math.floor((now - past) / (1000 * 60));

	if (diffInMinutes < 1) return "Just now";
	if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
	if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
	return `${Math.floor(diffInMinutes / 1440)}d ago`;
};
