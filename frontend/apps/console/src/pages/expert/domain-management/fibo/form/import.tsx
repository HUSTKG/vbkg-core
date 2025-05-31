import { useImportOntology } from "@vbkg/api-client";
import { ImportOntologySchema } from "@vbkg/schemas";
import { AppForm, Button, Input, Progress } from "@vbkg/ui";
import FileUploadFormItem from "../../../../../components/form-item/upload-file";
import { z } from "zod";

interface FormImportOntologyProps {
  importProgress: number;
  setIsImportModalOpen: (open: boolean) => void;
}

export default function FormImportOntology({
  importProgress,
  setIsImportModalOpen,
}: FormImportOntologyProps) {
  const { mutate: importOntology, isPending: loading } = useImportOntology({});

  const handleImportOntology = async (
    data: z.infer<typeof ImportOntologySchema>,
  ) => {
    importOntology({
      file_id: data?.file_id?.[0]?.id,
      url: data?.url,
      format: data.format,
    });
  };

  return (
    <AppForm
      fields={(form) => [
        {
          name: "source_type",
          label: "Import Source",
          type: "select",
          options: [
            { label: "From URL", value: "url" },
            { label: "Upload File", value: "file" },
          ],
          defaultValue: "url",
          required: true,
        },
        {
          name: "url",
          label: "Ontology URL",
          type:
            form.source_type && form.source_type === "url" ? "text" : "hidden",
          placeholder: "https://spec.edmcouncil.org/fibo/ontology/...",
        },
        {
          name: "file_id",
          label: "Upload File",
          type:
            form.source_type && form.source_type === "file"
              ? "custom"
              : "hidden",
          placeholder: "Chọn tệp FIBO ontology",
          customComponent: ({ value, onChange }) => (
            <FileUploadFormItem
              value={value}
              maxFiles={1}
              onChange={(value) => {
                onChange(value);
              }}
            />
          ),
        },
        {
          name: "format",
          label: "Format",
          type: "select",
          options: [
            { label: "RDF/XML", value: "rdf" },
            { label: "OWL", value: "owl" },
            { label: "Turtle (TTL)", value: "ttl" },
          ],
          defaultValue: "rdf",
          required: true,
        },
      ]}
      schema={ImportOntologySchema}
      onSubmit={handleImportOntology}
      submitButtonText={loading ? "Importing..." : "Import"}
      isLoading={loading}
      buttons={
        <div className="space-y-4">
          {loading && (
            <div className="space-y-2">
              <Progress value={importProgress} className="w-full" />
              <p className="text-sm text-gray-500 text-center">
                {importProgress}% completed
              </p>
            </div>
          )}
          <div className="flex justify-end space-x-2">
            <Button
              onClick={() => setIsImportModalOpen(false)}
              disabled={loading}
            >
              Hủy
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Importing..." : "Import"}
            </Button>
          </div>
        </div>
      }
    />
  );
}
