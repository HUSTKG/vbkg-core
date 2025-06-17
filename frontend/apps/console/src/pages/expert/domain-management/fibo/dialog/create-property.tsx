import { Dialog } from "@/components";
import FormCreateOntologyProperty from "../form/create-property";
import { OntologyClass } from "@vbkg/types";

interface CreaeOntologyPropertyDialogProps {
  isCreatePropertyModalOpen: boolean;
  setIsCreatePropertyModalOpen: (open: boolean) => void;
  ontologyClasses?: OntologyClass[];
}

export default function CreateOntologyPropertyDialog({
  isCreatePropertyModalOpen,
  setIsCreatePropertyModalOpen,
  ontologyClasses = [],
}: CreaeOntologyPropertyDialogProps) {
  return (
    <Dialog
      title="Create Ontology Property"
      description="Tạo mới một Ontology property"
      open={isCreatePropertyModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsCreatePropertyModalOpen}
    >
      <FormCreateOntologyProperty ontologyClasses={ontologyClasses} />
    </Dialog>
  );
}
