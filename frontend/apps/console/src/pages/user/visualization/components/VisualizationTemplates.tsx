import { BarChart3, Network, Table, TreePine } from "lucide-react";

export const VisualizationTemplates = ({ onSelectTemplate }) => {
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
