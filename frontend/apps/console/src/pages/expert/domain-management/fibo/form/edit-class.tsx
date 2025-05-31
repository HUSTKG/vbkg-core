import { useUpdateFiboClass } from "@vbkg/api-client";
import { UpdateFiboClassSchema } from "@vbkg/schemas";
import { FIBOClass } from "@vbkg/types";
import { AppForm, FieldConfig } from "@vbkg/ui";

interface FormEditFiboClassProps {
  selectedClass: FIBOClass;
  fiboClasses: FIBOClass[];
  getClassById: (id: number) => FIBOClass | undefined;
}

export default function FormEditFiboClass({
  selectedClass,
  fiboClasses,
  getClassById,
}: FormEditFiboClassProps) {
  const { mutate: updateFiboClass, isPending: loading } = useUpdateFiboClass(
    {},
  );
  const handleUpdateClass = (data: any) => {
    const updatedClass = {
      ...data,
      parent_class_id: data.parent_class_uri
        ? getClassById(data.parent_class_uri)?.id || null
        : null,
    };
    updateFiboClass(updatedClass);
  };

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
  return (
    <AppForm
      fields={getClassFormFields()}
      schema={UpdateFiboClassSchema}
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
