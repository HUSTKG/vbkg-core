import { Domain } from "@vbkg/types";
import { Badge, Dialog } from "@vbkg/ui";

interface ViewDomainDialogProps {
  isViewModalOpen: boolean;
  setIsViewModalOpen: (open: boolean) => void;
  selectedDomain: Domain | null;
}

export default function ViewDomainDialog({
  isViewModalOpen,
  setIsViewModalOpen,
  selectedDomain,
}: ViewDomainDialogProps) {
  return (
    <Dialog
      title="Chi Tiết Domain"
      description="Xem chi tiết thông tin về domain này"
      open={isViewModalOpen}
      size="2xl"
      onOpenChange={setIsViewModalOpen}
    >
      {selectedDomain && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Tên Domain
              </label>
              <p className="mt-1 font-mono">{selectedDomain.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Tên Hiển Thị
              </label>
              <p className="mt-1">{selectedDomain.display_name}</p>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-500">Mô Tả</label>
            <p className="mt-1">
              {selectedDomain.description || "Không có mô tả"}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Màu Sắc
              </label>
              <div className="mt-1 flex items-center space-x-2">
                <div
                  className="w-6 h-6 rounded-full border"
                  style={{ backgroundColor: selectedDomain.color }}
                />
                <span className="font-mono text-sm">
                  {selectedDomain.color}
                </span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Trạng Thái
              </label>
              <div className="mt-1">
                <Badge
                  variant={selectedDomain.is_active ? "default" : "secondary"}
                >
                  {selectedDomain.is_active ? "Hoạt động" : "Tạm dừng"}
                </Badge>
              </div>
            </div>
          </div>

          {selectedDomain.ontology_namespace && (
            <div>
              <label className="text-sm font-medium text-gray-500">
                Ontology Namespace
              </label>
              <p className="mt-1 font-mono text-sm break-all">
                {selectedDomain.ontology_namespace}
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="text-sm font-medium text-gray-500">
                Tạo Lúc
              </label>
              <p className="mt-1">
                {new Date(selectedDomain.created_at).toLocaleString("vi-VN")}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">
                Cập Nhật
              </label>
              <p className="mt-1">
                {new Date(selectedDomain.updated_at).toLocaleString("vi-VN")}
              </p>
            </div>
          </div>
        </div>
      )}
    </Dialog>
  );
}
