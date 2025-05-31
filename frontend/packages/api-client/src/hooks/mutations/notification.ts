import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
  ICreateNotificationRequest,
  ICreateNotificationResponse,
  IDeleteNotificationRequest,
  IDeleteNotificationResponse,
  IMarkNotificationReadRequest,
  IMarkNotificationReadResponse,
} from "@vbkg/types";
import { NotificationService } from "../../services/notification";

// Create a new notification
export const useCreateNotification = (
  options: UseMutationOptions<ICreateNotificationResponse, Error, ICreateNotificationRequest>,
) => {
  return useMutation<ICreateNotificationResponse, Error, ICreateNotificationRequest>({
    mutationFn: NotificationService.createNotification,
    ...options,
  });
};

// Delete a notification
export const useDeleteNotification = (
  options: UseMutationOptions<IDeleteNotificationResponse, Error, IDeleteNotificationRequest>,
) => {
  return useMutation<IDeleteNotificationResponse, Error, IDeleteNotificationRequest>({
    mutationFn: NotificationService.deleteNotification,
    ...options,
  });
};

// Mark notification as read
export const useMarkNotificationAsRead = (
  options: UseMutationOptions<IMarkNotificationReadResponse, Error, IMarkNotificationReadRequest>,
) => {
  return useMutation<IMarkNotificationReadResponse, Error, IMarkNotificationReadRequest>({
    mutationFn: NotificationService.markNotificationAsRead,
    ...options,
  });
};
