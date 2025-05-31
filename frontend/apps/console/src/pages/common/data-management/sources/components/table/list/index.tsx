import { DataSource } from "@vbkg/types";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
  DataTable,
  toast,
} from "@vbkg/ui";
import { Edit, Eye, Trash } from "lucide-react";
import React, { useCallback, useState } from "react";
import { dataSourceTableColumns } from "./columns";
import { useDatasources, useDeleteDatasource } from "@vbkg/api-client";
import { useNavigate } from "react-router";

const DataSourceList: React.FC = () => {
  const { data: dataSources } = useDatasources({});
  const [selectedRows, setSelectedRows] = useState<DataSource[]>([]);
  const navigate = useNavigate();

  const { mutate: deleteDataSource } = useDeleteDatasource({
    onSuccess: () => {
      toast("Xóa nguồn dữ liệu thành công");
    },
    onError: (error) => {
      toast("Xóa nguồn dữ liệu thất bại: " + error.message);
    },
  });

  const onRowSelectionChange = useCallback((rows: DataSource[]) => {
    console.log(rows);
    setSelectedRows(rows);
  }, []);

  // Định nghĩa các hành động
  const handleView = useCallback((row: DataSource) => {
    navigate("./" + row.id);
  }, []);

  const handleEdit = useCallback((row: DataSource) => {
    console.log("Chỉnh sửa:", row.id);
  }, []);

  const handleDelete = useCallback((row: DataSource) => {
    deleteDataSource({ id: row.id });
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Danh sách nguồn dữ liệu</CardTitle>
        <CardDescription>
          Danh sách các nguồn dữ liệu hiện có trong hệ thống. Bạn có thể xem,
          chỉnh sửa hoặc xóa nguồn dữ liệu.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <DataTable
          data={dataSources?.data}
          columns={dataSourceTableColumns}
          showRowSelection={true}
          onRowSelectionChange={onRowSelectionChange}
          showGlobalFilter={true}
          showColumnFilters={true}
          showPagination={true}
          showColumnToggle={true}
          pageSizeOptions={[5, 10, 20, 50]}
          defaultPageSize={10}
          selectionOptions={{ show: true }}
          actionsOptions={{
            show: true,
            position: "end",
            showInDropdown: true,
            dropdownLabel: "Hành động",
            actions: [
              {
                label: "Xem chi tiết",
                icon: <Eye className="h-4 w-4" />,
                onClick: handleView,
              },
              {
                label: "Chỉnh sửa",
                icon: <Edit className="h-4 w-4" />,
                onClick: handleEdit,
              },
              {
                label: "Xóa",
                icon: <Trash className="h-4 w-4" />,
                onClick: handleDelete,
                variant: "destructive",
              },
            ],
          }}
        />
      </CardContent>
      {selectedRows.length > 0 && (
        <CardFooter className="border-t bg-muted/50 px-6 py-4">
          <div className="flex items-center justify-between w-full">
            <div className="text-sm">
              Đã chọn {selectedRows.length} nguồn dữ liệu
            </div>
            <div className="flex space-x-2">
              <Button
                size="sm"
                onClick={() => console.log("Xử lý hàng loạt:", selectedRows)}
              >
                Xử lý hàng loạt
              </Button>
              <Button size="sm" onClick={() => setSelectedRows([])}>
                Bỏ chọn
              </Button>
            </div>
          </div>
        </CardFooter>
      )}
    </Card>
  );
};

export default DataSourceList;
