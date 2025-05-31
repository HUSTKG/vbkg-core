import { Domain } from "@vbkg/types";
import { AppForm, Dialog } from "@vbkg/ui";
import { UpdateDomainSchema } from "@vbkg/schemas";
import { z } from "zod";
import FormEditDomain from "../form/edit";

interface EditDomainDialogProps {
  isEditModalOpen: boolean;
  setIsEditModalOpen: (open: boolean) => void;
  selectedDomain: Domain | null;
  handleUpdateDomain: (data: z.infer<typeof UpdateDomainSchema>) => void;
  loading: boolean;
}
export default function EditDomainDialog({
  isEditModalOpen,
  setIsEditModalOpen,
  selectedDomain,
  handleUpdateDomain,
  loading,
}: EditDomainDialogProps) {
  return (
    <Dialog
      title="Chỉnh Sửa Domain"
      description="Chỉnh sửa thông tin domain này"
      open={isEditModalOpen}
      onOpenChange={setIsEditModalOpen}
    >
      {selectedDomain && <FormEditDomain />}
    </Dialog>
  );
}
