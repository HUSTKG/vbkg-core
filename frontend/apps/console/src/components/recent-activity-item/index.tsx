// packages/ui/src/recent-activity-item/index.tsx
import React from 'react';
import { cn } from '../../lib/utils';

export type ActivityStatus = 'success' | 'warning' | 'error' | 'info';

export interface RecentActivityItemProps {
  title: string;
  time: string;
  icon: React.ReactNode;
  description: string;
  status: ActivityStatus;
  onClick?: () => void;
  actionButton?: React.ReactNode;
  className?: string;
}

const RecentActivityItem: React.FC<RecentActivityItemProps> = ({
  title,
  time,
  icon,
  description,
  status,
  onClick,
  actionButton,
  className,
}) => {
  const getStatusColor = (status: ActivityStatus) => {
    switch (status) {
      case 'success':
        return 'text-green-500 bg-green-100 dark:bg-green-900/50 dark:text-green-300';
      case 'warning':
        return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/50 dark:text-yellow-300';
      case 'error':
        return 'text-red-500 bg-red-100 dark:bg-red-900/50 dark:text-red-300';
      case 'info':
      default:
        return 'text-blue-500 bg-blue-100 dark:bg-blue-900/50 dark:text-blue-300';
    }
  };

  const formattedTime = typeof time === 'string' 
    ? time 
    : new Date(time).toLocaleString();

  return (
    <div 
      className={cn(
        "flex items-start space-x-4 mb-4 pb-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0 last:mb-0 last:pb-0",
        onClick && "cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 p-2 -m-2 rounded-md transition-colors",
        className
      )}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className={cn("p-2 rounded-full", getStatusColor(status))}>
        {icon}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start">
          <h4 className="font-medium text-gray-900 dark:text-white truncate max-w-[75%]">
            {title}
          </h4>
          <span className="text-sm text-gray-500 dark:text-gray-400 flex-shrink-0">
            {formattedTime}
          </span>
        </div>
        
        <p className="text-gray-600 dark:text-gray-300 text-sm mt-1">
          {description}
        </p>
        
        {actionButton && (
          <div className="mt-2">
            {actionButton}
          </div>
        )}
      </div>
    </div>
  );
};

// Function to format time difference like "5 minutes ago", "2 hours ago", etc.
export const formatTimeAgo = (date: Date | string | number): string => {
  const now = new Date();
  const pastDate = new Date(date);
  const secondsDiff = Math.floor((now.getTime() - pastDate.getTime()) / 1000);
  
  if (secondsDiff < 60) {
    return `${secondsDiff} giây trước`;
  }
  
  const minutesDiff = Math.floor(secondsDiff / 60);
  if (minutesDiff < 60) {
    return `${minutesDiff} phút trước`;
  }
  
  const hoursDiff = Math.floor(minutesDiff / 60);
  if (hoursDiff < 24) {
    return `${hoursDiff} giờ trước`;
  }
  
  const daysDiff = Math.floor(hoursDiff / 24);
  if (daysDiff < 30) {
    return `${daysDiff} ngày trước`;
  }
  
  const monthsDiff = Math.floor(daysDiff / 30);
  if (monthsDiff < 12) {
    return `${monthsDiff} tháng trước`;
  }
  
  const yearsDiff = Math.floor(monthsDiff / 12);
  return `${yearsDiff} năm trước`;
};

// Pre-defined activity items for common use cases
export const DataAddedActivity: React.FC<Omit<RecentActivityItemProps, 'status' | 'icon'> & { icon?: React.ReactNode }> = 
  ({ icon, ...props }) => (
    <RecentActivityItem status="success" icon={icon} {...props} />
  );

export const ConflictDetectedActivity: React.FC<Omit<RecentActivityItemProps, 'status' | 'icon'> & { icon?: React.ReactNode }> = 
  ({ icon, ...props }) => (
    <RecentActivityItem status="warning" icon={icon} {...props} />
  );

export const ErrorActivity: React.FC<Omit<RecentActivityItemProps, 'status' | 'icon'> & { icon?: React.ReactNode }> = 
  ({ icon, ...props }) => (
    <RecentActivityItem status="error" icon={icon} {...props} />
  );

export const InfoActivity: React.FC<Omit<RecentActivityItemProps, 'status' | 'icon'> & { icon?: React.ReactNode }> = 
  ({ icon, ...props }) => (
    <RecentActivityItem status="info" icon={icon} {...props} />
  );

export default RecentActivityItem;
