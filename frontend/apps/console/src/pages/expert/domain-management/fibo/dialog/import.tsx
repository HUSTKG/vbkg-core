import { Dialog } from "@vbkg/ui";
import FormImportOntology from "../form/import";

interface ImportOntologyDialogProps {
  isImportModalOpen: boolean;
  setIsImportModalOpen: (open: boolean) => void;
  importProgress: number;
}

export default function ImportOntologyDialog({
  isImportModalOpen,
  setIsImportModalOpen,
  importProgress,
}: ImportOntologyDialogProps) {
  return (
    <Dialog
      title="Import FIBO Ontology"
      description="Nhập FIBO ontology từ URL hoặc tệp tin"
      size="2xl"
      showFooter={false}
      open={isImportModalOpen}
      onOpenChange={setIsImportModalOpen}
    >
      <FormImportOntology
        importProgress={importProgress}
        setIsImportModalOpen={setIsImportModalOpen}
      />
    </Dialog>
  );
}
