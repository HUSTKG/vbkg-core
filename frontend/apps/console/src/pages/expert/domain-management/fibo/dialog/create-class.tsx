import { FIBOClass } from "@vbkg/types";
import FormCreateFiboClass from "../form/create-class";
import { Dialog } from "@/components";

export default function CreateFiboClassDialog({
  isCreateClassModalOpen,
  setIsCreateClassModalOpen,
  fiboClasses = [],
}: {
  isCreateClassModalOpen: boolean;
  setIsCreateClassModalOpen: (open: boolean) => void;
  fiboClasses?: FIBOClass[];
}) {
  return (
    <Dialog
      title="Create FIBO Class"
      description="Tạo mới một FIBO class"
      open={isCreateClassModalOpen}
      size="2xl"
      showFooter={false}
      onOpenChange={setIsCreateClassModalOpen}
    >
      <FormCreateFiboClass fiboClasses={fiboClasses} />
    </Dialog>
  );
}
