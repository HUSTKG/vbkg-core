import { useCreateOntologyClass } from "@vbkg/api-client";
import { CreateOntologyClassSchema } from "@vbkg/schemas";
import { OntologyClass } from "@vbkg/types";
import { AppForm, FieldConfig } from "@/components";

interface FormCreateOntologyClassProps {
  ontologyClasses: OntologyClass[];
}

export default function FormCreateOntologyClass({
  ontologyClasses,
}: FormCreateOntologyClassProps) {
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
  const { mutate: createOntologyClass, isPending: loading } = useCreateOntologyClass(
    {},
  );
  const handleCreateClass = (data: any) => {
    const newClass = {
      ...data,
      parent_class_id: data.parent_class_uri
        ? ontologyClasses.find((c) => c.uri === data.parent_class_uri)?.id || null
        : null,
    };
    createOntologyClass(newClass);
  };
  return (
    <AppForm
      fields={getClassFormFields()}
      schema={CreateOntologyClassSchema}
      onSubmit={handleCreateClass}
      submitButtonText="Create Class"
      isLoading={loading}
    />
  );
}
