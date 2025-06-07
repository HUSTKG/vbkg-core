import { AppForm, Dialog } from "@/components";
import {
	useCreateEntity,
	useEntityTypes,
	useUpdateEntity,
} from "@vbkg/api-client";
import { CreateEntitySchema } from "@vbkg/schemas";
import { Entity } from "@vbkg/types";
import z from "zod";

export default function CreateEntityDialog({
	showCreateDialog,
	setShowCreateDialog,
	selectedEntity,
	mode,
}: {
	showCreateDialog: boolean;
	setShowCreateDialog: (open: boolean) => void;
	selectedEntity?: Entity;
	mode?: "create" | "edit";
}) {
	const { mutate: createKGEntity } = useCreateEntity({
		onSuccess: () => {
			setShowCreateDialog(false);
		},
		onError: (error) => {
			console.error("Failed to create entity:", error);
		},
	});

	const { mutate: updateKGEntity } = useUpdateEntity({
		onSuccess: () => {
			setShowCreateDialog(false);
		},
		onError: (error) => {
			console.error("Failed to update entity:", error);
		},
	});

	const { data: entityTypes } = useEntityTypes({});

	const handleSubmit = (data: z.infer<typeof CreateEntitySchema>) => {
		if (mode === "create") {
			createKGEntity({
				entity_text: data.entity_text,
				entity_type: data.entity_type,
				properties: data.properties ? (data.properties as any) : {},
				is_verified: data.is_verified || false,
				confidence: data.confidence || 0.5,
			});
		} else if (mode === "edit") {
			if (!selectedEntity) {
				console.error("No entity selected for editing");
				return;
			}
			updateKGEntity({
				id: selectedEntity?.id,
				entity_text: data.entity_text,
				entity_type: data.entity_type,
				properties: data.properties ? (data.properties as any) : {},
				is_verified: data.is_verified || false,
				confidence: data.confidence || 0.5,
			});
		}
	};

	return (
		<Dialog
			title={mode === "edit" ? "Edit Entity" : "Create Entity"}
			description={
				mode === "edit"
					? "Edit the details of the selected entity"
					: "Create a new entity in the knowledge graph"
			}
			open={showCreateDialog}
			size="2xl"
			onOpenChange={setShowCreateDialog}
		>
			<AppForm
				schema={CreateEntitySchema}
				onSubmit={(data) => {
					handleSubmit(data);
				}}
				defaultValues={
					mode === "edit" && selectedEntity
						? {
								entity_text: selectedEntity.entity_text,
								entity_type: selectedEntity.entity_type,
								properties: JSON.stringify(selectedEntity.properties) || "{}",
								is_verified: selectedEntity.is_verified,
								confidence: selectedEntity.confidence || 0.5,
							}
						: {}
				}
				fields={[
					{
						name: "entity_text",
						label: "Entity Text",
						type: "text",
						required: true,
					},
					{
						name: "entity_type",
						label: "Entity Type",
						type: "select",
						placeholder: "Select entity type",
						options:
							entityTypes?.data?.map((type) => ({
								value: type.name,
								label: type.display_name,
							})) || [],
						required: true,
					},
					{
						name: "properties",
						label: "Properties (JSON)",
						type: "textarea",
						placeholder: '{"industry": "Technology", "founded": "1976"}',
					},
					{
						name: "is_verified",
						label: "Mark as verified",
						type: "switch",
					},
				]}
			/>
		</Dialog>
	);
}
