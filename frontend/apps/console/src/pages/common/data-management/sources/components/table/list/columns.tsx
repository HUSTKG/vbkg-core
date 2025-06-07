import {
  ApiConnectionConfig,
  DatabaseConnectionConfig,
  DataSource,
  FileConnectionConfig,
  SourceType,
  UrlConnectionConfig,
} from "@vbkg/types";
import { Badge, SimpleColumnDef } from "@/components";
import { formatDate } from "@vbkg/utils";
import { Check, Database, FileText, Globe, Link, X } from "lucide-react";

export const dataSourceTableColumns = [
  {
    header: "Tên nguồn dữ liệu",
    accessorKey: "name", // Sử dụng "as const" giúp TypeScript hiểu đây là 'name' key
    cell: (row) => (
      <div>
        <div className="font-medium">{row?.name}</div>
        {row?.description && (
          <div className="text-xs text-muted-foreground truncate max-w-md">
            {row?.description}
          </div>
        )}
      </div>
    ),
  },
  {
    header: "Loại nguồn",
    accessorKey: "source_type",
    cell: (row) => {
      // Icon cho từng loại
      const getIcon = () => {
        switch (row?.source_type) {
          case SourceType.FILE:
            return <FileText className="h-4 w-4 text-blue-500" />;
          case SourceType.API:
            return <Globe className="h-4 w-4 text-green-500" />;
          case SourceType.DATABASE:
            return <Database className="h-4 w-4 text-purple-500" />;
          case SourceType.URL:
            return <Link className="h-4 w-4 text-orange-500" />;
          default:
            return null;
        }
      };

      return (
        <div className="flex items-center space-x-2">
          {getIcon()}
          <span className="capitalize">{row?.source_type}</span>
        </div>
      );
    },
  },
  {
    header: "Kết nối",
    id: "connection",
    // Sử dụng accessorFn với kiểu trả về string
    cell: (row) => {
      const value = getConnectionDetails(row);
      return (
        <div className="text-sm truncate max-w-[250px]" title={value}>
          {value}
        </div>
      );
    },
  },
  {
    header: "Ngày tạo",
    accessorKey: "created_at",
    cell: (row) => formatDate(row?.created_at),
  },
  {
    header: "Trạng thái",
    accessorKey: "is_active",
    cell: (row) => (
      <Badge
        variant={row?.is_active ? "success" : "destructive"}
        className="flex items-center gap-1 whitespace-nowrap"
      >
        {row?.is_active ? (
          <>
            <Check className="h-3 w-3" />
            <span>Hoạt động</span>
          </>
        ) : (
          <>
            <X className="h-3 w-3" />
            <span>Ngừng hoạt động</span>
          </>
        )}
      </Badge>
    ),
  },
] satisfies SimpleColumnDef<DataSource, any>[];

const getConnectionDetails = (dataSource?: DataSource) => {
  if (!dataSource) return "Không xác định";

  const { source_type, connection_details } = dataSource;

  switch (source_type) {
    case "file": {
      const details = connection_details as FileConnectionConfig;
      return `${details.file_format?.toUpperCase()} - ${details.file_path || "Chưa có đường dẫn"}`;
    }
    case "api": {
      const details = connection_details as ApiConnectionConfig;
      return `${details.method} - ${details.url}`;
    }
    case "database": {
      const details = connection_details as DatabaseConnectionConfig;
      return `${details.db_type} - ${details.host}:${details.port}/${details.database}`;
    }
    case "url": {
      const details = connection_details as UrlConnectionConfig;
      return details.url;
    }
    default:
      return "Không xác định";
  }
};
