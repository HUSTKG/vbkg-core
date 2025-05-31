// packages/ui/src/sidebar-menu/index.tsx
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Home } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface SidebarMenuItemProps {
  icon?: React.ReactNode;
  title: string;
  href?: string;
  isActive?: boolean;
  isSidebarCollapsed?: boolean;
  onClick?: () => void;
  badge?: React.ReactNode | string | number;
  children?: React.ReactNode;
  className?: string;
}

export const SidebarMenuItem: React.FC<SidebarMenuItemProps> = ({
  icon,
  title,
  href,
  isActive = false,
  isSidebarCollapsed = false,
  onClick,
  badge,
  children,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const hasSubmenu = React.Children.count(children) > 0;
  
  const toggleSubmenu = (e: React.MouseEvent) => {
    if (hasSubmenu) {
      e.preventDefault();
      setIsOpen(!isOpen);
    }
  };
  
  const handleClick = (e: React.MouseEvent) => {
    if (hasSubmenu) {
      toggleSubmenu(e);
    } else if (onClick) {
      e.preventDefault();
      onClick();
    }
  };
  
  const renderItem = () => (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center">
        {icon && (
          <div className={cn(
            "text-gray-500 dark:text-gray-400",
            isActive && "text-blue-600 dark:text-blue-400"
          )}>
            {icon}
          </div>
        )}
        {!isSidebarCollapsed && (
          <span className={cn(
            "ml-3 text-gray-700 dark:text-gray-300",
            isActive && "font-medium text-blue-600 dark:text-blue-400"
          )}>
            {title}
          </span>
        )}
      </div>
      
      {!isSidebarCollapsed && (
        <>
          {badge && (
            <span className="ml-auto mr-2 px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
              {badge}
            </span>
          )}
          
          {hasSubmenu && (
            <div className="ml-1">
              {isOpen ? (
                <ChevronDown size={16} className="text-gray-500 dark:text-gray-400" />
              ) : (
                <ChevronRight size={16} className="text-gray-500 dark:text-gray-400" />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
  
  return (
    <div className={className}>
      {href ? (
        <a
          href={href}
          onClick={hasSubmenu ? handleClick : undefined}
          className={cn(
            "flex items-center px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md mx-2",
            isActive && "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
          )}
        >
          {renderItem()}
        </a>
      ) : (
        <button
          onClick={handleClick}
          className={cn(
            "flex items-center w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md mx-2",
            isActive && "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400"
          )}
        >
          {renderItem()}
        </button>
      )}
      
      {!isSidebarCollapsed && hasSubmenu && isOpen && (
        <div className="pl-10 pr-4 mt-1 mb-1">
          {children}
        </div>
      )}
    </div>
  );
};

export interface SidebarSubItemProps {
  title: string;
  href: string;
  isActive?: boolean;
  onClick?: () => void;
  badge?: React.ReactNode | string | number;
  className?: string;
}

export const SidebarSubItem: React.FC<SidebarSubItemProps> = ({
  title,
  href,
  isActive = false,
  onClick,
  badge,
  className,
}) => {
  return (
    <a
      href={href}
      onClick={(e) => {
        if (onClick) {
          e.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "flex items-center justify-between py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400",
        isActive && "font-medium text-blue-600 dark:text-blue-400",
        className
      )}
    >
      <span>{title}</span>
      {badge && (
        <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300">
          {badge}
        </span>
      )}
    </a>
  );
};

export interface SidebarMenuProps {
  children: React.ReactNode;
  isCollapsed?: boolean;
  className?: string;
}

export const SidebarMenu: React.FC<SidebarMenuProps> = ({
  children,
  isCollapsed = false,
  className,
}) => {
  // Clone children to pass down the isCollapsed prop
  const updatedChildren = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, {
        ...child.props as any,
        isSidebarCollapsed: isCollapsed,
      });
    }
    return child;
  });
  
  return (
    <nav className={cn("py-4", className)}>
      {updatedChildren}
    </nav>
  );
};

// Special home item for convenience
interface SidebarHomeItemProps {
  href?: string;
  isActive?: boolean;
  isSidebarCollapsed?: boolean;
  onClick?: () => void;
  className?: string;
}

export const SidebarHomeItem: React.FC<SidebarHomeItemProps> = (props) => {
  return (
    <SidebarMenuItem
      title="Dashboard"
      icon={<Home size={20} />}
      {...props}
    />
  );
};

export default {
  Menu: SidebarMenu,
  Item: SidebarMenuItem,
  SubItem: SidebarSubItem,
  HomeItem: SidebarHomeItem,
};
