import { AppForm, FieldConfig } from "@/components";
import { UpdateDomainSchema } from "@vbkg/schemas";
import { Domain } from "@vbkg/types";
import { z } from "zod";

interface FormEditDomainProps {
  defaultValues: Domain;
  handleUpdateDomain: (data: z.infer<typeof UpdateDomainSchema>) => void;
  isLoading?: boolean;
}

export default function FormEditDomain({
  defaultValues: selectedDomain,
  handleUpdateDomain,
  isLoading,
}: FormEditDomainProps) {
  const getFormFields = (): FieldConfig[] => [
    {
      name: "name",
      label: "Tên Domain",
      type: "text",
      placeholder: "VD: financial, legal, business",
      required: true,
      description:
        "Tên duy nhất của domain (chỉ chứa chữ thường, số và dấu gạch dưới)",
    },
    {
      name: "display_name",
      label: "Tên Hiển Thị",
      type: "text",
      placeholder: "VD: Financial Services",
      required: true,
      description: "Tên hiển thị thân thiện với người dùng",
    },
    {
      name: "description",
      label: "Mô Tả",
      type: "textarea",
      placeholder: "Mô tả chi tiết về domain này...",
      description: "Mô tả về mục đích và phạm vi của domain",
    },
    {
      name: "color",
      label: "Màu Sắc",
      type: "text",
      defaultValue: "#6366F1",
      placeholder: "#6366F1",
      description: "Màu sắc đại diện cho domain (hex color)",
    },
    {
      name: "icon",
      label: "Icon",
      type: "text",
      placeholder: "VD: Database, Settings, BarChart3",
      description: "Tên icon Lucide React",
    },
    {
      name: "ontology_namespace",
      label: "Ontology Namespace",
      type: "text",
      placeholder: "https://example.org/ontology/",
      description: "Base namespace cho ontology của domain này",
    },
    {
      name: "is_active",
      label: "Kích Hoạt",
      type: "switch",
      defaultValue: true,
      description: "Domain có đang được sử dụng không",
    },
  ];
  return (
    <AppForm
      fields={getFormFields()}
      schema={UpdateDomainSchema}
      defaultValues={selectedDomain}
      onSubmit={handleUpdateDomain}
      submitButtonText="Cập Nhật Domain"
      isLoading={isLoading}
    />
  );
}
