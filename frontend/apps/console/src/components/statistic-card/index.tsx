import React from 'react';
import { cn } from '../../lib/utils';

export interface StatisticCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
  description?: string;
  onClick?: () => void;
  className?: string;
}

const colorMap = {
  blue: 'bg-blue-500 text-white',
  green: 'bg-green-500 text-white',
  red: 'bg-red-500 text-white',
  yellow: 'bg-amber-500 text-white',
  purple: 'bg-purple-500 text-white',
  indigo: 'bg-indigo-500 text-white',
  pink: 'bg-pink-500 text-white',
  orange: 'bg-orange-500 text-white',
  teal: 'bg-teal-500 text-white',
};

const StatisticCard: React.FC<StatisticCardProps> = ({
  title,
  value,
  icon,
  color = 'blue',
  trend,
  loading = false,
  description,
  onClick,
  className,
}) => {
  const colorClass = (colorMap as any)[color] || colorMap.blue;

  return (
    <div 
      className={cn(
        "bg-white dark:bg-gray-800 rounded-lg shadow p-5",
        onClick && "cursor-pointer hover:shadow-md transition-shadow",
        className
      )}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {title}
          </p>
          
          {loading ? (
            <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mt-1"></div>
          ) : (
            <h3 className="text-2xl font-semibold mt-1 text-gray-900 dark:text-white">
              {value}
            </h3>
          )}
          
          {trend && !loading && (
            <div className="flex items-center mt-1">
              <span 
                className={cn(
                  "text-xs font-medium",
                  trend.isPositive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                vs last period
              </span>
            </div>
          )}
          
          {description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
        
        {icon && (
          <div className={cn("p-3 rounded-full", colorClass)}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

// Pre-defined statistic cards for common use cases
export const NodeStatisticCard: React.FC<Omit<StatisticCardProps, 'title'>> = (props) => (
  <StatisticCard title="Số lượng node" {...props} />
);

export const RelationStatisticCard: React.FC<Omit<StatisticCardProps, 'title'>> = (props) => (
  <StatisticCard title="Số lượng quan hệ" {...props} />
);

export const ConflictStatisticCard: React.FC<Omit<StatisticCardProps, 'title'>> = (props) => (
  <StatisticCard title="Xung đột cần giải quyết" color="yellow" {...props} />
);

export const UserStatisticCard: React.FC<Omit<StatisticCardProps, 'title'>> = (props) => (
  <StatisticCard title="Người dùng" color="purple" {...props} />
);

export default StatisticCard;
