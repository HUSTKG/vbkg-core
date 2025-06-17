import { useUpdateOntologyClass } from "@vbkg/api-client";
import { UpdateOntologyClassSchema } from "@vbkg/schemas";
import { OntologyClass } from "@vbkg/types";
import { AppForm, FieldConfig, toast } from "@/components";

interface FormEditOntologyClassProps {
	selectedClass: OntologyClass;
	ontologyClasses: OntologyClass[];
	getClassById: (id: number) => OntologyClass | undefined;
}

export default function FormEditOntologyClass({
	selectedClass,
	ontologyClasses,
	getClassById,
}: FormEditOntologyClassProps) {
	const { mutate: updateOntologyClass, isPending: loading } = useUpdateOntologyClass({
		onSuccess: () => {
			toast.success("Cập nhật Ontology class thành công");
		},
		onError: (error) => {
			toast.error("Cập nhật Ontology class thất bại: " + error.message);
		},
	});
	const handleUpdateClass = (data: any) => {
		const updatedClass = {
			...data,
			id: selectedClass.id,
			parent_class_id: data.parent_class_uri
				? getClassById(data.parent_class_uri)?.id || null
				: null,
		};
		updateOntologyClass(updatedClass);
	};

	const getClassFormFields = (): FieldConfig[] => [
		{
			name: "uri",
			label: "URI",
			type: "text",
			placeholder: "https://spec.edmcouncil.org/ontology/ontology/...",
			required: true,
			description: "URI duy nhất của Ontology class",
		},
		{
			name: "label",
			label: "Label",
			type: "text",
			placeholder: "VD: Organization, Person, Financial Instrument",
			description: "Nhãn hiển thị của class",
		},
		{
			name: "description",
			label: "Description",
			type: "textarea",
			placeholder: "Mô tả chi tiết về class này...",
			description: "Mô tả về class",
		},
		{
			name: "domain",
			label: "Domain",
			type: "text",
			placeholder: "VD: FBC, SEC, FND",
			description: "Domain trong Ontology taxonomy",
		},
		{
			name: "parent_class_uri",
			label: "Parent Class",
			type: "select",
			options: ontologyClasses.map((c) => ({
				label: `${c.label || c.uri} (${c.domain || "No domain"})`,
				value: c.uri,
			})),
			description: "Class cha (nếu có)",
		},
		{
			name: "is_custom",
			label: "Custom Class",
			type: "switch",
			defaultValue: false,
			description: "Đây có phải là custom class không thuộc Ontology chuẩn",
		},
	];
	return (
		<AppForm
			fields={getClassFormFields()}
			schema={UpdateOntologyClassSchema}
			defaultValues={{
				...selectedClass,
				parent_class_uri: selectedClass.parent_class_id
					? getClassById(selectedClass.parent_class_id)?.uri
					: undefined,
			}}
			onSubmit={handleUpdateClass}
			submitButtonText="Update Class"
			isLoading={loading}
		/>
	);
}
