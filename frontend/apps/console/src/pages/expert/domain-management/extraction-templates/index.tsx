import React, { useState } from "react";
import {
  FileText,
  Settings,
  Play,
  Eye,
  Edit,
  Trash2,
  Copy,
} from "lucide-react";
import * as z from "zod";
import {
  ActionButton,
  AppForm,
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  DataTable,
  Dialog,
  FieldConfig,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SimpleColumnDef,
  StatisticCard,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
} from "@vbkg/ui";

// Types based on API schemas
interface ExtractionTemplate {
  id: string;
  name: string;
  description?: string;
  domain: string;
  entity_types: number[];
  relationship_types: number[];
  prompt_template: string;
  extraction_config: Record<string, any>;
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface Domain {
  id: number;
  name: string;
  display_name: string;
  color: string;
  is_active: boolean;
}

interface EntityType {
  id: number;
  name: string;
  display_name: string;
  color: string;
  is_active: boolean;
}

interface RelationshipType {
  id: number;
  name: string;
  display_name: string;
  color: string;
  is_active: boolean;
}

// Mock data
const mockDomains: Domain[] = [
  {
    id: 1,
    name: "financial",
    display_name: "Financial Services",
    color: "#3B82F6",
    is_active: true,
  },
  {
    id: 2,
    name: "legal",
    display_name: "Legal & Compliance",
    color: "#10B981",
    is_active: true,
  },
  {
    id: 3,
    name: "business",
    display_name: "Business Operations",
    color: "#F59E0B",
    is_active: true,
  },
  {
    id: 4,
    name: "general",
    display_name: "General Domain",
    color: "#6366F1",
    is_active: true,
  },
];

const mockEntityTypes: EntityType[] = [
  {
    id: 1,
    name: "organization",
    display_name: "Organization",
    color: "#3B82F6",
    is_active: true,
  },
  {
    id: 2,
    name: "person",
    display_name: "Person",
    color: "#10B981",
    is_active: true,
  },
  {
    id: 3,
    name: "financial_instrument",
    display_name: "Financial Instrument",
    color: "#F59E0B",
    is_active: true,
  },
  {
    id: 4,
    name: "currency",
    display_name: "Currency",
    color: "#EF4444",
    is_active: true,
  },
  {
    id: 5,
    name: "location",
    display_name: "Location",
    color: "#8B5CF6",
    is_active: true,
  },
  {
    id: 6,
    name: "contract",
    display_name: "Contract",
    color: "#F97316",
    is_active: true,
  },
];

const mockRelationshipTypes: RelationshipType[] = [
  {
    id: 1,
    name: "owns",
    display_name: "Owns",
    color: "#3B82F6",
    is_active: true,
  },
  {
    id: 2,
    name: "works_for",
    display_name: "Works For",
    color: "#10B981",
    is_active: true,
  },
  {
    id: 3,
    name: "located_in",
    display_name: "Located In",
    color: "#8B5CF6",
    is_active: true,
  },
  {
    id: 4,
    name: "party_to",
    display_name: "Party To",
    color: "#F97316",
    is_active: true,
  },
];

const mockExtractionTemplates: ExtractionTemplate[] = [
  {
    id: "1",
    name: "Financial Document Extraction",
    description: "Extract financial entities and relationships from documents",
    domain: "financial",
    entity_types: [1, 2, 3, 4],
    relationship_types: [1, 2],
    prompt_template: `Extract the following types of entities and relationships from this financial document:

**Entities to extract:**
- Organizations (companies, banks, financial institutions)
- Persons (executives, traders, customers)
- Financial Instruments (stocks, bonds, derivatives)
- Currencies (USD, EUR, etc.)

**Relationships to extract:**
- Ownership relationships
- Employment relationships

**Instructions:**
1. Identify all mentioned entities with their types
2. Extract relationships between entities
3. Provide confidence scores for each extraction
4. Include context sentences for verification

**Output format:**
Return JSON with entities and relationships arrays.`,
    extraction_config: {
      max_entities: 50,
      confidence_threshold: 0.7,
      include_context: true,
      max_context_length: 200,
    },
    is_active: true,
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-01-15T10:00:00Z",
  },
  {
    id: "2",
    name: "Legal Contract Analysis",
    description: "Extract legal entities and contractual relationships",
    domain: "legal",
    entity_types: [1, 2, 6, 5],
    relationship_types: [4],
    prompt_template: `Analyze this legal document and extract:

**Entities:**
- Organizations (law firms, companies, government agencies)
- Persons (lawyers, parties, witnesses)
- Contracts (agreements, terms, conditions)
- Locations (jurisdictions, addresses)

**Relationships:**
- Party-to-contract relationships

**Focus on:**
- Legal terminology and formal language
- Contract terms and conditions
- Parties' roles and responsibilities

Return structured JSON with high confidence extractions.`,
    extraction_config: {
      max_entities: 30,
      confidence_threshold: 0.8,
      include_context: true,
      legal_terminology_boost: true,
    },
    is_active: true,
    created_at: "2024-01-16T10:00:00Z",
    updated_at: "2024-01-16T10:00:00Z",
  },
  {
    id: "3",
    name: "Business Operations Extract",
    description: "General business entity and relationship extraction",
    domain: "business",
    entity_types: [1, 2, 5],
    relationship_types: [2, 3],
    prompt_template: `Extract business-related information from this document:

**Target Entities:**
- Organizations (companies, departments, teams)
- Persons (employees, managers, customers)
- Locations (offices, regions, markets)

**Target Relationships:**
- Employment relationships
- Location relationships

**Extraction Guidelines:**
- Focus on operational aspects
- Include organizational hierarchy
- Identify business processes and workflows

Provide clear, actionable extractions.`,
    extraction_config: {
      max_entities: 40,
      confidence_threshold: 0.75,
      include_hierarchy: true,
      business_context: true,
    },
    is_active: true,
    created_at: "2024-01-17T10:00:00Z",
    updated_at: "2024-01-17T10:00:00Z",
  },
];

// Form schema
const extractionTemplateSchema = z.object({
  name: z.string().min(1, "Tên template không được để trống").max(100),
  description: z.string().optional(),
  domain: z.string().min(1, "Domain không được để trống"),
  entity_types: z.array(z.number()).min(1, "Phải chọn ít nhất 1 entity type"),
  relationship_types: z
    .array(z.number())
    .min(1, "Phải chọn ít nhất 1 relationship type"),
  prompt_template: z.string().min(1, "Prompt template không được để trống"),
  extraction_config: z.record(z.any()).default({}),
  is_active: z.boolean().default(true),
});

const ExtractionTemplatesManagementPage: React.FC = () => {
  const [extractionTemplates, setExtractionTemplates] = useState<
    ExtractionTemplate[]
  >(mockExtractionTemplates);
  const [domains] = useState<Domain[]>(mockDomains);
  const [entityTypes] = useState<EntityType[]>(mockEntityTypes);
  const [relationshipTypes] = useState<RelationshipType[]>(
    mockRelationshipTypes,
  );
  const [selectedTemplate, setSelectedTemplate] =
    useState<ExtractionTemplate | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedDomainFilter, setSelectedDomainFilter] =
    useState<string>("all");

  // Helper functions
  const getDomainName = (domainKey: string) => {
    const domain = domains.find((d) => d.name === domainKey);
    return domain ? domain.display_name : domainKey;
  };

  const getEntityTypeName = (id: number) => {
    const entityType = entityTypes.find((et) => et.id === id);
    return entityType ? entityType.display_name : `Entity ${id}`;
  };

  const getRelationshipTypeName = (id: number) => {
    const relationshipType = relationshipTypes.find((rt) => rt.id === id);
    return relationshipType
      ? relationshipType.display_name
      : `Relationship ${id}`;
  };

  // Form fields configuration
  const getFormFields = (): FieldConfig[] => [
    {
      name: "name",
      label: "Tên Template",
      type: "text",
      placeholder: "VD: Financial Document Extraction",
      required: true,
      description: "Tên mô tả cho extraction template",
    },
    {
      name: "description",
      label: "Mô Tả",
      type: "textarea",
      placeholder: "Mô tả chi tiết về template này...",
      description: "Mô tả về mục đích và cách sử dụng template",
    },
    {
      name: "domain",
      label: "Domain",
      type: "select",
      options: domains
        .filter((d) => d.is_active)
        .map((domain) => ({
          label: domain.display_name,
          value: domain.name,
        })),
      required: true,
      description: "Chọn domain mà template này áp dụng",
    },
    {
      name: "entity_types",
      label: "Entity Types",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {entityTypes
            .filter((et) => et.is_active)
            .map((entityType) => (
              <div key={entityType.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`entity-${entityType.id}`}
                  checked={value?.includes(entityType.id) || false}
                  onChange={(e) => {
                    const currentValue = value || [];
                    if (e.target.checked) {
                      onChange([...currentValue, entityType.id]);
                    } else {
                      onChange(
                        currentValue.filter(
                          (id: number) => id !== entityType.id,
                        ),
                      );
                    }
                  }}
                  className="rounded border-gray-300"
                />
                <label
                  htmlFor={`entity-${entityType.id}`}
                  className="flex items-center space-x-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: entityType.color }}
                  />
                  <span>{entityType.display_name}</span>
                </label>
              </div>
            ))}
        </div>
      ),
      required: true,
      description: "Chọn các entity type sẽ được trích xuất",
    },
    {
      name: "relationship_types",
      label: "Relationship Types",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <div className="space-y-2 max-h-40 overflow-y-auto">
          {relationshipTypes
            .filter((rt) => rt.is_active)
            .map((relationshipType) => (
              <div
                key={relationshipType.id}
                className="flex items-center space-x-2"
              >
                <input
                  type="checkbox"
                  id={`relationship-${relationshipType.id}`}
                  checked={value?.includes(relationshipType.id) || false}
                  onChange={(e) => {
                    const currentValue = value || [];
                    if (e.target.checked) {
                      onChange([...currentValue, relationshipType.id]);
                    } else {
                      onChange(
                        currentValue.filter(
                          (id: number) => id !== relationshipType.id,
                        ),
                      );
                    }
                  }}
                  className="rounded border-gray-300"
                />
                <label
                  htmlFor={`relationship-${relationshipType.id}`}
                  className="flex items-center space-x-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: relationshipType.color }}
                  />
                  <span>{relationshipType.display_name}</span>
                </label>
              </div>
            ))}
        </div>
      ),
      required: true,
      description: "Chọn các relationship type sẽ được trích xuất",
    },
    {
      name: "prompt_template",
      label: "Prompt Template",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <Textarea
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nhập prompt template cho AI extraction..."
          rows={10}
          className="font-mono text-sm"
        />
      ),
      required: true,
      description: "Template prompt sẽ được gửi cho AI model để trích xuất",
    },
    {
      name: "extraction_config",
      label: "Cấu Hình Trích Xuất",
      type: "object",
      fields: [
        {
          name: "max_entities",
          label: "Max Entities",
          type: "number",
          defaultValue: 50,
          wrapperClassName: "col-span-6",
        },
        {
          name: "confidence_threshold",
          label: "Confidence Threshold",
          type: "number",
          defaultValue: 0.7,
          wrapperClassName: "col-span-6",
        },
        {
          name: "include_context",
          label: "Include Context",
          type: "switch",
          defaultValue: true,
          wrapperClassName: "col-span-6",
        },
        {
          name: "max_context_length",
          label: "Max Context Length",
          type: "number",
          defaultValue: 200,
          wrapperClassName: "col-span-6",
        },
      ],
      description: "Các tham số cấu hình cho quá trình trích xuất",
    },
    {
      name: "is_active",
      label: "Kích Hoạt",
      type: "switch",
      defaultValue: true,
      description: "Template có đang được sử dụng không",
    },
  ];

  // Filtered templates based on domain filter
  const filteredTemplates =
    selectedDomainFilter === "all"
      ? extractionTemplates
      : extractionTemplates.filter(
          (template) => template.domain === selectedDomainFilter,
        );

  // Table columns configuration
  const columns: SimpleColumnDef<ExtractionTemplate, any>[] = [
    {
      accessorKey: "name",
      header: "Tên Template",
      cell: (row) => (
        <div>
          <div className="font-medium">{row?.name}</div>
          <div className="text-sm text-gray-500">{row?.description}</div>
        </div>
      ),
    },
    {
      accessorKey: "domain",
      header: "Domain",
      cell: (row) => {
        const domain = domains.find((d) => d.name === row?.domain);
        return (
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: domain?.color || "#6366F1" }}
            />
            <span>{getDomainName(row?.domain || "")}</span>
          </div>
        );
      },
    },
    {
      accessorKey: "entity_types",
      header: "Entity Types",
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {row?.entity_types?.slice(0, 3).map((id) => (
            <Badge key={id} variant="outline" className="text-xs">
              {getEntityTypeName(id)}
            </Badge>
          ))}
          {row?.entity_types && row.entity_types.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{row.entity_types.length - 3} khác
            </Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: "relationship_types",
      header: "Relationship Types",
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {row?.relationship_types?.slice(0, 3).map((id) => (
            <Badge key={id} variant="outline" className="text-xs">
              {getRelationshipTypeName(id)}
            </Badge>
          ))}
          {row?.relationship_types && row.relationship_types.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{row.relationship_types.length - 3} khác
            </Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Trạng Thái",
      cell: (row) => (
        <Badge variant={row?.is_active ? "default" : "secondary"}>
          {row?.is_active ? "Hoạt động" : "Tạm dừng"}
        </Badge>
      ),
    },
    {
      accessorKey: "updated_at",
      header: "Cập Nhật",
      cell: (row) =>
        new Date(row?.updated_at || "").toLocaleDateString("vi-VN"),
    },
  ];

  // Action buttons for table
  const actionButtons: ActionButton<ExtractionTemplate>[] = [
    {
      label: "Xem",
      icon: <Eye size={16} />,
      onClick: (template) => {
        setSelectedTemplate(template);
        setIsViewModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Test",
      icon: <Play size={16} />,
      onClick: (template) => {
        setSelectedTemplate(template);
        setIsTestModalOpen(true);
      },
      variant: "ghost",
      className: "text-green-600 hover:text-green-800",
    },
    {
      label: "Sửa",
      icon: <Edit size={16} />,
      onClick: (template) => {
        setSelectedTemplate(template);
        setIsEditModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Sao chép",
      icon: <Copy size={16} />,
      onClick: (template) => {
        const newTemplate: ExtractionTemplate = {
          ...template,
          id: Date.now().toString(),
          name: `${template.name} (Copy)`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setExtractionTemplates((prev) => [...prev, newTemplate]);
      },
      variant: "ghost",
    },
    {
      label: "Xóa",
      icon: <Trash2 size={16} />,
      onClick: (template) => {
        if (confirm(`Bạn có chắc chắn muốn xóa template "${template.name}"?`)) {
          setExtractionTemplates((prev) =>
            prev.filter((t) => t.id !== template.id),
          );
        }
      },
      variant: "ghost",
      className: "text-red-600 hover:text-red-800",
    },
  ];

  const handleCreateTemplate = (
    data: z.infer<typeof extractionTemplateSchema>,
  ) => {
    setLoading(true);
    setTimeout(() => {
      const newTemplate: ExtractionTemplate = {
        id: Date.now().toString(),
        ...data,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setExtractionTemplates((prev) => [...prev, newTemplate]);
      setIsCreateModalOpen(false);
      setLoading(false);
    }, 1000);
  };

  const handleUpdateTemplate = (
    data: z.infer<typeof extractionTemplateSchema>,
  ) => {
    if (!selectedTemplate) return;

    setLoading(true);
    setTimeout(() => {
      setExtractionTemplates((prev) =>
        prev.map((t) =>
          t.id === selectedTemplate.id
            ? { ...t, ...data, updated_at: new Date().toISOString() }
            : t,
        ),
      );
      setIsEditModalOpen(false);
      setSelectedTemplate(null);
      setLoading(false);
    }, 1000);
  };

  // Statistics
  const stats = {
    totalTemplates: extractionTemplates.length,
    activeTemplates: extractionTemplates.filter((t) => t.is_active).length,
    domainTemplates: domains.reduce(
      (acc, domain) => {
        acc[domain.name] = extractionTemplates.filter(
          (t) => t.domain === domain.name,
        ).length;
        return acc;
      },
      {} as Record<string, number>,
    ),
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Extraction Templates
          </h1>
          <p className="text-gray-600 mt-1">
            Quản lý các template để trích xuất knowledge từ documents
          </p>
        </div>
        <Dialog
          title="Tạo Extraction Template Mới"
          description="Tạo một template mới để trích xuất knowledge từ documents."
          open={isCreateModalOpen}
          onOpenChange={setIsCreateModalOpen}
        >
          <AppForm
            fields={getFormFields()}
            schema={extractionTemplateSchema}
            onSubmit={handleCreateTemplate}
            submitButtonText="Tạo Template"
            isLoading={loading}
          />
        </Dialog>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatisticCard
          title="Tổng Templates"
          value={stats.totalTemplates}
          icon={<FileText size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Đang Hoạt Động"
          value={stats.activeTemplates}
          icon={<Settings size={20} />}
          color="green"
        />
        <StatisticCard
          title="Financial Templates"
          value={stats.domainTemplates.financial || 0}
          icon={<FileText size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Legal Templates"
          value={stats.domainTemplates.legal || 0}
          icon={<FileText size={20} />}
          color="orange"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium">Lọc theo Domain:</label>
              <Select
                value={selectedDomainFilter}
                onValueChange={setSelectedDomainFilter}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả Domains</SelectItem>
                  {domains.map((domain) => (
                    <SelectItem key={domain.id} value={domain.name}>
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: domain.color }}
                        />
                        <span>{domain.display_name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="templates" className="space-y-4">
        <TabsList>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="usage-stats">Usage Statistics</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                Extraction Templates
                {selectedDomainFilter !== "all" && (
                  <span className="text-base font-normal text-gray-500">
                    {" "}
                    trong domain "{getDomainName(selectedDomainFilter)}"
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={filteredTemplates}
                columns={columns}
                actionsOptions={{
                  show: true,
                  actions: actionButtons,
                  showInDropdown: true,
                  dropdownLabel: "Hành động",
                }}
                showGlobalFilter={true}
                showColumnFilters={true}
                showPagination={true}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage-stats" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Templates by Domain</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {domains.map((domain) => (
                    <div
                      key={domain.id}
                      className="flex justify-between items-center p-3 border rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: domain.color }}
                        />
                        <div>
                          <p className="font-medium">{domain.display_name}</p>
                          <p className="text-sm text-gray-500">{domain.name}</p>
                        </div>
                      </div>
                      <Badge variant="default">
                        {stats.domainTemplates[domain.name] || 0} templates
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Template Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 border rounded-lg">
                    <span className="font-medium">Active Templates</span>
                    <Badge variant="default">{stats.activeTemplates}</Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 border rounded-lg">
                    <span className="font-medium">Inactive Templates</span>
                    <Badge variant="secondary">
                      {stats.totalTemplates - stats.activeTemplates}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 border rounded-lg">
                    <span className="font-medium">Total Templates</span>
                    <Badge variant="outline">{stats.totalTemplates}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* View Template Modal */}
      <Dialog
        title="Chi Tiết Template"
        description="Xem chi tiết về template trích xuất knowledge."
        open={isViewModalOpen}
        onOpenChange={setIsViewModalOpen}
      >
        {selectedTemplate && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tên Template
                </label>
                <p className="mt-1 font-medium">{selectedTemplate.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Domain
                </label>
                <p className="mt-1">{getDomainName(selectedTemplate.domain)}</p>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Mô Tả</label>
              <p className="mt-1">
                {selectedTemplate.description || "Không có mô tả"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Entity Types
                </label>
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedTemplate.entity_types?.map((id) => (
                    <Badge key={id} variant="outline" className="text-xs">
                      {getEntityTypeName(id)}
                    </Badge>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Relationship Types
                </label>
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedTemplate.relationship_types?.map((id) => (
                    <Badge key={id} variant="outline" className="text-xs">
                      {getRelationshipTypeName(id)}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">
                Prompt Template
              </label>
              <div className="mt-2 bg-gray-100 p-4 rounded-lg">
                <pre className="text-sm whitespace-pre-wrap font-mono">
                  {selectedTemplate.prompt_template}
                </pre>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">
                Extraction Config
              </label>
              <div className="mt-2 bg-gray-100 p-4 rounded-lg">
                <pre className="text-sm">
                  {JSON.stringify(selectedTemplate.extraction_config, null, 2)}
                </pre>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Trạng Thái
                </label>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedTemplate.is_active ? "default" : "secondary"
                    }
                  >
                    {selectedTemplate.is_active ? "Hoạt động" : "Tạm dừng"}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tạo Lúc
                </label>
                <p className="mt-1 text-sm">
                  {new Date(selectedTemplate.created_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Cập Nhật
                </label>
                <p className="mt-1 text-sm">
                  {new Date(selectedTemplate.updated_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
            </div>
          </div>
        )}
      </Dialog>

      {/* Edit Template Modal */}
      <Dialog
        title="Chỉnh Sửa Template"
        description="Chỉnh sửa thông tin và cấu hình của template trích xuất knowledge."
        open={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
      >
        {selectedTemplate && (
          <AppForm
            fields={getFormFields()}
            schema={extractionTemplateSchema}
            defaultValues={selectedTemplate}
            onSubmit={handleUpdateTemplate}
            submitButtonText="Cập Nhật Template"
            isLoading={loading}
          />
        )}
      </Dialog>

      {/* Test Template Modal */}
      <Dialog
        title="Test Extraction Template"
        description="Chạy thử nghiệm với template trích xuất knowledge để kiểm tra kết quả."
        open={isTestModalOpen}
        onOpenChange={setIsTestModalOpen}
      >
        {selectedTemplate && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Template: {selectedTemplate.name}
              </label>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Test Document
              </label>
              <Textarea
                placeholder="Nhập văn bản để test extraction..."
                rows={8}
                className="mt-2"
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button onClick={() => setIsTestModalOpen(false)}>Hủy</Button>
              <Button>
                <Play size={16} className="mr-2" />
                Run Extraction
              </Button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Extraction Results
              </label>
              <div className="mt-2 bg-gray-100 p-4 rounded-lg">
                <p className="text-sm text-gray-500">
                  Kết quả extraction sẽ hiển thị ở đây sau khi chạy test...
                </p>
              </div>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
};

export default ExtractionTemplatesManagementPage;
