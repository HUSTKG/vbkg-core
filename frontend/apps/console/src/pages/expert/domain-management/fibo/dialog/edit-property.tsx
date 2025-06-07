import { FIBOClass, FIBOProperty } from "@vbkg/types";
import { Dialog } from "@/components";
import FormEditFiboProperty from "../form/edit-property";

interface EditFiboPropertyDialogProps {
  isEditPropertyModalOpen: boolean;
  setIsEditPropertyModalOpen: (open: boolean) => void;
  selectedProperty: FIBOProperty | null;
  getClassById: (id: number) => FIBOClass | undefined;
  fiboClasses: FIBOClass[];
}

export default function EditFiboPropertyDialog({
  isEditPropertyModalOpen,
  setIsEditPropertyModalOpen,
  selectedProperty,
  getClassById,
  fiboClasses,
}: EditFiboPropertyDialogProps) {
  return (
    <Dialog
      title="Edit FIBO Property"
      description="Chỉnh sửa FIBO property"
      open={isEditPropertyModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsEditPropertyModalOpen}
    >
      {selectedProperty && (
        <FormEditFiboProperty
          selectedProperty={selectedProperty}
          fiboClasses={fiboClasses}
          getClassById={getClassById} // Replace with actual class retrieval logic
        />
      )}
    </Dialog>
  );
}
