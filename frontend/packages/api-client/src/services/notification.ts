import {
  ICreateNotificationRequest,
  ICreateNotificationResponse,
  IDeleteNotificationRequest,
  IDeleteNotificationResponse,
  IMarkNotificationReadRequest,
  IMarkNotificationReadResponse,
  IReadNotificationRequest,
  IReadNotificationResponse,
  IReadNotificationsRequest,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const readNotifications = async (
  input: IReadNotificationsRequest,
): Promise<IReadNotificationResponse> => {
  return await api()
    .get<IReadNotificationResponse>(API_ENDPOINTS.READ_NOTIFICATIONS, {
      params: input,
    })
    .then((res) => res.data);
};

const readNotification = async (
  input: IReadNotificationRequest,
): Promise<IReadNotificationResponse> => {
  return await api()
    .get<IReadNotificationResponse>(API_ENDPOINTS.READ_NOTIFICATION(input.id), {
      params: input,
    })
    .then((res) => res.data);
};

const createNotification = async (
  input: ICreateNotificationRequest,
): Promise<ICreateNotificationResponse> => {
  return await api()
    .post<ICreateNotificationResponse>(API_ENDPOINTS.CREATE_NOTIFICATION, input)
    .then((res) => res.data);
};

const deleteNotification = async (
  input: IDeleteNotificationRequest,
): Promise<IDeleteNotificationResponse> => {
  return await api()
    .delete<IDeleteNotificationResponse>(
      API_ENDPOINTS.DELETE_NOTIFICATION(input.id),
    )
    .then((res) => res.data);
};

const markNotificationAsRead = async (
  input: IMarkNotificationReadRequest,
): Promise<IMarkNotificationReadResponse> => {
  return await api()
    .put<IMarkNotificationReadResponse>(
      API_ENDPOINTS.MARK_NOTIFICATION_READ(input.id),
      input,
    )
    .then((res) => res.data);
};

export const NotificationService = {
  readNotifications,
  readNotification,
  createNotification,
  deleteNotification,
  markNotificationAsRead,
};
