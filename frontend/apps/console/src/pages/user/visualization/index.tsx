import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  BarChart3, 
  Network,
  Table,
  TreePine,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  Trash2,
  Copy,
  Download,
  Upload,
  Settings,
  Save,
  X,
  Check,
  ChevronDown,
  ChevronRight,
  Star,
  Share,
  Play,
  Pause,
  RefreshCw,
  Maximize2,
  Minimize2,
  Layers,
  Palette,
  Sliders,
  Grid,
  List,
  Layout,
  Zap,
  Database,
  Users,
  TrendingUp,
  Clock,
  Globe,
  Lock,
  AlertCircle,
  Info,
  ExternalLink,
  FileText
} from 'lucide-react';
import { z } from 'zod';

// Import D3 for graph visualization
import * as d3 from 'd3';

// Reusable UI Components
const StatisticCard = ({ title, value, icon, trend, color = 'blue', onClick, className = '' }) => {
  const colorClasses = {
    blue: 'bg-blue-500 text-white',
    green: 'bg-green-500 text-white', 
    red: 'bg-red-500 text-white',
    yellow: 'bg-yellow-500 text-white',
    purple: 'bg-purple-500 text-white'
  };

  return (
    <div 
      className={`bg-white rounded-lg border shadow-sm p-6 ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''} ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {trend && (
            <p className={`text-sm ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

const DataTable = ({ data, columns, showGlobalFilter, onRowClick, onRowSelect }) => {
  const [filteredData, setFilteredData] = useState(data);
  const [globalFilter, setGlobalFilter] = useState('');
  const [selectedRows, setSelectedRows] = useState([]);

  useEffect(() => {
    if (globalFilter) {
      const filtered = data.filter(item =>
        Object.values(item).some(value =>
          String(value).toLowerCase().includes(globalFilter.toLowerCase())
        )
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(data);
    }
  }, [data, globalFilter]);

  const handleRowSelection = (row) => {
    const newSelection = selectedRows.includes(row.id) 
      ? selectedRows.filter(id => id !== row.id)
      : [...selectedRows, row.id];
    setSelectedRows(newSelection);
    onRowSelect?.(newSelection);
  };

  return (
    <div className="space-y-4">
      {showGlobalFilter && (
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search visualizations..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
      )}
      
      <div className="rounded-md border">
        <table className="w-full">
          <thead className="border-b bg-muted/50">
            <tr>
              <th className="p-3 text-left">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRows(filteredData.map(item => item.id));
                    } else {
                      setSelectedRows([]);
                    }
                  }}
                />
              </th>
              {columns.map((col, idx) => (
                <th key={idx} className="p-3 text-left text-sm font-medium">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, idx) => (
              <tr 
                key={idx} 
                className={`border-b hover:bg-muted/50 ${selectedRows.includes(row.id) ? 'bg-blue-50' : ''}`}
              >
                <td className="p-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.includes(row.id)}
                    onChange={() => handleRowSelection(row)}
                  />
                </td>
                {columns.map((col, colIdx) => (
                  <td 
                    key={colIdx} 
                    className="p-3 text-sm cursor-pointer"
                    onClick={() => onRowClick?.(row)}
                  >
                    {col.cell ? col.cell(row) : row[col.accessorKey]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const GeneralForm = ({ fields, onSubmit, submitButtonText = "Submit", schema, initialData = {} }) => {
  const [formData, setFormData] = useState(initialData);
  const [errors, setErrors] = useState({});

  const handleInputChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    try {
      const validatedData = schema ? schema.parse(formData) : formData;
      onSubmit(validatedData);
      setErrors({});
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = {};
        error.errors.forEach(err => {
          fieldErrors[err.path[0]] = err.message;
        });
        setErrors(fieldErrors);
      }
    }
  };

  const renderField = (field) => {
    switch (field.type) {
      case 'text':
      case 'email':
        return (
          <input
            type={field.type}
            placeholder={field.placeholder}
            value={formData[field.name] || ''}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        );
      
      case 'textarea':
        return (
          <textarea
            placeholder={field.placeholder}
            value={formData[field.name] || ''}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            rows={3}
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        );
      
      case 'select':
        return (
          <select
            value={formData[field.name] || ''}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">{field.placeholder}</option>
            {field.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
      
      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id={field.name}
              checked={formData[field.name] || false}
              onChange={(e) => handleInputChange(field.name, e.target.checked)}
            />
            <label htmlFor={field.name} className="text-sm font-medium">
              {field.label}
            </label>
          </div>
        );
      
      case 'number':
        return (
          <input
            type="number"
            placeholder={field.placeholder}
            value={formData[field.name] || ''}
            onChange={(e) => handleInputChange(field.name, parseFloat(e.target.value) || 0)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            min={field.min}
            max={field.max}
            step={field.step}
          />
        );
      
      case 'color':
        return (
          <input
            type="color"
            value={formData[field.name] || '#3b82f6'}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="w-full h-10 rounded-md border border-input"
          />
        );

      case 'json':
        return (
          <textarea
            placeholder={field.placeholder || 'Enter JSON configuration...'}
            value={formData[field.name] ? JSON.stringify(formData[field.name], null, 2) : ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleInputChange(field.name, parsed);
              } catch {
                // Invalid JSON, keep as string for now
                handleInputChange(field.name + '_raw', e.target.value);
              }
            }}
            rows={6}
            className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {fields.map(field => (
        <div key={field.name} className="space-y-2">
          {field.type !== 'checkbox' && (
            <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              {field.label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </label>
          )}
          {renderField(field)}
          {errors[field.name] && (
            <p className="text-sm text-red-500">{errors[field.name]}</p>
          )}
          {field.description && (
            <p className="text-sm text-muted-foreground">{field.description}</p>
          )}
        </div>
      ))}
      <button
        onClick={handleSubmit}
        className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background bg-primary text-primary-foreground hover:bg-primary/90 h-10 py-2 px-4"
      >
        {submitButtonText}
      </button>
    </div>
  );
};

// D3 Graph Visualization Component
const D3GraphVisualization = ({ data, config, width = 800, height = 600 }) => {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!data.nodes || !data.edges) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.edges).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = svg.append("g")
      .selectAll("line")
      .data(data.edges)
      .enter().append("line")
      .attr("stroke", config?.edge_config?.default_color || "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 2);

    // Create nodes
    const node = svg.append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter().append("circle")
      .attr("r", d => config?.node_config?.size_range?.[0] || 8)
      .attr("fill", d => config?.node_config?.color_mapping?.[d.type] || config?.node_config?.default_color || "#69b3a2")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Add labels
    const label = svg.append("g")
      .selectAll("text")
      .data(data.nodes)
      .enter().append("text")
      .text(d => d.name || d.label)
      .attr("font-size", 12)
      .attr("dx", 12)
      .attr("dy", 4);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);

      label
        .attr("x", d => d.x)
        .attr("y", d => d.y);
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [data, config, width, height]);

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      className="border rounded-lg bg-white"
    />
  );
};

// Visualization Preview Component
const VisualizationPreview = ({ visualization, data }) => {
  const renderVisualization = () => {
    switch (visualization.config.type) {
      case 'GRAPH':
        return (
          <D3GraphVisualization
            data={data}
            config={visualization.config.config}
            width={400}
            height={300}
          />
        );
      
      case 'TABLE':
        return (
          <div className="border rounded-lg p-4 bg-white">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="p-2 text-left">Entity</th>
                  <th className="p-2 text-left">Type</th>
                  <th className="p-2 text-left">Properties</th>
                </tr>
              </thead>
              <tbody>
                {data.rows?.slice(0, 5).map((row, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{row.name}</td>
                    <td className="p-2">{row.type}</td>
                    <td className="p-2">{Object.keys(row.properties || {}).length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      
      case 'CHART':
        return (
          <div className="border rounded-lg p-4 bg-white h-64 flex items-center justify-center">
            <div className="text-center">
              <BarChart3 size={48} className="mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">Chart Visualization</p>
              <p className="text-xs text-gray-400">Type: {visualization.config.config?.type || 'bar'}</p>
            </div>
          </div>
        );
      
      case 'TREE':
        return (
          <div className="border rounded-lg p-4 bg-white h-64 flex items-center justify-center">
            <div className="text-center">
              <TreePine size={48} className="mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">Tree Visualization</p>
              <p className="text-xs text-gray-400">Hierarchical Layout</p>
            </div>
          </div>
        );
      
      default:
        return (
          <div className="border rounded-lg p-4 bg-gray-50 h-64 flex items-center justify-center">
            <p className="text-gray-500">Preview not available</p>
          </div>
        );
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Preview</h4>
        <div className="flex items-center space-x-1">
          <span className={`inline-block w-2 h-2 rounded-full ${
            visualization.is_public ? 'bg-green-500' : 'bg-yellow-500'
          }`}></span>
          <span className="text-xs text-gray-500">
            {visualization.is_public ? 'Public' : 'Private'}
          </span>
        </div>
      </div>
      {renderVisualization()}
    </div>
  );
};

// Visualization Templates
const VisualizationTemplates = ({ onSelectTemplate }) => {
  const templates = [
    {
      id: 'entity-network',
      name: 'Entity Network',
      description: 'Interactive network graph showing entity relationships',
      type: 'GRAPH',
      icon: <Network size={24} />,
      config: {
        type: 'GRAPH',
        config: {
          node_config: {
            default_color: '#3b82f6',
            size_range: [8, 20],
            label_field: 'name'
          },
          edge_config: {
            default_color: '#6b7280',
            width_range: [1, 3]
          },
          layout: {
            type: 'FORCE',
            params: { strength: -300 }
          }
        }
      }
    },
    {
      id: 'company-hierarchy',
      name: 'Company Hierarchy',
      description: 'Hierarchical tree view of organizational structure',
      type: 'TREE',
      icon: <TreePine size={24} />,
      config: {
        type: 'TREE',
        config: {
          orientation: 'vertical',
          node_separation: 100,
          level_separation: 150
        }
      }
    },
    {
      id: 'entity-table',
      name: 'Entity Data Table',
      description: 'Tabular view of entities with sorting and filtering',
      type: 'TABLE',
      icon: <Table size={24} />,
      config: {
        type: 'TABLE',
        config: {
          columns: [
            { field: 'name', header: 'Name', sortable: true },
            { field: 'type', header: 'Type', sortable: true },
            { field: 'properties', header: 'Properties', sortable: false }
          ],
          pagination: true,
          page_size: 20
        }
      }
    },
    {
      id: 'analytics-dashboard',
      name: 'Analytics Dashboard',
      description: 'Chart-based analytics with multiple visualizations',
      type: 'CHART',
      icon: <BarChart3 size={24} />,
      config: {
        type: 'CHART',
        config: {
          type: 'BAR',
          axes: {
            x_field: 'type',
            y_field: 'count'
          },
          title: 'Entity Distribution'
        }
      }
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {templates.map(template => (
        <div
          key={template.id}
          onClick={() => onSelectTemplate(template)}
          className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
              {template.icon}
            </div>
            <div className="flex-1">
              <h3 className="font-medium text-sm">{template.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{template.description}</p>
              <div className="mt-2">
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded">
                  {template.type}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Mock Data
const mockVisualizations = [
  {
    id: '1',
    name: 'Company Network Analysis',
    description: 'Interactive network showing relationships between tech companies',
    entity_id: 'company-tech-sector',
    is_public: true,
    config: {
      type: 'GRAPH',
      config: {
        node_config: {
          default_color: '#3b82f6',
          color_mapping: { 'Company': '#3b82f6', 'Person': '#ef4444', 'Product': '#10b981' },
          size_range: [8, 20],
          label_field: 'name'
        },
        edge_config: {
          default_color: '#6b7280',
          width_range: [1, 3]
        },
        layout: { type: 'FORCE', params: {} }
      }
    },
    created_by: 'user1',
    created_at: '2024-01-20T10:00:00Z',
    updated_at: '2024-01-25T15:30:00Z'
  },
  {
    id: '2',
    name: 'Entity Properties Table',
    description: 'Comprehensive table view of all entities with properties',
    entity_id: null,
    is_public: false,
    config: {
      type: 'TABLE',
      config: {
        columns: [
          { field: 'name', header: 'Entity Name', sortable: true },
          { field: 'type', header: 'Type', sortable: true },
          { field: 'confidence', header: 'Confidence', sortable: true }
        ],
        pagination: true,
        page_size: 20
      }
    },
    created_by: 'user1',
    created_at: '2024-01-18T14:20:00Z',
    updated_at: '2024-01-24T09:45:00Z'
  },
  {
    id: '3',
    name: 'Investment Flow Chart',
    description: 'Bar chart showing investment flows between companies',
    entity_id: 'investment-data',
    is_public: true,
    config: {
      type: 'CHART',
      config: {
        type: 'BAR',
        axes: {
          x_field: 'company',
          y_field: 'investment_amount',
          color_field: 'sector'
        },
        title: 'Investment Distribution by Company'
      }
    },
    created_by: 'user2',
    created_at: '2024-01-22T11:15:00Z',
    updated_at: '2024-01-25T16:20:00Z'
  }
];

const mockGraphData = {
  nodes: [
    { id: '1', name: 'Apple Inc.', type: 'Company', x: 400, y: 300 },
    { id: '2', name: 'Tim Cook', type: 'Person', x: 300, y: 200 },
    { id: '3', name: 'iPhone', type: 'Product', x: 500, y: 200 },
    { id: '4', name: 'Microsoft', type: 'Company', x: 300, y: 400 },
    { id: '5', name: 'Google', type: 'Company', x: 500, y: 400 }
  ],
  edges: [
    { id: 'e1', source: '2', target: '1', type: 'CEO_OF' },
    { id: 'e2', source: '1', target: '3', type: 'PRODUCES' },
    { id: 'e3', source: '1', target: '4', type: 'COMPETES_WITH' },
    { id: 'e4', source: '1', target: '5', type: 'COMPETES_WITH' }
  ],
  rows: [
    { name: 'Apple Inc.', type: 'Company', properties: { sector: 'Technology', founded: '1976' } },
    { name: 'Tim Cook', type: 'Person', properties: { position: 'CEO', age: '63' } },
    { name: 'iPhone', type: 'Product', properties: { category: 'Smartphone', launch_year: '2007' } }
  ]
};

// Schemas
const CreateVisualizationSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  entity_id: z.string().optional(),
  is_public: z.boolean().default(false),
  config: z.object({
    type: z.enum(['GRAPH', 'TREE', 'TABLE', 'CHART']),
    config: z.record(z.any()).optional()
  })
});

// Main Visualization Management Component
const VisualizationManagementPage = () => {
  const [visualizations, setVisualizations] = useState(mockVisualizations);
  const [selectedVisualization, setSelectedVisualization] = useState(null);
  const [currentView, setCurrentView] = useState('gallery'); // 'gallery', 'table', 'templates'
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingVisualization, setEditingVisualization] = useState(null);
  const [selectedRows, setSelectedRows] = useState([]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Statistics
  const stats = useMemo(() => ({
    total: visualizations.length,
    public: visualizations.filter(v => v.is_public).length,
    private: visualizations.filter(v => !v.is_public).length,
    byType: {
      GRAPH: visualizations.filter(v => v.config.type === 'GRAPH').length,
      TABLE: visualizations.filter(v => v.config.type === 'TABLE').length,
      CHART: visualizations.filter(v => v.config.type === 'CHART').length,
      TREE: visualizations.filter(v => v.config.type === 'TREE').length
    }
  }), [visualizations]);

  // Form fields for creating/editing visualizations
  const visualizationFormFields = [
    {
      name: 'name',
      type: 'text',
      label: 'Visualization Name',
      placeholder: 'Enter visualization name...',
      required: true
    },
    {
      name: 'description',
      type: 'textarea',
      label: 'Description',
      placeholder: 'Describe your visualization...'
    },
    {
      name: 'entity_id',
      type: 'text',
      label: 'Entity ID',
      placeholder: 'Optional entity to focus on'
    },
    {
      name: 'config.type',
      type: 'select',
      label: 'Visualization Type',
      required: true,
      options: [
        { value: 'GRAPH', label: 'Graph Network' },
        { value: 'TABLE', label: 'Data Table' },
        { value: 'CHART', label: 'Chart/Analytics' },
        { value: 'TREE', label: 'Tree/Hierarchy' }
      ]
    },
    {
      name: 'is_public',
      type: 'checkbox',
      label: 'Make this visualization public'
    }
  ];

  // Table columns for visualization list
  const visualizationColumns = [
    {
      header: 'Visualization',
      accessorKey: 'name',
      cell: (row) => (
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
            {row.config.type === 'GRAPH' && <Network size={16} />}
            {row.config.type === 'TABLE' && <Table size={16} />}
            {row.config.type === 'CHART' && <BarChart3 size={16} />}
            {row.config.type === 'TREE' && <TreePine size={16} />}
          </div>
          <div>
            <div className="font-medium">{row.name}</div>
            <div className="text-sm text-gray-500">{row.description}</div>
          </div>
        </div>
      )
    },
    {
      header: 'Type',
      accessorKey: 'config.type',
      cell: (row) => (
        <span className="inline-block px-2 py-1 text-xs bg-gray-100 rounded">
          {row.config.type}
        </span>
      )
    },
    {
      header: 'Status',
      accessorKey: 'is_public',
      cell: (row) => (
        <div className="flex items-center space-x-1">
          {row.is_public ? (
            <>
              <Globe size={14} className="text-green-500" />
              <span className="text-sm text-green-700">Public</span>
            </>
          ) : (
            <>
              <Lock size={14} className="text-gray-500" />
              <span className="text-sm text-gray-700">Private</span>
            </>
          )}
        </div>
      )
    },
    {
      header: 'Created',
      accessorKey: 'created_at',
      cell: (row) => (
        <div className="text-sm text-gray-500">
          {new Date(row.created_at).toLocaleDateString()}
        </div>
      )
    },
    {
      header: 'Actions',
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSelectedVisualization(row)}
            className="p-1 hover:bg-gray-100 rounded"
            title="View"
          >
            <Eye size={16} />
          </button>
          <button
            onClick={() => handleEditVisualization(row)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Edit"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={() => handleDuplicateVisualization(row)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Duplicate"
          >
            <Copy size={16} />
          </button>
          <button
            onClick={() => handleDeleteVisualization(row.id)}
            className="p-1 hover:bg-gray-100 rounded text-red-500"
            title="Delete"
          >
            <Trash2 size={16} />
          </button>
        </div>
      )
    }
  ];

  // Handle creating new visualization
  const handleCreateVisualization = (formData) => {
    const newVisualization = {
      id: Date.now().toString(),
      ...formData,
      config: {
        type: formData['config.type'] || formData.config?.type,
        config: {}
      },
      created_by: 'current_user',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    setVisualizations(prev => [newVisualization, ...prev]);
    setShowCreateModal(false);
  };

  // Handle editing visualization
  const handleEditVisualization = (visualization) => {
    setEditingVisualization(visualization);
    setShowEditModal(true);
  };

  // Handle updating visualization
  const handleUpdateVisualization = (formData) => {
    setVisualizations(prev =>
      prev.map(viz =>
        viz.id === editingVisualization.id
          ? { 
              ...viz, 
              ...formData,
              config: {
                type: formData['config.type'] || formData.config?.type || viz.config.type,
                config: viz.config.config
              },
              updated_at: new Date().toISOString()
            }
          : viz
      )
    );
    setShowEditModal(false);
    setEditingVisualization(null);
  };

  // Handle duplicate visualization
  const handleDuplicateVisualization = (visualization) => {
    const duplicated = {
      ...visualization,
      id: Date.now().toString(),
      name: `${visualization.name} (Copy)`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    setVisualizations(prev => [duplicated, ...prev]);
  };

  // Handle delete visualization
  const handleDeleteVisualization = (id) => {
    if (window.confirm('Are you sure you want to delete this visualization?')) {
      setVisualizations(prev => prev.filter(viz => viz.id !== id));
      if (selectedVisualization?.id === id) {
        setSelectedVisualization(null);
      }
    }
  };

  // Handle template selection
  const handleSelectTemplate = (template) => {
    setShowCreateModal(true);
    // Pre-fill form with template data
    setTimeout(() => {
      const nameInput = document.querySelector('input[name="name"]');
      const typeSelect = document.querySelector('select[name="config.type"]');
      if (nameInput) nameInput.value = template.name;
      if (typeSelect) typeSelect.value = template.type;
    }, 100);
  };

  // Handle bulk actions
  const handleBulkDelete = () => {
    if (selectedRows.length === 0) return;
    if (window.confirm(`Delete ${selectedRows.length} selected visualizations?`)) {
      setVisualizations(prev => prev.filter(viz => !selectedRows.includes(viz.id)));
      setSelectedRows([]);
    }
  };

  const handleBulkExport = () => {
    const selectedVizs = visualizations.filter(viz => selectedRows.includes(viz.id));
    const exportData = {
      visualizations: selectedVizs,
      exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `visualizations-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Visualization Management</h1>
            <p className="text-gray-600 mt-1">Create, manage, and share data visualizations</p>
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setCurrentView(currentView === 'gallery' ? 'table' : 'gallery')}
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title={currentView === 'gallery' ? 'Table View' : 'Gallery View'}
            >
              {currentView === 'gallery' ? <List size={20} /> : <Grid size={20} />}
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Create Visualization</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Statistics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatisticCard
            title="Total Visualizations"
            value={stats.total}
            icon={<BarChart3 size={20} />}
            trend={{ value: 12, isPositive: true }}
            color="blue"
          />
          <StatisticCard
            title="Public Visualizations"
            value={stats.public}
            icon={<Globe size={20} />}
            color="green"
          />
          <StatisticCard
            title="Graph Networks"
            value={stats.byType.GRAPH}
            icon={<Network size={20} />}
            color="purple"
          />
          <StatisticCard
            title="Data Tables"
            value={stats.byType.TABLE}
            icon={<Table size={20} />}
            color="yellow"
          />
        </div>

        {/* View Selector */}
        <div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
          <button
            onClick={() => setCurrentView('gallery')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === 'gallery' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Gallery View
          </button>
          <button
            onClick={() => setCurrentView('table')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === 'table' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Table View
          </button>
          <button
            onClick={() => setCurrentView('templates')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === 'templates' 
                ? 'bg-blue-100 text-blue-700' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Templates
          </button>
        </div>

        {/* Bulk Actions */}
        {selectedRows.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-800">
                {selectedRows.length} visualizations selected
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleBulkExport}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  Export Selected
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                >
                  Delete Selected
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        {currentView === 'gallery' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Visualization Gallery */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg border shadow-sm">
                <div className="p-6 border-b">
                  <h2 className="text-lg font-semibold">Visualizations</h2>
                </div>
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {visualizations.map(viz => (
                      <div 
                        key={viz.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                          selectedVisualization?.id === viz.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                        }`}
                        onClick={() => setSelectedVisualization(viz)}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                              {viz.config.type === 'GRAPH' && <Network size={16} />}
                              {viz.config.type === 'TABLE' && <Table size={16} />}
                              {viz.config.type === 'CHART' && <BarChart3 size={16} />}
                              {viz.config.type === 'TREE' && <TreePine size={16} />}
                            </div>
                            <div>
                              <h3 className="font-medium text-sm">{viz.name}</h3>
                              <p className="text-xs text-gray-500">{viz.config.type}</p>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1">
                            {viz.is_public ? (
                              <Globe size={14} className="text-green-500" />
                            ) : (
                              <Lock size={14} className="text-gray-400" />
                            )}
                          </div>
                        </div>
                        
                        <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                          {viz.description}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <time className="text-xs text-gray-400">
                            {new Date(viz.updated_at).toLocaleDateString()}
                          </time>
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditVisualization(viz);
                              }}
                              className="p-1 hover:bg-gray-100 rounded"
                            >
                              <Edit size={12} />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDuplicateVisualization(viz);
                              }}
                              className="p-1 hover:bg-gray-100 rounded"
                            >
                              <Copy size={12} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Visualization Preview */}
            <div>
              <div className="bg-white rounded-lg border shadow-sm">
                <div className="p-6 border-b">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold">Preview</h2>
                    {selectedVisualization && (
                      <button
                        onClick={() => setIsFullscreen(true)}
                        className="p-2 hover:bg-gray-100 rounded"
                        title="Fullscreen"
                      >
                        <Maximize2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
                <div className="p-6">
                  {selectedVisualization ? (
                    <VisualizationPreview
                      visualization={selectedVisualization}
                      data={mockGraphData}
                    />
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Network size={48} className="mx-auto mb-4 opacity-50" />
                      <p>Select a visualization to preview</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === 'table' && (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">All Visualizations</h2>
            </div>
            <div className="p-6">
              <DataTable
                data={visualizations}
                columns={visualizationColumns}
                showGlobalFilter={true}
                onRowClick={setSelectedVisualization}
                onRowSelect={setSelectedRows}
              />
            </div>
          </div>
        )}

        {currentView === 'templates' && (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">Visualization Templates</h2>
              <p className="text-sm text-gray-600 mt-1">
                Quick start with pre-configured visualization templates
              </p>
            </div>
            <div className="p-6">
              <VisualizationTemplates onSelectTemplate={handleSelectTemplate} />
            </div>
          </div>
        )}
      </div>

      {/* Create Visualization Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Create New Visualization</h2>
                <button 
                  onClick={() => setShowCreateModal(false)} 
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-6">
              <GeneralForm
                fields={visualizationFormFields}
                schema={CreateVisualizationSchema}
                onSubmit={handleCreateVisualization}
                submitButtonText="Create Visualization"
              />
            </div>
          </div>
        </div>
      )}

      {/* Edit Visualization Modal */}
      {showEditModal && editingVisualization && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Edit Visualization</h2>
                <button 
                  onClick={() => setShowEditModal(false)} 
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-6">
              <GeneralForm
                fields={visualizationFormFields}
                schema={CreateVisualizationSchema}
                onSubmit={handleUpdateVisualization}
                submitButtonText="Update Visualization"
                initialData={{
                  ...editingVisualization,
                  'config.type': editingVisualization.config.type
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Fullscreen Visualization Modal */}
      {isFullscreen && selectedVisualization && (
        <div className="fixed inset-0 bg-black bg-opacity-95 flex items-center justify-center z-50">
          <div className="w-full h-full p-8 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white text-xl font-semibold">
                {selectedVisualization.name}
              </h2>
              <button
                onClick={() => setIsFullscreen(false)}
                className="text-white p-2 hover:bg-white hover:bg-opacity-20 rounded"
              >
                <Minimize2 size={20} />
              </button>
            </div>
            <div className="flex-1 flex items-center justify-center">
              {selectedVisualization.config.type === 'GRAPH' ? (
                <D3GraphVisualization
                  data={mockGraphData}
                  config={selectedVisualization.config.config}
                  width={Math.min(window.innerWidth - 100, 1200)}
                  height={Math.min(window.innerHeight - 200, 800)}
                />
              ) : (
                <div className="bg-white rounded-lg p-8">
                  <VisualizationPreview
                    visualization={selectedVisualization}
                    data={mockGraphData}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualizationManagementPage;
