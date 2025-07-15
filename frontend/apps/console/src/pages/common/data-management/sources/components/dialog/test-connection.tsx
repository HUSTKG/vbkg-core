import { ConfirmDialog } from "@/components";

interface TestConnectionDataSourceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function TestConnectionDataSourceDialog({
  open,
  onOpenChange,
}: TestConnectionDataSourceDialogProps) {
  return (
    <ConfirmDialog
      message="Đang kiểm tra kết nối đến nguồn dữ liệu..."
      isOpen={open}
      onCancel={() => onOpenChange(false)}
      onConfirm={() => onOpenChange(false)}
      title="Kiểm tra kết nối"
    />
  );
}
