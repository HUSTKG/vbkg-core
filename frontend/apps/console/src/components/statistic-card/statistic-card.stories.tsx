import type { Meta, StoryObj } from '@storybook/react';
import StatisticCard, { NodeStatisticCard, RelationStatisticCard } from './index';
import { Database, Activity, AlertTriangle, Users } from 'lucide-react';

const meta: Meta<typeof StatisticCard> = {
  title: 'UI/StatisticCard',
  component: StatisticCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof StatisticCard>;

export const Default: Story = {
  args: {
    title: 'Số lượng node',
    value: '12,543',
    icon: <Database size={20} className="text-white" />,
    color: 'blue',
  },
};

export const WithTrend: Story = {
  args: {
    title: 'Số lượng quan hệ',
    value: '48,294',
    icon: <Activity size={20} className="text-white" />,
    color: 'green',
    trend: {
      value: 12,
      isPositive: true,
    },
  },
};

export const Negative: Story = {
  args: {
    title: 'Xung đột cần giải quyết',
    value: '23',
    icon: <AlertTriangle size={20} className="text-white" />,
    color: 'yellow',
    trend: {
      value: 5,
      isPositive: false,
    },
  },
};

export const WithDescription: Story = {
  args: {
    title: 'Người dùng',
    value: '158',
    icon: <Users size={20} className="text-white" />,
    color: 'purple',
    description: 'Tăng 15% trong tháng qua',
  },
};

export const Loading: Story = {
  args: {
    title: 'Đang tải dữ liệu',
    value: '',
    loading: true,
  },
};

export const NodeStatistic: Story = {
  render: () => <NodeStatisticCard value="12,543" icon={<Database size={20} className="text-white" />} />,
};

export const RelationStatistic: Story = {
  render: () => <RelationStatisticCard value="48,294" icon={<Activity size={20} className="text-white" />} />,
};
