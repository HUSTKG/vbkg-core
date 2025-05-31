// src/notification-item/notification-item.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import NotificationItem, { 
  SuccessNotification, 
  WarningNotification, 
  ErrorNotification, 
  InfoNotification 
} from './index';
import { Bell, Info, CheckCircle, AlertCircle, AlertTriangle } from 'lucide-react';

const meta: Meta<typeof NotificationItem> = {
  title: 'UI/NotificationItem',
  component: NotificationItem,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '500px', backgroundColor: 'white', borderRadius: '8px', overflow: 'hidden' }} className="dark:bg-gray-800">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof NotificationItem>;

export const Default: Story = {
  args: {
    id: '1',
    title: 'System Update',
    message: 'The system will be updated to version 2.5.0 tonight at 2:00 AM.',
    time: new Date().toISOString(),
    type: 'info',
    icon: <Bell size={16} />,
  },
};

export const InfoNotificationExample: Story = {
  args: {
    id: '2',
    title: 'New feature available',
    message: 'The custom visualization tool is now available. Check it out in your dashboard.',
    time: new Date(Date.now() - 35 * 60 * 1000).toISOString(), // 35 minutes ago
    type: 'info',
    icon: <Info size={16} />,
  },
};

export const SuccessNotificationExample: Story = {
  args: {
    id: '3',
    title: 'Data import completed',
    message: 'Successfully imported 245 entities and 1,089 relationships from your CSV file.',
    time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    type: 'success',
    icon: <CheckCircle size={16} />,
  },
};

export const WarningNotificationExample: Story = {
  args: {
    id: '4',
    title: 'Storage space low',
    message: 'Your knowledge graph storage is at 85% capacity. Consider upgrading your plan or removing unused data.',
    time: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 hours ago
    type: 'warning',
    icon: <AlertTriangle size={16} />,
  },
};

export const ErrorNotificationExample: Story = {
  args: {
    id: '5',
    title: 'Pipeline execution failed',
    message: 'The data integration pipeline failed during execution. Check the logs for details.',
    time: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    type: 'error',
    icon: <AlertCircle size={16} />,
  },
};

export const WithActions: Story = {
  args: {
    id: '6',
    title: 'Access request pending',
    message: 'User "John Smith" has requested access to the Knowledge Graph API.',
    time: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    type: 'info',
    icon: <Info size={16} />,
    actions: [
      { label: 'Approve', onClick: () => alert('Approved') },
      { label: 'Deny', onClick: () => alert('Denied') },
    ],
  },
};

export const Unread: Story = {
  args: {
    id: '7',
    title: 'New comment on your ontology',
    message: 'Sarah Thompson commented on your "Product" ontology class definition.',
    time: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
    type: 'info',
    icon: <Bell size={16} />,
    read: false,
  },
};

export const Read: Story = {
  args: {
    id: '8',
    title: 'Weekly report generated',
    message: 'Your weekly knowledge graph analytics report is now available for review.',
    time: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
    type: 'info',
    icon: <Bell size={16} />,
    read: true,
  },
};

export const WithMarkAsReadAndDelete: Story = {
  args: {
    id: '9',
    title: 'Scheduled maintenance complete',
    message: 'The scheduled maintenance has been completed successfully. All systems are operational.',
    time: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
    type: 'success',
    icon: <CheckCircle size={16} />,
    read: false,
    onMarkAsRead: (id) => console.log(`Marked notification ${id} as read`),
    onDelete: (id) => console.log(`Deleted notification ${id}`),
  },
};

export const WithOnClick: Story = {
  args: {
    id: '10',
    title: 'New conflict detected',
    message: 'A data conflict has been detected between two entities that need resolution.',
    time: new Date(Date.now() - 45 * 60 * 1000).toISOString(), // 45 minutes ago
    type: 'warning',
    icon: <AlertTriangle size={16} />,
    read: false,
    onClick: () => alert('Notification clicked - navigating to conflict resolution page'),
  },
};

export const LongMessage: Story = {
  args: {
    id: '11',
    title: 'System update summary',
    message: 'The latest system update includes improvements to the query engine performance, enhanced visualization capabilities, new data integration pipelines, and fixes for several minor bugs reported by users. For detailed release notes, please visit the documentation.',
    time: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    type: 'info',
    icon: <Info size={16} />,
  },
};

// Using predefined notification components
export const PrebuiltComponents: Story = {
  render: () => (
    <div>
      <InfoNotification
        id="info-1"
        title="Information message"
        message="This is an informational notification."
        time={new Date().toISOString()}
        icon={<Info size={16} />}
      />
      <SuccessNotification
        id="success-1"
        title="Success message"
        message="Operation completed successfully."
        time={new Date().toISOString()}
        icon={<CheckCircle size={16} />}
      />
      <WarningNotification
        id="warning-1"
        title="Warning message"
        message="This action may have side effects."
        time={new Date().toISOString()}
        icon={<AlertTriangle size={16} />}
      />
      <ErrorNotification
        id="error-1"
        title="Error message"
        message="An error occurred while processing your request."
        time={new Date().toISOString()}
        icon={<AlertCircle size={16} />}
      />
    </div>
  ),
};
