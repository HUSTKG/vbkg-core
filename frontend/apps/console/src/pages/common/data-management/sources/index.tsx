import CreateDataSourceSheet from "./components/sheet/CreateDataSourceSheet";
import DataSourceList from "./components/table/list";

export default function ConfigureDataSource() {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Quản lý nguồn</h1>
        <CreateDataSourceSheet />
      </div>

      <DataSourceList />
    </div>
  );
}
