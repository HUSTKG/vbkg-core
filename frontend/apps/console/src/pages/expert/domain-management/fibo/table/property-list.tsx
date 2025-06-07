import { FIBOClass, FIBOProperty } from "@vbkg/types";
import { ActionButton, Badge, DataTable, SimpleColumnDef } from "@/components";
import { Edit, ExternalLink, Eye, Trash2 } from "lucide-react";
import { useState } from "react";
import EditFiboPropertyDialog from "../dialog/edit-property";
import ViewFiboPropertyDialog from "../dialog/view-property";

interface PropertyListTableProps {
  properties: FIBOProperty[];
  getClassById: (id: number) => FIBOClass | undefined;
  fiboClasses: FIBOClass[];
}
export default function PropertyListTable({
  properties,
  getClassById,
  fiboClasses,
}: PropertyListTableProps) {
  const [selectedProperty, setSelectedProperty] = useState<FIBOProperty | null>(
    null,
  );
  const [isEditPropertyModalOpen, setIsEditPropertyModalOpen] = useState(false);
  const [isViewPropertyModalOpen, setIsViewPropertyModalOpen] = useState(false);
  // Table columns for FIBO Properties
  const propertyColumns: SimpleColumnDef<FIBOProperty, any>[] = [
    {
      accessorKey: "label",
      header: "Label",
      cell: (row) => (
        <div>
          <div className="font-medium">{row?.label || "No Label"}</div>
          <div className="text-xs text-gray-500 font-mono truncate max-w-xs">
            {row?.uri}
          </div>
        </div>
      ),
    },
    {
      accessorKey: "property_type",
      header: "Type",
      cell: (row) => (
        <Badge
          variant={row?.property_type === "object" ? "default" : "secondary"}
        >
          {row?.property_type === "object" ? "Object" : "Datatype"}
        </Badge>
      ),
    },
    {
      accessorKey: "domain_class_id",
      header: "Domain → Range",
      cell: (row) => {
        const domainClass = row?.domain_class_id
          ? getClassById(row.domain_class_id)
          : null;
        const rangeClass = row?.range_class_id
          ? getClassById(row.range_class_id)
          : null;
        return (
          <div className="text-sm">
            <span className="text-blue-600">{domainClass?.label || "Any"}</span>
            <span className="mx-1">→</span>
            <span className="text-green-600">
              {rangeClass?.label ||
                (row?.property_type === "datatype" ? "Literal" : "Any")}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: "is_custom",
      header: "Source",
      cell: (row) => (
        <Badge variant={row?.is_custom ? "outline" : "default"}>
          {row?.is_custom ? "Custom" : "FIBO"}
        </Badge>
      ),
    },
    {
      accessorKey: "updated_at",
      header: "Updated",
      cell: (row) =>
        new Date(row?.updated_at || "").toLocaleDateString("vi-VN"),
    },
  ];

  const propertyActionButtons: ActionButton<FIBOProperty>[] = [
    {
      label: "Xem",
      icon: <Eye size={16} />,
      onClick: (prop) => {
        setSelectedProperty(prop);
        setIsViewPropertyModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "Sửa",
      icon: <Edit size={16} />,
      onClick: (prop) => {
        setSelectedProperty(prop);
        setIsEditPropertyModalOpen(true);
      },
      variant: "ghost",
    },
    {
      label: "URI",
      icon: <ExternalLink size={16} />,
      onClick: (prop) => {
        window.open(prop.uri, "_blank");
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
  return (
    <>
      <DataTable
        data={properties}
        columns={propertyColumns}
        actionsOptions={{
          show: true,
          actions: propertyActionButtons,
          showInDropdown: true,
          dropdownLabel: "Actions",
        }}
        showGlobalFilter={false}
        showColumnFilters={true}
        showPagination={true}
      />
      <EditFiboPropertyDialog
        isEditPropertyModalOpen={isEditPropertyModalOpen}
        setIsEditPropertyModalOpen={setIsEditPropertyModalOpen}
        selectedProperty={selectedProperty}
        getClassById={getClassById}
        fiboClasses={fiboClasses}
      />
      <ViewFiboPropertyDialog
        isViewPropertyModalOpen={isViewPropertyModalOpen}
        setIsViewPropertyModalOpen={setIsViewPropertyModalOpen}
        selectedProperty={selectedProperty}
        getClassById={getClassById}
      />
    </>
  );
}
