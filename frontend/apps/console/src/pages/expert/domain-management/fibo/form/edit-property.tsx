import { useUpdateFiboProperty } from "@vbkg/api-client";
import { UpdateFiboPropertySchema } from "@vbkg/schemas";
import { FIBOClass, FIBOProperty } from "@vbkg/types";
import { AppForm, FieldConfig, toast } from "@vbkg/ui";
import { z } from "zod";

interface FormEditFiboPropertyProps {
  selectedProperty: FIBOProperty;
  fiboClasses: FIBOClass[];
  getClassById: (id: number) => FIBOClass | undefined;
}

export default function FormEditFiboProperty({
  selectedProperty,
  fiboClasses,
  getClassById,
}: FormEditFiboPropertyProps) {
  const { mutate: updateProperty, isPending: loading } = useUpdateFiboProperty({
    onSuccess: () => {
      toast("Property updated successfully");
    },
    onError: (error) => {
      toast(`Error updating property: ${error.message}`);
    },
  });

  const handleUpdateProperty = async (
    data: z.infer<typeof UpdateFiboPropertySchema>,
  ) => {
    updateProperty({
      ...data,
      id: selectedProperty.id,
      domain_class_id: data.domain_class_uri
        ? fiboClasses.find((c) => c.uri === data.domain_class_uri)?.id
        : null,
      range_class_id: data.range_class_uri
        ? fiboClasses.find((c) => c.uri === data.range_class_uri)?.id
        : null,
    });
  };

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
  return (
    <AppForm
      fields={getPropertyFormFields()}
      schema={UpdateFiboPropertySchema}
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
