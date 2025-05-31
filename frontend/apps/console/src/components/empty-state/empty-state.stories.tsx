// src/empty-state/empty-state.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import EmptyState, { 
  SearchEmptyState, 
  DataEmptyState, 
  ErrorEmptyState, 
  LoadingEmptyState 
} from './index';
import { FileQuestion, BrainCircuit, FileX, DatabaseIcon, HelpCircle } from 'lucide-react';
import { Button } from '../ui/button';

const meta: Meta<typeof EmptyState> = {
  title: 'UI/EmptyState',
  component: EmptyState,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '600px' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof EmptyState>;

export const Default: Story = {
  args: {
    title: 'No data available',
    description: 'There is no data to display right now.',
    bordered: true,
  },
};

export const WithIcon: Story = {
  args: {
    title: 'No documents found',
    description: 'It looks like there are no documents in this folder.',
    icon: <FileQuestion size={48} className="text-gray-400 dark:text-gray-500" />,
    bordered: true,
  },
};

export const WithAction: Story = {
  args: {
    title: 'Your knowledge base is empty',
    description: 'Start by adding some data to your knowledge graph.',
    icon: <BrainCircuit size={48} className="text-gray-400 dark:text-gray-500" />,
    action: <Button>Add Data</Button>,
    bordered: true,
  },
};

export const Search: Story = {
  render: (args) => (
    <SearchEmptyState {...args} />
  ),
  args: {
    title: 'No results found',
    description: "Try adjusting your search or filter to find what you're looking for.",
    bordered: true,
  },
};

export const DataEmpty: Story = {
  render: (args) => (
    <DataEmptyState 
      onAdd={() => console.log('Add button clicked')} 
      addLabel="Add Entity" 
      {...args} 
    />
  ),
  args: {
    title: 'No entities found',
    description: 'Your knowledge graph does not have any entities yet. Start by adding your first entity.',
    bordered: true,
  },
};

export const Error: Story = {
  render: (args) => (
    <ErrorEmptyState 
      onRetry={() => console.log('Retry clicked')} 
      retryLabel="Try Again" 
      {...args} 
    />
  ),
  args: {
    title: 'Failed to load data',
    description: 'An error occurred while fetching the data. Please try again.',
    bordered: true,
  },
};

export const Loading: Story = {
  render: (args) => (
    <LoadingEmptyState {...args} />
  ),
  args: {
    title: 'Loading data',
    description: 'Please wait while we load your information...',
    bordered: true,
  },
};

export const Small: Story = {
  args: {
    title: 'No notifications',
    description: 'You don\'t have any new notifications.',
    size: 'sm',
    bordered: true,
  },
};

export const Large: Story = {
  args: {
    title: 'Welcome to your knowledge graph',
    description: 'This is where your organization\'s knowledge will be stored and connected. Start by adding your first entities and relationships.',
    icon: <DatabaseIcon size={64} className="text-blue-500 dark:text-blue-400" />,
    action: (
      <div className="flex space-x-3">
        <Button>Get Started</Button>
        <Button variant="outline">Learn More</Button>
      </div>
    ),
    size: 'lg',
    bordered: true,
  },
};

export const Custom: Story = {
  args: {
    title: 'Need help getting started?',
    description: 'Check out our documentation or contact our support team for assistance.',
    icon: <HelpCircle size={48} className="text-purple-500 dark:text-purple-400" />,
    action: (
      <div className="mt-3 space-y-2">
        <Button className="w-full" variant="outline">View Documentation</Button>
        <Button className="w-full" variant="default">Contact Support</Button>
      </div>
    ),
    type: 'custom',
    bordered: true,
  },
};

export const NonBordered: Story = {
  args: {
    title: 'No data found',
    description: 'The requested data could not be found.',
    icon: <FileX size={48} className="text-gray-400 dark:text-gray-500" />,
    bordered: false,
  },
};

export const NonCentered: Story = {
  args: {
    title: 'Empty state with left alignment',
    description: 'This empty state is aligned to the left instead of being centered.',
    icon: <FileX size={48} className="text-gray-400 dark:text-gray-500" />,
    action: <Button>Take Action</Button>,
    bordered: true,
    centered: false,
  },
};
