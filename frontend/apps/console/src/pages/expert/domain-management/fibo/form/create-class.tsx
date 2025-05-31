import { useCreateFiboClass } from "@vbkg/api-client";
import { CreateFiboClassSchema } from "@vbkg/schemas";
import { FIBOClass } from "@vbkg/types";
import { AppForm, FieldConfig } from "@vbkg/ui";

interface FormCreateFiboClassProps {
  fiboClasses: FIBOClass[];
}

export default function FormCreateFiboClass({
  fiboClasses,
}: FormCreateFiboClassProps) {
  const getClassFormFields = (): FieldConfig[] => [
    {
      name: "uri",
      label: "URI",
      type: "text",
      placeholder: "https://spec.edmcouncil.org/fibo/ontology/...",
      required: true,
      description: "URI duy nhất của FIBO class",
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
      description: "Domain trong FIBO taxonomy",
    },
    {
      name: "parent_class_uri",
      label: "Parent Class",
      type: "select",
      options: fiboClasses.map((c) => ({
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
      description: "Đây có phải là custom class không thuộc FIBO chuẩn",
    },
  ];
  const { mutate: createFiboClass, isPending: loading } = useCreateFiboClass(
    {},
  );
  const handleCreateClass = (data: any) => {
    const newClass = {
      ...data,
      parent_class_id: data.parent_class_uri
        ? fiboClasses.find((c) => c.uri === data.parent_class_uri)?.id || null
        : null,
    };
    createFiboClass(newClass);
  };
  return (
    <AppForm
      fields={getClassFormFields()}
      schema={CreateFiboClassSchema}
      onSubmit={handleCreateClass}
      submitButtonText="Create Class"
      isLoading={loading}
    />
  );
}
