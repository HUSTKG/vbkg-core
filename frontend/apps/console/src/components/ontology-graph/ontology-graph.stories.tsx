// src/ontology-graph/ontology-graph.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import OntologyGraph from './index';
import { useState } from 'react';

const meta: Meta<typeof OntologyGraph> = {
  title: 'UI/OntologyGraph',
  component: OntologyGraph,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '800px', height: '600px' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof OntologyGraph>;

// Sample classes and relations for the graph
const sampleClasses = [
  {
    id: 1,
    name: 'Person',
    description: 'Represents a human individual',
  },
  {
    id: 2,
    name: 'Organization',
    description: 'A company, institution, or other formal group',
  },
  {
    id: 3,
    name: 'Product',
    description: 'An item or service offered by an organization',
  },
  {
    id: 4,
    name: 'Location',
    description: 'A physical place or geographical area',
  },
  {
    id: 5,
    name: 'Event',
    description: 'A scheduled occurrence or happening',
  },
];

const sampleRelations = [
  {
    id: 1,
    name: 'WORKS_AT',
    source: 1, // Person
    target: 2, // Organization
    description: 'Indicates employment relationship',
  },
  {
    id: 2,
    name: 'PRODUCES',
    source: 2, // Organization
    target: 3, // Product
    description: 'Indicates creation or manufacturing of a product',
  },
  {
    id: 3,
    name: 'LOCATED_IN',
    source: 2, // Organization
    target: 4, // Location
    description: 'Indicates physical location',
  },
  {
    id: 4,
    name: 'ATTENDS',
    source: 1, // Person
    target: 5, // Event
    description: 'Indicates attendance at an event',
  },
  {
    id: 5,
    name: 'ORGANIZES',
    source: 2, // Organization
    target: 5, // Event
    description: 'Indicates organization of an event',
  },
  {
    id: 6,
    name: 'VISITS',
    source: 1, // Person
    target: 4, // Location
    description: 'Indicates a visit to a location',
  },
];

export const Default: Story = {
  args: {
    classes: sampleClasses,
    relations: sampleRelations,
    height: 500,
  },
};

export const WithSelectedNode: Story = {
  args: {
    classes: sampleClasses,
    relations: sampleRelations,
    selectedNodeId: 2, // Organization is selected
    height: 500,
  },
};

export const SimpleRenderMode: Story = {
  args: {
    classes: sampleClasses,
    relations: sampleRelations,
    renderMode: 'simple',
    height: 500,
  },
};

export const Loading: Story = {
  args: {
    classes: [],
    relations: [],
    isLoading: true,
    height: 500,
  },
};

export const Empty: Story = {
  args: {
    classes: [],
    relations: [],
    height: 500,
  },
};

export const Interactive: Story = {
  render: () => {
    const InteractiveGraph = () => {
      const [selectedNodeId, setSelectedNodeId] = useState<string | number | null>(null);
      
      const handleSelectNode = (type: 'class' | 'relation', id: string | number) => {
        console.log(`Selected ${type} with id: ${id}`);
        setSelectedNodeId(id);
      };
      
      return (
        <div className="space-y-4">
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-2">Interactive Ontology Graph</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Click on a node to select it. Currently selected node ID: {selectedNodeId || 'None'}
            </p>
            <OntologyGraph 
              classes={sampleClasses}
              relations={sampleRelations}
              onSelectNode={handleSelectNode}
              selectedNodeId={selectedNodeId || undefined}
              height={400}
            />
          </div>
        </div>
      );
    };
    
    return <InteractiveGraph />;
  },
};

export const WithControls: Story = {
  args: {
    classes: sampleClasses,
    relations: sampleRelations,
    height: 500,
    showControls: true,
    isZoomable: true,
    isDraggable: true,
  },
};

export const WithoutControls: Story = {
  args: {
    classes: sampleClasses,
    relations: sampleRelations,
    height: 500,
    showControls: false,
    isZoomable: false,
    isDraggable: false,
  },
};

export const LargeGraph: Story = {
  args: {
    classes: [
      ...sampleClasses,
      { id: 6, name: 'Document', description: 'A file or paper document' },
      { id: 7, name: 'Project', description: 'A structured endeavor with a specific goal' },
      { id: 8, name: 'Department', description: 'An organizational unit within a company' },
      { id: 9, name: 'Technology', description: 'A technological tool or platform' },
      { id: 10, name: 'Skill', description: 'A particular ability or expertise' },
    ],
    relations: [
      ...sampleRelations,
      { id: 7, name: 'PART_OF', source: 8, target: 2, description: 'Department is part of Organization' },
      { id: 8, name: 'CREATED_BY', source: 6, target: 1, description: 'Document created by Person' },
      { id: 9, name: 'WORKS_ON', source: 1, target: 7, description: 'Person works on Project' },
      { id: 10, name: 'USES', source: 2, target: 9, description: 'Organization uses Technology' },
      { id: 11, name: 'HAS_SKILL', source: 1, target: 10, description: 'Person has Skill' },
      { id: 12, name: 'REQUIRES', source: 7, target: 10, description: 'Project requires Skill' },
    ],
    height: 500,
  },
};
