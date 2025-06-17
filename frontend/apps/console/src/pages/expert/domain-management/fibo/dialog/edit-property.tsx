import { OntologyClass, OntologyProperty } from "@vbkg/types";
import { Dialog } from "@/components";
import FormEditOntologyProperty from "../form/edit-property";

interface EditOntologyPropertyDialogProps {
  isEditPropertyModalOpen: boolean;
  setIsEditPropertyModalOpen: (open: boolean) => void;
  selectedProperty: OntologyProperty | null;
  getClassById: (id: number) => OntologyClass | undefined;
  ontologyClasses: OntologyClass[];
}

export default function EditOntologyPropertyDialog({
  isEditPropertyModalOpen,
  setIsEditPropertyModalOpen,
  selectedProperty,
  getClassById,
  ontologyClasses,
}: EditOntologyPropertyDialogProps) {
  return (
    <Dialog
      title="Edit Ontology Property"
      description="Chỉnh sửa Ontology property"
      open={isEditPropertyModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsEditPropertyModalOpen}
    >
      {selectedProperty && (
        <FormEditOntologyProperty
          selectedProperty={selectedProperty}
          ontologyClasses={ontologyClasses}
          getClassById={getClassById} // Replace with actual class retrieval logic
        />
      )}
    </Dialog>
  );
}
