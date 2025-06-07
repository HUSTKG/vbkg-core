import { useCreateFiboProperty } from "@vbkg/api-client";
import { CreateFiboPropertySchema } from "@vbkg/schemas";
import { FIBOClass } from "@vbkg/types";
import { AppForm, FieldConfig } from "@/components";
import { z } from "zod";

interface FormCreateFiboPropertyProps {
  fiboClasses: FIBOClass[];
}

export default function FormCreateFiboProperty({
  fiboClasses,
}: FormCreateFiboPropertyProps) {
  const getPropertyFormFields = (): FieldConfig[] => [
    {
      name: "uri",
      label: "URI",
      type: "text",
      placeholder: "https://spec.edmcouncil.org/fibo/ontology/...",
      required: true,
      description: "URI duy nhất của FIBO property",
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
      options: fiboClasses.map((c) => ({
        label: `${c.label || c.uri} (${c.domain || "No domain"})`,
        value: c.uri,
      })),
      description: "Class nguồn của property (subject)",
    },
    {
      name: "range_class_uri",
      label: "Range Class",
      type: "select",
      options: fiboClasses.map((c) => ({
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
      description: "Đây có phải là custom property không thuộc FIBO chuẩn",
    },
  ];

  const { mutate: createFiboProperty, isPending: loading } =
    useCreateFiboProperty({});

  const handleCreateProperty = async (
    data: z.infer<typeof CreateFiboPropertySchema>,
  ) => {
    createFiboProperty({
      ...data,
    });
  };

  return (
    <AppForm
      fields={getPropertyFormFields()}
      schema={CreateFiboPropertySchema}
      onSubmit={handleCreateProperty}
      submitButtonText="Create Property"
      isLoading={loading}
    />
  );
}
