import React, { useState } from "react";
import {
  Tag,
  Database,
  Eye,
  Edit,
  Trash2,
  Link,
  TrendingUp,
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
import {
  useDomains,
  useEntityTypes,
  useEntityTypesByDomain,
} from "@vbkg/api-client";

// Types based on API schemas
interface EntityType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  color: string;
  icon?: string;
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

// Form schema
const entityTypeSchema = z.object({
  name: z.string().min(1, "Tên entity type không được để trống").max(50),
  display_name: z.string().min(1, "Tên hiển thị không được để trống").max(100),
  description: z.string().optional(),
  color: z.string().default("#3B82F6"),
  icon: z.string().optional(),
  extraction_pattern: z.string().optional(),
  examples: z.array(z.string()).default([]),
  is_active: z.boolean().default(true),
  domain_ids: z.array(z.number()).default([]),
  primary_domain_id: z.number().optional(),
  validation_rules: z.record(z.any()).optional(),
});

const EntityTypesManagementPage: React.FC = () => {
  const { data: domainResponse } = useDomains({
    limit: 100,
  });
  const domains = domainResponse?.data || [];
  const [selectedEntityType, setSelectedEntityType] =
    useState<EntityType | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isDomainMappingModalOpen, setIsDomainMappingModalOpen] =
    useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedDomainFilter, setSelectedDomainFilter] =
    useState<string>("all");

  const { data: entityTypesResponse } = useEntityTypes({
    limit: 200,
  });

  const entityTypes = entityTypesResponse?.data || [];

  // Form fields configuration
  const getFormFields = (isEdit: boolean = false): FieldConfig[] => [
    {
      name: "name",
      label: "Tên Entity Type",
      type: "text",
      placeholder: "VD: organization, person, financial_instrument",
      required: true,
      disabled: isEdit,
      description:
        "Tên duy nhất của entity type (chỉ chứa chữ thường, số và dấu gạch dưới)",
    },
    {
      name: "display_name",
      label: "Tên Hiển Thị",
      type: "text",
      placeholder: "VD: Organization, Person, Financial Instrument",
      required: true,
      description: "Tên hiển thị thân thiện với người dùng",
    },
    {
      name: "description",
      label: "Mô Tả",
      type: "textarea",
      placeholder: "Mô tả chi tiết về entity type này...",
      description: "Mô tả về mục đích và đặc điểm của entity type",
    },
    {
      name: "color",
      label: "Màu Sắc",
      type: "text",
      defaultValue: "#3B82F6",
      placeholder: "#3B82F6",
      description: "Màu sắc đại diện cho entity type (hex color)",
    },
    {
      name: "icon",
      label: "Icon",
      type: "text",
      placeholder: "VD: Building, User, TrendingUp",
      description: "Tên icon Lucide React",
    },
    {
      name: "extraction_pattern",
      label: "Pattern Trích Xuất",
      type: "text",
      placeholder: "VD: /^[A-Z][a-z]+ (Inc|Corp|Ltd)$/",
      description: "Regex pattern để trích xuất entity từ text",
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
          placeholder: "VD: Apple Inc.",
          wrapperClassName: "col-span-12",
        },
      ],
      description: "Các ví dụ điển hình của entity type này",
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
      description: "Chọn các domain mà entity type này thuộc về",
    },
    {
      name: "is_active",
      label: "Kích Hoạt",
      type: "switch",
      defaultValue: true,
      description: "Entity type có đang được sử dụng không",
    },
  ];

  // Filtered entity types based on domain filter
  const filteredEntityTypes =
    selectedDomainFilter === "all"
      ? entityTypes
      : entityTypes.filter((et) =>
          et.domains?.some((d) => d.name === selectedDomainFilter),
        );

  // Table columns configuration
  const columns: SimpleColumnDef<EntityType, any>[] = [
    {
      accessorKey: "name",
      header: "Tên Entity Type",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: row?.color || "#3B82F6" }}
          />
          <span className="font-mono text-sm">{row?.name}</span>
        </div>
      ),
    },
    {
      accessorKey: "display_name",
      header: "Tên Hiển Thị",
      cell: (row) => <span className="font-medium">{row?.display_name}</span>,
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
    {
      accessorKey: "updated_at",
      header: "Cập Nhật",
      cell: (row) =>
        new Date(row?.updated_at || "").toLocaleDateString("vi-VN"),
    },
  ];

  // Action buttons for table
  const actionButtons: ActionButton<EntityType>[] = [
    {
      label: "Xem",
      icon: <Eye size={16} />,
      onClick: (entityType) => {
        setSelectedEntityType(entityType);
        setIsViewModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Sửa",
      icon: <Edit size={16} />,
      onClick: (entityType) => {
        setSelectedEntityType(entityType);
        setIsEditModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Domain Mapping",
      icon: <Link size={16} />,
      onClick: (entityType) => {
        setSelectedEntityType(entityType);
        setIsDomainMappingModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Xóa",
      icon: <Trash2 size={16} />,
      onClick: (entityType) => {
        if (
          confirm(
            `Bạn có chắc chắn muốn xóa entity type "${entityType.display_name}"?`,
          )
        ) {
          setEntityTypes((prev) =>
            prev.filter((et) => et.id !== entityType.id),
          );
        }
      },
      variant: "ghost",
      className: "text-red-600 hover:text-red-800",
    },
  ];

  const handleCreateEntityType = (data: z.infer<typeof entityTypeSchema>) => {
    setLoading(true);
    setTimeout(() => {
      const newEntityType: EntityType = {
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
      setEntityTypes((prev) => [...prev, newEntityType]);
      setIsCreateModalOpen(false);
      setLoading(false);
    }, 1000);
  };

  const handleUpdateEntityType = (data: z.infer<typeof entityTypeSchema>) => {
    if (!selectedEntityType) return;

    setLoading(true);
    setTimeout(() => {
      setEntityTypes((prev) =>
        prev.map((et) =>
          et.id === selectedEntityType.id
            ? {
                ...et,
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
            : et,
        ),
      );
      setIsEditModalOpen(false);
      setSelectedEntityType(null);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Quản Lý Entity Types
          </h1>
          <p className="text-gray-600 mt-1">
            Quản lý các loại thực thể trong hệ thống knowledge graph
          </p>
        </div>
        <Dialog
          title="Tạo Entity Type Mới"
          description="Tạo một loại thực thể mới để sử dụng trong hệ thống"
          open={isCreateModalOpen}
          onOpenChange={setIsCreateModalOpen}
        >
          <AppForm
            fields={getFormFields()}
            schema={entityTypeSchema}
            onSubmit={handleCreateEntityType}
            submitButtonText="Tạo Entity Type"
            isLoading={loading}
          />
        </Dialog>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatisticCard
          title="Tổng Entity Types"
          value={entityTypes.length}
          icon={<Tag size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Đang Hoạt Động"
          value={entityTypes.filter((et) => et.is_active).length}
          icon={<Database size={20} />}
          color="green"
        />
        <StatisticCard
          title="Tổng Sử Dụng"
          value={entityTypes
            .reduce((sum, et) => sum + (et.usage_count || 0), 0)
            .toLocaleString()}
          icon={<TrendingUp size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Domains Mapped"
          value={domains.length}
          icon={<Link size={20} />}
          color="orange"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent>
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
      <Tabs defaultValue="entity-types" className="space-y-4">
        <TabsList>
          <TabsTrigger value="entity-types">Danh Sách Entity Types</TabsTrigger>
          <TabsTrigger value="bulk-operations">Thao Tác Hàng Loạt</TabsTrigger>
        </TabsList>

        <TabsContent value="entity-types" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                Entity Types
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
                data={filteredEntityTypes}
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

        <TabsContent value="bulk-operations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Thao Tác Hàng Loạt</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                Chức năng thao tác hàng loạt đang được phát triển
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* View Entity Type Modal */}
      <Dialog
        title="Chi Tiết Entity Type"
        description="Xem chi tiết thông tin của loại thực thể"
        open={isViewModalOpen}
        onOpenChange={setIsViewModalOpen}
      >
        {selectedEntityType && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tên Entity Type
                </label>
                <p className="mt-1 font-mono">{selectedEntityType.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tên Hiển Thị
                </label>
                <p className="mt-1">{selectedEntityType.display_name}</p>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Mô Tả</label>
              <p className="mt-1">
                {selectedEntityType.description || "Không có mô tả"}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Màu Sắc
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <div
                    className="w-6 h-6 rounded-full border"
                    style={{ backgroundColor: selectedEntityType.color }}
                  />
                  <span className="font-mono text-sm">
                    {selectedEntityType.color}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Sử Dụng
                </label>
                <p className="mt-1 font-semibold">
                  {selectedEntityType.usage_count?.toLocaleString() || 0}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Trạng Thái
                </label>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedEntityType.is_active ? "default" : "secondary"
                    }
                  >
                    {selectedEntityType.is_active ? "Hoạt động" : "Tạm dừng"}
                  </Badge>
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">
                Domains
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedEntityType.domains?.map((domain) => (
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

            {selectedEntityType.examples &&
              selectedEntityType.examples.length > 0 && (
                <div>
                  <label className="text-sm font-medium text-gray-500">
                    Ví Dụ
                  </label>
                  <div className="mt-2">
                    <ul className="list-disc list-inside space-y-1">
                      {selectedEntityType.examples.map((example, index) => (
                        <li key={index} className="text-sm">
                          {example}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

            {selectedEntityType.extraction_pattern && (
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Pattern Trích Xuất
                </label>
                <p className="mt-1 font-mono text-sm bg-gray-100 p-2 rounded">
                  {selectedEntityType.extraction_pattern}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Tạo Lúc
                </label>
                <p className="mt-1">
                  {new Date(selectedEntityType.created_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Cập Nhật
                </label>
                <p className="mt-1">
                  {new Date(selectedEntityType.updated_at).toLocaleString(
                    "vi-VN",
                  )}
                </p>
              </div>
            </div>
          </div>
        )}
      </Dialog>

      {/* Edit Entity Type Modal */}
      <Dialog
        title="Chỉnh Sửa Entity Type"
        description="Chỉnh sửa thông tin của loại thực thể"
        open={isEditModalOpen}
        onOpenChange={setIsEditModalOpen}
      >
        {selectedEntityType && (
          <AppForm
            fields={getFormFields(true)}
            schema={entityTypeSchema}
            defaultValues={{
              ...selectedEntityType,
              examples:
                selectedEntityType.examples?.map((ex) => ({ value: ex })) || [],
              domain_ids:
                selectedEntityType.domains?.map((d) => d.domain_id) || [],
              primary_domain_id: selectedEntityType.domains?.find(
                (d) => d.is_primary,
              )?.domain_id,
            }}
            onSubmit={handleUpdateEntityType}
            submitButtonText="Cập Nhật Entity Type"
            isLoading={loading}
          />
        )}
      </Dialog>
    </div>
  );
};

export default EntityTypesManagementPage;
