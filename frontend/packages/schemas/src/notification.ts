import { z } from "zod";

// Schema for retrieving notifications with optional filters
export const ReadNotificationsSchema = z.object({
  skip: z.number().min(0).default(0), // Pagination offset
  limit: z.number().min(1).default(100), // Pagination limit
  unread_only: z.boolean().default(false), // Optional filter for unread notifications
});

// Schema for retrieving a specific notification by ID
export const ReadNotificationByIdSchema = z.object({
  notification_id: z.string().uuid(), // Notification ID must be a valid UUID
});

// Schema for creating a notification
export const CreateNotificationSchema = z.object({
  title: z.string().min(1), // Notification title is required
  message: z.string().min(1), // Notification message is required
  icon: z.string().optional(), // Optional notification icon
});

// Schema for marking a notification as read
export const MarkNotificationAsReadSchema = z.object({
  notification_id: z.string().uuid(), // Notification ID must be a valid UUID
});

// Schema for updating a notification
export const UpdateNotificationSchema = z.object({
  notification_id: z.string().uuid(), // Notification ID must be a valid UUID
  title: z.string().optional(), // Optional title update
  message: z.string().optional(), // Optional message update
  icon: z.string().optional(), // Optional icon update
  is_read: z.boolean().optional(), // Optional read status update
});

// Schema for deleting a notification
export const DeleteNotificationSchema = z.object({
  notification_id: z.string().uuid(), // Notification ID must be a valid UUID
});
