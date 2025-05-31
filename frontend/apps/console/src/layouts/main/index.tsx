import React, { useState } from "react";
import { cn } from "../../lib/utils";
import { Header } from "./header";
import Sidebar, { MenuItem } from "./sidebar";
import { Toaster } from "../../components/ui/sonner";

export interface AppLayoutProps {
  children: React.ReactNode;
  menuItems?: MenuItem[];
  onSearch?: (query: string) => void;
  onNotificationClick?: () => void;
  notificationCount?: number;
  userName?: string;
  onNavigation?: (path: string) => void;
  userAvatar?: string;
  userEmail?: string;
  onLogout?: () => void;
  profileMenuItems?: {
    icon: React.ReactNode;
    label: string;
    onClick: () => void;
  }[];
}

// Default menu items that can be overridden via props
const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  menuItems = [],
  onSearch,
  onNotificationClick,
  notificationCount = 0,
  onNavigation,
  userName = "User",
  userAvatar,
  onLogout,
  userEmail,
  profileMenuItems,
}) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar
        onNavigation={onNavigation}
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        menuItems={menuItems}
      />
      {/* Main Content */}
      <div
        className={cn(
          "w-screen transition-all duration-300",
          isSidebarOpen ? "pl-64" : "pl-20",
        )}
      >
        {/* Top Navigation */}

        <Header
          onSearch={onSearch}
          onNotificationClick={onNotificationClick}
          notificationCount={notificationCount}
          userName={userName}
          userAvatar={userAvatar}
          isSidebarOpen={isSidebarOpen}
          userEmail={userEmail}
          onLogout={onLogout}
          profileMenuItems={profileMenuItems}
        />
        {/* Page Content */}
        <main className="pt-16 h-full overflow-auto">
          <div className="p-6">{children}</div>
        </main>
      </div>
      <Toaster />
    </div>
  );
};

export default AppLayout;
