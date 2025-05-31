// src/search-bar/search-bar.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import SearchBar from './index';
import { useState } from 'react';

const meta: Meta<typeof SearchBar> = {
  title: 'UI/SearchBar',
  component: SearchBar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '400px' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof SearchBar>;

export const Default: Story = {
  args: {
    placeholder: 'Tìm kiếm...',
  },
};

export const WithInitialValue: Story = {
  args: {
    placeholder: 'Tìm kiếm...',
    initialValue: 'React components',
  },
};

export const WithFilter: Story = {
  args: {
    placeholder: 'Tìm kiếm...',
    showFilter: true,
    onFilterClick: () => alert('Filter clicked'),
  },
};

export const WithSuggestions: Story = {
  args: {
    placeholder: 'Tìm kiếm sản phẩm...',
    suggestions: [
      'iPhone 13', 
      'iPhone 13 Pro', 
      'iPhone 13 Pro Max', 
      'Samsung Galaxy S21',
      'Samsung Galaxy S22',
      'Google Pixel 6',
    ],
  },
};

export const WithHistory: Story = {
  args: {
    placeholder: 'Tìm kiếm...',
    history: [
      { id: '1', text: 'knowledge graph', timestamp: new Date().toISOString() },
      { id: '2', text: 'ontology', timestamp: new Date().toISOString() },
      { id: '3', text: 'semantic web', timestamp: new Date(Date.now() - 86400000).toISOString() },
    ],
    saveHistory: true,
  },
};

// Interactive version with state
export const Interactive: Story = {
  render: () => {
    const SearchBarWithState = () => {
      const [value, setValue] = useState('');
      const [history, setHistory] = useState([
        { id: '1', text: 'knowledge graph', timestamp: new Date().toISOString() },
        { id: '2', text: 'ontology', timestamp: new Date().toISOString() },
      ]);
      
      const handleSearch = (query: string) => {
        console.log(`Searched for: ${query}`);
        const newHistoryItem = {
          id: Date.now().toString(),
          text: query,
          timestamp: new Date().toISOString(),
        };
        setHistory([newHistoryItem, ...history.slice(0, 4)]);
      };
      
      return (
        <SearchBar
          placeholder="Nhập từ khóa tìm kiếm..."
          initialValue={value}
          onChange={setValue}
          onSearch={handleSearch}
          history={history}
          onHistoryItemClick={(item: any) => {
            setValue(item.text);
            handleSearch(item.text);
          }}
          saveHistory
        />
      );
    };
    
    return <SearchBarWithState />;
  },
};

export const Loading: Story = {
  args: {
    placeholder: 'Tìm kiếm...',
    loading: true,
  },
};
