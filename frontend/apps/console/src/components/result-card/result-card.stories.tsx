// src/result-card/result-card.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import ResultCard from './index';

const meta: Meta<typeof ResultCard> = {
  title: 'UI/ResultCard',
  component: ResultCard,
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
type Story = StoryObj<typeof ResultCard>;

export const Default: Story = {
  args: {
    id: '1',
    type: 'Person',
    name: 'Elon Musk',
    properties: {
      birthDate: '1971-06-28',
      occupation: 'CEO',
      nationality: 'South African / Canadian / American'
    },
  },
};

export const WithRelations: Story = {
  args: {
    id: '1',
    type: 'Person',
    name: 'Elon Musk',
    properties: {
      birthDate: '1971-06-28',
      occupation: 'CEO',
      nationality: 'South African / Canadian / American'
    },
    relations: [
      { type: 'CEO_OF', target: 'Tesla, Inc.', targetType: 'Organization' },
      { type: 'CEO_OF', target: 'SpaceX', targetType: 'Organization' },
      { type: 'FOUNDER_OF', target: 'Neuralink', targetType: 'Organization' },
      { type: 'FOUNDER_OF', target: 'The Boring Company', targetType: 'Organization' }
    ],
  },
};

export const Organization: Story = {
  args: {
    id: '2',
    type: 'Organization',
    name: 'Tesla, Inc.',
    properties: {
      foundingDate: '2003-07-01',
      industry: 'Automotive, Clean Energy',
      headquarters: 'Austin, Texas, United States',
      website: 'tesla.com',
      employees: '127,855 (2022)'
    },
    relations: [
      { type: 'PRODUCES', target: 'Model S', targetType: 'Product' },
      { type: 'PRODUCES', target: 'Model 3', targetType: 'Product' },
      { type: 'PRODUCES', target: 'Model X', targetType: 'Product' },
      { type: 'PRODUCES', target: 'Model Y', targetType: 'Product' },
      { type: 'CEO', target: 'Elon Musk', targetType: 'Person' }
    ],
  },
};

export const Product: Story = {
  args: {
    id: '3',
    type: 'Product',
    name: 'iPhone 13',
    properties: {
      releaseDate: '2021-09-24',
      manufacturer: 'Apple Inc.',
      price: '$799',
      storage: '128GB, 256GB, 512GB',
      colors: 'Pink, Blue, Midnight, Starlight, Red'
    },
    relations: [
      { type: 'MANUFACTURED_BY', target: 'Apple Inc.', targetType: 'Organization' },
      { type: 'SUCCEEDS', target: 'iPhone 12', targetType: 'Product' },
      { type: 'PREDECESSOR_OF', target: 'iPhone 14', targetType: 'Product' }
    ],
  },
};

export const WithHighlightedTerms: Story = {
  args: {
    id: '4',
    type: 'Research Paper',
    name: 'Knowledge Graphs: Data in Context for Responsive Businesses',
    properties: {
      author: 'Jane Smith, PhD',
      publishDate: '2022-05-15',
      abstract: 'This paper explores how knowledge graphs provide context to enterprise data, enabling more responsive business operations and decision making.',
      keywords: 'knowledge graph, semantic web, ontology, data integration',
      citations: '37'
    },
    relations: [
      { type: 'AUTHORED_BY', target: 'Jane Smith', targetType: 'Person' },
      { type: 'CITES', target: 'The Semantic Web Revisited', targetType: 'Research Paper' },
      { type: 'PUBLISHED_IN', target: 'Journal of Knowledge Management', targetType: 'Publication' }
    ],
    highlightTerms: ['knowledge graph', 'semantic web', 'ontology'],
  },
};

export const WithLotsOfProperties: Story = {
  args: {
    id: '5',
    type: 'Movie',
    name: 'Inception',
    properties: {
      director: 'Christopher Nolan',
      releaseYear: '2010',
      runtime: '148 minutes',
      genre: 'Science Fiction, Action, Thriller',
      boxOffice: '$836.8 million',
      budget: '$160 million',
      starring: 'Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page, Tom Hardy, Ken Watanabe',
      cinematography: 'Wally Pfister',
      music: 'Hans Zimmer',
      productionCompany: 'Warner Bros. Pictures, Legendary Pictures',
      country: 'United States, United Kingdom',
      language: 'English',
      awards: 'Academy Award for Best Cinematography, Best Sound Editing, Best Sound Mixing, Best Visual Effects'
    },
    relations: [
      { type: 'DIRECTED_BY', target: 'Christopher Nolan', targetType: 'Person' },
      { type: 'STARS', target: 'Leonardo DiCaprio', targetType: 'Person' },
      { type: 'PRODUCED_BY', target: 'Warner Bros.', targetType: 'Organization' }
    ],
  },
};

export const WithArrayProps: Story = {
  args: {
    id: '6',
    type: 'Project',
    name: 'Knowledge Graph Platform',
    properties: [
      { key: 'startDate', value: '2023-01-15' },
      { key: 'status', value: 'In Progress' },
      { key: 'budget', value: '$750,000' },
      { key: 'team', value: '8 engineers, 2 data scientists, 1 project manager' },
      { key: 'technologies', value: 'Neo4j, React, Python, Docker' },
      { key: 'completion', value: '65%' }
    ],
    relations: [
      { type: 'MANAGED_BY', target: 'Sarah Johnson', targetType: 'Person' },
      { type: 'OWNED_BY', target: 'Data Systems Department', targetType: 'Department' }
    ],
  },
};

export const ExpandedByDefault: Story = {
  args: {
    id: '7',
    type: 'Event',
    name: 'International Knowledge Graph Conference 2023',
    properties: {
      startDate: '2023-05-15',
      endDate: '2023-05-17',
      location: 'Berlin, Germany',
      organizer: 'Knowledge Graph Association',
      attendees: '1,200+ professionals and academics'
    },
    relations: [
      { type: 'ORGANIZED_BY', target: 'Knowledge Graph Association', targetType: 'Organization' },
      { type: 'HOSTED_AT', target: 'Berlin Conference Center', targetType: 'Location' },
      { type: 'FEATURED', target: 'Knowledge Graph Standards', targetType: 'Topic' },
      { type: 'KEYNOTE_BY', target: 'Dr. Michael Stevens', targetType: 'Person' }
    ],
  },
};

export const WithViewDetails: Story = {
  args: {
    id: '8',
    type: 'Publication',
    name: 'The Definitive Guide to Knowledge Graphs',
    properties: {
      publisher: 'Tech Publishing House',
      publicationDate: '2022-11-30',
      format: 'Hardcover, eBook, Audiobook',
      pages: '342',
      language: 'English'
    },
    onViewDetails: (id) => alert(`View details for item ${id}`),
  },
};

export const WithRelationClick: Story = {
  args: {
    id: '9',
    type: 'Person',
    name: 'Albert Einstein',
    properties: {
      birthDate: '1879-03-14',
      deathDate: '1955-04-18',
      field: 'Physics',
      knownFor: 'Theory of Relativity, Mass-energy equivalence (E=mc²)',
      awards: 'Nobel Prize in Physics (1921)'
    },
    relations: [
      { type: 'DEVELOPED', target: 'Theory of Relativity', targetType: 'Scientific Theory' },
      { type: 'WORKED_AT', target: 'Institute for Advanced Study', targetType: 'Organization' },
      { type: 'INFLUENCED', target: 'Modern Physics', targetType: 'Field' }
    ],
    onRelationClick: (relation) => alert(`Clicked on relation: ${relation.type} → ${relation.target}`),
  },
};
