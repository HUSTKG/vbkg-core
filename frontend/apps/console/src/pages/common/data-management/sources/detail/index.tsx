import React, { useState } from "react";
import { useParams, useNavigate } from "react-router";
import {
  FileText,
  Globe,
  Database,
  Link as LinkIcon,
  Check,
  X,
  Upload,
  RefreshCw,
  Eye,
  EyeOff,
  ChevronLeft,
  Shield,
  Terminal,
  Clock,
  Info,
  Edit,
  Trash,
  Plus,
  Files,
} from "lucide-react";
import {
  ApiConnectionConfig,
  DatabaseConnectionConfig,
  FileConnectionConfig,
  FileUpload,
  SourceType,
  UrlConnectionConfig,
} from "@vbkg/types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  ScrollArea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Separator,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
  toast,
} from "@vbkg/ui";
import {
  useDatasource,
  useFileUploads,
  useFilePublicUrl,
} from "@vbkg/api-client";
import DownloadFileButton from "../../../../../components/button/DownloadFileButton";
import FileSelectorDialog from "../../../../../components/dialog/file-selector";
import { PipelineTemplateDialog } from "../components/dialog/pipeline-template";

// Định nghĩa kiểu dữ liệu cho lịch sử kết nối
interface ConnectionLog {
  id: string;
  datasource_id: string;
  status: "success" | "error";
  message: string;
  details?: string;
  created_at: string;
}

// Mock data cho datasource chi tiết

// Mock data cho lịch sử kết nối
const mockConnectionLogs: ConnectionLog[] = [
  {
    id: "log-1",
    datasource_id: "ds-1",
    status: "success",
    message: "Kết nối thành công",
    details: "Đã đọc được 1,245 dòng dữ liệu",
    created_at: "2025-05-17T15:30:00Z",
  },
  {
    id: "log-2",
    datasource_id: "ds-1",
    status: "error",
    message: "Lỗi kết nối",
    details:
      "Không thể mở file: File không tồn tại hoặc không có quyền truy cập",
    created_at: "2025-05-16T09:15:00Z",
  },
  {
    id: "log-3",
    datasource_id: "ds-1",
    status: "success",
    message: "Kết nối thành công",
    details: "Đã đọc được 1,245 dòng dữ liệu",
    created_at: "2025-05-15T11:45:00Z",
  },
];

// Component chính cho trang chi tiết DataSource
const DataSourceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: dataSource } = useDatasource(
    {
      id: id!,
    },
    {
      enabled: !!id,
    },
  );

  const { data: files } = useFileUploads({
    datasource_id: id,
  });

  const {
    source_type,
    connection_details,
    credentials,
    created_at,
    created_by,
    updated_at,
    is_active,
    description,
    name,
  } = dataSource?.data || {};

  // States
  const [connectionLogs, setConnectionLogs] =
    useState<ConnectionLog[]>(mockConnectionLogs);
  const [isEditing, setIsEditing] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showPipelineTemplateDialog, setShowPipelineTemplateDialog] =
    useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [testConnectionStatus, setTestConnectionStatus] = useState<
    null | "success" | "error"
  >(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("vi-VN", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  // Lấy icon tương ứng với loại datasource
  const getSourceTypeIcon = (type?: string) => {
    switch (type) {
      case "file":
        return <FileText className="h-5 w-5 text-blue-500" />;
      case "api":
        return <Globe className="h-5 w-5 text-green-500" />;
      case "database":
        return <Database className="h-5 w-5 text-purple-500" />;
      case "url":
        return <LinkIcon className="h-5 w-5 text-orange-500" />;
      default:
        return null;
    }
  };

  // Xử lý kiểm tra kết nối
  const handleTestConnection = async () => {
    setIsLoading(true);
    setTestConnectionStatus(null);

    // Giả lập API call
    setTimeout(() => {
      // Random success/error để demo
      const isSuccess = Math.random() > 0.3;

      setTestConnectionStatus(isSuccess ? "success" : "error");

      // Thêm log mới
      const newLog: ConnectionLog = {
        id: `log-${Date.now()}`,
        datasource_id: id!,
        status: isSuccess ? "success" : "error",
        message: isSuccess ? "Kết nối thành công" : "Lỗi kết nối",
        details: isSuccess
          ? "Đã đọc được 1,245 dòng dữ liệu"
          : "Không thể mở file: File không tồn tại hoặc không có quyền truy cập",
        created_at: new Date().toISOString(),
      };

      setConnectionLogs([newLog, ...connectionLogs]);
      setIsLoading(false);

      toast(isSuccess ? "Kết nối thành công" : "Kết nối thất bại", {
        description: isSuccess
          ? "Đã kiểm tra kết nối thành công đến nguồn dữ liệu"
          : "Không thể kết nối đến nguồn dữ liệu. Vui lòng kiểm tra lại cấu hình",
        className: isSuccess ? "bg-green-500" : "bg-red-500",
      });
    }, 2000);
  };

  // Xử lý upload file
  const handleUploadFile = (file: FileUpload[]) => {
    if (!file) return;
  };

  // Xử lý toggle active
  const handleToggleActive = () => {};

  // Render chi tiết kết nối dựa trên loại nguồn dữ liệu
  const renderConnectionDetails = () => {
    switch (source_type) {
      case "file": {
        const details = connection_details as FileConnectionConfig;
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Đường dẫn file</Label>
                <div className="flex mt-1">
                  <Input
                    value={details.file_path || ""}
                    readOnly={!isEditing}
                    className="flex-1"
                  />
                  {source_type === "file" && (
                    <Button
                      className="ml-2"
                      onClick={() => setShowUploadDialog(true)}
                    >
                      <Upload className="h-4 w-4 mr-1" />
                      Tải lên
                    </Button>
                  )}
                </div>
              </div>
              <div>
                <Label>Định dạng file</Label>
                <Select
                  defaultValue={details.file_format}
                  disabled={!isEditing}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn định dạng file" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                    <SelectItem value="txt">Text (TXT)</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Mã hóa</Label>
                <Select defaultValue={details.encoding} disabled={!isEditing}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn mã hóa" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="utf-8">UTF-8</SelectItem>
                    <SelectItem value="ascii">ASCII</SelectItem>
                    <SelectItem value="iso-8859-1">ISO-8859-1</SelectItem>
                    <SelectItem value="windows-1252">Windows-1252</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {details.file_format === "csv" && (
                <div>
                  <Label>Ký tự phân cách</Label>
                  <Input
                    value={details.delimiter || ","}
                    readOnly={!isEditing}
                  />
                </div>
              )}
            </div>
          </div>
        );
      }

      case "api": {
        const details = connection_details as ApiConnectionConfig;
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Label>URL</Label>
                <Input value={details.url} readOnly={!isEditing} />
              </div>
              <div>
                <Label>Phương thức</Label>
                <Select defaultValue={details.method} disabled={!isEditing}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn phương thức" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GET">GET</SelectItem>
                    <SelectItem value="POST">POST</SelectItem>
                    <SelectItem value="PUT">PUT</SelectItem>
                    <SelectItem value="DELETE">DELETE</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Loại xác thực</Label>
                <Select
                  defaultValue={details.auth_type || "none"}
                  disabled={!isEditing}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn loại xác thực" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Không có</SelectItem>
                    <SelectItem value="basic">Basic Auth</SelectItem>
                    <SelectItem value="bearer">Bearer Token</SelectItem>
                    <SelectItem value="api_key">API Key</SelectItem>
                    <SelectItem value="oauth">OAuth 2.0</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {details.headers && Object.keys(details.headers).length > 0 && (
              <div>
                <Label>Headers</Label>
                <div className="border rounded-md overflow-hidden mt-1">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Key</TableHead>
                        <TableHead>Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(details.headers).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell>{key}</TableCell>
                          <TableCell>{value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}

            {details.query_params &&
              Object.keys(details.query_params).length > 0 && (
                <div>
                  <Label>Query Parameters</Label>
                  <div className="border rounded-md overflow-hidden mt-1">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Key</TableHead>
                          <TableHead>Value</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(details.query_params).map(
                          ([key, value]) => (
                            <TableRow key={key}>
                              <TableCell>{key}</TableCell>
                              <TableCell>{String(value)}</TableCell>
                            </TableRow>
                          ),
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
          </div>
        );
      }

      case "database": {
        const details = connection_details as DatabaseConnectionConfig;
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Loại database</Label>
                <Select defaultValue={details.db_type} disabled={!isEditing}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn loại database" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="postgres">PostgreSQL</SelectItem>
                    <SelectItem value="mysql">MySQL</SelectItem>
                    <SelectItem value="mssql">SQL Server</SelectItem>
                    <SelectItem value="oracle">Oracle</SelectItem>
                    <SelectItem value="sqlite">SQLite</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Host</Label>
                <Input value={details.host} readOnly={!isEditing} />
              </div>
              <div>
                <Label>Port</Label>
                <Input value={details.port.toString()} readOnly={!isEditing} />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Tên database</Label>
                <Input value={details.database} readOnly={!isEditing} />
              </div>
              <div>
                <Label>Username</Label>
                <Input value={details.username} readOnly={!isEditing} />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between">
                  <Label>SSL</Label>
                  <Switch checked={details.ssl} disabled={!isEditing} />
                </div>
              </div>
              {details.table && (
                <div>
                  <Label>Bảng</Label>
                  <Input value={details.table} readOnly={!isEditing} />
                </div>
              )}
            </div>

            {details.query && (
              <div>
                <Label>SQL Query</Label>
                <Textarea
                  value={details.query}
                  readOnly={!isEditing}
                  className="font-mono text-sm"
                  rows={3}
                />
              </div>
            )}
          </div>
        );
      }

      case "url": {
        const details = connection_details as UrlConnectionConfig;
        return (
          <div className="space-y-4">
            <div>
              <Label>URL</Label>
              <Input value={details.url} readOnly={!isEditing} />
            </div>

            {details.headers && Object.keys(details.headers).length > 0 && (
              <div>
                <Label>Headers</Label>
                <div className="border rounded-md overflow-hidden mt-1">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Key</TableHead>
                        <TableHead>Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {Object.entries(details.headers).map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell>{key}</TableCell>
                          <TableCell>{value}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}

            {details.scrape_config && (
              <div>
                <Label>Cấu hình Scrape</Label>
                <div className="border rounded-md p-4 mt-1">
                  <div className="mb-4">
                    <Label>Selector</Label>
                    <Input
                      value={details.scrape_config.selector}
                      readOnly={!isEditing}
                    />
                  </div>

                  <Label>Fields Mapping</Label>
                  <div className="border rounded-md overflow-hidden mt-1">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Field</TableHead>
                          <TableHead>Selector</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(details.scrape_config.fields).map(
                          ([key, value]) => (
                            <TableRow key={key}>
                              <TableCell>{key}</TableCell>
                              <TableCell>{value as string}</TableCell>
                            </TableRow>
                          ),
                        )}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      }

      default:
        return <p>Không có thông tin chi tiết</p>;
    }
  };

  // Render credentials
  const renderCredentials = () => {
    if (!credentials) {
      return (
        <div className="py-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Shield className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="mb-1 text-lg font-semibold">
            Chưa có thông tin xác thực
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            Thêm thông tin xác thực để kết nối đến nguồn dữ liệu này
          </p>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Thêm thông tin xác thực
          </Button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label>Loại xác thực</Label>
            <Select defaultValue={credentials.auth_type} disabled={!isEditing}>
              <SelectTrigger>
                <SelectValue placeholder="Chọn loại xác thực" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="api_key">API Key</SelectItem>
                <SelectItem value="oauth">OAuth 2.0</SelectItem>
                <SelectItem value="basic">Basic Auth</SelectItem>
                <SelectItem value="token">Token</SelectItem>
                <SelectItem value="certificate">Certificate</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="border rounded-md overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Key</TableHead>
                <TableHead>Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(credentials).map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell>{key}</TableCell>
                  <TableCell>
                    {key.toLowerCase().includes("password") ||
                    key.toLowerCase().includes("secret") ||
                    key.toLowerCase().includes("key") ? (
                      <div className="flex items-center">
                        <Input
                          type={showPassword ? "text" : "password"}
                          value={value as string}
                          readOnly={!isEditing}
                          className="font-mono"
                        />
                        <Button
                          size="icon"
                          onClick={() => setShowPassword(!showPassword)}
                          className="ml-2"
                        >
                          {showPassword ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    ) : (
                      <Input value={value as string} readOnly={!isEditing} />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="flex justify-end">
          <p className="text-sm text-muted-foreground">
            Cập nhật lần cuối: {formatDate(credentials.updated_at)}
          </p>
        </div>
      </div>
    );
  };

  // Render connection logs
  const renderConnectionLogs = () => {
    return (
      <div>
        <div className="mb-4">
          <h3 className="text-lg font-medium mb-2">Lịch sử kết nối</h3>
          {connectionLogs.length === 0 ? (
            <p className="text-muted-foreground">Chưa có lịch sử kết nối</p>
          ) : (
            <div className="border rounded-md overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Thời gian</TableHead>
                    <TableHead>Trạng thái</TableHead>
                    <TableHead>Thông báo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {connectionLogs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>{formatDate(log.created_at)}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            log.status === "success" ? "success" : "destructive"
                          }
                        >
                          {log.status === "success" ? (
                            <div className="flex items-center">
                              <Check className="h-3 w-3 mr-1" />
                              <span>Thành công</span>
                            </div>
                          ) : (
                            <div className="flex items-center">
                              <X className="h-3 w-3 mr-1" />
                              <span>Lỗi</span>
                            </div>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Accordion type="single" collapsible>
                          <AccordionItem value={log.id}>
                            <AccordionTrigger>{log.message}</AccordionTrigger>
                            <AccordionContent>{log.details}</AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center mb-6">
        <Button size="icon" className="mr-2" onClick={() => navigate(-1)}>
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-3xl font-bold">Chi tiết nguồn dữ liệu</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Thông tin cơ bản</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center">
                {getSourceTypeIcon(source_type)}
                <div className="ml-3">
                  <p className="text-sm font-medium">Loại nguồn</p>
                  <p className="text-sm capitalize">{source_type}</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium">ID</p>
                <p className="text-sm font-mono">{id}</p>
              </div>

              <div>
                <p className="text-sm font-medium">Ngày tạo</p>
                <p className="text-sm">{formatDate(created_at)}</p>
              </div>

              <div>
                <p className="text-sm font-medium">Cập nhật lần cuối</p>
                <p className="text-sm">{formatDate(updated_at)}</p>
              </div>

              <div>
                <p className="text-sm font-medium">Người tạo</p>
                <p className="text-sm">{created_by}</p>
              </div>

              <div className="flex items-center justify-between pt-2">
                <p className="text-sm font-medium">Trạng thái</p>
                <Switch
                  checked={is_active}
                  onCheckedChange={handleToggleActive}
                />
              </div>
              <Badge
                variant={is_active ? "success" : "destructive"}
                className="w-full justify-center py-1"
              >
                {is_active ? "Đang hoạt động" : "Ngừng hoạt động"}
              </Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Hành động</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                className="w-full justify-start"
                onClick={() => setShowPipelineTemplateDialog(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Tạo pipeline
              </Button>
              <Button
                className="w-full justify-start"
                onClick={() => setIsEditing(!isEditing)}
              >
                <Edit className="mr-2 h-4 w-4" />
                {isEditing ? "Hủy chỉnh sửa" : "Chỉnh sửa"}
              </Button>

              <Button className="w-full justify-start">
                <Trash className="mr-2 h-4 w-4" />
                Xóa nguồn dữ liệu
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Main content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl">{name}</CardTitle>
                  {description && (
                    <CardDescription className="mt-2">
                      {description}
                    </CardDescription>
                  )}
                </div>
                {isEditing ? (
                  <div className="flex gap-2">
                    <Button onClick={() => setIsEditing(false)}>Hủy</Button>
                    <Button>Lưu thay đổi</Button>
                  </div>
                ) : null}
              </div>
            </CardHeader>

            <CardContent>
              <Tabs defaultValue="details">
                <TabsList className="grid grid-cols-4 mb-8">
                  <TabsTrigger value="details" className="flex items-center">
                    <Info className="h-4 w-4 mr-2" />
                    <span>Thông tin</span>
                  </TabsTrigger>
                  <TabsTrigger
                    value="credentials"
                    className="flex items-center"
                  >
                    <Shield className="h-4 w-4 mr-2" />
                    <span>Xác thực</span>
                  </TabsTrigger>
                  {source_type !== SourceType.FILE && (
                    <TabsTrigger
                      value="connection"
                      className="flex items-center"
                    >
                      <Terminal className="h-4 w-4 mr-2" />
                      <span>Kiểm tra kết nối</span>
                    </TabsTrigger>
                  )}
                  {source_type === SourceType.FILE && (
                    <TabsTrigger value="files" className="flex items-center">
                      <Files className="h-4 w-4 mr-2" />
                      <span>Files</span>
                    </TabsTrigger>
                  )}
                  <TabsTrigger value="logs" className="flex items-center">
                    <Clock className="h-4 w-4 mr-2" />
                    <span>Lịch sử</span>
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="details">
                  <div className="space-y-8">
                    <div>
                      <h3 className="text-lg font-medium mb-4">
                        Thông tin kết nối
                      </h3>
                      {renderConnectionDetails()}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="credentials">
                  <div className="space-y-8">
                    <div>
                      <h3 className="text-lg font-medium mb-4">
                        Thông tin xác thực
                      </h3>
                      {renderCredentials()}
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="files">
                  <div className="space-y-8">
                    {files?.data && files?.data.length > 0 ? (
                      <div>
                        {files?.data?.map((file) => (
                          <div
                            key={file.id}
                            className="flex items-center justify-between border-b py-2"
                          >
                            <div className="flex items-center">
                              <Files className="h-5 w-5 text-blue-500 mr-2" />
                              <span>{file.file_name}</span>
                            </div>
                            <DownloadFileButton file_id={file.id} />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div>
                        <h3 className="text-lg font-medium mb-4">Files</h3>
                        <p className="text-sm text-muted-foreground">
                          Chưa có file nào được tải lên
                        </p>
                      </div>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="connection">
                  <div className="space-y-8">
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-lg font-medium">
                          Kiểm tra kết nối
                        </h3>
                        <Button
                          onClick={handleTestConnection}
                          disabled={isLoading}
                          className="flex items-center"
                        >
                          {isLoading ? (
                            <>
                              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                              <span>Đang kiểm tra...</span>
                            </>
                          ) : (
                            <>
                              <Terminal className="mr-2 h-4 w-4" />
                              <span>Kiểm tra kết nối</span>
                            </>
                          )}
                        </Button>
                      </div>

                      {testConnectionStatus === "success" && (
                        <Alert variant="success">
                          <Check className="h-4 w-4" />
                          <AlertTitle>Kết nối thành công</AlertTitle>
                          <AlertDescription>
                            Đã kiểm tra kết nối thành công đến nguồn dữ liệu.
                          </AlertDescription>
                        </Alert>
                      )}

                      {testConnectionStatus === "error" && (
                        <Alert variant="destructive">
                          <X className="h-4 w-4" />
                          <AlertTitle>Kết nối thất bại</AlertTitle>
                          <AlertDescription>
                            Không thể kết nối đến nguồn dữ liệu. Vui lòng kiểm
                            tra lại cấu hình và thông tin xác thực.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>

                    {source_type === "file" && (
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <h3 className="text-lg font-medium">Upload file</h3>
                          <Button onClick={() => setShowUploadDialog(true)}>
                            <Upload className="mr-2 h-4 w-4" />
                            <span>Tải lên file mới</span>
                          </Button>
                        </div>

                        <p className="text-sm text-muted-foreground">
                          Tải lên file mới để thay thế file hiện tại. Hệ thống
                          sẽ tự động cập nhật đường dẫn file.
                        </p>
                      </div>
                    )}

                    <Separator />

                    {renderConnectionLogs()}
                  </div>
                </TabsContent>

                <TabsContent value="logs">
                  <ScrollArea className="h-[500px] pr-4">
                    {renderConnectionLogs()}
                  </ScrollArea>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialog upload file */}
      <FileSelectorDialog
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        onSelect={(file) => handleUploadFile(file)}
        datasource_id={id}
      />
      <PipelineTemplateDialog
        open={showPipelineTemplateDialog}
        onOpenChange={setShowPipelineTemplateDialog}
        dataSourceId={id!}
        sourceType={source_type}
      />
    </div>
  );
};

export default DataSourceDetailPage;
