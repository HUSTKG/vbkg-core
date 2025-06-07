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
      message="Testing connection to the data source..."
      isOpen={open}
      onCancel={() => onOpenChange(false)}
      onConfirm={() => onOpenChange(false)}
      title="Test Connection"
    />
  );
}
