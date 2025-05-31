import { useState, useEffect, useMemo } from "react";
import {
  Activity,
  Users,
  Clock,
  TrendingUp,
  Database,
  Search,
  Download,
  Eye,
  Edit,
  Trash2,
  Plus,
  Key,
  Code,
  BarChart3,
  CheckCircle,
  Copy,
  Lock,
  Unlock,
  User,
  MessageSquare,
  GitBranch,
  Upload,
  LogIn,
  LogOut,
  Monitor,
  Globe2,
  X,
  Check,
} from "lucide-react";
import { z } from "zod";
import { AppForm, DataTable, StatisticCard } from "@vbkg/ui";

// Activity Timeline Component
const ActivityTimeline = ({ activities, onActivityClick }) => {
  const getActivityIcon = (type) => {
    const iconMap = {
      user_login: <LogIn size={16} />,
      user_logout: <LogOut size={16} />,
      entity_create: <Plus size={16} />,
      entity_update: <Edit size={16} />,
      entity_delete: <Trash2 size={16} />,
      relationship_create: <GitBranch size={16} />,
      search_query: <Search size={16} />,
      visualization_create: <BarChart3 size={16} />,
      api_call: <Code size={16} />,
      file_upload: <Upload size={16} />,
      chat_message: <MessageSquare size={16} />,
    };
    return iconMap[type] || <Activity size={16} />;
  };

  const getActivityColor = (type) => {
    const colorMap = {
      user_login: "bg-green-100 text-green-600",
      user_logout: "bg-gray-100 text-gray-600",
      entity_create: "bg-blue-100 text-blue-600",
      entity_update: "bg-yellow-100 text-yellow-600",
      entity_delete: "bg-red-100 text-red-600",
      relationship_create: "bg-purple-100 text-purple-600",
      search_query: "bg-indigo-100 text-indigo-600",
      visualization_create: "bg-green-100 text-green-600",
      api_call: "bg-orange-100 text-orange-600",
      file_upload: "bg-teal-100 text-teal-600",
      chat_message: "bg-pink-100 text-pink-600",
    };
    return colorMap[type] || "bg-gray-100 text-gray-600";
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const past = new Date(timestamp);
    const diffInMinutes = Math.floor((now - past) / (1000 * 60));

    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  return (
    <div className="space-y-4">
      {activities.map((activity, index) => (
        <div
          key={activity.id}
          className="flex items-start space-x-4 p-4 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
          onClick={() => onActivityClick?.(activity)}
        >
          <div
            className={`p-2 rounded-full ${getActivityColor(activity.type)}`}
          >
            {getActivityIcon(activity.type)}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {activity.title}
              </h4>
              <time className="text-xs text-gray-500 flex-shrink-0">
                {formatTimeAgo(activity.timestamp)}
              </time>
            </div>

            <p className="text-sm text-gray-600 mt-1">{activity.description}</p>

            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <User size={12} />
                <span>{activity.user}</span>
              </div>
              {activity.ip_address && (
                <div className="flex items-center space-x-1">
                  <Globe2 size={12} />
                  <span>{activity.ip_address}</span>
                </div>
              )}
              {activity.user_agent && (
                <div className="flex items-center space-x-1">
                  <Monitor size={12} />
                  <span>{activity.user_agent.split(" ")[0]}</span>
                </div>
              )}
            </div>

            {activity.metadata && Object.keys(activity.metadata).length > 0 && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                <details>
                  <summary className="cursor-pointer text-gray-600">
                    Additional Details
                  </summary>
                  <div className="mt-1 space-y-1">
                    {Object.entries(activity.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="font-medium">{key}:</span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// API Key Card Component
const ApiKeyCard = ({ apiKey, onEdit, onDelete, onToggle }) => {
  const [showKey, setShowKey] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatKey = (key) => {
    if (showKey) return key;
    return key.substring(0, 8) + "•".repeat(24) + key.substring(key.length - 4);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "inactive":
        return "bg-gray-100 text-gray-800";
      case "expired":
        return "bg-red-100 text-red-800";
      case "suspended":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="bg-white border rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-medium">{apiKey.name}</h3>
          <p className="text-sm text-gray-600 mt-1">{apiKey.description}</p>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`px-2 py-1 text-xs rounded-full ${getStatusColor(apiKey.status)}`}
          >
            {apiKey.status}
          </span>
          <div className="flex items-center space-x-1">
            <button
              onClick={onEdit}
              className="p-1 hover:bg-gray-100 rounded"
              title="Edit"
            >
              <Edit size={16} />
            </button>
            <button
              onClick={onToggle}
              className="p-1 hover:bg-gray-100 rounded"
              title={apiKey.status === "active" ? "Disable" : "Enable"}
            >
              {apiKey.status === "active" ? (
                <Lock size={16} />
              ) : (
                <Unlock size={16} />
              )}
            </button>
            <button
              onClick={onDelete}
              className="p-1 hover:bg-gray-100 rounded text-red-500"
              title="Delete"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <label className="text-xs font-medium text-gray-500 uppercase">
            API Key
          </label>
          <div className="flex items-center space-x-2 mt-1">
            <code className="flex-1 p-2 bg-gray-50 rounded text-sm font-mono">
              {formatKey(apiKey.key)}
            </code>
            <button
              onClick={() => setShowKey(!showKey)}
              className="p-2 hover:bg-gray-100 rounded"
              title={showKey ? "Hide Key" : "Show Key"}
            >
              {showKey ? (
                <Eye size={16} />
              ) : (
                <Eye size={16} className="opacity-50" />
              )}
            </button>
            <button
              onClick={handleCopyKey}
              className="p-2 hover:bg-gray-100 rounded"
              title="Copy Key"
            >
              {copied ? (
                <Check size={16} className="text-green-500" />
              ) : (
                <Copy size={16} />
              )}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Created:</span>
            <div>{new Date(apiKey.created_at).toLocaleDateString()}</div>
          </div>
          <div>
            <span className="text-gray-500">Last Used:</span>
            <div>
              {apiKey.last_used
                ? new Date(apiKey.last_used).toLocaleDateString()
                : "Never"}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Requests:</span>
            <div>{apiKey.request_count?.toLocaleString() || 0}</div>
          </div>
          <div>
            <span className="text-gray-500">Rate Limit:</span>
            <div>{apiKey.rate_limit || "Unlimited"}</div>
          </div>
        </div>

        {apiKey.scopes && apiKey.scopes.length > 0 && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">
              Permissions
            </label>
            <div className="flex flex-wrap gap-1 mt-1">
              {apiKey.scopes.map((scope) => (
                <span
                  key={scope}
                  className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                >
                  {scope}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Mock Data
const mockActivities = [
  {
    id: "1",
    type: "user_login",
    title: "User Login",
    description: "john.doe@example.com logged in from Chrome on Windows",
    user: "John Doe",
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    ip_address: "192.168.1.100",
    user_agent: "Chrome/120.0.0.0",
    metadata: {
      login_method: "password",
      session_duration: "2h 15m",
      location: "New York, US",
    },
  },
  {
    id: "2",
    type: "entity_create",
    title: "Entity Created",
    description: 'Created new company entity "OpenAI Inc."',
    user: "Jane Smith",
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
    ip_address: "10.0.0.50",
    user_agent: "Firefox/119.0",
    metadata: {
      entity_type: "Company",
      entity_id: "ent_12345",
      confidence: 0.95,
    },
  },
  {
    id: "3",
    type: "search_query",
    title: "Knowledge Search",
    description: 'Searched for "artificial intelligence companies"',
    user: "Bob Wilson",
    timestamp: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
    ip_address: "172.16.0.25",
    user_agent: "Safari/17.0",
    metadata: {
      query: "artificial intelligence companies",
      results_count: 47,
      response_time: "120ms",
    },
  },
  {
    id: "4",
    type: "api_call",
    title: "API Request",
    description: "GET /api/v1/entities endpoint accessed",
    user: "API Client",
    timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
    ip_address: "203.0.113.10",
    user_agent: "Python-requests/2.31.0",
    metadata: {
      endpoint: "/api/v1/entities",
      method: "GET",
      status_code: 200,
      response_time: "85ms",
      api_key: "ak_1234...5678",
    },
  },
  {
    id: "5",
    type: "visualization_create",
    title: "Visualization Created",
    description: 'Created new network graph "Tech Company Ecosystem"',
    user: "Alice Johnson",
    timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
    ip_address: "192.168.1.150",
    user_agent: "Chrome/120.0.0.0",
    metadata: {
      visualization_type: "GRAPH",
      entity_count: 25,
      relationship_count: 40,
    },
  },
];

const mockApiKeys = [
  {
    id: "1",
    name: "Production API Key",
    description: "Main API key for production application",
    key: "ak_1234567890abcdef1234567890abcdef12345678",
    status: "active",
    created_at: "2024-01-15T10:00:00Z",
    last_used: "2024-01-25T14:30:00Z",
    request_count: 15420,
    rate_limit: "1000 req/hour",
    scopes: ["read:entities", "write:entities", "read:relationships"],
  },
  {
    id: "2",
    name: "Development Key",
    description: "API key for development and testing",
    key: "ak_abcdef1234567890abcdef1234567890abcdef12",
    status: "active",
    created_at: "2024-01-10T09:00:00Z",
    last_used: "2024-01-24T16:45:00Z",
    request_count: 892,
    rate_limit: "100 req/hour",
    scopes: ["read:entities", "read:relationships"],
  },
  {
    id: "3",
    name: "Analytics Dashboard",
    description: "Read-only key for analytics dashboard",
    key: "ak_fedcba0987654321fedcba0987654321fedcba09",
    status: "inactive",
    created_at: "2024-01-05T11:30:00Z",
    last_used: null,
    request_count: 0,
    rate_limit: "500 req/hour",
    scopes: ["read:analytics", "read:stats"],
  },
];

// Schemas
const CreateApiKeySchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  rate_limit: z.string().optional(),
  scopes: z.array(z.string()).min(1, "At least one permission is required"),
  expires_at: z.string().optional(),
});

// User Activities Page Component
const UserActivitiesPage = () => {
  const [activities, setActivities] = useState(mockActivities);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [filters, setFilters] = useState({
    user: "",
    type: "",
    dateFrom: "",
    dateTo: "",
  });
  const [currentView, setCurrentView] = useState("timeline"); // 'timeline', 'table'

  // Statistics
  const stats = useMemo(() => {
    const now = new Date();
    const today = activities.filter((a) => {
      const activityDate = new Date(a.timestamp);
      return activityDate.toDateString() === now.toDateString();
    }).length;

    const uniqueUsers = new Set(activities.map((a) => a.user)).size;
    const apiCalls = activities.filter((a) => a.type === "api_call").length;
    const entityOperations = activities.filter((a) =>
      ["entity_create", "entity_update", "entity_delete"].includes(a.type),
    ).length;

    return {
      todayActivities: today,
      uniqueUsers,
      apiCalls,
      entityOperations,
    };
  }, [activities]);

  // Activity table columns
  const activityColumns = [
    {
      header: "Activity",
      accessorKey: "title",
      cell: (row) => (
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-full ${getActivityColor(row.type)}`}>
            {getActivityIcon(row.type)}
          </div>
          <div>
            <div className="font-medium text-sm">{row.title}</div>
            <div className="text-xs text-gray-500">{row.description}</div>
          </div>
        </div>
      ),
    },
    {
      header: "User",
      accessorKey: "user",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <User size={16} className="text-gray-400" />
          <span className="text-sm">{row.user}</span>
        </div>
      ),
    },
    {
      header: "Time",
      accessorKey: "timestamp",
      cell: (row) => (
        <div className="text-sm text-gray-600">
          {new Date(row.timestamp).toLocaleString()}
        </div>
      ),
    },
    {
      header: "IP Address",
      accessorKey: "ip_address",
      cell: (row) => (
        <code className="text-xs bg-gray-100 p-1 rounded">
          {row.ip_address}
        </code>
      ),
    },
    {
      header: "Actions",
      cell: (row) => (
        <button
          onClick={() => setSelectedActivity(row)}
          className="p-1 hover:bg-gray-100 rounded"
          title="View Details"
        >
          <Eye size={16} />
        </button>
      ),
    },
  ];

  const getActivityIcon = (type) => {
    const iconMap = {
      user_login: <LogIn size={16} />,
      user_logout: <LogOut size={16} />,
      entity_create: <Plus size={16} />,
      entity_update: <Edit size={16} />,
      entity_delete: <Trash2 size={16} />,
      relationship_create: <GitBranch size={16} />,
      search_query: <Search size={16} />,
      visualization_create: <BarChart3 size={16} />,
      api_call: <Code size={16} />,
      file_upload: <Upload size={16} />,
      chat_message: <MessageSquare size={16} />,
    };
    return iconMap[type] || <Activity size={16} />;
  };

  const getActivityColor = (type) => {
    const colorMap = {
      user_login: "bg-green-100 text-green-600",
      user_logout: "bg-gray-100 text-gray-600",
      entity_create: "bg-blue-100 text-blue-600",
      entity_update: "bg-yellow-100 text-yellow-600",
      entity_delete: "bg-red-100 text-red-600",
      relationship_create: "bg-purple-100 text-purple-600",
      search_query: "bg-indigo-100 text-indigo-600",
      visualization_create: "bg-green-100 text-green-600",
      api_call: "bg-orange-100 text-orange-600",
      file_upload: "bg-teal-100 text-teal-600",
      chat_message: "bg-pink-100 text-pink-600",
    };
    return colorMap[type] || "bg-gray-100 text-gray-600";
  };

  // Handle export
  const handleExportActivities = () => {
    const exportData = {
      activities: activities,
      exported_at: new Date().toISOString(),
      total_count: activities.length,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `user-activities-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              User Activities
            </h1>
            <p className="text-gray-600 mt-1">
              Monitor and track user actions across the platform
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() =>
                setCurrentView(
                  currentView === "timeline" ? "table" : "timeline",
                )
              }
              className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              title={
                currentView === "timeline" ? "Table View" : "Timeline View"
              }
            >
              {currentView === "timeline" ? (
                <BarChart3 size={20} />
              ) : (
                <Activity size={20} />
              )}
            </button>
            <button
              onClick={handleExportActivities}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
            >
              <Download size={16} />
              <span>Export</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Statistics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatisticCard
            title="Today's Activities"
            value={stats.todayActivities}
            icon={<Activity size={20} />}
            trend={{ value: 15, isPositive: true }}
            color="blue"
          />
          <StatisticCard
            title="Active Users"
            value={stats.uniqueUsers}
            icon={<Users size={20} />}
            color="green"
          />
          <StatisticCard
            title="API Calls"
            value={stats.apiCalls}
            icon={<Code size={20} />}
            trend={{ value: 8, isPositive: true }}
            color="orange"
          />
          <StatisticCard
            title="Entity Operations"
            value={stats.entityOperations}
            icon={<Database size={20} />}
            color="purple"
          />
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">User</label>
              <input
                type="text"
                placeholder="Filter by user..."
                value={filters.user}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, user: e.target.value }))
                }
                className="w-full h-10 px-3 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Activity Type
              </label>
              <select
                value={filters.type}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, type: e.target.value }))
                }
                className="w-full h-10 px-3 border rounded-lg"
              >
                <option value="">All Types</option>
                <option value="user_login">User Login</option>
                <option value="entity_create">Entity Create</option>
                <option value="search_query">Search Query</option>
                <option value="api_call">API Call</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                From Date
              </label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateFrom: e.target.value }))
                }
                className="w-full h-10 px-3 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">To Date</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, dateTo: e.target.value }))
                }
                className="w-full h-10 px-3 border rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Activities Display */}
        {currentView === "timeline" ? (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">Activity Timeline</h2>
            </div>
            <div className="p-6">
              <ActivityTimeline
                activities={activities}
                onActivityClick={setSelectedActivity}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">Activity Table</h2>
            </div>
            <div className="p-6">
              <DataTable
                data={activities}
                columns={activityColumns}
                showGlobalFilter={true}
                onRowClick={setSelectedActivity}
              />
            </div>
          </div>
        )}
      </div>

      {/* Activity Detail Modal */}
      {selectedActivity && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Activity Details</h2>
                <button
                  onClick={() => setSelectedActivity(null)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center space-x-3">
                <div
                  className={`p-3 rounded-full ${getActivityColor(selectedActivity.type)}`}
                >
                  {getActivityIcon(selectedActivity.type)}
                </div>
                <div>
                  <h3 className="font-medium">{selectedActivity.title}</h3>
                  <p className="text-sm text-gray-600">
                    {selectedActivity.description}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    User
                  </label>
                  <p className="mt-1">{selectedActivity.user}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Timestamp
                  </label>
                  <p className="mt-1">
                    {new Date(selectedActivity.timestamp).toLocaleString()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    IP Address
                  </label>
                  <p className="mt-1 font-mono text-sm">
                    {selectedActivity.ip_address}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    User Agent
                  </label>
                  <p className="mt-1 text-sm">{selectedActivity.user_agent}</p>
                </div>
              </div>

              {selectedActivity.metadata && (
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Additional Information
                  </label>
                  <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                    {Object.entries(selectedActivity.metadata).map(
                      ([key, value]) => (
                        <div key={key} className="flex justify-between py-1">
                          <span className="font-medium text-sm">{key}:</span>
                          <span className="text-sm">{String(value)}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// API Access Management Page Component
const ApiAccessPage = () => {
  const [apiKeys, setApiKeys] = useState(mockApiKeys);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);
  const [currentView, setCurrentView] = useState("keys"); // 'keys', 'docs', 'logs', 'analytics'

  // API key form fields
  const apiKeyFormFields = [
    {
      name: "name",
      type: "text",
      label: "API Key Name",
      placeholder: "Enter a descriptive name...",
      required: true,
    },
    {
      name: "description",
      type: "textarea",
      label: "Description",
      placeholder: "What will this API key be used for?",
    },
    {
      name: "rate_limit",
      type: "text",
      label: "Rate Limit",
      placeholder: "e.g., 1000 req/hour",
    },
    {
      name: "scopes",
      type: "multiselect",
      label: "Permissions",
      required: true,
      options: [
        { value: "read:entities", label: "Read Entities" },
        { value: "write:entities", label: "Write Entities" },
        { value: "delete:entities", label: "Delete Entities" },
        { value: "read:relationships", label: "Read Relationships" },
        { value: "write:relationships", label: "Write Relationships" },
        { value: "read:analytics", label: "Read Analytics" },
        { value: "read:stats", label: "Read Statistics" },
        { value: "admin", label: "Admin Access" },
      ],
    },
    {
      name: "expires_at",
      type: "text",
      label: "Expiration Date (Optional)",
      placeholder: "YYYY-MM-DD",
    },
  ];

  // Statistics
  const stats = useMemo(() => {
    const totalKeys = apiKeys.length;
    const activeKeys = apiKeys.filter((k) => k.status === "active").length;
    const totalRequests = apiKeys.reduce(
      (sum, k) => sum + (k.request_count || 0),
      0,
    );
    const avgRequestsPerKey =
      totalKeys > 0 ? Math.round(totalRequests / totalKeys) : 0;

    return {
      totalKeys,
      activeKeys,
      totalRequests,
      avgRequestsPerKey,
    };
  }, [apiKeys]);

  // Handle create API key
  const handleCreateApiKey = (formData) => {
    const newKey = {
      id: Date.now().toString(),
      ...formData,
      key: `ak_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`,
      status: "active",
      created_at: new Date().toISOString(),
      last_used: null,
      request_count: 0,
    };

    setApiKeys((prev) => [newKey, ...prev]);
    setShowCreateModal(false);
  };

  // Handle edit API key
  const handleEditApiKey = (key) => {
    setEditingKey(key);
    setShowCreateModal(true);
  };

  // Handle delete API key
  const handleDeleteApiKey = (keyId) => {
    if (
      window.confirm(
        "Are you sure you want to delete this API key? This action cannot be undone.",
      )
    ) {
      setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
    }
  };

  // Handle toggle API key status
  const handleToggleApiKey = (keyId) => {
    setApiKeys((prev) =>
      prev.map((k) =>
        k.id === keyId
          ? { ...k, status: k.status === "active" ? "inactive" : "active" }
          : k,
      ),
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              API Access Management
            </h1>
            <p className="text-gray-600 mt-1">
              Manage API keys, monitor usage, and configure access permissions
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 flex items-center space-x-2"
            >
              <Plus size={16} />
              <span>Create API Key</span>
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Statistics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatisticCard
            title="Total API Keys"
            value={stats.totalKeys}
            icon={<Key size={20} />}
            color="blue"
          />
          <StatisticCard
            title="Active Keys"
            value={stats.activeKeys}
            icon={<CheckCircle size={20} />}
            trend={{ value: 12, isPositive: true }}
            color="green"
          />
          <StatisticCard
            title="Total Requests"
            value={stats.totalRequests.toLocaleString()}
            icon={<BarChart3 size={20} />}
            trend={{ value: 25, isPositive: true }}
            color="purple"
          />
          <StatisticCard
            title="Avg Requests/Key"
            value={stats.avgRequestsPerKey}
            icon={<TrendingUp size={20} />}
            color="orange"
          />
        </div>

        {/* View Selector */}
        <div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
          <button
            onClick={() => setCurrentView("keys")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === "keys"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            API Keys
          </button>
          <button
            onClick={() => setCurrentView("docs")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === "docs"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Documentation
          </button>
          <button
            onClick={() => setCurrentView("logs")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === "logs"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            API Logs
          </button>
          <button
            onClick={() => setCurrentView("analytics")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              currentView === "analytics"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Analytics
          </button>
        </div>

        {/* Main Content */}
        {currentView === "keys" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {apiKeys.map((apiKey) => (
              <ApiKeyCard
                key={apiKey.id}
                apiKey={apiKey}
                onEdit={() => handleEditApiKey(apiKey)}
                onDelete={() => handleDeleteApiKey(apiKey.id)}
                onToggle={() => handleToggleApiKey(apiKey.id)}
              />
            ))}
          </div>
        )}

        {currentView === "docs" && (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">API Documentation</h2>
            </div>
            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-md font-medium mb-3">Authentication</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Include your API key in the Authorization header:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <code className="text-sm">
                    Authorization: Bearer YOUR_API_KEY
                  </code>
                </div>
              </div>

              <div>
                <h3 className="text-md font-medium mb-3">Base URL</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <code className="text-sm">
                    https://api.knowledgegraph.com/v1
                  </code>
                </div>
              </div>

              <div>
                <h3 className="text-md font-medium mb-3">Endpoints</h3>
                <div className="space-y-4">
                  <div className="border rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        GET
                      </span>
                      <code className="text-sm">/api/v1/entities</code>
                    </div>
                    <p className="text-sm text-gray-600">
                      Retrieve entities from the knowledge graph
                    </p>
                  </div>

                  <div className="border rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        POST
                      </span>
                      <code className="text-sm">/api/v1/entities</code>
                    </div>
                    <p className="text-sm text-gray-600">
                      Create a new entity in the knowledge graph
                    </p>
                  </div>

                  <div className="border rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        GET
                      </span>
                      <code className="text-sm">/api/v1/relationships</code>
                    </div>
                    <p className="text-sm text-gray-600">
                      Retrieve relationships between entities
                    </p>
                  </div>

                  <div className="border rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                        GET
                      </span>
                      <code className="text-sm">/api/v1/search</code>
                    </div>
                    <p className="text-sm text-gray-600">
                      Search entities and relationships
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === "logs" && (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">API Request Logs</h2>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {[
                  {
                    method: "GET",
                    endpoint: "/api/v1/entities",
                    status: 200,
                    time: "2024-01-25T15:30:00Z",
                    ip: "192.168.1.100",
                  },
                  {
                    method: "POST",
                    endpoint: "/api/v1/entities",
                    status: 201,
                    time: "2024-01-25T15:25:00Z",
                    ip: "10.0.0.50",
                  },
                  {
                    method: "GET",
                    endpoint: "/api/v1/search",
                    status: 200,
                    time: "2024-01-25T15:20:00Z",
                    ip: "172.16.0.25",
                  },
                  {
                    method: "GET",
                    endpoint: "/api/v1/relationships",
                    status: 404,
                    time: "2024-01-25T15:15:00Z",
                    ip: "203.0.113.10",
                  },
                ].map((log, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 border rounded hover:bg-gray-50"
                  >
                    <div className="flex items-center space-x-4">
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          log.method === "GET"
                            ? "bg-green-100 text-green-800"
                            : log.method === "POST"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {log.method}
                      </span>
                      <code className="text-sm">{log.endpoint}</code>
                      <span
                        className={`px-2 py-1 text-xs rounded ${
                          log.status < 300
                            ? "bg-green-100 text-green-800"
                            : log.status < 400
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                        }`}
                      >
                        {log.status}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{log.ip}</span>
                      <span>{new Date(log.time).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {currentView === "analytics" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg border shadow-sm p-6">
                <h3 className="text-lg font-semibold mb-4">Request Volume</h3>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <BarChart3 size={48} className="mx-auto mb-2" />
                    <p>Request volume chart would go here</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg border shadow-sm p-6">
                <h3 className="text-lg font-semibold mb-4">Response Times</h3>
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Clock size={48} className="mx-auto mb-2" />
                    <p>Response time metrics would go here</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">Top Endpoints</h3>
              <div className="space-y-3">
                {[
                  {
                    endpoint: "/api/v1/entities",
                    requests: 1250,
                    percentage: 45,
                  },
                  { endpoint: "/api/v1/search", requests: 892, percentage: 32 },
                  {
                    endpoint: "/api/v1/relationships",
                    requests: 456,
                    percentage: 16,
                  },
                  {
                    endpoint: "/api/v1/visualizations",
                    requests: 189,
                    percentage: 7,
                  },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3">
                      <code className="text-sm">{item.endpoint}</code>
                      <span className="text-sm text-gray-500">
                        {item.requests} requests
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-8">
                        {item.percentage}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit API Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  {editingKey ? "Edit API Key" : "Create New API Key"}
                </h2>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingKey(null);
                  }}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div className="p-6">
              <AppForm
                fields={apiKeyFormFields}
                schema={CreateApiKeySchema}
                onSubmit={handleCreateApiKey}
                submitButtonText={
                  editingKey ? "Update API Key" : "Create API Key"
                }
                initialData={editingKey || {}}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main Component that combines both pages
const UserActivitiesAndApiAccess = () => {
  const [activePage, setActivePage] = useState("activities"); // 'activities' or 'api'

  return (
    <div>
      {/* Page Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-3">
          <div className="flex space-x-1">
            <button
              onClick={() => setActivePage("activities")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activePage === "activities"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              User Activities
            </button>
            <button
              onClick={() => setActivePage("api")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activePage === "api"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              API Access
            </button>
          </div>
        </div>
      </div>

      {/* Page Content */}
      {activePage === "activities" ? <UserActivitiesPage /> : <ApiAccessPage />}
    </div>
  );
};

export default UserActivitiesAndApiAccess;
