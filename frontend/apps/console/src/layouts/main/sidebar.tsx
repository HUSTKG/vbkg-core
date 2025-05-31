import { ChevronDown, Menu, X } from "lucide-react";
import { useState } from "react";

const cn = (...classes: any) => classes.filter(Boolean).join(" ");

export interface MenuItem {
  title: string;
  icon?: React.ReactNode;
  path?: string;
  submenu?: MenuItem[];
  badge?: string;
}

interface SidebarProps {
  menuItems?: MenuItem[];
  isSidebarOpen?: boolean;
  setIsSidebarOpen?: (isOpen: boolean) => void;
  onNavigation?: (path: string) => void;
  activeItem?: string;
}

const Sidebar = ({
  menuItems = [],
  isSidebarOpen = true,
  onNavigation,
  setIsSidebarOpen = () => {},
  activeItem = "/dashboard",
}: SidebarProps) => {
  const [expandedMenus, setExpandedMenus] = useState<Record<string, boolean>>(
    {},
  );

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleSubmenu = (title: string) => {
    setExpandedMenus((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  const isActive = (path?: string) => {
    return path === activeItem;
  };

  const isParentActive = (item: MenuItem) => {
    if (item.path && isActive(item.path)) return true;
    return item.submenu?.some((subItem) => isActive(subItem.path)) || false;
  };

  return (
    <div
      className={cn(
        "h-screen fixed inset-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 ease-in-out",
        isSidebarOpen ? "w-64" : "w-16",
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <div
          className={cn(
            "transition-all duration-300",
            isSidebarOpen ? "opacity-100" : "opacity-0 w-0",
          )}
        >
          {isSidebarOpen && (
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                VBKG
              </h1>
            </div>
          )}
        </div>
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200 text-gray-600 dark:text-gray-400"
          aria-label={isSidebarOpen ? "Thu gọn sidebar" : "Mở rộng sidebar"}
        >
          {isSidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {/* Navigation */}
      <div className="py-6 px-3 h-full overflow-y-auto">
        <nav aria-label="Main Navigation">
          <ul className="space-y-1">
            {menuItems.map((item, idx) => (
              <li key={idx}>
                {item.submenu ? (
                  // Menu with submenu
                  <div>
                    <button
                      onClick={() => toggleSubmenu(item.title)}
                      className={cn(
                        "w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-all duration-200",
                        isParentActive(item)
                          ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
                          : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800",
                        !isSidebarOpen && "justify-center",
                      )}
                      aria-expanded={expandedMenus[item.title]}
                      aria-controls={`submenu-${idx}`}
                    >
                      <div className="flex items-center min-w-0">
                        {item.icon && (
                          <div className="flex-shrink-0 text-gray-500 dark:text-gray-400">
                            {item.icon}
                          </div>
                        )}
                        {isSidebarOpen && (
                          <span
                            className={cn("truncate", item.icon ? "ml-3" : "")}
                          >
                            {item.title}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        {isSidebarOpen && item.badge && (
                          <span className="px-1.5 py-0.5 text-xs font-medium bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded">
                            {item.badge}
                          </span>
                        )}
                        {isSidebarOpen && (
                          <ChevronDown
                            size={14}
                            className={cn(
                              "flex-shrink-0 transition-transform duration-200 text-gray-400",
                              expandedMenus[item.title] ? "rotate-180" : "",
                            )}
                          />
                        )}
                      </div>
                    </button>

                    {/* Submenu */}
                    {isSidebarOpen && expandedMenus[item.title] && (
                      <ul id={`submenu-${idx}`} className="mt-1 space-y-1">
                        {item.submenu?.map((subItem, subIdx) => (
                          <li key={subIdx}>
                            <div
                              onClick={() => {
                                if (onNavigation) {
                                  onNavigation(subItem.path || "");
                                }
                              }}
                              className={cn(
                                "flex items-center px-3 py-1.5 ml-6 text-sm rounded-md transition-all duration-200 border-l border-gray-200 dark:border-gray-700 pl-4",
                                isActive(subItem.path)
                                  ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white border-gray-900 dark:border-white"
                                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white",
                              )}
                            >
                              <span className="truncate">{subItem.title}</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : item.path ? (
                  // Simple menu item
                  <div
                    onClick={() => {
                      if (onNavigation && item.path) {
                        onNavigation(item.path);
                      }
                    }}
                    className={cn(
                      "flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-all duration-200",
                      isActive(item.path)
                        ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800",
                      !isSidebarOpen && "justify-center",
                    )}
                  >
                    <div className="flex items-center min-w-0">
                      {item.icon && (
                        <div className="flex-shrink-0 text-gray-500 dark:text-gray-400">
                          {item.icon}
                        </div>
                      )}
                      {isSidebarOpen && (
                        <span
                          className={cn("truncate", item.icon ? "ml-3" : "")}
                        >
                          {item.title}
                        </span>
                      )}
                    </div>
                    {isSidebarOpen && item.badge && (
                      <span className="px-1.5 py-0.5 text-xs font-medium bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded">
                        {item.badge}
                      </span>
                    )}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;
