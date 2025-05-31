import React, { useState } from "react";
import {
  Link2,
  Database,
  Upload as UploadIcon,
  CheckCircle,
  X,
  Eye,
  Trash2,
  Lightbulb,
  ArrowRight,
  RefreshCw,
  Plus,
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
  Input,
  Progress,
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
} from "@vbkg/ui";
import {
  useCreateEntityMapping,
  useEntityMappings,
  useSuggestFiboClasses,
} from "@vbkg/api-client";

// Types based on API schemas
interface FIBOClass {
  id: number;
  uri: string;
  label?: string;
  description?: string;
  domain?: string;
  properties?: Record<string, any>;
  parent_class_id?: number;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

interface FIBOProperty {
  id: number;
  uri: string;
  label?: string;
  description?: string;
  property_type: "object" | "datatype";
  domain_class_id?: number;
  range_class_id?: number;
  is_custom: boolean;
  created_at: string;
  updated_at: string;
}

interface EntityType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  color: string;
  is_active: boolean;
}

interface RelationshipType {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  color: string;
  is_active: boolean;
}

interface RelationshipMapping {
  id: number;
  relationship_type: string;
  relationship_type_id?: number;
  fibo_property_uri: string;
  fibo_property?: FIBOProperty;
  confidence?: number;
  is_verified: boolean;
  mapping_status: "pending" | "mapped" | "rejected" | "needs_review";
  mapping_notes?: string;
  auto_mapped: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface MappingSuggestion {
  entity_text?: string;
  entity_type?: string;
  relationship_type?: string;
  source_entity_type?: string;
  target_entity_type?: string;
  suggestions: (FIBOClass | FIBOProperty)[];
  loading: boolean;
}

// Mock data
const mockEntityTypes: EntityType[] = [
  {
    id: 1,
    name: "organization",
    display_name: "Organization",
    description: "Companies and institutions",
    color: "#3B82F6",
    is_active: true,
  },
  {
    id: 2,
    name: "person",
    display_name: "Person",
    description: "Individual persons",
    color: "#10B981",
    is_active: true,
  },
  {
    id: 3,
    name: "financial_instrument",
    display_name: "Financial Instrument",
    description: "Financial products",
    color: "#F59E0B",
    is_active: true,
  },
  {
    id: 4,
    name: "currency",
    display_name: "Currency",
    description: "Monetary units",
    color: "#EF4444",
    is_active: true,
  },
];

const mockRelationshipTypes: RelationshipType[] = [
  {
    id: 1,
    name: "owns",
    display_name: "Owns",
    description: "Ownership relationship",
    color: "#3B82F6",
    is_active: true,
  },
  {
    id: 2,
    name: "works_for",
    display_name: "Works For",
    description: "Employment relationship",
    color: "#10B981",
    is_active: true,
  },
  {
    id: 3,
    name: "located_in",
    display_name: "Located In",
    description: "Geographic relationship",
    color: "#8B5CF6",
    is_active: true,
  },
];

const mockRelationshipMappings: RelationshipMapping[] = [
  {
    id: 1,
    relationship_type: "owns",
    relationship_type_id: 1,
    fibo_property_uri: "https://spec.edmcouncil.org/fibo/ontology/FBC/owns",
    fibo_property: {
      id: 1,
      uri: "https://spec.edmcouncil.org/fibo/ontology/FBC/owns",
      label: "owns",
      description: "Ownership relationship",
      property_type: "object",
      is_custom: false,
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-01-15T10:00:00Z",
    },
    confidence: 0.98,
    is_verified: true,
    mapping_status: "mapped",
    auto_mapped: true,
    created_at: "2024-01-15T10:00:00Z",
    updated_at: "2024-01-15T10:00:00Z",
  },
];

const FIBOMappingManagementPage: React.FC = () => {
  const { data: entityMappingResponse } = useEntityMappings({
    limit: 200,
  });

  const entityMappings = entityMappingResponse?.data || [];

  const [relationshipMappings, setRelationshipMappings] = useState<
    RelationshipMapping[]
  >(mockRelationshipMappings);
  const [entityTypes] = useState<EntityType[]>(mockEntityTypes);
  const [relationshipTypes] = useState<RelationshipType[]>(
    mockRelationshipTypes,
  );

  // Modal states
  const [selectedMapping, setSelectedMapping] = useState<
    EntityMapping | RelationshipMapping | null
  >(null);
  const [isEntityMappingWizardOpen, setIsEntityMappingWizardOpen] =
    useState(false);
  const [isRelationshipMappingWizardOpen, setIsRelationshipMappingWizardOpen] =
    useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [isBulkMappingOpen, setIsBulkMappingOpen] = useState(false);

  // Wizard states
  const [entityMappingStep, setEntityMappingStep] = useState(1);
  const [relationshipMappingStep, setRelationshipMappingStep] = useState(1);

  const [suggestionState, setSuggestionState] = useState<MappingSuggestion>({
    suggestions: [],
    loading: false,
  });

  const [loading, setLoading] = useState(false);

  // Helper functions
  const getEntityTypeById = (id: number) =>
    entityTypes.find((et) => et.id === id);
  const getRelationshipTypeById = (id: number) =>
    relationshipTypes.find((rt) => rt.id === id);

  // Entity mapping wizard steps
  const EntityMappingWizard: React.FC = () => {
    const { mutate: createEntityMapping } = useCreateEntityMapping({});
    const [wizardData, setWizardData] = useState<{
      entity_type_id?: number;
      entity_text?: string;
      selected_fibo_uri?: string;
    }>({});

    const { data: suggestFiboClasses, isFetching: isLoadingClassSuggestions } =
      useSuggestFiboClasses({
        entity_type_id: getEntityTypeById(wizardData?.entity_type_id),
        entity_text: wizardData?.entity_text,
        max_suggestions: 10,
      });

    const handleEntityTypeSelect = (entityTypeId: string) => {
      setWizardData((prev) => ({ ...prev, entity_type_id: entityTypeId }));
      getSuggestionForEntity(entityTypeId, wizardData.entity_text);
      setEntityMappingStep(2);
    };

    const handleSuggestionSelect = (suggestion: FIBOClass) => {
      setWizardData((prev) => ({ ...prev, selected_fibo_uri: suggestion.uri }));
      setEntityMappingStep(3);
    };

    const handleCreateMapping = (formData: any) => {
      setLoading(true);
      setTimeout(() => {
        const entityType = getEntityTypeById(wizardData.entity_type_id!);
        const fiboClass = suggestionState.suggestions.find(
          (s) => s.uri === wizardData.selected_fibo_uri,
        ) as FIBOClass;

        const newMapping: EntityMapping = {
          entity_type: entityType!.name,
          entity_type_id: wizardData.entity_type_id,
          fibo_class_uri: wizardData.selected_fibo_uri!,
          fibo_class: fiboClass,
          confidence: formData.confidence || 0.9,
          mapping_notes: formData.mapping_notes,
          is_verified: formData.is_verified,
          mapping_status: formData.is_verified ? "mapped" : "pending",
          auto_mapped: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        createEntityMapping({
          mapping: newMapping,
        });

        setIsEntityMappingWizardOpen(false);
        setEntityMappingStep(1);
        setWizardData({});
        setSuggestionState({ suggestions: [], loading: false });
        setLoading(false);
      }, 1000);
    };

    if (entityMappingStep === 1) {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Step 1: Select Entity Type</h3>

          <div>
            <label className="text-sm font-medium">
              Entity Text (Optional)
            </label>
            <Input
              placeholder="VD: Apple Inc., Goldman Sachs..."
              value={wizardData.entity_text || ""}
              onChange={(e) =>
                setWizardData((prev) => ({
                  ...prev,
                  entity_text: e.target.value,
                }))
              }
              className="mt-1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Nhập example text để cải thiện suggestions
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">Choose Entity Type</label>
            <div className="grid grid-cols-2 gap-3 mt-2">
              {entityTypes
                .filter((et) => et.is_active)
                .map((entityType) => (
                  <button
                    key={entityType.id}
                    onClick={() => handleEntityTypeSelect(entityType.id)}
                    className="p-4 border rounded-lg hover:bg-blue-50 hover:border-blue-300 text-left transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: entityType.color }}
                      />
                      <div>
                        <p className="font-medium">{entityType.display_name}</p>
                        <p className="text-sm text-gray-500">
                          {entityType.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
            </div>
          </div>
        </div>
      );
    }

    if (entityMappingStep === 2) {
      const selectedEntityType = getEntityTypeById(wizardData.entity_type_id!);

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Step 2: Select FIBO Class</h3>
            <Button size="sm" onClick={() => setEntityMappingStep(1)}>
              Back
            </Button>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm">
              <strong>Entity Type:</strong> {selectedEntityType?.display_name}
              {wizardData.entity_text && (
                <span className="ml-2">
                  <strong>Example:</strong> "{wizardData.entity_text}"
                </span>
              )}
            </p>
          </div>

          {isLoadingClassSuggestions ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
              <span className="ml-2">Getting FIBO suggestions...</span>
            </div>
          ) : (
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">
                  Suggested FIBO Classes
                </span>
              </div>

              <div className="space-y-2">
                {suggestFiboClasses?.data?.map((suggestion, index) => {
                  const fiboClass = suggestion;
                  return (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(fiboClass)}
                      className="w-full p-4 border rounded-lg hover:bg-green-50 hover:border-green-300 text-left transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">
                            {fiboClass.label || "No Label"}
                          </p>
                          <p className="text-sm text-gray-600">
                            {fiboClass.description}
                          </p>
                          <p className="text-xs text-gray-500 font-mono mt-1">
                            {fiboClass.uri}
                          </p>
                        </div>
                        <Badge variant="outline">{fiboClass.domain}</Badge>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (entityMappingStep === 3) {
      const selectedEntityType = getEntityTypeById(wizardData.entity_type_id!);
      const selectedFIBOClass = suggestionState.suggestions.find(
        (s) => s.uri === wizardData.selected_fibo_uri,
      ) as FIBOClass;

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Step 3: Confirm Mapping</h3>
            <Button size="sm" onClick={() => setEntityMappingStep(2)}>
              Back
            </Button>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center space-x-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: selectedEntityType?.color }}
              />
              <span className="font-medium">
                {selectedEntityType?.display_name}
              </span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
              <span className="font-medium">{selectedFIBOClass?.label}</span>
              <Badge variant="outline">{selectedFIBOClass?.domain}</Badge>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {selectedFIBOClass?.description}
            </p>
          </div>

          <AppForm
            fields={[
              {
                name: "confidence",
                label: "Confidence Score",
                type: "number",
                defaultValue: 0.9,
                placeholder: "0.9",
                description: "Độ tin cậy của mapping (0-1)",
              },
              {
                name: "mapping_notes",
                label: "Mapping Notes",
                type: "textarea",
                placeholder: "Ghi chú về mapping này...",
                description: "Ghi chú bổ sung",
              },
              {
                name: "is_verified",
                label: "Verify Mapping",
                type: "switch",
                defaultValue: false,
                description: "Đánh dấu mapping đã được xác nhận",
              },
            ]}
            schema={z.object({
              confidence: z.number().min(0).max(1).optional(),
              mapping_notes: z.string().optional(),
              is_verified: z.boolean().default(false),
            })}
            onSubmit={handleCreateMapping}
            submitButtonText="Create Mapping"
            isLoading={loading}
          />
        </div>
      );
    }

    return null;
  };

  // Relationship mapping wizard
  const RelationshipMappingWizard: React.FC = () => {
    const [wizardData, setWizardData] = useState<{
      relationship_type_id?: number;
      source_entity_type_id?: number;
      target_entity_type_id?: number;
      selected_fibo_uri?: string;
    }>({});

    const handleRelationshipTypeSelect = (relationshipTypeId: number) => {
      setWizardData((prev) => ({
        ...prev,
        relationship_type_id: relationshipTypeId,
      }));
      setRelationshipMappingStep(2);
    };

    const handleEntityTypesSelect = () => {
      getSuggestionForRelationship(
        wizardData.relationship_type_id!,
        wizardData.source_entity_type_id,
        wizardData.target_entity_type_id,
      );
      setRelationshipMappingStep(3);
    };

    const handleSuggestionSelect = (suggestion: FIBOProperty) => {
      setWizardData((prev) => ({ ...prev, selected_fibo_uri: suggestion.uri }));
      setRelationshipMappingStep(4);
    };

    const handleCreateMapping = (formData: any) => {
      setLoading(true);
      setTimeout(() => {
        const relationshipType = getRelationshipTypeById(
          wizardData.relationship_type_id!,
        );
        const fiboProperty = suggestionState.suggestions.find(
          (s) => s.uri === wizardData.selected_fibo_uri,
        ) as FIBOProperty;

        const newMapping: RelationshipMapping = {
          id: Date.now(),
          relationship_type: relationshipType!.name,
          relationship_type_id: wizardData.relationship_type_id,
          fibo_property_uri: wizardData.selected_fibo_uri!,
          fibo_property: fiboProperty,
          confidence: formData.confidence || 0.9,
          mapping_notes: formData.mapping_notes,
          is_verified: formData.is_verified,
          mapping_status: formData.is_verified ? "mapped" : "pending",
          auto_mapped: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        setRelationshipMappings((prev) => [...prev, newMapping]);
        setIsRelationshipMappingWizardOpen(false);
        setRelationshipMappingStep(1);
        setWizardData({});
        setSuggestionState({ suggestions: [], loading: false });
        setLoading(false);
      }, 1000);
    };

    if (relationshipMappingStep === 1) {
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            Step 1: Select Relationship Type
          </h3>

          <div className="space-y-2">
            {relationshipTypes
              .filter((rt) => rt.is_active)
              .map((relationshipType) => (
                <button
                  key={relationshipType.id}
                  onClick={() =>
                    handleRelationshipTypeSelect(relationshipType.id)
                  }
                  className="w-full p-4 border rounded-lg hover:bg-blue-50 hover:border-blue-300 text-left transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: relationshipType.color }}
                    />
                    <div>
                      <p className="font-medium">
                        {relationshipType.display_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {relationshipType.description}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
          </div>
        </div>
      );
    }

    if (relationshipMappingStep === 2) {
      const selectedRelationshipType = getRelationshipTypeById(
        wizardData.relationship_type_id!,
      );

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Step 2: Select Entity Types (Optional)
            </h3>
            <Button size="sm" onClick={() => setRelationshipMappingStep(1)}>
              Back
            </Button>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm">
              <strong>Relationship Type:</strong>{" "}
              {selectedRelationshipType?.display_name}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Source Entity Type</label>
              <Select
                value={wizardData.source_entity_type_id?.toString() || ""}
                onValueChange={(value) =>
                  setWizardData((prev) => ({
                    ...prev,
                    source_entity_type_id: value ? parseInt(value) : undefined,
                  }))
                }
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select source type" />
                </SelectTrigger>
                <SelectContent>
                  {entityTypes.map((et) => (
                    <SelectItem key={et.id} value={et.id.toString()}>
                      {et.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Target Entity Type</label>
              <Select
                value={wizardData.target_entity_type_id?.toString() || ""}
                onValueChange={(value) =>
                  setWizardData((prev) => ({
                    ...prev,
                    target_entity_type_id: value ? parseInt(value) : undefined,
                  }))
                }
              >
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select target type" />
                </SelectTrigger>
                <SelectContent>
                  {entityTypes.map((et) => (
                    <SelectItem key={et.id} value={et.id.toString()}>
                      {et.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button onClick={() => handleEntityTypesSelect()}>Continue</Button>
          </div>
        </div>
      );
    }

    if (relationshipMappingStep === 3) {
      const selectedRelationshipType = getRelationshipTypeById(
        wizardData.relationship_type_id!,
      );

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">
              Step 3: Select FIBO Property
            </h3>
            <Button size="sm" onClick={() => setRelationshipMappingStep(2)}>
              Back
            </Button>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm">
              <strong>Relationship Type:</strong>{" "}
              {selectedRelationshipType?.display_name}
              {wizardData.source_entity_type_id && (
                <span className="ml-2">
                  <strong>Source:</strong>{" "}
                  {
                    getEntityTypeById(wizardData.source_entity_type_id)
                      ?.display_name
                  }
                </span>
              )}
              {wizardData.target_entity_type_id && (
                <span className="ml-2">
                  <strong>Target:</strong>{" "}
                  {
                    getEntityTypeById(wizardData.target_entity_type_id)
                      ?.display_name
                  }
                </span>
              )}
            </p>
          </div>

          {suggestionState.loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
              <span className="ml-2">Getting FIBO suggestions...</span>
            </div>
          ) : (
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Lightbulb className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">
                  Suggested FIBO Properties
                </span>
              </div>

              <div className="space-y-2">
                {suggestionState.suggestions.map((suggestion, index) => {
                  const fiboProperty = suggestion as FIBOProperty;
                  return (
                    <button
                      key={index}
                      onClick={() => handleSuggestionSelect(fiboProperty)}
                      className="w-full p-4 border rounded-lg hover:bg-green-50 hover:border-green-300 text-left transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">
                            {fiboProperty.label || "No Label"}
                          </p>
                          <p className="text-sm text-gray-600">
                            {fiboProperty.description}
                          </p>
                          <p className="text-xs text-gray-500 font-mono mt-1">
                            {fiboProperty.uri}
                          </p>
                        </div>
                        <Badge
                          variant={
                            fiboProperty.property_type === "object"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {fiboProperty.property_type}
                        </Badge>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (relationshipMappingStep === 4) {
      const selectedRelationshipType = getRelationshipTypeById(
        wizardData.relationship_type_id!,
      );
      const selectedFIBOProperty = suggestionState.suggestions.find(
        (s) => s.uri === wizardData.selected_fibo_uri,
      ) as FIBOProperty;

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Step 4: Confirm Mapping</h3>
            <Button size="sm" onClick={() => setRelationshipMappingStep(3)}>
              Back
            </Button>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center space-x-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: selectedRelationshipType?.color }}
              />
              <span className="font-medium">
                {selectedRelationshipType?.display_name}
              </span>
              <ArrowRight className="h-4 w-4 text-gray-400" />
              <span className="font-medium">{selectedFIBOProperty?.label}</span>
              <Badge
                variant={
                  selectedFIBOProperty?.property_type === "object"
                    ? "default"
                    : "secondary"
                }
              >
                {selectedFIBOProperty?.property_type}
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {selectedFIBOProperty?.description}
            </p>
          </div>

          <AppForm
            fields={[
              {
                name: "confidence",
                label: "Confidence Score",
                type: "number",
                defaultValue: 0.9,
                placeholder: "0.9",
                description: "Độ tin cậy của mapping (0-1)",
              },
              {
                name: "mapping_notes",
                label: "Mapping Notes",
                type: "textarea",
                placeholder: "Ghi chú về mapping này...",
                description: "Ghi chú bổ sung",
              },
              {
                name: "is_verified",
                label: "Verify Mapping",
                type: "switch",
                defaultValue: false,
                description: "Đánh dấu mapping đã được xác nhận",
              },
            ]}
            schema={z.object({
              confidence: z.number().min(0).max(1).optional(),
              mapping_notes: z.string().optional(),
              is_verified: z.boolean().default(false),
            })}
            onSubmit={handleCreateMapping}
            submitButtonText="Create Mapping"
            isLoading={loading}
          />
        </div>
      );
    }

    return null;
  };

  // Table columns for Entity Mappings
  const entityMappingColumns: SimpleColumnDef<EntityMapping, any>[] = [
    {
      accessorKey: "entity_type",
      header: "Entity Type",
      cell: (row) => {
        const entityType = entityTypes.find(
          (et) => et.name === row?.entity_type,
        );
        return (
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entityType?.color || "#6366F1" }}
            />
            <span className="font-medium">
              {entityType?.display_name || row?.entity_type}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: "fibo_class",
      header: "FIBO Class",
      cell: (row) => (
        <div>
          <div className="font-medium text-sm">
            {row?.fibo_class?.label || "Unknown"}
          </div>
          <div className="text-xs text-gray-500 truncate max-w-xs">
            {row?.fibo_class_uri}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "confidence",
      header: "Confidence",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <Progress value={(row?.confidence || 0) * 100} className="w-16 h-2" />
          <span className="text-sm">
            {((row?.confidence || 0) * 100).toFixed(0)}%
          </span>
        </div>
      ),
    },
    {
      accessorKey: "mapping_status",
      header: "Status",
      cell: (row) => {
        const statusColors = {
          pending: "bg-yellow-100 text-yellow-800",
          mapped: "bg-green-100 text-green-800",
          rejected: "bg-red-100 text-red-800",
          needs_review: "bg-orange-100 text-orange-800",
        };
        const statusLabels = {
          pending: "Pending",
          mapped: "Mapped",
          rejected: "Rejected",
          needs_review: "Needs Review",
        };
        return (
          <Badge className={statusColors[row?.mapping_status || "pending"]}>
            {statusLabels[row?.mapping_status || "pending"]}
          </Badge>
        );
      },
    },
    {
      accessorKey: "is_verified",
      header: "Verified",
      cell: (row) =>
        row?.is_verified ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <X size={16} className="text-gray-400" />
        ),
    },
  ];

  // Table columns for Relationship Mappings
  const relationshipMappingColumns: SimpleColumnDef<
    RelationshipMapping,
    any
  >[] = [
    {
      accessorKey: "relationship_type",
      header: "Relationship Type",
      cell: (row) => {
        const relationshipType = relationshipTypes.find(
          (rt) => rt.name === row?.relationship_type,
        );
        return (
          <div className="flex items-center space-x-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: relationshipType?.color || "#6366F1" }}
            />
            <span className="font-medium">
              {relationshipType?.display_name || row?.relationship_type}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: "fibo_property",
      header: "FIBO Property",
      cell: (row) => (
        <div>
          <div className="font-medium text-sm">
            {row?.fibo_property?.label || "Unknown"}
          </div>
          <div className="text-xs text-gray-500 truncate max-w-xs">
            {row?.fibo_property_uri}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "confidence",
      header: "Confidence",
      cell: (row) => (
        <div className="flex items-center space-x-2">
          <Progress value={(row?.confidence || 0) * 100} className="w-16 h-2" />
          <span className="text-sm">
            {((row?.confidence || 0) * 100).toFixed(0)}%
          </span>
        </div>
      ),
    },
    {
      accessorKey: "mapping_status",
      header: "Status",
      cell: (row) => {
        const statusColors = {
          pending: "bg-yellow-100 text-yellow-800",
          mapped: "bg-green-100 text-green-800",
          rejected: "bg-red-100 text-red-800",
          needs_review: "bg-orange-100 text-orange-800",
        };
        const statusLabels = {
          pending: "Pending",
          mapped: "Mapped",
          rejected: "Rejected",
          needs_review: "Needs Review",
        };
        return (
          <Badge className={statusColors[row?.mapping_status || "pending"]}>
            {statusLabels[row?.mapping_status || "pending"]}
          </Badge>
        );
      },
    },
    {
      accessorKey: "is_verified",
      header: "Verified",
      cell: (row) =>
        row?.is_verified ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <X size={16} className="text-gray-400" />
        ),
    },
  ];

  // Action buttons
  const actionButtons: ActionButton<any>[] = [
    {
      label: "View",
      icon: <Eye size={16} />,
      onClick: (mapping) => {
        setSelectedMapping(mapping);
        setIsViewModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Verify",
      icon: <CheckCircle size={16} />,
      onClick: (mapping) => {
        if ("entity_type" in mapping) {
          setEntityMappings((prev) =>
            prev.map((m) =>
              m.id === mapping.id
                ? {
                    ...m,
                    is_verified: !m.is_verified,
                    mapping_status: !m.is_verified ? "mapped" : "pending",
                  }
                : m,
            ),
          );
        } else {
          setRelationshipMappings((prev) =>
            prev.map((m) =>
              m.id === mapping.id
                ? {
                    ...m,
                    is_verified: !m.is_verified,
                    mapping_status: !m.is_verified ? "mapped" : "pending",
                  }
                : m,
            ),
          );
        }
      },
      variant: "ghost",
      className: "text-green-600 hover:text-green-800",
    },
    {
      label: "Delete",
      icon: <Trash2 size={16} />,
      onClick: (mapping) => {
        if (confirm("Are you sure you want to delete this mapping?")) {
          if ("entity_type" in mapping) {
            setEntityMappings((prev) =>
              prev.filter((m) => m.id !== mapping.id),
            );
          } else {
            setRelationshipMappings((prev) =>
              prev.filter((m) => m.id !== mapping.id),
            );
          }
        }
      },
      variant: "ghost",
      className: "text-red-600 hover:text-red-800",
    },
  ];

  // Statistics
  const stats = {
    totalEntityMappings: entityMappings.length,
    verifiedEntityMappings: entityMappings.filter((m) => m.is_verified).length,
    totalRelationshipMappings: relationshipMappings.length,
    verifiedRelationshipMappings: relationshipMappings.filter(
      (m) => m.is_verified,
    ).length,
    pendingMappings: [...entityMappings, ...relationshipMappings].filter(
      (m) => m.mapping_status === "pending",
    ).length,
    autoMappings: [...entityMappings, ...relationshipMappings].filter(
      (m) => m.auto_mapped,
    ).length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            FIBO Mapping Management
          </h1>
          <p className="text-gray-600 mt-1">
            Create and manage mappings between your types and FIBO ontology with
            AI-powered suggestions
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setIsEntityMappingWizardOpen(true)}>
            <Plus size={16} className="mr-2" />
            Add Entity Mapping
          </Button>
          <Button onClick={() => setIsRelationshipMappingWizardOpen(true)}>
            <Plus size={16} className="mr-2" />
            Add Relationship Mapping
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatisticCard
          title="Entity Mappings"
          value={stats.totalEntityMappings}
          icon={<Database size={20} />}
          color="blue"
        />
        <StatisticCard
          title="Verified Entities"
          value={stats.verifiedEntityMappings}
          icon={<CheckCircle size={20} />}
          color="green"
        />
        <StatisticCard
          title="Relationship Mappings"
          value={stats.totalRelationshipMappings}
          icon={<Link2 size={20} />}
          color="purple"
        />
        <StatisticCard
          title="Verified Relationships"
          value={stats.verifiedRelationshipMappings}
          icon={<CheckCircle size={20} />}
          color="green"
        />
        <StatisticCard
          title="Pending Review"
          value={stats.pendingMappings}
          icon={<X size={20} />}
          color="yellow"
        />
        <StatisticCard
          title="Auto Mapped"
          value={stats.autoMappings}
          icon={<UploadIcon size={20} />}
          color="indigo"
        />
      </div>

      {/* Main Content */}
      <Tabs defaultValue="entity-mappings" className="space-y-4">
        <TabsList>
          <TabsTrigger value="entity-mappings">Entity Mappings</TabsTrigger>
          <TabsTrigger value="relationship-mappings">
            Relationship Mappings
          </TabsTrigger>
          <TabsTrigger value="bulk-operations">Bulk Operations</TabsTrigger>
        </TabsList>

        <TabsContent value="entity-mappings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                Entity Type Mappings ({entityMappings.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={entityMappings}
                columns={entityMappingColumns}
                actionsOptions={{
                  show: true,
                  actions: actionButtons,
                  showInDropdown: true,
                  dropdownLabel: "Actions",
                }}
                showGlobalFilter={true}
                showColumnFilters={true}
                showPagination={true}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="relationship-mappings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>
                Relationship Type Mappings ({relationshipMappings.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={relationshipMappings}
                columns={relationshipMappingColumns}
                actionsOptions={{
                  show: true,
                  actions: actionButtons,
                  showInDropdown: true,
                  dropdownLabel: "Actions",
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
              <CardTitle>Bulk Mapping Operations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-medium">Auto-Mapping</h3>
                  <p className="text-sm text-gray-600">
                    Automatically create mappings for unmapped entity and
                    relationship types using AI suggestions.
                  </p>
                  <Button className="w-full">
                    <Lightbulb size={16} className="mr-2" />
                    Run Auto-Mapping
                  </Button>
                </div>

                <div className="space-y-4">
                  <h3 className="font-medium">Bulk Verification</h3>
                  <p className="text-sm text-gray-600">
                    Verify all pending mappings with high confidence scores.
                  </p>
                  <Button className="w-full">
                    <CheckCircle size={16} className="mr-2" />
                    Bulk Verify (80%+ confidence)
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* View Mapping Modal */}
      <Dialog
        title="View Mapping Details"
        description="Detailed information about the selected mapping"
        open={isViewModalOpen}
        onOpenChange={setIsViewModalOpen}
      >
        {selectedMapping && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  {"entity_type" in selectedMapping
                    ? "Entity Type"
                    : "Relationship Type"}
                </label>
                <p className="mt-1 font-medium">
                  {"entity_type" in selectedMapping
                    ? selectedMapping.entity_type
                    : selectedMapping.relationship_type}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  {"entity_type" in selectedMapping
                    ? "FIBO Class"
                    : "FIBO Property"}
                </label>
                <p className="mt-1">
                  {"entity_type" in selectedMapping
                    ? selectedMapping.fibo_class?.label || "Unknown"
                    : selectedMapping.fibo_property?.label || "Unknown"}
                </p>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">URI</label>
              <p className="mt-1 font-mono text-sm break-all">
                {"entity_type" in selectedMapping
                  ? selectedMapping.fibo_class_uri
                  : selectedMapping.fibo_property_uri}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Confidence
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <Progress
                    value={(selectedMapping.confidence || 0) * 100}
                    className="w-20 h-2"
                  />
                  <span className="text-sm">
                    {((selectedMapping.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Status
                </label>
                <div className="mt-1">
                  <Badge variant="default">
                    {selectedMapping.mapping_status}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Verified
                </label>
                <div className="mt-1">
                  <Badge
                    variant={
                      selectedMapping.is_verified ? "default" : "secondary"
                    }
                  >
                    {selectedMapping.is_verified ? "Yes" : "No"}
                  </Badge>
                </div>
              </div>
            </div>

            {selectedMapping.mapping_notes && (
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Notes
                </label>
                <p className="mt-1">{selectedMapping.mapping_notes}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Created
                </label>
                <p className="mt-1">
                  {new Date(selectedMapping.created_at).toLocaleString("vi-VN")}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Updated
                </label>
                <p className="mt-1">
                  {new Date(selectedMapping.updated_at).toLocaleString("vi-VN")}
                </p>
              </div>
            </div>
          </div>
        )}
      </Dialog>
      <Dialog
        title="Create Entity Mapping"
        size="2xl"
        description="Map your entity types to FIBO classes"
        open={isEntityMappingWizardOpen}
        onOpenChange={setIsEntityMappingWizardOpen}
      >
        <EntityMappingWizard />
      </Dialog>

      <Dialog
        title="Create Relationship Mapping"
        size="2xl"
        description="Map your relationship types to FIBO properties"
        open={isRelationshipMappingWizardOpen}
        onOpenChange={setIsRelationshipMappingWizardOpen}
      >
        <RelationshipMappingWizard />
      </Dialog>
    </div>
  );
};

export default FIBOMappingManagementPage;
