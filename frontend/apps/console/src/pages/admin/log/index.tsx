import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
	Sheet,
	SheetContent,
	SheetDescription,
	SheetHeader,
	SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
	ChevronDown,
	Download,
	Filter,
	Pause,
	Play,
	RefreshCw,
	Search,
} from "lucide-react";
import { usePipelineStepLogs } from "@vbkg/api-client";
import { useSearchParams } from "react-router";
import { IPipelineStepLogEntry } from "@vbkg/types";

// Định nghĩa types
type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

interface LogDetails {
	[key: string]: any;
}

interface Log {
	id: string;
	step_run_id: string;
	pipeline_run_id: string;
	log_level: LogLevel;
	message: string;
	timestamp: string;
	created_at: string;
	details?: LogDetails | null;
}

interface Filters {
	log_level: LogLevel | "";
	start_time: string;
	end_time: string;
	search: string;
	skip: number;
	limit: number;
}

interface LogLevelBadgeProps {
	level: LogLevel | null | undefined;
}

interface LogDetailsSheetProps {
	log: Log | null;
	isOpen: boolean;
	onOpenChange: (open: boolean) => void;
}

const LogLevelBadge: React.FC<LogLevelBadgeProps> = ({ level }) => {
	if (!level) return null;

	const variants: Record<LogLevel, string> = {
		DEBUG: "outline",
		INFO: "default",
		WARN: "secondary",
		ERROR: "destructive",
	};

	const colors: Record<LogLevel, string> = {
		DEBUG: "text-slate-600 bg-slate-50 border-slate-200 hover:bg-slate-100",
		INFO: "text-blue-700 bg-blue-50 border-blue-200 hover:bg-blue-100",
		WARN: "text-amber-700 bg-amber-50 border-amber-200 hover:bg-amber-100",
		ERROR: "text-red-700 bg-red-50 border-red-200 hover:bg-red-100",
	};

	const labels: Record<LogLevel, string> = {
		DEBUG: "GỠ LỖI",
		INFO: "THÔNG TIN",
		WARN: "CẢNH BÁO",
		ERROR: "LỖI",
	};

	return (
		<Badge
			variant={variants[level] as any}
			className={`${colors[level]} font-medium px-3 py-1`}
		>
			{labels[level]}
		</Badge>
	);
};

const LogDetailsSheet: React.FC<LogDetailsSheetProps> = ({
	log,
	isOpen,
	onOpenChange,
}) => {
	if (!log) return null;

	return (
		<Sheet open={isOpen} onOpenChange={onOpenChange}>
			<SheetContent className="sm:max-w-2xl">
				<SheetHeader className="pb-6">
					<SheetTitle className="flex items-center gap-3 text-xl">
						Chi Tiết Log
						<LogLevelBadge level={log.log_level} />
					</SheetTitle>
					<SheetDescription className="text-slate-600">
						{log.timestamp
							? new Date(log.timestamp).toLocaleString("vi-VN")
							: "Không có thời gian"}
					</SheetDescription>
				</SheetHeader>

				<div className="space-y-6 px-4">
					<div className="space-y-2">
						<Label className="text-sm font-semibold text-slate-700">
							Tiêu đề
						</Label>
						<div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
							<p className="text-sm text-slate-800 leading-relaxed">
								{log.message || "Không có tin nhắn"}
							</p>
						</div>
					</div>

					{log.details && (
						<div className="space-y-2">
							<Label className="text-sm font-semibold text-slate-700">
								Chi Tiết
							</Label>
							<ScrollArea className="bg-slate-900 border border-slate-300 rounded-lg p-4 h-80 overflow-hidden">
								<pre className="text-xs text-slate-100 text-wrap overflow-auto leading-relaxed">
									{JSON.stringify(log.details, null, 2)}
								</pre>
							</ScrollArea>
						</div>
					)}

					<div className="grid grid-cols-2 gap-4">
						<div className="space-y-2">
							<Label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
								ID Log
							</Label>
							<p className="font-mono text-sm text-slate-800 bg-slate-50 px-3 py-2 rounded border break-all">
								{log.id || "N/A"}
							</p>
						</div>
						<div className="space-y-2">
							<Label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
								ID Step Run
							</Label>
							<p className="font-mono text-sm text-slate-800 bg-slate-50 px-3 py-2 rounded border break-all">
								{log.step_run_id || "N/A"}
							</p>
						</div>
						<div className="space-y-2">
							<Label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
								Thời Gian
							</Label>
							<p className="text-sm text-slate-800 bg-slate-50 px-3 py-2 rounded border">
								{log.timestamp
									? new Date(log.timestamp).toLocaleString("vi-VN")
									: "N/A"}
							</p>
						</div>
						<div className="space-y-2">
							<Label className="text-xs font-medium text-slate-500 uppercase tracking-wider">
								Tạo Lúc
							</Label>
							<p className="text-sm text-slate-800 bg-slate-50 px-3 py-2 rounded border">
								{log.created_at
									? new Date(log.created_at).toLocaleString("vi-VN")
									: "N/A"}
							</p>
						</div>
					</div>
				</div>
			</SheetContent>
		</Sheet>
	);
};

const PipelineStepLogsPage: React.FC = () => {
	const [searchParams] = useSearchParams();
	const stepRunId = searchParams.get("step_run_id");
	const pipelineRunId = searchParams.get("pipeline_run_id");

	const [filters, setFilters] = useState<Filters>({
		log_level: "",
		start_time: "",
		end_time: "",
		search: "",
		skip: 0,
		limit: 100,
	});

	const [selectedLog, setSelectedLog] = useState<Log | null>(null);
	const [isDetailOpen, setIsDetailOpen] = useState<boolean>(false);
	const [isAutoRefresh, setIsAutoRefresh] = useState<boolean>(true);

	const { data, isLoading } = usePipelineStepLogs({
		step_run_id: stepRunId || undefined,
		pipeline_run_id: pipelineRunId || undefined,
		...filters,
		log_level: filters.log_level || undefined,
	});

	const handleLogClick = (log: Log): void => {
		if (!log) return;
		setSelectedLog(log);
		setIsDetailOpen(true);
	};

	const handleExportLogs = (): void => {
		if (!data?.data || data.data.length === 0) {
			alert("Không có dữ liệu để xuất");
			return;
		}

		try {
			const csv = [
				["Thời Gian", "Cấp Độ", "Tin Nhắn", "Chi Tiết"],
				...data.data.map((log) => [
					log.timestamp || "",
					log.log_level || "",
					log.message || "",
					JSON.stringify(log.details || {}),
				]),
			]
				.map((row) =>
					row.map((cell) => `"${cell.replace(/"/g, '""')}"`).join(","),
				)
				.join("\n");

			const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = `step-logs-${stepRunId || "unknown"}-${new Date().toISOString()}.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (error) {
			console.error("Lỗi khi xuất logs:", error);
			alert("Có lỗi xảy ra khi xuất dữ liệu");
		}
	};

	const filteredLogs: IPipelineStepLogEntry[] =
		data?.data?.filter((log) => {
			if (!log) return false;

			if (
				filters.search &&
				log.message &&
				!log.message.toLowerCase().includes(filters.search.toLowerCase())
			) {
				return false;
			}
			return true;
		}) || [];

	const logLevelOptions: { value: LogLevel; label: string }[] = [
		{ value: "DEBUG", label: "GỠ LỖI" },
		{ value: "INFO", label: "THÔNG TIN" },
		{ value: "WARN", label: "CẢNH BÁO" },
		{ value: "ERROR", label: "LỖI" },
	];

	return (
		<div className="container mx-auto p-8 space-y-8 bg-slate-50 min-h-screen">
			<div className="flex items-center justify-between bg-white rounded-xl p-6 shadow-sm border border-slate-200">
				<div className="space-y-2">
					<h1 className="text-3xl font-bold text-slate-900">
						Logs Pipeline Step
					</h1>
					<p className="text-slate-600 font-medium">
						ID Step Run:{" "}
						<span className="font-mono text-blue-700 bg-blue-50 px-2 py-1 rounded">
							{stepRunId || "Không xác định"}
						</span>
					</p>
				</div>

				<div className="flex items-center gap-3">
					<Button
						variant="outline"
						size="sm"
						onClick={() => setIsAutoRefresh(!isAutoRefresh)}
						className={`transition-all duration-200 ${
							isAutoRefresh
								? "bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100"
								: "hover:bg-slate-100"
						}`}
					>
						{isAutoRefresh ? (
							<Pause className="h-4 w-4 mr-2" />
						) : (
							<Play className="h-4 w-4 mr-2" />
						)}
						Tự Động Làm Mới
					</Button>

					<Button
						variant="outline"
						size="sm"
						onClick={handleExportLogs}
						className="hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-all duration-200"
					>
						<Download className="h-4 w-4 mr-2" />
						Xuất File
					</Button>
				</div>
			</div>

			{/* Bộ lọc */}
			<Card className="shadow-sm border-slate-200">
				<CardHeader className="pb-4 bg-slate-50/50 rounded-t-xl">
					<CardTitle className="text-lg flex items-center gap-3 text-slate-800">
						<div className="p-2 bg-blue-100 rounded-lg">
							<Filter className="h-5 w-5 text-blue-700" />
						</div>
						Bộ Lọc
					</CardTitle>
				</CardHeader>
				<CardContent className="p-6">
					<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
						<div className="space-y-2">
							<Label
								htmlFor="search"
								className="text-sm font-semibold text-slate-700"
							>
								Tìm Kiếm Tin Nhắn
							</Label>
							<div className="relative">
								<Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
								<Input
									id="search"
									placeholder="Tìm kiếm trong tin nhắn..."
									value={filters.search}
									onChange={(e) =>
										setFilters((prev) => ({ ...prev, search: e.target.value }))
									}
									className="pl-10 border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
								/>
							</div>
						</div>

						<div className="space-y-2">
							<Label
								htmlFor="log-level"
								className="text-sm font-semibold text-slate-700"
							>
								Cấp Độ Log
							</Label>
							<Select
								value={filters.log_level}
								onValueChange={(value: LogLevel | "") =>
									setFilters((prev) => ({ ...prev, log_level: value }))
								}
							>
								<SelectTrigger className="border-slate-300 focus:border-blue-500 focus:ring-blue-500/20">
									<SelectValue placeholder="Tất cả cấp độ" />
								</SelectTrigger>
								<SelectContent>
									{logLevelOptions.map((option) => (
										<SelectItem key={option.value} value={option.value}>
											{option.label}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</div>

						<div className="space-y-2">
							<Label
								htmlFor="start-time"
								className="text-sm font-semibold text-slate-700"
							>
								Thời Gian Bắt Đầu
							</Label>
							<Input
								id="start-time"
								type="datetime-local"
								value={filters.start_time}
								onChange={(e) =>
									setFilters((prev) => ({
										...prev,
										start_time: e.target.value,
									}))
								}
								className="border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
							/>
						</div>

						<div className="space-y-2">
							<Label
								htmlFor="end-time"
								className="text-sm font-semibold text-slate-700"
							>
								Thời Gian Kết Thúc
							</Label>
							<Input
								id="end-time"
								type="datetime-local"
								value={filters.end_time}
								onChange={(e) =>
									setFilters((prev) => ({ ...prev, end_time: e.target.value }))
								}
								className="border-slate-300 focus:border-blue-500 focus:ring-blue-500/20"
							/>
						</div>
					</div>
				</CardContent>
			</Card>

			{/* Bảng Logs */}
			<Card className="shadow-sm border-slate-200">
				<CardHeader className="pb-4 bg-slate-50/50 rounded-t-xl">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg text-slate-800">
							Logs Thực Thi
						</CardTitle>
						<div className="flex items-center gap-3 text-sm text-slate-600">
							{isAutoRefresh && (
								<RefreshCw className="h-4 w-4 animate-spin text-emerald-600" />
							)}
							<span className="bg-slate-100 px-3 py-1 rounded-full font-medium">
								{data?.meta?.total || 0} tổng số logs
							</span>
						</div>
					</div>
				</CardHeader>
				<CardContent className="p-0">
					<ScrollArea className="h-[600px]">
						<div className="min-w-full">
							<div className="grid grid-cols-12 gap-4 px-6 py-4 bg-slate-100 border-b border-slate-200 font-semibold text-sm text-slate-700">
								<div className="col-span-3">Thời Gian</div>
								<div className="col-span-2">Cấp Độ</div>
								<div className="col-span-5">Tin Nhắn</div>
								<div className="col-span-2">Thao Tác</div>
							</div>

							<div className="divide-y divide-slate-200">
								{isLoading ? (
									Array.from({ length: 5 }).map((_, i) => (
										<div key={i} className="grid grid-cols-12 gap-4 px-6 py-5">
											<div className="col-span-3">
												<Skeleton className="h-4 w-full" />
											</div>
											<div className="col-span-2">
												<Skeleton className="h-6 w-16" />
											</div>
											<div className="col-span-5">
												<Skeleton className="h-4 w-full" />
											</div>
											<div className="col-span-2">
												<Skeleton className="h-8 w-20" />
											</div>
										</div>
									))
								) : filteredLogs.length === 0 ? (
									<div className="text-center py-16 text-slate-500">
										<div className="text-lg font-medium mb-2">
											Không tìm thấy logs
										</div>
										<div className="text-sm">Thử điều chỉnh bộ lọc của bạn</div>
									</div>
								) : (
									filteredLogs.map((log) => (
										<div
											key={log.id}
											className="grid grid-cols-12 gap-4 px-6 py-5 hover:bg-slate-50 cursor-pointer border-b border-slate-100 transition-colors duration-150"
											onClick={() => handleLogClick(log)}
										>
											<div className="col-span-3 font-mono text-sm text-slate-600">
												{log.timestamp
													? new Date(log.timestamp).toLocaleString("vi-VN")
													: "Không có thời gian"}
											</div>
											<div className="col-span-2">
												<LogLevelBadge level={log.log_level} />
											</div>
											<div className="col-span-5 space-y-1">
												<div
													className="truncate text-slate-800 font-medium"
													title={log.message || "Không có tin nhắn"}
												>
													{log.message || "Không có tin nhắn"}
												</div>
												{log.details && (
													<div className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full inline-block">
														Có chi tiết bổ sung
													</div>
												)}
											</div>
											<div className="col-span-2">
												<Button
													variant="ghost"
													size="sm"
													onClick={(e) => {
														e.stopPropagation();
														handleLogClick(log);
													}}
													className="text-slate-600 hover:text-blue-700 hover:bg-blue-50 transition-colors duration-150"
												>
													<ChevronDown className="h-4 w-4 mr-1" />
													Chi Tiết
												</Button>
											</div>
										</div>
									))
								)}
							</div>
						</div>
					</ScrollArea>
				</CardContent>
			</Card>

			<LogDetailsSheet
				log={selectedLog}
				isOpen={isDetailOpen}
				onOpenChange={setIsDetailOpen}
			/>
		</div>
	);
};

export default PipelineStepLogsPage;
