import React, { useState } from "react";
import {
  GitBranch,
  ArrowRight,
  Eye,
  Edit,
  Trash2,
  Link,
  CheckCircle,
} from "lucide-react";
import * as z from "zod";
import {
  ActionButton,
  AppForm,
  Badge,
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
} from "@/components";
import { useDomains, useRelationshipTypes } from "@vbkg/api-client";

// Types based on API schemas
interface RelationshipType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  source_entity_types?: number[];
  target_entity_types?: number[];
  is_bidirectional: boolean;
  color: string;
  extraction_pattern?: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
  domains?: DomainMapping[];
  usage_count?: number;
}

interface DomainMapping {
  id: number;
  domain_id: number;
  domain_name: string;
  domain_display_name: string;
  is_primary: boolean;
  domain_specific_config?: Record<string, any>;
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

// Form schema
const relationshipTypeSchema = z.object({
  name: z.string().min(1, "Tên relationship type không được để trống").max(50),
  display_name: z.string().min(1, "Tên hiển thị không được để trống").max(100),
  description: z.string().optional(),
  source_entity_types: z.array(z.number()).optional(),
  target_entity_types: z.array(z.number()).optional(),
  is_bidirectional: z.boolean().default(false),
  color: z.string().default("#10B981"),
  extraction_pattern: z.string().optional(),
  examples: z.array(z.string()).default([]),
  is_active: z.boolean().default(true),
  domain_ids: z.array(z.number()).default([]),
  primary_domain_id: z.number().optional(),
  validation_rules: z.record(z.any()).optional(),
});

const RelationshipTypesManagementPage: React.FC = () => {
  const { data: relationshipTypesResponse } = useRelationshipTypes({
    limit: 200,
  });
  const { data: domainsResponse } = useDomains({});
  const domains = domainsResponse?.data || [];
  const relationshipTypes = relationshipTypesResponse?.data || [];
  const [entityTypes] = useState<EntityType[]>(mockEntityTypes);
  const [selectedRelationshipType, setSelectedRelationshipType] =
    useState<RelationshipType | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedDomainFilter, setSelectedDomainFilter] =
    useState<string>("all");

  // Form fields configuration
  const getFormFields = (isEdit: boolean = false): FieldConfig[] => [
    {
      name: "name",
      label: "Tên Relationship Type",
      type: "text",
      placeholder: "VD: owns, works_for, located_in",
      required: true,
      disabled: isEdit,
      description:
        "Tên duy nhất của relationship type (chỉ chứa chữ thường, số và dấu gạch dưới)",
    },
    {
      name: "display_name",
      label: "Tên Hiển Thị",
      type: "text",
      placeholder: "VD: Owns, Works For, Located In",
      required: true,
      description: "Tên hiển thị thân thiện với người dùng",
    },
    {
      name: "description",
      label: "Mô Tả",
      type: "textarea",
      placeholder: "Mô tả chi tiết về relationship type này...",
      description: "Mô tả về mục đích và đặc điểm của relationship type",
    },
    {
      name: "source_entity_types",
      label: "Source Entity Types",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <div className="space-y-2">
          {entityTypes
            .filter((et) => et.is_active)
            .map((entityType) => (
              <div key={entityType.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`source-${entityType.id}`}
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
                  htmlFor={`source-${entityType.id}`}
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
      description:
        "Chọn các entity type có thể làm nguồn (source) của relationship",
    },
    {
      name: "target_entity_types",
      label: "Target Entity Types",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <div className="space-y-2">
          {entityTypes
            .filter((et) => et.is_active)
            .map((entityType) => (
              <div key={entityType.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`target-${entityType.id}`}
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
                  htmlFor={`target-${entityType.id}`}
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
      description:
        "Chọn các entity type có thể làm đích (target) của relationship",
    },
    {
      name: "is_bidirectional",
      label: "Quan Hệ Hai Chiều",
      type: "switch",
      defaultValue: false,
      description:
        "Relationship có thể đi theo cả hai chiều không (A → B và B → A)",
    },
    {
      name: "color",
      label: "Màu Sắc",
      type: "text",
      defaultValue: "#10B981",
      placeholder: "#10B981",
      description: "Màu sắc đại diện cho relationship type (hex color)",
    },
    {
      name: "extraction_pattern",
      label: "Pattern Trích Xuất",
      type: "text",
      placeholder: "VD: /\\b(owns|owned by)\\b/i",
      description: "Regex pattern để trích xuất relationship từ text",
    },
    {
      name: "examples",
      label: "Ví Dụ",
      type: "array",
      arrayItemLabel: "Ví dụ",
      minItems: 0,
      maxItems: 10,
      fields: [
        {
          name: "value",
          label: "Giá trị",
          type: "text",
          placeholder: "VD: Company owns subsidiary",
          wrapperClassName: "col-span-12",
        },
      ],
      description: "Các ví dụ điển hình của relationship type này",
    },
    {
      name: "domain_ids",
      label: "Domains",
      type: "custom",
      customComponent: ({ value, onChange }) => (
        <div className="space-y-2">
          {domains
            .filter((d) => d.is_active)
            .map((domain) => (
              <div key={domain.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`domain-${domain.id}`}
                  checked={value?.includes(domain.id) || false}
                  onChange={(e) => {
                    const currentValue = value || [];
                    if (e.target.checked) {
                      onChange([...currentValue, domain.id]);
                    } else {
                      onChange(
                        currentValue.filter((id: number) => id !== domain.id),
                      );
                    }
                  }}
                  className="rounded border-gray-300"
                />
                <label
                  htmlFor={`domain-${domain.id}`}
                  className="flex items-center space-x-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: domain.color }}
                  />
                  <span>{domain.display_name}</span>
                </label>
              </div>
            ))}
        </div>
      ),
      description: "Chọn các domain mà relationship type này thuộc về",
    },
    {
      name: "is_active",
      label: "Kích Hoạt",
      type: "switch",
      defaultValue: true,
      description: "Relationship type có đang được sử dụng không",
    },
  ];

  // Filtered relationship types based on domain filter
  const filteredRelationshipTypes =
    selectedDomainFilter === "all"
      ? relationshipTypes
      : relationshipTypes.filter((rt) =>
          rt.domains?.some((d) => d.name === selectedDomainFilter),
        );

  // Helper function to get entity type name by id
  const getEntityTypeName = (id: number) => {
    const entityType = entityTypes.find((et) => et.id === id);
    return entityType ? entityType.display_name : `Entity ${id}`;
  };

  // Table columns configuration
  const columns: SimpleColumnDef<RelationshipType, any>[] = [
    {
      accessorKey: "name",
      header: "Tên Relationship Type",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: row?.color || "#10B981" }}
          />
          <span className="font-mono text-sm">{row?.name}</span>
          {row?.is_bidirectional && (
            <Badge variant="outline" className="text-xs">
              <ArrowRight size={10} className="mr-1" />
              <ArrowRight size={10} className="transform rotate-180 -ml-2" />
            </Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: "display_name",
      header: "Tên Hiển Thị",
      cell: (row) => <span className="font-medium">{row?.display_name}</span>,
    },
    {
      accessorKey: "source_entity_types",
      header: "Source → Target",
      cell: (row) => {
        const sourceTypes =
          row?.source_entity_types
            ?.map((id) => getEntityTypeName(id))
            .join(", ") || "Any";
        const targetTypes =
          row?.target_entity_types
            ?.map((id) => getEntityTypeName(id))
            .join(", ") || "Any";
        return (
          <div className="text-sm">
            <span className="text-blue-600">{sourceTypes}</span>
            <ArrowRight size={12} className="inline mx-1" />
            <span className="text-green-600">{targetTypes}</span>
          </div>
        );
      },
    },
    {
      accessorKey: "domains",
      header: "Domains",
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {row?.domains?.slice(0, 2).map((domain) => (
            <Badge
              key={domain.id}
              variant={domain.is_primary ? "default" : "secondary"}
              className="text-xs"
            >
              {domain.domain_display_name}
              {domain.is_primary && " (Primary)"}
            </Badge>
          ))}
          {row?.domains && row.domains.length > 2 && (
            <Badge variant="outline" className="text-xs">
              +{row.domains.length - 2} khác
            </Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: "usage_count",
      header: "Sử Dụng",
      cell: (row) => (
        <span className="text-sm font-medium">
          {row?.usage_count?.toLocaleString() || 0}
        </span>
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
  ];

  // Action buttons for table
  const actionButtons: ActionButton<RelationshipType>[] = [
    {
      label: "Xem",
      icon: <Eye size={16} />,
      onClick: (relationshipType) => {
        setSelectedRelationshipType(relationshipType);
        setIsViewModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Sửa",
      icon: <Edit size={16} />,
      onClick: (relationshipType) => {
        setSelectedRelationshipType(relationshipType);
        setIsEditModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Validate",
      icon: <CheckCircle size={16} />,
      onClick: (relationshipType) => {
        setSelectedRelationshipType(relationshipType);
        setIsValidationModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Xóa",
      icon: <Trash2 size={16} />,
      onClick: (relationshipType) => {
        if (
          confirm(
            `Bạn có chắc chắn muốn xóa relationship type "${relationshipType.display_name}"?`,
          )
        ) {
          setRelationshipTypes((prev) =>
            prev.filter((rt) => rt.id !== relationshipType.id),
          );
        }
      },
      variant: "ghost",
      className: "text-red-600 hover:text-red-800",
    },
  ];

  const handleCreateRelationshipType = (
    data: z.infer<typeof relationshipTypeSchema>,
  ) => {
    setLoading(true);
    setTimeout(() => {
      const newRelationshipType: RelationshipType = {
        id: Date.now(),
        ...data,
        examples:
          data.examples
            ?.map((ex) => (typeof ex === "string" ? ex : ex.value))
            .filter(Boolean) || [],
        domains:
          data.domain_ids?.map((domainId) => {
            const domain = domains.find((d) => d.id === domainId);
            return {
              id: Date.now() + domainId,
              domain_id: domainId,
              domain_name: domain?.name || "",
              domain_display_name: domain?.display_name || "",
              is_primary: domainId === data.primary_domain_id,
            };
          }) || [],
        usage_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setRelationshipTypes((prev) => [...prev, newRelationshipType]);
      setIsCreateModalOpen(false);
      setLoading(false);
    }, 1000);
  };

  const handleUpdateRelationshipType = (
    data: z.infer<typeof relationshipTypeSchema>,
  ) => {
    if (!selectedRelationshipType) return;

    setLoading(true);
    setTimeout(() => {
      setRelationshipTypes((prev) =>
        prev.map((rt) =>
          rt.id === selectedRelationshipType.id
            ? {
                ...rt,
                ...data,
                examples:
                  data.examples
                    ?.map((ex) => (typeof ex === "string" ? ex : ex.value))
                    .filter(Boolean) || [],
                domains:
                  data.domain_ids?.map((domainId) => {
                    const domain = domains.find((d) => d.id === domainId);
                    return {
                      id: Date.now() + domainId,
                      domain_id: domainId,
                      domain_name: domain?.name || "",
                      domain_display_name: domain?.display_name || "",
                      is_primary: domainId === data.primary_domain_id,
                    };
                  }) || [],
                updated_at: new Date().toISOString(),
              }
            : rt,
        ),
      );
      setIsEditModalOpen(false);
      setSelectedRelationshipType(null);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Quản Lý Relationship Types
          </h1>
          <p className="text-gray-600 mt-1">
            Quản lý các loại quan hệ trong hệ thống knowledge graph
          </p>
        </div>
        <Dialog
          title="Tạo Relationship Type Mới"
          description="Tạo một loại quan hệ mới cho hệ thống knowledge graph của bạn"
          open={isCreateModalOpen}
          onOpenChange={setIsCreateModalOpen}
        >
          <AppForm
            fields={getFormFields()}
            schema={relationshipTypeSchema}
            onSubmit={handleCreateRelationshipType}
            submitButtonText="Tạo Relationship Type"
            isLoading={loading}
          />
        </Dialog>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatisticCard
          title="Tổng Relationship Types"
          value={relationshipTypes.length}
          icon={<GitBranch size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Đang Hoạt Động"
          value={relationshipTypes.filter((rt) => rt.is_active).length}
          icon={<CheckCircle size={20} />}
          color="green"
        />
        <StatisticCard
          title="Hai Chiều"
          value={relationshipTypes.filter((rt) => rt.is_bidirectional).length}
          icon={<ArrowRight size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Tổng Sử Dụng"
          value={relationshipTypes
            .reduce((sum, rt) => sum + (rt.usage_count || 0), 0)
            .toLocaleString()}
          icon={<Link size={20} />}
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
      <Tabs defaultValue="relationship-types" className="space-y-4">
        <TabsList>
          <TabsTrigger value="relationship-types">
            Danh Sách Relationship Types
          </TabsTrigger>
          <TabsTrigger value="validation">Validation & Constraints</TabsTrigger>
        </TabsList>

        <TabsContent value="relationship-types" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                Relationship Types
                {selectedDomainFilter !== "all" && (
                  <span className="text-base font-normal text-gray-500">
                    {" "}
                    trong domain "
                    {
                      domains.find((d) => d.name === selectedDomainFilter)
                        ?.display_name
                    }
                    "
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={filteredRelationshipTypes}
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

        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Relationship Type Constraints</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {relationshipTypes.map((rt) => (
                  <div key={rt.id} className="border rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">{rt.display_name}</h4>
                      <Badge variant={rt.is_active ? "default" : "secondary"}>
                        {rt.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <div className="text-sm text-gray-600">
                      <p>
                        <strong>Source Types:</strong>{" "}
                        {rt.source_entity_types
                          ?.map((id) => getEntityTypeName(id))
                          .join(", ") || "Any"}
                      </p>
                      <p>
                        <strong>Target Types:</strong>{" "}
                        {rt.target_entity_types
                          ?.map((id) => getEntityTypeName(id))
                          .join(", ") || "Any"}
                      </p>
                      <p>
                        <strong>Bidirectional:</strong>{" "}
                        {rt.is_bidirectional ? "Yes" : "No"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* View Relationship Type Modal */}
      <Dialog
        title="Chi Tiết Relationship Type"
        description="Xem chi tiết về relationship type này"
        open={isViewModalOpen}
        onOpenChange={setIsViewModalOpen}
      >
        {selectedRelationshipType && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tên Relationship Type
                </label>
                <p className="mt-1 font-mono">
                  {selectedRelationshipType.name}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tên Hiển Thị
                </label>
                <p className="mt-1">{selectedRelationshipType.display_name}</p>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Mô Tả</label>
              <p className="mt-1">
                {selectedRelationshipType.description || "Không có mô tả"}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Source Entity Types
                </label>
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedRelationshipType.source_entity_types?.map((id) => (
                    <Badge key={id} variant="outline" className="text-xs">
                      {getEntityTypeName(id)}
                    </Badge>
                  )) || <span className="text-gray-400">Any</span>}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Target Entity Types
                </label>
                <div className="mt-2 flex flex-wrap gap-1">
                  {selectedRelationshipType.target_entity_types?.map((id) => (
                    <Badge key={id} variant="outline" className="text-xs">
                      {getEntityTypeName(id)}
                    </Badge>
                  )) || <span className="text-gray-400">Any</span>}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Màu Sắc
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <div
                    className="w-6 h-6 rounded-full border"
                    style={{ backgroundColor: selectedRelationshipType.color }}
                  />
                  <span className="font-mono text-sm">
                    {selectedRelationshipType.color}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Hai Chiều
                </label>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedRelationshipType.is_bidirectional
                        ? "default"
                        : "secondary"
                    }
                  >
                    {selectedRelationshipType.is_bidirectional ? "Có" : "Không"}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Sử Dụng
                </label>
                <p className="mt-1 font-semibold">
                  {selectedRelationshipType.usage_count?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Trạng Thái
                </label>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedRelationshipType.is_active
                        ? "default"
                        : "secondary"
                    }
                  >
                    {selectedRelationshipType.is_active
                      ? "Hoạt động"
                      : "Tạm dừng"}
                  </Badge>
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">
                Domains
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedRelationshipType.domains?.map((domain) => (
                  <Badge
                    key={domain.id}
                    variant={domain.is_primary ? "default" : "secondary"}
                  >
                    {domain.domain_display_name}
                    {domain.is_primary && " (Primary)"}
                  </Badge>
                ))}
              </div>
            </div>

            {selectedRelationshipType.examples &&
              selectedRelationshipType.examples.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Ví Dụ
                  </label>
                  <div className="mt-2">
                    <ul className="list-disc list-inside space-y-1">
                      {selectedRelationshipType.examples.map(
                        (example, index) => (
                          <li key={index} className="text-sm">
                            {example}
                          </li>
                        ),
                      )}
                    </ul>
                  </div>
                </div>
              )}

            {selectedRelationshipType.extraction_pattern && (
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Pattern Trích Xuất
                </label>
                <p className="mt-1 font-mono text-sm bg-gray-100 p-2 rounded">
                  {selectedRelationshipType.extraction_pattern}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tạo Lúc
                </label>
                <p className="mt-1">
                  {new Date(selectedRelationshipType.created_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Cập Nhật
                </label>
                <p className="mt-1">
                  {new Date(selectedRelationshipType.updated_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
            </div>
          </div>
        )}
      </Dialog>

      {/* Edit Relationship Type Modal */}
      <Dialog
        title="Chỉnh Sửa Relationship Type"
        dscription="Chỉnh sửa thông tin relationship type này"
        open={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
      >
        {selectedRelationshipType && (
          <AppForm
            fields={getFormFields(true)}
            schema={relationshipTypeSchema}
            defaultValues={{
              ...selectedRelationshipType,
              examples:
                selectedRelationshipType.examples?.map((ex) => ({
                  value: ex,
                })) || [],
              domain_ids:
                selectedRelationshipType.domains?.map((d) => d.domain_id) || [],
              primary_domain_id: selectedRelationshipType.domains?.find(
                (d) => d.is_primary,
              )?.domain_id,
            }}
            onSubmit={handleUpdateRelationshipType}
            submitButtonText="Cập Nhật Relationship Type"
            isLoading={loading}
          />
        )}
      </Dialog>
    </div>
  );
};

export default RelationshipTypesManagementPage;
