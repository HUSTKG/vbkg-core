export type NotificationBase = {
  title: string;
  message: string;
  icon?: string;
  link?: string;
};

export type NotificationCreate = NotificationBase & {
  user_id: string;
  is_read?: boolean;
};

export type NotificationUpdate = Partial<NotificationBase> & {
  is_read?: boolean;
};

export type Notification = NotificationBase & {
  id: string;
  user_id: string;
  is_read: boolean;
  created_at: Date;
};

export type NotificationInDB = Notification;

export type BatchNotificationCreate = {
  user_ids: string[];
  notification: NotificationBase;
};

export type NotificationCount = {
  total: number;
  unread: number;
};

export type MarkNotificationsAsRead = {
  notification_ids: string[];
};
