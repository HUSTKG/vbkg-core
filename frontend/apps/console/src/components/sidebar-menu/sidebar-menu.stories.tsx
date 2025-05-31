// src/sidebar-menu/sidebar-menu.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { SidebarMenu, SidebarMenuItem, SidebarSubItem, SidebarHomeItem } from './index';
import { Database, Settings, Users, FileText, BarChart, Server, Mail } from 'lucide-react';

const meta: Meta<typeof SidebarMenu> = {
  title: 'UI/SidebarMenu',
  component: SidebarMenu,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '280px', height: '600px', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof SidebarMenu>;

export const Default: Story = {
  render: () => (
    <SidebarMenu>
      <SidebarHomeItem href="/" isActive={true} />
      <SidebarMenuItem 
        title="Knowledge Management" 
        icon={<Database size={20} />}
      >
        <SidebarSubItem title="Resolve Conflicts" href="/resolve-conflicts" />
        <SidebarSubItem title="Review New Data" href="/review-data" />
        <SidebarSubItem title="Add Data Manually" href="/add-data" isActive={true} />
      </SidebarMenuItem>
      <SidebarMenuItem 
        title="Administration" 
        icon={<Settings size={20} />}
      >
        <SidebarSubItem title="Monitor Performance" href="/monitor" />
        <SidebarSubItem title="Manage Users" href="/users" />
        <SidebarSubItem title="Manage Ontology" href="/ontology" />
      </SidebarMenuItem>
      <SidebarMenuItem
        title="User Interaction"
        icon={<Users size={20} />}
      >
        <SidebarSubItem title="Send Feedback" href="/feedback" />
        <SidebarSubItem title="Query Knowledge" href="/query" />
      </SidebarMenuItem>
    </SidebarMenu>
  ),
};

export const Collapsed: Story = {
  render: () => (
    <SidebarMenu isCollapsed={true}>
      <SidebarHomeItem href="/" />
      <SidebarMenuItem 
        title="Knowledge Management" 
        icon={<Database size={20} />}
      />
      <SidebarMenuItem 
        title="Administration" 
        icon={<Settings size={20} />}
      />
      <SidebarMenuItem
        title="User Interaction"
        icon={<Users size={20} />}
      />
      <SidebarMenuItem
        title="Documentation"
        icon={<FileText size={20} />}
      />
    </SidebarMenu>
  ),
};

export const WithBadges: Story = {
  render: () => (
    <SidebarMenu>
      <SidebarHomeItem href="/" />
      <SidebarMenuItem 
        title="Knowledge Management" 
        icon={<Database size={20} />}
        badge={5}
      >
        <SidebarSubItem title="Resolve Conflicts" href="/resolve-conflicts" badge={3} />
        <SidebarSubItem title="Review New Data" href="/review-data" badge={2} />
        <SidebarSubItem title="Add Data Manually" href="/add-data" />
      </SidebarMenuItem>
      <SidebarMenuItem 
        title="Reports" 
        icon={<BarChart size={20} />}
        badge="New"
      >
        <SidebarSubItem title="Performance Reports" href="/reports/performance" />
        <SidebarSubItem title="User Activity" href="/reports/activity" badge="New" />
        <SidebarSubItem title="System Logs" href="/reports/logs" />
      </SidebarMenuItem>
    </SidebarMenu>
  ),
};

export const NestedStructure: Story = {
  render: () => (
    <SidebarMenu>
      <SidebarHomeItem href="/" />
      <SidebarMenuItem 
        title="Data Management" 
        icon={<Database size={20} />}
      >
        <SidebarSubItem title="Knowledge Base" href="/kb" />
        <SidebarSubItem title="Data Sources" href="/sources" />
        <SidebarSubItem title="Integrations" href="/integrations" />
      </SidebarMenuItem>
      <SidebarMenuItem 
        title="System" 
        icon={<Server size={20} />}
      >
        <SidebarSubItem title="Monitoring" href="/system/monitor" />
        <SidebarSubItem title="Configuration" href="/system/config" />
        <SidebarSubItem title="Backups" href="/system/backups" />
        <SidebarSubItem title="Updates" href="/system/updates" badge="1" />
      </SidebarMenuItem>
      <SidebarMenuItem 
        title="Communications" 
        icon={<Mail size={20} />}
      >
        <SidebarSubItem title="Messages" href="/comms/messages" badge={3} />
        <SidebarSubItem title="Announcements" href="/comms/announcements" />
        <SidebarSubItem title="Feedback" href="/comms/feedback" />
      </SidebarMenuItem>
    </SidebarMenu>
  ),
};

// Individual component stories
export const HomeItem: Story = {
  render: () => <SidebarHomeItem href="/" isActive={true} />,
};

export const MenuItem: Story = {
  render: () => (
    <SidebarMenuItem 
      title="Knowledge Management" 
      icon={<Database size={20} />}
      isActive={true}
    />
  ),
};

export const SubItem: Story = {
  render: () => <SidebarSubItem title="Resolve Conflicts" href="/resolve-conflicts" isActive={true} />,
};
