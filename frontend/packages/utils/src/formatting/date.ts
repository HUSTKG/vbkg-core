import { format, formatDistance } from "date-fns";

export const formatDate = (date?: Date | string): string => {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  return format(d, "PP");
};

export const formatDateTime = (date: Date | string): string => {
  const d = typeof date === "string" ? new Date(date) : date;
  return format(d, "PPpp");
};

export const formatRelativeTime = (date: Date | string): string => {
  const d = typeof date === "string" ? new Date(date) : date;
  return formatDistance(d, new Date(), { addSuffix: true });
};
