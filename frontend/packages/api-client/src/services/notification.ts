import {
	ICreateNotificationRequest,
	ICreateNotificationResponse,
	IDeleteNotificationRequest,
	IDeleteNotificationResponse,
	IMarkNotificationReadRequest,
	IMarkNotificationReadResponse,
	IReadNotificationResponse,
	IReadNotificationsRequest,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const readNotifications = async (input: IReadNotificationsRequest) => {
	return await api().get<IReadNotificationResponse>(
		API_ENDPOINTS.READ_NOTIFICATIONS,
		{
			params: input,
		},
	);
};

const createNotification = async (input: ICreateNotificationRequest) => {
	return await api().post<ICreateNotificationResponse>(
		API_ENDPOINTS.CREATE_NOTIFICATION,
		input,
	);
};

const deleteNotification = async (input: IDeleteNotificationRequest) => {
	return await api().delete<IDeleteNotificationResponse>(
		API_ENDPOINTS.DELETE_NOTIFICATION(input.id),
	);
};

const markNotificationAsRead = async (input: IMarkNotificationReadRequest) => {
	return await api().put<IMarkNotificationReadResponse>(
		API_ENDPOINTS.MARK_NOTIFICATION_READ(input.id),
		input,
	);
};

export const NotificationService = {
	readNotifications,
	createNotification,
	deleteNotification,
	markNotificationAsRead,
};
