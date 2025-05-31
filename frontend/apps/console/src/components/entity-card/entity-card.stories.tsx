import type { Meta, StoryObj } from '@storybook/react';
import EntityCard from './index';

const meta: Meta<typeof EntityCard> = {
  title: 'UI/EntityCard',
  component: EntityCard,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof EntityCard>;

export const Default: Story = {
  args: {
    id: '1',
    name: 'Apple Inc.',
    type: 'Organization',
    properties: [
      { key: 'founded', value: '1976' },
      { key: 'headquarters', value: 'Cupertino, California, US' },
      { key: 'revenue', value: '$365.8 billion' },
      { key: 'employees', value: '154,000' },
      { key: 'ceo', value: 'Tim Cook' },
    ],
  },
};

export const WithRelations: Story = {
  args: {
    id: '1',
    name: 'Apple Inc.',
    type: 'Organization',
    properties: [
      { key: 'founded', value: '1976' },
      { key: 'headquarters', value: 'Cupertino, California, US' },
    ],
    relations: [
      { type: 'PRODUCES', target: 'iPhone', targetType: 'Product' },
      { type: 'PRODUCES', target: 'MacBook', targetType: 'Product' },
      { type: 'EMPLOYS', target: 'Tim Cook', targetType: 'Person' },
    ],
  },
};

export const Selectable: Story = {
  args: {
    id: '1',
    name: 'Apple Inc.',
    type: 'Organization',
    properties: [
      { key: 'founded', value: '1976' },
      { key: 'headquarters', value: 'Cupertino, California, US' },
    ],
    isSelectable: true,
    selectedProperties: ['founded'],
  },
};
