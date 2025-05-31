import { Domain } from "@vbkg/types";
import { Trash2, Edit, Eye } from "lucide-react";
import {
  ActionButton,
  Badge,
  DataTable,
  SimpleColumnDef,
  toast,
} from "@vbkg/ui";
import ViewDomainDialog from "../dialog/view";
import { useUpdateDomain } from "@vbkg/api-client";
import { useState } from "react";
import EditDomainDialog from "../dialog/edit";
import { z } from "zod";
import { UpdateDomainSchema } from "@vbkg/schemas";

interface DomainListTableProps {
  domains: Domain[];
}

export default function DomainListTable({ domains }: DomainListTableProps) {
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);

  // Table columns configuration
  const columns: SimpleColumnDef<Domain, any>[] = [
    {
      accessorKey: "name",
      header: "Tên Domain",
      cell: (row) => (
        <div className="flex items-center uppercase space-x-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: row?.color || "#6366F1" }}
          />
          <span className="font-mono text-sm">{row?.name}</span>
        </div>
      ),
    },
    {
      accessorKey: "display_name",
      header: "Tên Hiển Thị",
      cell: (row) => <span className="font-medium">{row?.display_name}</span>,
    },
    {
      accessorKey: "description",
      header: "Mô Tả",
      cell: (row) => (
        <span className="text-gray-600 max-w-xs truncate">
          {row?.description || "Không có mô tả"}
        </span>
      ),
    },
    {
      accessorKey: "is_active",
      header: "Trạng Thái",
      cell: (row) => (
        <Badge variant={row?.is_active ? "default" : "secondary"}>
          {row?.is_active ? "Hoạt động" : "Tạm dừng"}
        </Badge>
      ),
    },
    {
      accessorKey: "updated_at",
      header: "Cập Nhật",
      cell: (row) =>
        new Date(row?.updated_at || "").toLocaleDateString("vi-VN"),
    },
  ];

  // Action buttons for table
  const actionButtons: ActionButton<Domain>[] = [
    {
      label: "Xem",
      icon: <Eye size={16} />,
      onClick: (domain) => {
        setSelectedDomain(domain);
        setIsViewModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Sửa",
      icon: <Edit size={16} />,
      onClick: (domain) => {
        setSelectedDomain(domain);
        setIsEditModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Xóa",
      icon: <Trash2 size={16} />,
      onClick: () => {},
      variant: "ghost",
      className: "text-red-600 hover:text-red-800",
    },
  ];
  const { mutate: updateDomain, isPending } = useUpdateDomain({
    onSuccess: () => {
      toast("Cập nhật domain thành công");
    },
    onError: (error) => {
      toast("Cập nhật domain thất bại: " + error.message);
    },
  });

  const handleUpdateDomain = (data: z.infer<typeof UpdateDomainSchema>) => {
    if (!selectedDomain) return;

    updateDomain({
      id: selectedDomain.id.toString(),
      ...data,
    });
  };

  return (
    <>
      <DataTable
        data={domains}
        columns={columns}
        actionsOptions={{
          show: true,
          actions: actionButtons,
          showInDropdown: true,
          dropdownLabel: "Hành động",
        }}
        showGlobalFilter={true}
        showColumnFilters={true}
        showPagination={true}
      />
      {/* View Domain Modal */}
      <ViewDomainDialog
        isViewModalOpen={isViewModalOpen}
        setIsViewModalOpen={setIsViewModalOpen}
        selectedDomain={selectedDomain}
      />
      {/* Edit Domain Modal */}
      <EditDomainDialog
        isEditModalOpen={isEditModalOpen}
        setIsEditModalOpen={setIsEditModalOpen}
        selectedDomain={selectedDomain}
        handleUpdateDomain={handleUpdateDomain}
        loading={isPending}
      />
    </>
  );
}
