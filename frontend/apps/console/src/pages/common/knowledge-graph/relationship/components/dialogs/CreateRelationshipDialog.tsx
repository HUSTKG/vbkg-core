import { AppForm, Dialog } from "@/components";
import {
	useCreateRelationship,
	useKGEntitiesSearch,
	useRelationshipTypes,
} from "@vbkg/api-client";
import { CreateRelationshipSchema } from "@vbkg/schemas";
import { Relationship } from "@vbkg/types";
import z from "zod";

interface CreateRelationshipDialogProps {
	showCreateDialog: boolean;
	setShowCreateDialog: (open: boolean) => void;
	selectedRelationship?: Relationship; // Adjust type as needed
	mode?: "create" | "edit";
}

export default function CreateRelationshipDialog({
	showCreateDialog,
	setShowCreateDialog,
	selectedRelationship,
	mode = "create",
}: CreateRelationshipDialogProps) {
	const { data: relationshipTypes } = useRelationshipTypes({});
	const { data: entities } = useKGEntitiesSearch({
		limit: 100,
	});
	const { mutate: createRelationship } = useCreateRelationship({
		onSuccess: () => {
			setShowCreateDialog(false);
		},
		onError: (error) => {
			console.error("Failed to create relationship:", error);
		},
	});
	const handleSubmit = (data: z.infer<typeof CreateRelationshipSchema>) => {
		createRelationship({
			relationship_type: data.relationship_type,
			source_entity_id: data.source_entity_id,
			target_entity_id: data.target_entity_id,
			properties: data.properties ? (data.properties as any) : {},
			is_verified: data.is_verified,
			verification_notes: data.verification_notes || "",
		});
	};
	return (
		<Dialog
			title={mode === "create" ? "Create Relationship" : "Edit Relationship"}
			description={
				mode === "create"
					? "Create a new relationship between entities"
					: "Edit the selected relationship"
			}
			open={showCreateDialog}
			onOpenChange={setShowCreateDialog}
		>
			<AppForm
				onSubmit={handleSubmit}
				defaultValues={
					mode === "edit"
						? {
								source_entity_id: selectedRelationship?.source_entity.id,
								target_entity_id: selectedRelationship?.target_entity.id,
								relationship_type: selectedRelationship?.relationship_type,
								properties: JSON.stringify(selectedRelationship?.properties) || "{}",
								is_verified: selectedRelationship?.is_verified || false,
								verification_notes: "",
							}
						: {}
				}
				fields={[
					{
						name: "source_entity_id",
						type: "select",
						label: "Source Entity",
						placeholder: "Select source entity",
						options:
							entities?.data?.map((entity) => ({
								value: entity.id,
								label: `${entity.entity_text} (${entity.entity_type})`,
							})) || [],
						required: true,
					},
					{
						name: "target_entity_id",
						type: "select",
						label: "Target Entity",
						placeholder: "Select target entity",
						options:
							entities?.data?.map((entity) => ({
								value: entity.id,
								label: `${entity.entity_text} (${entity.entity_type})`,
							})) || [],
						required: true,
					},
					{
						name: "relationship_type",
						type: "select",
						label: "Relationship Type",
						placeholder: "Select relationship type",
						options:
							relationshipTypes?.data?.map((type) => ({
								value: type.name,
								label: type.display_name,
							})) || [],
						required: true,
					},
					{
						name: "properties",
						type: "textarea",
						label: "Properties (JSON)",
					},
					{
						name: "is_verified",
						type: "switch",
						label: "Is Verified?",
					},
					{
						name: "verification_notes",
						type: "textarea",
						label: "Verification Notes",
					},
				]}
				schema={CreateRelationshipSchema}
			/>
		</Dialog>
	);
}
