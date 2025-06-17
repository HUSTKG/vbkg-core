import { OntologyClass } from "@vbkg/types";
import FormCreateOntologyClass from "../form/create-class";
import { Dialog } from "@/components";

export default function CreateOntologyClassDialog({
  isCreateClassModalOpen,
  setIsCreateClassModalOpen,
  ontologyClasses = [],
}: {
  isCreateClassModalOpen: boolean;
  setIsCreateClassModalOpen: (open: boolean) => void;
  ontologyClasses?: OntologyClass[];
}) {
  return (
    <Dialog
      title="Create Ontology Class"
      description="Tạo mới một Ontology class"
      open={isCreateClassModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsCreateClassModalOpen}
    >
      <FormCreateOntologyClass ontologyClasses={ontologyClasses} />
    </Dialog>
  );
}
