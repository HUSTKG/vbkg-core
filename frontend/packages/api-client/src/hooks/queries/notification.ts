import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
	IReadNotificationsRequest,
	IReadNotificationResponse,
} from "@vbkg/types";
import { NotificationService } from "../../services/notification";

// Fetch all notifications
export const useNotifications = (
	input: IReadNotificationsRequest,
	options?: UseQueryOptions<IReadNotificationResponse, Error>,
) => {
	return useQuery<IReadNotificationResponse, Error>({
		queryKey: ["notifications", input],
		queryFn: () => NotificationService.readNotifications(input),
		...options,
	});
};
