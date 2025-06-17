import { OntologyClass } from "@vbkg/types";
import FormEditOntologyClass from "../form/edit-class";
import { Dialog } from "@/components";

interface EditOntologyClassDialogProps {
  isEditClassModalOpen: boolean;
  ontologyClasses: OntologyClass[];
  setIsEditClassModalOpen: (open: boolean) => void;
  selectedClass: OntologyClass | null;
  getClassById: (id: number) => OntologyClass | undefined;
}

export default function EditOntologyClassDialog({
  isEditClassModalOpen,
  setIsEditClassModalOpen,
  selectedClass,
  ontologyClasses,
  getClassById,
}: EditOntologyClassDialogProps) {
  return (
    <Dialog
      title="Edit Ontology Class"
      description="Chỉnh sửa Ontology class"
      size="2xl"
      showFooter={false}
      open={isEditClassModalOpen}
      onOpenChange={setIsEditClassModalOpen}
    >
      {selectedClass && (
        <FormEditOntologyClass
          getClassById={getClassById}
          ontologyClasses={ontologyClasses}
          selectedClass={selectedClass}
        />
      )}
    </Dialog>
  );
}
