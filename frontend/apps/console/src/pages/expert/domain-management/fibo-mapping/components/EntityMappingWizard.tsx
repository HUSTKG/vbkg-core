import { Lightbulb, ArrowRight, RefreshCw } from "lucide-react";
import * as z from "zod";
import {
	useCreateEntityMapping,
	useEntityTypes,
	useSuggestFiboClasses,
} from "@vbkg/api-client";
import { AppForm, Badge, Button, Input } from "@/components";
import { EntityType, FIBOClassSuggestion } from "@vbkg/types";
import { useState } from "react";
import { useDebounce } from "use-debounce";

interface EntityMappingWizardProps {
	setIsEntityMappingWizardOpen: (open: boolean) => void;
	refetchEntityMappings: () => void;
}

export default function EntityMappingWizard({
	setIsEntityMappingWizardOpen,
	refetchEntityMappings,
}: EntityMappingWizardProps) {
	const getEntityTypeById = (id?: number) =>
		entityTypes.find((et: EntityType) => et.id === id);

	const [entityMappingStep, setEntityMappingStep] = useState(1);

	const [searchQuery, setSearchQuery] = useState("");

	const [searchQueryDebounced] = useDebounce(searchQuery, 500);

	const { data: entityTypesResponse } = useEntityTypes({
		query: searchQueryDebounced,
		is_mapped: false,
		limit: 10
	});

	const entityTypes = entityTypesResponse?.data || [];


	const [entityWizardData, setEntityWizardData] = useState<{
		entity_text?: string;
		entity_type_id?: number;
		selected_fibo_uri?: string;
		selected_fibo_class?: FIBOClassSuggestion;
	}>({});
	const { data: suggestFiboClasses, isFetching: isLoadingClassSuggestions } =
		useSuggestFiboClasses({
			entity_type_id: entityWizardData?.entity_type_id,
			entity_text: entityWizardData?.entity_text,
			max_suggestions: 10,
		});

	const createEntityMapping = useCreateEntityMapping({
		onSuccess: () => {
			refetchEntityMappings();
			setIsEntityMappingWizardOpen(false);
			setEntityMappingStep(1);
			setEntityWizardData({});
		},
		onError: (error) => {
			console.error("Failed to create entity mapping:", error);
		},
	});

	const handleEntityTypeSelect = (entityTypeId: number) => {
		setEntityWizardData((prev: any) => ({
			...prev,
			entity_type_id: entityTypeId,
		}));
		setEntityMappingStep(2);
	};

	const handleSuggestionSelect = (suggestion: FIBOClassSuggestion) => {
		setEntityWizardData((prev: any) => ({
			...prev,
			selected_fibo_uri: suggestion.fibo_class.uri,
			selected_fibo_class: suggestion,
		}));
		setEntityMappingStep(3);
	};

	const handleCreateMapping = (formData: any) => {
		const entityType = getEntityTypeById(entityWizardData.entity_type_id);

		const newMapping = {
			entity_type: entityType?.name,
			entity_type_id: entityWizardData.entity_type_id,
			fibo_class_uri: entityWizardData.selected_fibo_uri!,
			confidence: formData.confidence || 0.9,
			mapping_notes: formData.mapping_notes,
			is_verified: formData.is_verified,
			mapping_status: formData.is_verified
				? ("mapped" as const)
				: ("pending" as const),
			auto_mapped: false,
		};

		createEntityMapping.mutate({ ...newMapping });
	};

	if (entityMappingStep === 1) {
		return (
			<div className="space-y-4">
				<h3 className="text-lg font-semibold">Step 1: Select Entity Type</h3>

				<div>
					<label className="text-sm font-medium">Search Entity Type</label>
					<Input
						placeholder="VD: Apple Inc., Goldman Sachs..."
						value={searchQuery}
						onChange={(e) => setSearchQuery(e.target.value)}
						className="mt-1"
					/>
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
		const selectedEntityType = getEntityTypeById(
			entityWizardData?.entity_type_id,
		);

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
						{entityWizardData.entity_text && (
							<span className="ml-2">
								<strong>Example:</strong> "{entityWizardData.entity_text}"
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
							{suggestFiboClasses?.data?.map((suggestion, index) => (
								<button
									key={index}
									onClick={() => handleSuggestionSelect(suggestion)}
									className="w-full p-4 border rounded-lg hover:bg-green-50 hover:border-green-300 text-left transition-colors"
								>
									<div className="flex justify-between items-start">
										<div>
											<p className="font-medium">
												{suggestion.fibo_class.label || "No Label"}
											</p>
											<p className="text-sm text-gray-600">
												{suggestion.fibo_class.description}
											</p>
											<p className="text-xs text-gray-500 font-mono mt-1">
												{suggestion.fibo_class.uri}
											</p>
										</div>
										<Badge variant="outline">
											{suggestion.fibo_class.domain}
										</Badge>
									</div>
								</button>
							))}
						</div>
					</div>
				)}
			</div>
		);
	}

	if (entityMappingStep === 3) {
		const selectedEntityType = getEntityTypeById(
			entityWizardData.entity_type_id,
		);
		const selectedFIBOClass = entityWizardData.selected_fibo_class;

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
						<span className="font-medium">
							{selectedFIBOClass?.fibo_class.label}
						</span>
						<Badge variant="outline">
							{selectedFIBOClass?.fibo_class.domain}
						</Badge>
					</div>
					<p className="text-sm text-gray-600 mt-2">
						{selectedFIBOClass?.fibo_class.description}
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
					isLoading={createEntityMapping.isPending}
				/>
			</div>
		);
	}

	return null;
}
