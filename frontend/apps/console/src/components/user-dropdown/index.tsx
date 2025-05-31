// packages/ui/src/user-dropdown/index.tsx
import { Bell, ChevronDown, HelpCircle, LogOut, Moon, Settings, Sun } from 'lucide-react';
import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../lib/utils';

export interface UserMenuLink {
  label: string;
  href: string;
  icon?: React.ReactNode;
  onClick?: () => void;
}

export interface UserDropdownProps {
  userName: string;
  userEmail?: string;
  userRole?: string;
  userAvatar?: string | React.ReactNode;
  links?: UserMenuLink[];
  onLogout?: () => void;
  onSettingsClick?: () => void;
  onThemeToggle?: () => void;
  isDarkMode?: boolean;
  unreadNotifications?: number;
  onNotificationsClick?: () => void;
  className?: string;
}

const UserDropdown: React.FC<UserDropdownProps> = ({
  userName,
  userEmail,
  userRole,
  userAvatar,
  links = [],
  onLogout,
  onSettingsClick,
  onThemeToggle,
  isDarkMode = false,
  unreadNotifications = 0,
  onNotificationsClick,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  // Generate avatar with user's initials if no avatar provided
  const renderAvatar = () => {
    if (typeof userAvatar === 'string') {
      return (
        <img 
          src={userAvatar} 
          alt={userName} 
          className="w-8 h-8 rounded-full object-cover"
        />
      );
    } else if (React.isValidElement(userAvatar)) {
      return userAvatar;
    } else {
      // Generate initials from name
      const initials = userName
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
      
      return (
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
          {initials}
        </div>
      );
    }
  };

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      <div className="flex items-center space-x-3">
        {onNotificationsClick && (
          <button 
            onClick={onNotificationsClick}
            className="relative p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Notifications"
          >
            <Bell size={20} />
            {unreadNotifications > 0 && (
              <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs text-white bg-red-500 rounded-full">
                {unreadNotifications > 99 ? '99+' : unreadNotifications}
              </span>
            )}
          </button>
        )}
        
        <button 
          onClick={toggleDropdown}
          className="flex items-center space-x-2 focus:outline-none"
          aria-expanded={isOpen}
          aria-haspopup="true"
        >
          {renderAvatar()}
          <div className="hidden md:block text-left">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300">{userName}</div>
            {userRole && (
              <div className="text-xs text-gray-500 dark:text-gray-400">{userRole}</div>
            )}
          </div>
          <ChevronDown 
            size={16} 
            className={cn(
              "text-gray-500 dark:text-gray-400 transition-transform duration-200",
              isOpen && "transform rotate-180"
            )}
          />
        </button>
      </div>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-10">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="font-medium text-gray-900 dark:text-white">{userName}</div>
            {userEmail && (
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5 truncate">{userEmail}</div>
            )}
            {userRole && (
              <div className="mt-1 inline-block px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                {userRole}
              </div>
            )}
          </div>
          
          <div className="py-1">
            {links.map((link, index) => (
              <a 
                key={index}
                href={link.href}
                onClick={(e) => {
                  if (link.onClick) {
                    e.preventDefault();
                    link.onClick();
                    setIsOpen(false);
                  }
                }}
                className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                {link.icon && <span className="mr-2 text-gray-500 dark:text-gray-400">{link.icon}</span>}
                {link.label}
              </a>
            ))}
          </div>
          
          <div className="border-t border-gray-200 dark:border-gray-700 py-1">
            <button
              onClick={() => {
                if (onThemeToggle) {
                  onThemeToggle();
                  setIsOpen(false);
                }
              }}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              {isDarkMode ? (
                <>
                  <Sun size={16} className="mr-2 text-gray-500 dark:text-gray-400" />
                  Chế độ sáng
                </>
              ) : (
                <>
                  <Moon size={16} className="mr-2 text-gray-500 dark:text-gray-400" />
                  Chế độ tối
                </>
              )}
            </button>
            
            <button
              onClick={() => {
                if (onSettingsClick) {
                  onSettingsClick();
                  setIsOpen(false);
                }
              }}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <Settings size={16} className="mr-2 text-gray-500 dark:text-gray-400" />
              Cài đặt
            </button>
            
            <a 
              href="#" 
              className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              <HelpCircle size={16} className="mr-2 text-gray-500 dark:text-gray-400" />
              Trợ giúp
            </a>
          </div>
          
          {onLogout && (
            <div className="border-t border-gray-200 dark:border-gray-700 py-1">
              <button
                onClick={() => {
                  onLogout();
                  setIsOpen(false);
                }}
                className="w-full flex items-center px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:text-red-400 dark:hover:bg-gray-700"
              >
                <LogOut size={16} className="mr-2" />
                Đăng xuất
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UserDropdown;
