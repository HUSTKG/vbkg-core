// packages/ui/src/empty-state/index.tsx
import React from 'react';
import { File, FileSearch, Plus, DatabaseIcon, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/utils';

export type EmptyStateType = 'default' | 'search' | 'data' | 'error' | 'loading' | 'custom';

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  type?: EmptyStateType;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  bordered?: boolean;
  centered?: boolean;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  type = 'default',
  className,
  size = 'md',
  bordered = false,
  centered = true,
}) => {
  // Default icons based on type
  const getDefaultIcon = () => {
    switch (type) {
      case 'search':
        return <FileSearch size={48} className="text-gray-400 dark:text-gray-500" />;
      case 'data':
        return <DatabaseIcon size={48} className="text-gray-400 dark:text-gray-500" />;
      case 'error':
        return <AlertCircle size={48} className="text-red-500 dark:text-red-400" />;
      case 'loading':
        return <RefreshCw size={48} className="text-blue-500 dark:text-blue-400 animate-spin" />;
      case 'default':
      default:
        return <File size={48} className="text-gray-400 dark:text-gray-500" />;
    }
  };

  // Size classes
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'py-6 px-4';
      case 'lg':
        return 'py-16 px-8';
      case 'md':
      default:
        return 'py-12 px-6';
    }
  };

  // Icon size based on component size
  const getIconSize = () => {
    switch (size) {
      case 'sm':
        return 'h-12 w-12';
      case 'lg':
        return 'h-24 w-24';
      case 'md':
      default:
        return 'h-16 w-16';
    }
  };
  
  return (
    <div 
      className={cn(
        getSizeClasses(),
        bordered && "border border-gray-200 dark:border-gray-700 rounded-lg",
        centered && "flex flex-col items-center justify-center text-center",
        className
      )}
    >
      <div className={cn(
        "flex flex-col gap-4",
        centered && "items-center text-center"
      )}>
        <div className={cn(
          "inline-flex rounded-full",
          type === 'error' ? "bg-red-100 dark:bg-red-900/30 p-3" :
          type === 'loading' ? "bg-blue-100 dark:bg-blue-900/30 p-3" :
          "bg-gray-100 dark:bg-gray-800 p-3"
        )}>
          <div className={getIconSize()}>
            {icon || getDefaultIcon()}
          </div>
        </div>
        
        <div className="space-y-1">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            {title}
          </h3>
          
          {description && (
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
              {description}
            </p>
          )}
        </div>
        
        {action && (
          <div className="mt-2">
            {action}
          </div>
        )}
      </div>
    </div>
  );
};

// Pre-configured empty states
export const SearchEmptyState: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="search" 
    description={props.description || "Thử sử dụng các từ khóa khác hoặc điều chỉnh bộ lọc của bạn."}
    {...props}
  />
);

export const DataEmptyState: React.FC<Omit<EmptyStateProps, 'type' | 'action'> & { 
  onAdd?: () => void, 
  addLabel?: string 
}> = ({ onAdd, addLabel = "Thêm mới", ...props }) => {
  const actionButton = onAdd ? (
    <button 
      onClick={onAdd}
      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      <Plus size={16} className="mr-2" />
      {addLabel}
    </button>
  ) : undefined;

  return (
    <EmptyState 
      type="data" 
      description={props.description || "Bắt đầu bằng cách thêm dữ liệu mới vào hệ thống."}
      action={actionButton}
      {...props}
    />
  );
};

export const ErrorEmptyState: React.FC<Omit<EmptyStateProps, 'type' | 'action'> & { 
  onRetry?: () => void, 
  retryLabel?: string 
}> = ({ onRetry, retryLabel = "Thử lại", ...props }) => {
  const actionButton = onRetry ? (
    <button 
      onClick={onRetry}
      className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
    >
      <RefreshCw size={16} className="mr-2" />
      {retryLabel}
    </button>
  ) : undefined;

  return (
    <EmptyState 
      type="error" 
      description={props.description || "Không thể tải dữ liệu. Vui lòng thử lại sau."}
      action={actionButton}
      {...props}
    />
  );
};

export const LoadingEmptyState: React.FC<Omit<EmptyStateProps, 'type'>> = (props) => (
  <EmptyState 
    type="loading" 
    description={props.description || "Vui lòng đợi trong giây lát..."}
    {...props}
  />
);

export default EmptyState;
