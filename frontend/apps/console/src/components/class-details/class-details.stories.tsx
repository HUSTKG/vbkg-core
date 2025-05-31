// src/class-details/class-details.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import ClassDetails from './index';
import { useState } from 'react';

const meta: Meta<typeof ClassDetails> = {
  title: 'UI/ClassDetails',
  component: ClassDetails,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <div style={{ width: '800px' }}>
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof ClassDetails>;

// Sample class for display
const sampleClass = {
  id: 1,
  name: 'Person',
  description: 'Represents an individual human being with personal and professional characteristics.',
  properties: [
    { name: 'name', type: 'string', required: true, description: 'Full name of the person' },
    { name: 'birthDate', type: 'date', required: false, description: 'Date of birth' },
    { name: 'email', type: 'string', required: false, description: 'Email address' },
    { name: 'occupation', type: 'string', required: false, description: 'Professional role or job title' },
    { name: 'address', type: 'object', required: false, description: 'Physical address information' },
  ],
};

// Larger sample class with more properties
const detailedClass = {
  id: 2,
  name: 'Organization',
  description: 'Represents a company, institution, or any formal group of people with a particular purpose.',
  properties: [
    { name: 'name', type: 'string', required: true, description: 'Official name of the organization' },
    { name: 'foundingDate', type: 'date', required: false, description: 'Date when the organization was established' },
    { name: 'industry', type: 'string', required: false, description: 'Primary industry or sector' },
    { name: 'description', type: 'string', required: false, description: 'Detailed description of the organization' },
    { name: 'headquarters', type: 'object', required: false, description: 'Location of the main office' },
    { name: 'website', type: 'url', required: false, description: 'Official website URL' },
    { name: 'employeeCount', type: 'number', required: false, description: 'Number of employees' },
    { name: 'revenue', type: 'number', required: false, description: 'Annual revenue' },
    { name: 'isPublic', type: 'boolean', required: false, description: 'Whether the company is publicly traded' },
    { name: 'stockSymbol', type: 'string', required: false, description: 'Stock market symbol if publicly traded' },
    { name: 'subsidiaries', type: 'array', required: false, description: 'List of subsidiary organizations' },
  ],
};

export const Default: Story = {
  args: {
    classItem: sampleClass,
  },
};

export const Empty: Story = {
  args: {
    classItem: null,
  },
};

export const ReadOnly: Story = {
  args: {
    classItem: sampleClass,
    readOnly: true,
  },
};

export const WithDetailedProperties: Story = {
  args: {
    classItem: detailedClass,
  },
};

export const Interactive: Story = {
  render: () => {
    const InteractiveClassDetails = () => {
      const [currentClass, setCurrentClass] = useState(sampleClass);
      
      const handleUpdate = (updatedClass: any) => {
        console.log('Class updated:', updatedClass);
        setCurrentClass(updatedClass);
      };
      
      const handleDelete = (id: any) => {
        console.log(`Delete class with ID: ${id}`);
        alert(`Class with ID: ${id} would be deleted in a real application.`);
      };
      
      return (
        <div className="space-y-4">
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
            <h3 className="text-lg font-medium mb-2">Interactive Class Editor</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Try editing the class details below. Changes will be logged to the console.
            </p>
            <ClassDetails 
              classItem={currentClass}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
              onCancel={() => console.log('Edit cancelled')}
            />
          </div>
        </div>
      );
    };
    
    return <InteractiveClassDetails />;
  },
};

export const ValidationErrors: Story = {
  render: () => {
    const ClassWithErrors = () => {
      // Create a class with invalid property (duplicate names)
      const invalidClass = {
        ...sampleClass,
        properties: [
          ...sampleClass.properties,
          { name: 'name', type: 'string', required: false, description: 'Duplicate property name' },
        ],
      };
      
      return (
        <ClassDetails 
          classItem={invalidClass}
          onUpdate={(updatedClass) => console.log('Updated:', updatedClass)}
          onCancel={() => console.log('Cancelled')}
        />
      );
    };
    
    return <ClassWithErrors />;
  },
};

export const WithNoProperties: Story = {
  args: {
    classItem: {
      id: 3,
      name: 'EmptyClass',
      description: 'A class with no properties defined yet.',
      properties: [],
    },
  },
};
