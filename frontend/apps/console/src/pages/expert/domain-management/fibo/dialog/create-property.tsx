import { Dialog } from "@vbkg/ui";
import FormCreateFiboProperty from "../form/create-property";
import { FIBOClass } from "@vbkg/types";

interface CreaeFiboPropertyDialogProps {
  isCreatePropertyModalOpen: boolean;
  setIsCreatePropertyModalOpen: (open: boolean) => void;
  fiboClasses?: FIBOClass[];
}

export default function CreateFiboPropertyDialog({
  isCreatePropertyModalOpen,
  setIsCreatePropertyModalOpen,
  fiboClasses = [],
}: CreaeFiboPropertyDialogProps) {
  return (
    <Dialog
      title="Create FIBO Property"
      description="Tạo mới một FIBO property"
      open={isCreatePropertyModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsCreatePropertyModalOpen}
    >
      <FormCreateFiboProperty fiboClasses={fiboClasses} />
    </Dialog>
  );
}
