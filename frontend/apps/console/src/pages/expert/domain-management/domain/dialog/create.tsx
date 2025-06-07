import { Dialog } from "@/components";
import FormCreateDialog from "../form/create";

interface CreateDomainDialogProps {
  isCreateModalOpen: boolean;
  setIsCreateModalOpen: (open: boolean) => void;
  handleCreateDomain: (data: any) => void;
  isLoading: boolean;
}

export default function CreateDomainDialog({
  isCreateModalOpen,
  setIsCreateModalOpen,
  handleCreateDomain,
  isLoading,
}: CreateDomainDialogProps) {
  return (
    <Dialog
      title="Tạo Domain Mới"
      description="Tạo một domain mới để quản lý các entity và relationship trong hệ thống knowledge graph"
      open={isCreateModalOpen}
      onOpenChange={setIsCreateModalOpen}
    >
      <FormCreateDialog
        handleCreateDomain={handleCreateDomain}
        isLoading={isLoading}
      />
    </Dialog>
  );
}
