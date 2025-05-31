import { FIBOClass, FIBOProperty } from "@vbkg/types";
import { Badge, Dialog } from "@vbkg/ui";

interface ViewFiboPropertyDialogProps {
  isViewPropertyModalOpen: boolean;
  setIsViewPropertyModalOpen: (open: boolean) => void;
  selectedProperty: FIBOProperty | null;
  getClassById: (id: number) => FIBOClass | undefined;
}

export default function ViewFiboPropertyDialog({
  isViewPropertyModalOpen,
  setIsViewPropertyModalOpen,
  selectedProperty,
  getClassById,
}: ViewFiboPropertyDialogProps) {
  return (
    <Dialog
      title="View FIBO Property"
      description="Xem chi tiết FIBO property"
      open={isViewPropertyModalOpen}
      onOpenChange={setIsViewPropertyModalOpen}
    >
      {selectedProperty && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">URI</label>
              <p className="mt-1 font-mono text-sm break-all">
                {selectedProperty.uri}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Label</label>
              <p className="mt-1">{selectedProperty.label || "No label"}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">
              Description
            </label>
            <p className="mt-1">
              {selectedProperty.description || "No description"}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Property Type
              </label>
              <Badge
                variant={
                  selectedProperty.property_type === "object"
                    ? "default"
                    : "secondary"
                }
              >
                {selectedProperty.property_type === "object"
                  ? "Object Property"
                  : "Datatype Property"}
              </Badge>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Domain Class
              </label>
              <p className="mt-1">
                {selectedProperty.domain_class_id
                  ? getClassById(selectedProperty.domain_class_id)?.label ||
                    "Unknown"
                  : "Any"}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Range</label>
              <p className="mt-1">
                {selectedProperty.range_class_id
                  ? getClassById(selectedProperty.range_class_id)?.label ||
                    "Unknown"
                  : selectedProperty.property_type === "datatype"
                    ? "Literal"
                    : "Any"}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Created
              </label>
              <p className="mt-1">
                {new Date(selectedProperty.created_at).toLocaleString("vi-VN")}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Updated
              </label>
              <p className="mt-1">
                {new Date(selectedProperty.updated_at).toLocaleString("vi-VN")}
              </p>
            </div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
