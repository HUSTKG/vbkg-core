import ProfileDropdown from "@/components/profile-dropdown";
import { cn } from "@/lib/utils";
import { Bell, Search, User } from "lucide-react";
import { useState } from "react";

interface HeaderProps {
  onSearch?: (query: string) => void;
  onNotificationClick?: () => void;
  notificationCount: number;
  userName: string;
  isSidebarOpen: boolean;
  userAvatar?: string;
  userEmail?: string;
  onLogout?: () => void;
  profileMenuItems?: {
    icon: React.ReactNode;
    label: string;
    onClick: () => void;
  }[];
}

export function Header({
  onSearch,
  onNotificationClick,
  notificationCount,
  userName,
  isSidebarOpen,
  userAvatar,
  userEmail,
  onLogout,
  profileMenuItems,
}: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) {
      onSearch(searchQuery);
    }
  };
  return (
    <header
      className={cn(
        "bg-white dark:bg-gray-800 shadow-sm h-16 w-full fixed z-10",
        isSidebarOpen ? "pr-64" : "pr-20",
      )}
    >
      <div className="flex items-center h-full px-6">
        <div className="flex items-center ml-auto space-x-4">
          <button
            className="relative p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
            onClick={onNotificationClick}
            aria-label={`${notificationCount} unread notifications`}
          >
            <Bell size={20} />
            {notificationCount > 0 && (
              <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs text-white bg-red-500 rounded-full">
                {notificationCount}
              </span>
            )}
          </button>

          <div className="flex items-center space-x-2">
            <ProfileDropdown
              userName={userName}
              userEmail={userEmail}
              avatarUrl={userAvatar}
              onLogout={onLogout}
              triggerClassName="flex items-center space-x-2"
              menuAlign="end"
              menuWidth="w-56"
              navigationItems={profileMenuItems}
              showUserNameInTrigger={true}
              avatarFallback={<User className="h-4 w-4" />}
              avatarAlt="User Avatar"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
