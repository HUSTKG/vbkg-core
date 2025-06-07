import { DataSource } from "@vbkg/types";
import { DeleteDialog } from "@/components";

interface DeleteDataSourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedSource?: DataSource;
}

export default function DeleteDataSourceDialog({
  open,
  onOpenChange,
  selectedSource,
}: DeleteDataSourceDialogProps) {
  return (
    <DeleteDialog
      isOpen={open}
      onCancel={() => onOpenChange(false)}
      onConfirm={() => {
        onOpenChange(false);
      }}
      title="Delete Data Source"
      message={`Are you sure you want to delete "${selectedSource?.name}"? This action cannot be undone.`}
    />
  );
}
