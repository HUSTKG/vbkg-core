import { AppForm, Badge, Button, Input } from "@/components";
import {
	useCreateRelationshipMapping,
	useRelationshipTypes,
	useSuggestFiboProperties,
} from "@vbkg/api-client";
import { FIBOPropertySuggestion, RelationshipType } from "@vbkg/types";
import { ArrowRight, Lightbulb, RefreshCw } from "lucide-react";
import { useState } from "react";
import { useDebounce } from "use-debounce";
import z from "zod";

interface RelationshipMappingWizardProps {
	setIsRelationshipMappingWizardOpen: (open: boolean) => void;
	refetchRelationshipMappings: () => void;
}

export default function RelationshipMappingWizard({
	setIsRelationshipMappingWizardOpen,
	refetchRelationshipMappings,
}: RelationshipMappingWizardProps) {
	const [searchQuery, setSearchQuery] = useState("");
	const [searchQueryDebounced] = useDebounce(searchQuery, 500);

	const { data: relationshipTypesResponse } = useRelationshipTypes({
		query: searchQueryDebounced,
		is_mapped: false
	});
	const relationshipTypes = relationshipTypesResponse?.data || [];

	// Wizard states
	const [relationshipMappingStep, setRelationshipMappingStep] = useState(1);
	const [relationshipWizardData, setRelationshipWizardData] = useState<{
		relationship_type_id?: number;
		source_entity_type_id?: number;
		target_entity_type_id?: number;
		selected_fibo_uri?: string;
		selected_fibo_property?: FIBOPropertySuggestion;
		relationship_text?: string;
	}>({});

	const getRelationshipTypeById = (id?: number) =>
		relationshipTypes.find((rt: RelationshipType) => rt.id === id);

	const createRelationshipMapping = useCreateRelationshipMapping({
		onSuccess: () => {
			refetchRelationshipMappings();
			setIsRelationshipMappingWizardOpen(false);
			setRelationshipMappingStep(1);
			setRelationshipWizardData({});
		},
		onError: (error) => {
			console.error("Failed to create relationship mapping:", error);
		},
	});
	const {
		data: suggestFiboProperties,
		isFetching: isLoadingPropertySuggestions,
	} = useSuggestFiboProperties({
		relationship_type_id: relationshipWizardData?.relationship_type_id!,
		source_entity_type_id: relationshipWizardData?.source_entity_type_id!,
		target_entity_type_id: relationshipWizardData?.target_entity_type_id!,
	});

	const handleRelationshipTypeSelect = (relationshipTypeId: number) => {
		setRelationshipWizardData((prev) => ({
			...prev,
			relationship_type_id: relationshipTypeId,
		}));
		setRelationshipMappingStep(2);
	};

	const handleSuggestionSelect = (suggestion: FIBOPropertySuggestion) => {
		setRelationshipWizardData((prev) => ({
			...prev,
			selected_fibo_uri: suggestion.fibo_property.uri,
			selected_fibo_property: suggestion,
		}));
		setRelationshipMappingStep(3);
	};

	const handleCreateMapping = (formData: any) => {
		const relationshipType = getRelationshipTypeById(
			relationshipWizardData.relationship_type_id,
		);

		const newMapping = {
			relationship_type: relationshipType?.name,
			relationship_type_id: relationshipWizardData.relationship_type_id,
			fibo_property_uri: relationshipWizardData.selected_fibo_uri!,
			confidence: formData.confidence || 0.9,
			mapping_notes: formData.mapping_notes,
			is_verified: formData.is_verified,
			mapping_status: formData.is_verified
				? ("mapped" as const)
				: ("pending" as const),
			auto_mapped: false,
		};

		createRelationshipMapping.mutate({ ...newMapping });
	};

	// Similar implementation to EntityMappingWizard but for relationships
	if (relationshipMappingStep === 1) {
		return (
			<div className="space-y-4">
				<h3 className="text-lg font-semibold">
					Step 1: Select Relationship Type
				</h3>
				<div>
					<label className="text-sm font-medium">Search Relationship Type</label>
					<Input
						placeholder="VD: Apple Inc., Goldman Sachs..."
						value={searchQuery}
						onChange={(e) => setSearchQuery(e.target.value)}
						className="mt-1"
					/>
				</div>
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
			relationshipWizardData.relationship_type_id,
		);

		return (
			<div className="space-y-4">
				<div className="flex items-center justify-between">
					<h3 className="text-lg font-semibold">Step 2: Select FIBO Class</h3>
					<Button size="sm" onClick={() => setRelationshipMappingStep(1)}>
						Back
					</Button>
				</div>

				<div className="bg-blue-50 p-3 rounded-lg">
					<p className="text-sm">
						<strong>Relationship Type:</strong>{" "}
						{selectedRelationshipType?.display_name}
						{relationshipWizardData.relationship_text && (
							<span className="ml-2">
								<strong>Example:</strong> "
								{relationshipWizardData.relationship_text}"
							</span>
						)}
					</p>
				</div>

				{isLoadingPropertySuggestions ? (
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
							{suggestFiboProperties?.data?.map((suggestion, index) => (
								<button
									key={index}
									onClick={() => handleSuggestionSelect(suggestion)}
									className="w-full p-4 border rounded-lg hover:bg-green-50 hover:border-green-300 text-left transition-colors"
								>
									<div className="flex justify-between items-start">
										<div>
											<p className="font-medium">
												{suggestion.fibo_property.label || "No Label"}
											</p>
											<p className="text-sm text-gray-600">
												{suggestion.fibo_property.description}
											</p>
											<p className="text-xs text-gray-500 font-mono mt-1">
												{suggestion.fibo_property.uri}
											</p>
										</div>
										<Badge variant="outline">
											{suggestion.fibo_property.domain}
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

	if (relationshipMappingStep === 3) {
		const selectedRelationshipType = getRelationshipTypeById(
			relationshipWizardData.relationship_type_id,
		);
		const selectedFIBOClass = relationshipWizardData.selected_fibo_property;

		return (
			<div className="space-y-4">
				<div className="flex items-center justify-between">
					<h3 className="text-lg font-semibold">Step 3: Confirm Mapping</h3>
					<Button size="sm" onClick={() => setRelationshipMappingStep(2)}>
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
						<span className="font-medium">
							{selectedFIBOClass?.fibo_property.label}
						</span>
						<Badge variant="outline">
							{selectedFIBOClass?.fibo_property.domain}
						</Badge>
					</div>
					<p className="text-sm text-gray-600 mt-2">
						{selectedFIBOClass?.fibo_property?.description}
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
					isLoading={createRelationshipMapping.isPending}
				/>
			</div>
		);
	}

	return null;
}
