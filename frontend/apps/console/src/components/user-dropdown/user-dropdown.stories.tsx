// src/user-dropdown/user-dropdown.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import UserDropdown from './index';
import { Settings, User, HelpCircle, FileText, Key } from 'lucide-react';

const meta: Meta<typeof UserDropdown> = {
  title: 'UI/UserDropdown',
  component: UserDropdown,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof UserDropdown>;

export const Default: Story = {
  args: {
    userName: 'John Doe',
    userEmail: 'john.doe@example.com',
    onLogout: () => console.log('Logout clicked'),
    onSettingsClick: () => console.log('Settings clicked'),
    onThemeToggle: () => console.log('Theme toggle clicked'),
    isDarkMode: false,
  },
};

export const WithRole: Story = {
  args: {
    userName: 'Jane Smith',
    userEmail: 'jane.smith@example.com',
    userRole: 'Administrator',
    onLogout: () => console.log('Logout clicked'),
    onSettingsClick: () => console.log('Settings clicked'),
  },
};

export const WithAvatar: Story = {
  args: {
    userName: 'Alex Johnson',
    userEmail: 'alex.johnson@example.com',
    userAvatar: 'https://i.pravatar.cc/300',
    onLogout: () => console.log('Logout clicked'),
  },
};

export const WithCustomLinks: Story = {
  args: {
    userName: 'Emily Davis',
    userEmail: 'emily.davis@example.com',
    links: [
      { 
        label: 'My Profile', 
        href: '/profile', 
        icon: <User size={16} /> 
      },
      { 
        label: 'Settings', 
        href: '/settings', 
        icon: <Settings size={16} /> 
      },
      { 
        label: 'API Keys', 
        href: '/api-keys', 
        icon: <Key size={16} /> 
      },
      { 
        label: 'Documentation', 
        href: '/docs', 
        icon: <FileText size={16} /> 
      },
      { 
        label: 'Help', 
        href: '/help', 
        icon: <HelpCircle size={16} /> 
      },
    ],
    onLogout: () => console.log('Logout clicked'),
  },
};

export const WithNotifications: Story = {
  args: {
    userName: 'Robert Brown',
    userRole: 'Editor',
    unreadNotifications: 5,
    onNotificationsClick: () => console.log('Notifications clicked'),
    onLogout: () => console.log('Logout clicked'),
  },
};

export const DarkMode: Story = {
  args: {
    userName: 'Sarah Wilson',
    userEmail: 'sarah.wilson@example.com',
    isDarkMode: true,
    onThemeToggle: () => console.log('Theme toggle clicked'),
    onLogout: () => console.log('Logout clicked'),
  },
  parameters: {
    backgrounds: { default: 'dark' },
  },
};
