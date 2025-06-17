import { useUpdateOntologyProperty } from "@vbkg/api-client";
import { UpdateOntologyPropertySchema } from "@vbkg/schemas";
import { OntologyClass, OntologyProperty } from "@vbkg/types";
import { AppForm, FieldConfig, toast } from "@/components";
import { z } from "zod";

interface FormEditOntologyPropertyProps {
  selectedProperty: OntologyProperty;
  ontologyClasses: OntologyClass[];
  getClassById: (id: number) => OntologyClass | undefined;
}

export default function FormEditOntologyProperty({
  selectedProperty,
  ontologyClasses,
  getClassById,
}: FormEditOntologyPropertyProps) {
  const { mutate: updateProperty, isPending: loading } = useUpdateOntologyProperty({
    onSuccess: () => {
      toast("Property updated successfully");
    },
    onError: (error) => {
      toast(`Error updating property: ${error.message}`);
    },
  });

  const handleUpdateProperty = async (
    data: z.infer<typeof UpdateOntologyPropertySchema>,
  ) => {
    updateProperty({
      ...data,
      id: selectedProperty.id,
      domain_class_id: data.domain_class_uri
        ? ontologyClasses.find((c) => c.uri === data.domain_class_uri)?.id
        : null,
      range_class_id: data.range_class_uri
        ? ontologyClasses.find((c) => c.uri === data.range_class_uri)?.id
        : null,
    });
  };

  const getPropertyFormFields = (): FieldConfig[] => [
    {
      name: "uri",
      label: "URI",
      type: "text",
      placeholder: "https://spec.edmcouncil.org/ontology/ontology/...",
      required: true,
      description: "URI duy nhất của Ontology property",
    },
    {
      name: "label",
      label: "Label",
      type: "text",
      placeholder: "VD: owns, employedBy, hasName",
      description: "Nhãn hiển thị của property",
    },
    {
      name: "description",
      label: "Description",
      type: "textarea",
      placeholder: "Mô tả chi tiết về property này...",
      description: "Mô tả về property",
    },
    {
      name: "property_type",
      label: "Property Type",
      type: "select",
      options: [
        { label: "Object Property", value: "object" },
        { label: "Datatype Property", value: "datatype" },
      ],
      required: true,
      description:
        "Loại property: object (liên kết classes) hoặc datatype (dữ liệu literal)",
    },
    {
      name: "domain_class_uri",
      label: "Domain Class",
      type: "select",
      options: ontologyClasses.map((c) => ({
        label: `${c.label || c.uri} (${c.domain || "No domain"})`,
        value: c.uri,
      })),
      description: "Class nguồn của property (subject)",
    },
    {
      name: "range_class_uri",
      label: "Range Class",
      type: "select",
      options: ontologyClasses.map((c) => ({
        label: `${c.label || c.uri} (${c.domain || "No domain"})`,
        value: c.uri,
      })),
      description: "Class đích của property (object) - chỉ cho object property",
    },
    {
      name: "is_custom",
      label: "Custom Property",
      type: "switch",
      defaultValue: false,
      description: "Đây có phải là custom property không thuộc Ontology chuẩn",
    },
  ];
  return (
    <AppForm
      fields={getPropertyFormFields()}
      schema={UpdateOntologyPropertySchema}
      defaultValues={{
        ...selectedProperty,
        domain_class_uri: selectedProperty.domain_class_id
          ? getClassById(selectedProperty.domain_class_id)?.uri
          : undefined,
        range_class_uri: selectedProperty.range_class_id
          ? getClassById(selectedProperty.range_class_id)?.uri
          : undefined,
      }}
      onSubmit={handleUpdateProperty}
      submitButtonText="Update Property"
      isLoading={loading}
    />
  );
}
