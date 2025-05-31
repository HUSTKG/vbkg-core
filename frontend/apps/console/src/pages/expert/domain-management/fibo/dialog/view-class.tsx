import { Badge, Dialog } from "@vbkg/ui";

interface ViewFiboClassDialogProps {
  isViewClassModalOpen: boolean;
  setIsViewClassModalOpen: (open: boolean) => void;
  selectedClass: any; // Replace with actual type
  getClassById: (id: number) => any; // Replace with actual type
}

export default function ViewFiboClassDialog({
  isViewClassModalOpen,
  setIsViewClassModalOpen,
  selectedClass,
  getClassById,
}: ViewFiboClassDialogProps) {
  return (
    <Dialog
      title="View FIBO Class"
      description="Xem chi tiết FIBO class"
      size="2xl"
      open={isViewClassModalOpen}
      onOpenChange={setIsViewClassModalOpen}
    >
      {selectedClass && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">URI</label>
              <p className="mt-1 font-mono text-sm break-all">
                {selectedClass.uri}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Label</label>
              <p className="mt-1">{selectedClass.label || "No label"}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">
              Description
            </label>
            <p className="mt-1">
              {selectedClass.description || "No description"}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Domain
              </label>
              <p className="mt-1">{selectedClass.domain || "No domain"}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Type</label>
              <Badge variant={selectedClass.is_custom ? "outline" : "default"}>
                {selectedClass.is_custom ? "Custom" : "FIBO"}
              </Badge>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Parent Class
              </label>
              <p className="mt-1">
                {selectedClass.parent_class_id
                  ? getClassById(selectedClass.parent_class_id)?.label ||
                    "Unknown"
                  : "No parent"}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Created
              </label>
              <p className="mt-1">
                {new Date(selectedClass.created_at).toLocaleString("vi-VN")}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Updated
              </label>
              <p className="mt-1">
                {new Date(selectedClass.updated_at).toLocaleString("vi-VN")}
              </p>
            </div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
