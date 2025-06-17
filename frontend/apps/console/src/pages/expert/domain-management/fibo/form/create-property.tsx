import { useCreateOntologyProperty } from "@vbkg/api-client";
import { CreateOntologyPropertySchema } from "@vbkg/schemas";
import { OntologyClass } from "@vbkg/types";
import { AppForm, FieldConfig } from "@/components";
import { z } from "zod";

interface FormCreateOntologyPropertyProps {
  ontologyClasses: OntologyClass[];
}

export default function FormCreateOntologyProperty({
  ontologyClasses,
}: FormCreateOntologyPropertyProps) {
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

  const { mutate: createOntologyProperty, isPending: loading } =
    useCreateOntologyProperty({});

  const handleCreateProperty = async (
    data: z.infer<typeof CreateOntologyPropertySchema>,
  ) => {
    createOntologyProperty({
      ...data,
    });
  };

  return (
    <AppForm
      fields={getPropertyFormFields()}
      schema={CreateOntologyPropertySchema}
      onSubmit={handleCreateProperty}
      submitButtonText="Create Property"
      isLoading={loading}
    />
  );
}
