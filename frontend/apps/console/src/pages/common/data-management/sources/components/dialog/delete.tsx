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
      title="Xóa nguồn dữ liệu"
      message={`Bạn có chắc chắn muốn xóa "${selectedSource?.name}"? Hành động này không thể hoàn tác.`}
    />
  );
}
