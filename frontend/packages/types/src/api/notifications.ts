import { ApiResponse, PaginatedResponse } from "../models";
import { NotificationCreate, NotificationUpdate } from "../models/notification";

export interface IReadNotificationsRequest {
  skip: number;
  limit: number;
  unread_only: number;
}

export interface IReadNotificationsResponse
  extends PaginatedResponse<Notification> {}

export interface IReadNotificationRequest {
  id: string;
}
export interface IReadNotificationResponse extends ApiResponse<Notification> {}

export interface ICreateNotificationRequest extends NotificationCreate {}
export interface ICreateNotificationResponse
  extends ApiResponse<Notification> {}

export interface IMarkNotificationReadRequest {
  id: string;
}
export interface IMarkNotificationReadResponse
  extends ApiResponse<Notification> {}

export interface IUpdateNotificationRequest extends NotificationUpdate {
  id: string;
}
export interface IUpdateNotificationResponse
  extends ApiResponse<Notification> {}

export interface IDeleteNotificationRequest {
  id: string;
}
export interface IDeleteNotificationResponse extends ApiResponse<unknown> {}
