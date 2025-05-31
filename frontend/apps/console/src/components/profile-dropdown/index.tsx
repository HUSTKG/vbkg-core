import React from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { User, Settings, HelpCircle, LogOut, ChevronDown } from 'lucide-react';

export type NavigationItem = {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
};

export type ProfileDropdownProps = {
  /** User's full name */
  userName: string;
  /** User's email address */
  userEmail?: string;
  /** URL to the user's avatar image */
  avatarUrl?: string;
  /** Alt text for the avatar image */
  avatarAlt?: string;
  /** Initials or fallback content when avatar image fails to load */
  avatarFallback?: React.ReactNode;
  /** Show the username in the trigger button */
  showUserNameInTrigger?: boolean;
  /** Navigation items to display in the dropdown */
  navigationItems?: NavigationItem[];
  /** Handler for the logout action */
  onLogout?: () => void;
  /** Class name for custom styling of the dropdown trigger */
  triggerClassName?: string;
  /** Alignment of the dropdown menu */
  menuAlign?: 'start' | 'center' | 'end';
  /** Width of the dropdown menu */
  menuWidth?: string;
};

const ProfileDropdown: React.FC<ProfileDropdownProps> = ({
  userName,
  userEmail,
  avatarUrl,
  avatarAlt = "User avatar",
  avatarFallback,
  showUserNameInTrigger = true,
  navigationItems = [
    {
      icon: <User className="h-4 w-4" />,
      label: "My Profile",
      onClick: () => console.log("Profile clicked")
    },
    {
      icon: <Settings className="h-4 w-4" />,
      label: "Settings",
      onClick: () => console.log("Settings clicked")
    },
    {
      icon: <HelpCircle className="h-4 w-4" />,
      label: "Help & Support",
      onClick: () => console.log("Help clicked")
    }
  ],
  onLogout,
  triggerClassName = "",
  menuAlign = "end",
  menuWidth = "w-56"
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className={`focus:outline-none ${triggerClassName}`}>
        <div className="flex items-center gap-2 p-2 rounded-full hover:bg-slate-100 transition-colors">
          <Avatar className="h-8 w-8 border border-slate-200">
            <AvatarImage src={avatarUrl} alt={avatarAlt} />
            <AvatarFallback className="bg-slate-200 text-slate-600">
              {avatarFallback || <User className="h-4 w-4" />}
            </AvatarFallback>
          </Avatar>
          {showUserNameInTrigger && (
            <span className="text-sm font-medium hidden sm:block">{userName}</span>
          )}
          <ChevronDown className="h-4 w-4 hidden sm:block" />
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={menuAlign} className={menuWidth}>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{userName}</p>
            <p className="text-xs text-slate-500">{userEmail}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          {navigationItems.map((item, index) => (
            <DropdownMenuItem 
              key={index} 
              className="cursor-pointer"
              onClick={item.onClick}
            >
              <span className="mr-2">{item.icon}</span>
              <span>{item.label}</span>
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          className="cursor-pointer text-red-600 focus:text-red-600"
          onClick={onLogout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default ProfileDropdown;
