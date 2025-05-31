// src/recent-activity-item/recent-activity-item.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import RecentActivityItem, { 
  DataAddedActivity, 
  ConflictDetectedActivity, 
  ErrorActivity as _ErrorActivity, 
  InfoActivity as _InfoActivity 
} from './index';

import { 
  Plus, 
  AlertTriangle, 
  X, 
  Info, 
  Settings,
  RefreshCw,
  UserPlus,
  Database,
  FileText
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const meta: Meta<typeof RecentActivityItem> = {
  title: 'UI/RecentActivityItem',
  component: RecentActivityItem,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '600px', backgroundColor: 'white', padding: '16px', borderRadius: '8px' }} className="dark:bg-gray-800">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof RecentActivityItem>;

export const Default: Story = {
  args: {
    title: 'Data Added',
    time: '5 minutes ago',
    icon: <Plus size={16} />,
    description: '42 new entities were added to the knowledge graph.',
    status: 'success',
  },
};

export const SuccessActivity: Story = {
  args: {
    title: 'Import Completed',
    time: '2 minutes ago',
    icon: <Plus size={16} />,
    description: 'Successfully imported 128 nodes and 256 relationships from CSV file.',
    status: 'success',
  },
};

export const WarningActivity: Story = {
  args: {
    title: 'Conflict Detected',
    time: '15 minutes ago',
    icon: <AlertTriangle size={16} />,
    description: 'Detected conflicting data between two sources. Manual resolution required.',
    status: 'warning',
  },
};

export const ErrorActivity: Story = {
  args: {
    title: 'Import Failed',
    time: '1 hour ago',
    icon: <X size={16} />,
    description: 'Failed to import data from external source due to connection error.',
    status: 'error',
  },
};

export const InfoActivity: Story = {
  args: {
    title: 'System Update',
    time: '3 hours ago',
    icon: <Info size={16} />,
    description: 'The system was updated to version 2.4.0 with new features and bug fixes.',
    status: 'info',
  },
};

export const WithActionButton: Story = {
  args: {
    title: 'Approval Needed',
    time: '30 minutes ago',
    icon: <AlertTriangle size={16} />,
    description: 'New ontology class definitions require approval before being applied.',
    status: 'warning',
    actionButton: (
      <Button size="sm">Review & Approve</Button>
    ),
  },
};

export const WithMultipleActionButtons: Story = {
  args: {
    title: 'Configuration Change Requested',
    time: '45 minutes ago',
    icon: <Settings size={16} />,
    description: 'User "Alex Miller" has requested changes to the data pipeline configuration.',
    status: 'info',
    actionButton: (
      <div className="flex space-x-2">
        <Button size="sm" variant="outline">View Details</Button>
        <Button size="sm">Approve</Button>
      </div>
    ),
  },
};

export const WithLongDescription: Story = {
  args: {
    title: 'Weekly System Report',
    time: '2 days ago',
    icon: <FileText size={16} />,
    description: 'The weekly system report has been generated. The report includes performance metrics, user activity statistics, and data growth trends. Overall, the system performance has improved by 15% compared to last week.',
    status: 'info',
  },
};

export const Clickable: Story = {
  args: {
    title: 'User Registered',
    time: '1 day ago',
    icon: <UserPlus size={16} />,
    description: 'New user "Sarah Wilson" has registered and is awaiting approval.',
    status: 'info',
    onClick: () => alert('Activity item clicked'),
  },
};

export const MultipleItems: Story = {
  render: () => (
    <div className="space-y-4">
      <DataAddedActivity
        title="Database Synced"
        time="5 minutes ago"
        icon={<Database size={16} />}
        description="Successfully synchronized with external database. 256 new entities added."
      />
      <ConflictDetectedActivity
        title="Schema Conflict"
        time="30 minutes ago"
        icon={<AlertTriangle size={16} />}
        description="Detected conflict in schema definition between two ontology versions."
      />
      <_ErrorActivity
        title="Export Failed"
        time="2 hours ago"
        icon={<X size={16} />}
        description="Failed to export data to CSV format due to encoding issues."
      />
      <_InfoActivity
        title="Maintenance Scheduled"
        time="1 day ago"
        icon={<RefreshCw size={16} />}
        description="System maintenance scheduled for tomorrow at 02:00 AM. Expected downtime: 30 minutes."
      />
    </div>
  ),
};

export const TimeFormatting: Story = {
  render: () => (
    <div className="space-y-4">
      <RecentActivityItem
        title="Just Now"
        time={new Date().toISOString()}
        icon={<Plus size={16} />}
        description="This activity happened just now."
        status="success"
      />
      <RecentActivityItem
        title="Minutes Ago"
        time={new Date(Date.now() - 10 * 60 * 1000).toISOString()}
        icon={<Plus size={16} />}
        description="This activity happened minutes ago."
        status="success"
      />
      <RecentActivityItem
        title="Hours Ago"
        time={new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString()}
        icon={<Plus size={16} />}
        description="This activity happened hours ago."
        status="success"
      />
      <RecentActivityItem
        title="Days Ago"
        time={new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()}
        icon={<Plus size={16} />}
        description="This activity happened days ago."
        status="success"
      />
    </div>
  ),
};
