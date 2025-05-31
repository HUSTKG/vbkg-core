import { FIBOClass } from "@vbkg/types";
import FormEditFiboClass from "../form/edit-class";
import { Dialog } from "@vbkg/ui";

interface EditFiboClassDialogProps {
  isEditClassModalOpen: boolean;
  fiboClasses: FIBOClass[];
  setIsEditClassModalOpen: (open: boolean) => void;
  selectedClass: FIBOClass | null;
  getClassById: (id: number) => FIBOClass | undefined;
}

export default function EditFiboClassDialog({
  isEditClassModalOpen,
  setIsEditClassModalOpen,
  selectedClass,
  fiboClasses,
  getClassById,
}: EditFiboClassDialogProps) {
  return (
    <Dialog
      title="Edit FIBO Class"
      description="Chỉnh sửa FIBO class"
      size="2xl"
      showFooter={false}
      open={isEditClassModalOpen}
      onOpenChange={setIsEditClassModalOpen}
    >
      {selectedClass && (
        <FormEditFiboClass
          getClassById={getClassById}
          fiboClasses={fiboClasses}
          selectedClass={selectedClass}
        />
      )}
    </Dialog>
  );
}
