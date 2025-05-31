import React, { useState, useEffect, useMemo } from "react";
import {
  Search,
  TrendingUp,
  Database,
  GitBranch,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Download,
  RefreshCw,
  Settings,
  Eye,
} from "lucide-react";
import { z } from "zod";

// Import your custom components (simulated here)
const DataTable = ({
  data,
  columns,
  showGlobalFilter,
  showColumnFilters,
  showPagination,
  onRowSelectionChange,
}: any) => {
  const [filteredData, setFilteredData] = useState(data);
  const [globalFilter, setGlobalFilter] = useState("");
  const [selectedRows, setSelectedRows] = useState([]);

  useEffect(() => {
    if (globalFilter) {
      const filtered = data.filter((item: any) =>
        Object.values(item).some((value) =>
          String(value).toLowerCase().includes(globalFilter.toLowerCase()),
        ),
      );
      setFilteredData(filtered);
    } else {
      setFilteredData(data);
    }
  }, [data, globalFilter]);

  const handleRowSelection = (row: any) => {
    const newSelection = selectedRows.includes(row.id)
      ? selectedRows.filter((id) => id !== row.id)
      : [...selectedRows, row.id];
    setSelectedRows(newSelection);
    onRowSelectionChange?.(newSelection);
  };

  return (
    <div className="space-y-4">
      {showGlobalFilter && (
        <div className="flex items-center space-x-2">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Tìm kiếm..."
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
              <th className="p-2 text-left">
                <input
                  type="checkbox"
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRows(filteredData.map((item) => item.id));
                    } else {
                      setSelectedRows([]);
                    }
                  }}
                />
              </th>
              {columns.map((col, idx) => (
                <th key={idx} className="p-2 text-left font-medium">
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredData.map((row, idx) => (
              <tr
                key={idx}
                className={`border-b hover:bg-muted/50 ${selectedRows.includes(row.id) ? "bg-blue-50" : ""}`}
              >
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selectedRows.includes(row.id)}
                    onChange={() => handleRowSelection(row)}
                  />
                </td>
                {columns.map((col, colIdx) => (
                  <td key={colIdx} className="p-2">
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

const GeneralForm = ({
  fields,
  onSubmit,
  submitButtonText = "Submit",
  schema,
}) => {
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});

  const handleInputChange = (name, value) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    try {
      const validatedData = schema.parse(formData);
      onSubmit(validatedData);
      setErrors({});
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors = {};
        error.errors.forEach((err) => {
          fieldErrors[err.path[0]] = err.message;
        });
        setErrors(fieldErrors);
      }
    }
  };

  const renderField = (field) => {
    switch (field.type) {
      case "text":
      case "email":
        return (
          <input
            type={field.type}
            placeholder={field.placeholder}
            value={formData[field.name] || ""}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        );

      case "select":
        return (
          <select
            value={formData[field.name] || ""}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">{field.placeholder}</option>
            {field.options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );

      case "checkbox":
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

      case "number":
        return (
          <input
            type="number"
            placeholder={field.placeholder}
            value={formData[field.name] || ""}
            onChange={(e) =>
              handleInputChange(field.name, parseFloat(e.target.value) || 0)
            }
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            min={0}
            max={1}
            step={0.1}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {fields.map((field) => (
        <div key={field.name} className="space-y-2">
          {field.type !== "checkbox" && (
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

const StatisticCard = ({
  title,
  value,
  icon,
  trend,
  color = "blue",
  onClick,
}) => {
  const colorClasses = {
    blue: "bg-blue-500 text-white",
    green: "bg-green-500 text-white",
    red: "bg-red-500 text-white",
    yellow: "bg-yellow-500 text-white",
    purple: "bg-purple-500 text-white",
  };

  return (
    <div
      className={`bg-white rounded-lg border shadow-sm p-6 ${onClick ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          {trend && (
            <p
              className={`text-sm ${trend.isPositive ? "text-green-600" : "text-red-600"}`}
            >
              {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>{icon}</div>
      </div>
    </div>
  );
};

const ResultCard = ({
  id,
  type,
  name,
  properties,
  relations = [],
  onViewDetails,
  highlightTerms = [],
}) => {
  const [expanded, setExpanded] = useState(false);

  const highlightText = (text) => {
    if (highlightTerms.length === 0) return text;

    const regex = new RegExp(`(${highlightTerms.join("|")})`, "gi");
    const parts = text.toString().split(regex);

    return (
      <>
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark key={i} className="bg-yellow-200">
              {part}
            </mark>
          ) : (
            part
          ),
        )}
      </>
    );
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      <div className="p-4 border-b">
        <div className="flex justify-between items-start">
          <div>
            <span className="inline-block px-2 py-1 text-xs font-medium rounded bg-blue-100 text-blue-800 mb-2">
              {highlightText(type)}
            </span>
            <h3 className="text-lg font-medium">{highlightText(name)}</h3>
          </div>
          <div className="flex items-center space-x-1">
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(id)}
                className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
              >
                <ExternalLink size={16} />
              </button>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            >
              {expanded ? "↑" : "↓"}
            </button>
          </div>
        </div>
      </div>

      <div className="p-4">
        <h4 className="text-sm font-medium text-gray-500 mb-2">Properties</h4>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {Object.entries(properties).map(([key, value]) => (
            <div key={key} className="bg-gray-50 p-2 rounded">
              <span className="text-xs font-medium text-gray-500 block">
                {key}
              </span>
              <span className="text-sm">{highlightText(String(value))}</span>
            </div>
          ))}
        </div>

        {expanded && relations.length > 0 && (
          <>
            <h4 className="text-sm font-medium text-gray-500 mb-2">
              Relations
            </h4>
            <ul className="space-y-2">
              {relations.map((relation, index) => (
                <li
                  key={index}
                  className="flex items-center space-x-2 text-sm p-2 rounded-md hover:bg-gray-100"
                >
                  <span className="px-2 py-1 text-xs rounded bg-purple-100 text-purple-800">
                    {highlightText(relation.type)}
                  </span>
                  <span className="text-gray-500">→</span>
                  <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">
                    {relation.targetType}
                  </span>
                  <span className="font-medium">
                    {highlightText(relation.target)}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}

        {!expanded && relations.length > 0 && (
          <button
            onClick={() => setExpanded(true)}
            className="text-sm text-blue-600 hover:underline flex items-center"
          >
            ↓ Show {relations.length} relations
          </button>
        )}
      </div>
    </div>
  );
};

// Search Schema
const SearchKGEntitiesSchema = z.object({
  query: z.string().min(1, "Search query is required"),
  entity_type: z.string().optional(),
  limit: z.number().min(1).max(100).default(20),
  min_confidence: z.number().min(0).max(1).default(0.5),
  verified_only: z.boolean().default(false),
  semantic_search: z.boolean().default(false),
});

// Mock Data
const mockEntities = [
  {
    id: "1",
    entity_text: "Apple Inc.",
    entity_type: "Company",
    properties: {
      sector: "Technology",
      founded: "1976",
      revenue: "$394.3B",
      employees: "164,000",
      headquarters: "Cupertino, CA",
    },
    confidence: 0.95,
    is_verified: true,
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-01-20T15:30:00Z",
  },
  {
    id: "2",
    entity_text: "Tim Cook",
    entity_type: "Person",
    properties: {
      position: "CEO",
      age: "63",
      nationality: "American",
      education: "Auburn University",
      tenure: "2011-present",
    },
    confidence: 0.92,
    is_verified: true,
    created_at: "2024-01-16T11:20:00Z",
    updated_at: "2024-01-21T09:15:00Z",
  },
  {
    id: "3",
    entity_text: "iPhone 15",
    entity_type: "Product",
    properties: {
      category: "Smartphone",
      launch_year: "2023",
      price_range: "$799-$1199",
      display: "6.1 inch",
      storage: "128GB-1TB",
    },
    confidence: 0.98,
    is_verified: true,
    created_at: "2024-01-17T14:45:00Z",
    updated_at: "2024-01-22T16:20:00Z",
  },
  {
    id: "4",
    entity_text: "Microsoft Corporation",
    entity_type: "Company",
    properties: {
      sector: "Technology",
      founded: "1975",
      revenue: "$211.9B",
      employees: "221,000",
      headquarters: "Redmond, WA",
    },
    confidence: 0.94,
    is_verified: true,
    created_at: "2024-01-18T08:30:00Z",
    updated_at: "2024-01-23T12:45:00Z",
  },
  {
    id: "5",
    entity_text: "ChatGPT",
    entity_type: "Product",
    properties: {
      category: "AI Software",
      launch_year: "2022",
      developer: "OpenAI",
      users: "100M+",
      type: "Language Model",
    },
    confidence: 0.89,
    is_verified: false,
    created_at: "2024-01-19T13:15:00Z",
    updated_at: "2024-01-24T10:30:00Z",
  },
];

const mockRelationships = [
  {
    id: "1",
    relationship_type: "CEO_OF",
    source: "Tim Cook",
    target: "Apple Inc.",
    properties: { start_date: "2011-08-24", salary: "$3M" },
    confidence: 0.98,
  },
  {
    id: "2",
    relationship_type: "PRODUCES",
    source: "Apple Inc.",
    target: "iPhone 15",
    properties: { revenue_contribution: "50%", units_sold: "20M+" },
    confidence: 0.95,
  },
  {
    id: "3",
    relationship_type: "COMPETES_WITH",
    source: "Apple Inc.",
    target: "Microsoft Corporation",
    properties: { market: "Technology", intensity: "High" },
    confidence: 0.87,
  },
];

// Main Knowledge Search Component
const KnowledgeSearchPage = () => {
  const [searchResults, setSearchResults] = useState({
    entities: [],
    relationships: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedResults, setSelectedResults] = useState([]);
  const [currentView, setCurrentView] = useState("overview"); // 'overview', 'entities', 'relationships'
  const [stats, setStats] = useState({
    totalEntities: mockEntities.length,
    totalRelationships: mockRelationships.length,
    verifiedEntities: mockEntities.filter((e) => e.is_verified).length,
    avgConfidence: (
      mockEntities.reduce((sum, e) => sum + e.confidence, 0) /
      mockEntities.length
    ).toFixed(2),
  });

  // Search form fields
  const searchFormFields = [
    {
      name: "query",
      type: "text",
      label: "Search Query",
      placeholder: "Enter search terms...",
      required: true,
      description: "Search across entities and relationships",
    },
    {
      name: "entity_type",
      type: "select",
      label: "Entity Type",
      placeholder: "All types",
      options: [
        { value: "Company", label: "Company" },
        { value: "Person", label: "Person" },
        { value: "Product", label: "Product" },
        { value: "Location", label: "Location" },
      ],
    },
    {
      name: "min_confidence",
      type: "number",
      label: "Minimum Confidence",
      placeholder: "0.5",
      description: "Filter results by confidence score (0-1)",
    },
    {
      name: "limit",
      type: "number",
      label: "Result Limit",
      placeholder: "20",
      description: "Maximum number of results to return",
    },
    {
      name: "verified_only",
      type: "checkbox",
      label: "Verified entities only",
    },
    {
      name: "semantic_search",
      type: "checkbox",
      label: "Enable semantic search",
    },
  ];

  // Entity table columns
  const entityColumns = [
    {
      header: "Entity",
      accessorKey: "entity_text",
      cell: (row) => (
        <div>
          <div className="font-medium">{row.entity_text}</div>
          <div className="text-sm text-gray-500">{row.entity_type}</div>
        </div>
      ),
    },
    {
      header: "Confidence",
      accessorKey: "confidence",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <div className="w-16 bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full"
              style={{ width: `${row.confidence * 100}%` }}
            />
          </div>
          <span className="text-sm">{(row.confidence * 100).toFixed(1)}%</span>
        </div>
      ),
    },
    {
      header: "Status",
      accessorKey: "is_verified",
      cell: (row) => (
        <div className="flex items-center space-x-1">
          {row.is_verified ? (
            <>
              <CheckCircle size={16} className="text-green-500" />
              <span className="text-sm text-green-700">Verified</span>
            </>
          ) : (
            <>
              <AlertCircle size={16} className="text-yellow-500" />
              <span className="text-sm text-yellow-700">Pending</span>
            </>
          )}
        </div>
      ),
    },
    {
      header: "Properties",
      accessorKey: "properties",
      cell: (row) => (
        <div className="text-sm text-gray-600">
          {Object.keys(row.properties || {}).length} properties
        </div>
      ),
    },
    {
      header: "Actions",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <button className="p-1 hover:bg-gray-100 rounded">
            <Eye size={16} />
          </button>
          <button className="p-1 hover:bg-gray-100 rounded">
            <ExternalLink size={16} />
          </button>
        </div>
      ),
    },
  ];

  // Handle search
  const handleSearch = (searchData) => {
    setIsLoading(true);
    setSearchQuery(searchData.query);

    // Simulate API call
    setTimeout(() => {
      let filteredEntities = mockEntities;
      let filteredRelationships = mockRelationships;

      // Apply filters
      if (searchData.query) {
        filteredEntities = filteredEntities.filter(
          (entity) =>
            entity.entity_text
              .toLowerCase()
              .includes(searchData.query.toLowerCase()) ||
            entity.entity_type
              .toLowerCase()
              .includes(searchData.query.toLowerCase()) ||
            Object.values(entity.properties).some((prop) =>
              String(prop)
                .toLowerCase()
                .includes(searchData.query.toLowerCase()),
            ),
        );

        filteredRelationships = filteredRelationships.filter(
          (rel) =>
            rel.relationship_type
              .toLowerCase()
              .includes(searchData.query.toLowerCase()) ||
            rel.source.toLowerCase().includes(searchData.query.toLowerCase()) ||
            rel.target.toLowerCase().includes(searchData.query.toLowerCase()),
        );
      }

      if (searchData.entity_type) {
        filteredEntities = filteredEntities.filter(
          (entity) => entity.entity_type === searchData.entity_type,
        );
      }

      if (searchData.min_confidence) {
        filteredEntities = filteredEntities.filter(
          (entity) => entity.confidence >= searchData.min_confidence,
        );
      }

      if (searchData.verified_only) {
        filteredEntities = filteredEntities.filter(
          (entity) => entity.is_verified,
        );
      }

      if (searchData.limit) {
        filteredEntities = filteredEntities.slice(0, searchData.limit);
        filteredRelationships = filteredRelationships.slice(
          0,
          searchData.limit,
        );
      }

      setSearchResults({
        entities: filteredEntities,
        relationships: filteredRelationships,
      });
      setIsLoading(false);
    }, 1000);
  };

  const entityRelations = useMemo(() => {
    return searchResults.entities.map((entity) => ({
      ...entity,
      relations: mockRelationships
        .filter(
          (rel) =>
            rel.source === entity.entity_text ||
            rel.target === entity.entity_text,
        )
        .map((rel) => ({
          type: rel.relationship_type,
          target: rel.source === entity.entity_text ? rel.target : rel.source,
          targetType: rel.source === entity.entity_text ? "Entity" : "Entity",
        })),
    }));
  }, [searchResults.entities]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Knowledge Search
            </h1>
            <p className="text-gray-600 mt-1">
              Search and explore entities and relationships in the knowledge
              graph
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Download size={16} className="mr-2" />
              Export Results
            </button>
            <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
              <Settings size={16} className="mr-2" />
              Advanced
            </button>
          </div>
        </div>

        {/* Statistics Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatisticCard
            title="Total Entities"
            value={stats.totalEntities}
            icon={<Database size={20} />}
            trend={{ value: 12, isPositive: true }}
            color="blue"
            onClick={() => setCurrentView("entities")}
          />
          <StatisticCard
            title="Total Relationships"
            value={stats.totalRelationships}
            icon={<GitBranch size={20} />}
            trend={{ value: 8, isPositive: true }}
            color="green"
            onClick={() => setCurrentView("relationships")}
          />
          <StatisticCard
            title="Verified Entities"
            value={stats.verifiedEntities}
            icon={<CheckCircle size={20} />}
            color="purple"
          />
          <StatisticCard
            title="Avg Confidence"
            value={`${(stats.avgConfidence * 100).toFixed(0)}%`}
            icon={<TrendingUp size={20} />}
            color="yellow"
          />
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Search size={20} className="text-gray-400" />
            <h2 className="text-lg font-semibold">Search Knowledge Graph</h2>
          </div>

          <GeneralForm
            fields={searchFormFields}
            schema={SearchKGEntitiesSchema}
            onSubmit={handleSearch}
            submitButtonText={isLoading ? "Searching..." : "Search"}
          />
        </div>

        {/* View Toggle */}
        {(searchResults.entities.length > 0 ||
          searchResults.relationships.length > 0) && (
          <div className="flex items-center space-x-1 bg-white rounded-lg border shadow-sm p-1">
            <button
              onClick={() => setCurrentView("overview")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                currentView === "overview"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setCurrentView("entities")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                currentView === "entities"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Entities ({searchResults.entities.length})
            </button>
            <button
              onClick={() => setCurrentView("relationships")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                currentView === "relationships"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Relationships ({searchResults.relationships.length})
            </button>
          </div>
        )}

        {/* Search Results */}
        {currentView === "overview" && searchResults.entities.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {entityRelations.map((entity) => (
              <ResultCard
                key={entity.id}
                id={entity.id}
                type={entity.entity_type}
                name={entity.entity_text}
                properties={entity.properties}
                relations={entity.relations}
                onViewDetails={(id) => console.log("View details:", id)}
                highlightTerms={searchQuery ? [searchQuery] : []}
              />
            ))}
          </div>
        )}

        {currentView === "entities" && (
          <div className="bg-white rounded-lg border shadow-sm">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Entity Results</h2>
                <span className="text-sm text-gray-500">
                  {searchResults.entities.length} entities found
                </span>
              </div>
            </div>
            <div className="p-6">
              <DataTable
                data={searchResults.entities}
                columns={entityColumns}
                showGlobalFilter={true}
                showColumnFilters={true}
                showPagination={true}
                onRowSelectionChange={setSelectedResults}
              />
            </div>
          </div>
        )}

        {currentView === "relationships" && (
          <div className="bg-white rounded-lg border shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Relationship Results</h2>
              <span className="text-sm text-gray-500">
                {searchResults.relationships.length} relationships found
              </span>
            </div>
            <div className="space-y-4">
              {searchResults.relationships.map((rel) => (
                <div
                  key={rel.id}
                  className="border rounded-lg p-4 hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="inline-block px-2 py-1 text-xs font-medium rounded bg-purple-100 text-purple-800">
                        {rel.relationship_type}
                      </span>
                      <div className="mt-2 text-sm">
                        <span className="font-medium">{rel.source}</span>
                        <span className="mx-2 text-gray-400">→</span>
                        <span className="font-medium">{rel.target}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        Confidence: {(rel.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <button className="p-2 hover:bg-gray-100 rounded">
                      <ExternalLink size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-flex items-center space-x-2">
              <RefreshCw size={20} className="animate-spin" />
              <span>Searching knowledge graph...</span>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading &&
          searchResults.entities.length === 0 &&
          searchResults.relationships.length === 0 &&
          searchQuery && (
            <div className="text-center py-12">
              <Search size={48} className="mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No results found
              </h3>
              <p className="text-gray-600">
                Try adjusting your search terms or filters to find what you're
                looking for.
              </p>
            </div>
          )}
      </div>
    </div>
  );
};

export default KnowledgeSearchPage;
