// packages/ui/src/notification-item/index.tsx
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  Info,
  MoreVertical,
  X,
} from "lucide-react";
import React from "react";
import { cn } from "../../lib/utils";

export type NotificationType = "info" | "success" | "warning" | "error";

export interface NotificationItemProps {
  id: string | number;
  title: string;
  message: string;
  time: string | Date;
  type?: NotificationType;
  icon?: React.ReactNode;
  read?: boolean;
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
  onMarkAsRead?: (id: string | number) => void;
  onDelete?: (id: string | number) => void;
  onClick?: () => void;
  className?: string;
}

const getTypeIcon = (type: NotificationType) => {
  switch (type) {
    case "success":
      return <CheckCircle size={16} />;
    case "warning":
      return <AlertTriangle size={16} />;
    case "error":
      return <AlertCircle size={16} />;
    case "info":
    default:
      return <Info size={16} />;
  }
};

const getTypeStyles = (type: NotificationType) => {
  switch (type) {
    case "success":
      return "text-green-500 bg-green-100 dark:bg-green-900/30 dark:text-green-400";
    case "warning":
      return "text-amber-500 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400";
    case "error":
      return "text-red-500 bg-red-100 dark:bg-red-900/30 dark:text-red-400";
    case "info":
    default:
      return "text-blue-500 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400";
  }
};

const formatTime = (time: string | Date): string => {
  const date = typeof time === "string" ? new Date(time) : time;
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000); // seconds

  if (diff < 60) {
    return `${diff} giây trước`;
  }

  const minutes = Math.floor(diff / 60);
  if (minutes < 60) {
    return `${minutes} phút trước`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} giờ trước`;
  }

  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days} ngày trước`;
  }

  // For older notifications, display the actual date
  return date.toLocaleDateString();
};

const NotificationItem: React.FC<NotificationItemProps> = ({
  id,
  title,
  message,
  time,
  type = "info",
  read = false,
  actions = [],
  onMarkAsRead,
  onDelete,
  onClick,
  className,
}) => {
  const [showActions, setShowActions] = React.useState(false);

  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onMarkAsRead) {
      onMarkAsRead(id);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(id);
    }
  };

  const toggleActions = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowActions(!showActions);
  };

  return (
    <div
      className={cn(
        "relative border-b border-gray-200 dark:border-gray-700 last:border-b-0 p-4",
        !read && "bg-blue-50 dark:bg-blue-900/10",
        onClick && "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50",
        className,
      )}
      onClick={onClick}
    >
      <div className="flex items-center">
        <div className={cn("p-2 flex rounded-full mr-3", getTypeStyles(type))}>
          {getTypeIcon(type)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start">
            <h4
              className={cn(
                "font-medium text-gray-900 dark:text-white mb-1 pr-6",
                !read && "font-semibold",
              )}
            >
              {title}
            </h4>
            <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap ml-2">
              {formatTime(time)}
            </span>
          </div>

          <p className="text-gray-600 dark:text-gray-300 text-sm mb-2">
            {message}
          </p>

          {actions.length > 0 && (
            <div className="flex space-x-3 mt-2">
              {actions.map((action, index) => (
                <button
                  key={index}
                  onClick={(e) => {
                    e.stopPropagation();
                    action.onClick();
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-start space-x-1 ml-2">
          {!read && onMarkAsRead && (
            <button
              onClick={handleMarkAsRead}
              className="p-1 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
              title="Đánh dấu đã đọc"
              aria-label="Đánh dấu đã đọc"
            >
              <CheckCircle size={16} />
            </button>
          )}

          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-1 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
              title="Xóa thông báo"
              aria-label="Xóa thông báo"
            >
              <X size={16} />
            </button>
          )}

          {actions.length > 0 && (
            <div className="relative">
              <button
                onClick={toggleActions}
                className="p-1 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                title="Hành động khác"
                aria-label="Hành động khác"
                aria-expanded={showActions}
              >
                <MoreVertical size={16} />
              </button>

              {showActions && (
                <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-10">
                  {actions.map((action, index) => (
                    <button
                      key={index}
                      onClick={(e) => {
                        e.stopPropagation();
                        action.onClick();
                        setShowActions(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {!read && (
        <div className="absolute top-1/2 left-0 transform -translate-y-1/2 w-1 h-full bg-blue-500 rounded-r-full" />
      )}
    </div>
  );
};

// Pre-defined notification items
export const SuccessNotification: React.FC<
  Omit<NotificationItemProps, "type">
> = (props) => <NotificationItem type="success" {...props} />;

export const WarningNotification: React.FC<
  Omit<NotificationItemProps, "type">
> = (props) => <NotificationItem type="warning" {...props} />;

export const ErrorNotification: React.FC<
  Omit<NotificationItemProps, "type">
> = (props) => <NotificationItem type="error" {...props} />;

export const InfoNotification: React.FC<Omit<NotificationItemProps, "type">> = (
  props,
) => <NotificationItem type="info" {...props} />;

export default NotificationItem;
