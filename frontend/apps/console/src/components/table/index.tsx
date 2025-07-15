import { rankItem } from "@tanstack/match-sorter-utils";
import {
	CellContext,
	ColumnDef,
	ColumnFiltersState,
	FilterFn,
	PaginationState,
	RowData,
	RowSelectionState,
	SortingState,
	StringOrTemplateHeader,
	VisibilityState,
	createColumnHelper,
	flexRender,
	getCoreRowModel,
	getFilteredRowModel,
	getPaginationRowModel,
	getSortedRowModel,
	useReactTable,
} from "@tanstack/react-table";
import React, { useCallback, useEffect, useMemo, useState } from "react";

// Import Shadcn UI components
import { Button } from "../ui/button";
import { Checkbox } from "../ui/checkbox";
import {
	DropdownMenu,
	DropdownMenuCheckboxItem,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Input } from "../ui/input";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "../ui/select";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "../ui/table";

// Import icons
import {
	ChevronDown,
	ChevronLeft,
	ChevronRight,
	ChevronUp,
	ChevronsLeft,
	ChevronsRight,
	ChevronsUpDown,
	Filter as FilterIcon,
	Loader2,
	MoreHorizontal,
	Search,
	Settings2,
	X,
} from "lucide-react";

// Define type for action button
export interface ActionButton<TData> {
	label: string;
	icon?: React.ReactNode;
	onClick: (row: TData) => void;
	variant?:
		| "default"
		| "destructive"
		| "outline"
		| "secondary"
		| "ghost"
		| "link";
	className?: string;
}

// Simple column definition that users will provide
export interface SimpleColumnDef<TData extends RowData, TValue> {
	id?: string;
	header: StringOrTemplateHeader<TData, TValue>;
	accessorKey?: keyof TData; // Use this or accessorFn
	accessorFn?: (row: TData) => TValue;
	cell?: (row?: TData) => React.ReactNode;
	enableSorting?: boolean;
	enableFiltering?: boolean;
	enableHiding?: boolean;
	className?: string;
	meta?: Record<string, any>;
}

// Options for selecting rows
export interface SelectionOptions {
	show?: boolean;
	columnId?: string;
}

// Options for actions column
export interface ActionsOptions<TData> {
	show?: boolean;
	columnId?: string;
	position?: "start" | "end";
	actions: ActionButton<TData>[];
	showInDropdown?: boolean;
	dropdownLabel?: string;
}

// Server-side callback parameters
export interface ServerSideParams {
	pagination: {
		pageIndex: number;
		pageSize: number;
	};
	sorting: SortingState;
	columnFilters: ColumnFiltersState;
	globalFilter: string;
}

// Server-side callback functions
export interface ServerSideCallbacks {
	onPaginationChange?: (params: ServerSideParams) => void;
	onSortingChange?: (params: ServerSideParams) => void;
	onColumnFiltersChange?: (params: ServerSideParams) => void;
	onGlobalFilterChange?: (params: ServerSideParams) => void;
}

// Hàm fuzzy search cho global filter
const fuzzyFilter: FilterFn<any> = (row, columnId, value, addMeta) => {
	// Rank how closely the item matches
	const itemRank = rankItem(row.getValue(columnId), value);

	// Store ranking info for potential UI usage
	addMeta({
		itemRank,
	});

	// Return if the item should be filtered in
	return itemRank.passed;
};

// Props cho component DataTable
interface DataTableProps<TData extends RowData, TValue> {
	data?: TData[];
	columns: SimpleColumnDef<TData, TValue>[];

	// Display options
	showGlobalFilter?: boolean;
	showColumnFilters?: boolean;
	showPagination?: boolean;
	showRowSelection?: boolean;
	showColumnToggle?: boolean;

	// Pagination options
	pageSizeOptions?: number[];
	defaultPageSize?: number;

	// Server-side processing options
	manualPagination?: boolean;
	manualSorting?: boolean;
	manualFiltering?: boolean;
	totalCount?: number; // Required when using manual pagination
	loading?: boolean;

	// Callbacks
	onRowSelectionChange?: (rows: TData[]) => void;
	serverSideCallbacks?: ServerSideCallbacks;

	// Selection and actions
	selectionOptions?: SelectionOptions;
	actionsOptions?: ActionsOptions<TData>;

	// Debounce delay for server-side filters (ms)
	filterDebounceMs?: number;
}

// Function component cho DataTable
function DataTable<TData extends RowData, TValue>({
	data = [],
	columns: simpleColumns,
	showGlobalFilter = true,
	showColumnFilters = true,
	showPagination = true,
	showRowSelection = false,
	showColumnToggle = true,
	pageSizeOptions = [10, 20, 30, 50, 100],
	defaultPageSize = 10,
	manualPagination = false,
	manualSorting = false,
	manualFiltering = false,
	totalCount = 0,
	loading = false,
	onRowSelectionChange,
	serverSideCallbacks,
	selectionOptions = { show: false },
	actionsOptions,
	filterDebounceMs = 300,
}: DataTableProps<TData, TValue>) {
	// State
	const [sorting, setSorting] = useState<SortingState>([]);
	const [globalFilter, setGlobalFilter] = useState("");
	const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
	const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
	const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
	const [showColumnFilterRow, setShowColumnFilterRow] = useState(false);
	const [pagination, setPagination] = useState<PaginationState>({
		pageIndex: 0,
		pageSize: defaultPageSize,
	});

	// Debounce timer refs
	const globalFilterTimeoutRef = React.useRef<NodeJS.Timeout>(null);
	const columnFiltersTimeoutRef = React.useRef<NodeJS.Timeout>(null);

	// Helper function to get current server params
	const getCurrentServerParams = useCallback(
		(): ServerSideParams => ({
			pagination,
			sorting,
			columnFilters,
			globalFilter,
		}),
		[pagination, sorting, columnFilters, globalFilter],
	);

	// Debounced server-side filter handlers
	const handleServerSideGlobalFilter = useCallback(
		(value: string) => {
			if (globalFilterTimeoutRef.current) {
				clearTimeout(globalFilterTimeoutRef.current);
			}

			if (manualFiltering && serverSideCallbacks?.onGlobalFilterChange) {
				globalFilterTimeoutRef.current = setTimeout(() => {
					serverSideCallbacks.onGlobalFilterChange!({
						...getCurrentServerParams(),
						globalFilter: value,
					});
				}, filterDebounceMs);
			}
		},
		[
			manualFiltering,
			serverSideCallbacks,
			getCurrentServerParams,
			filterDebounceMs,
		],
	);

	const handleServerSideColumnFilters = useCallback(
		(filters: ColumnFiltersState) => {
			if (columnFiltersTimeoutRef.current) {
				clearTimeout(columnFiltersTimeoutRef.current);
			}

			if (manualFiltering && serverSideCallbacks?.onColumnFiltersChange) {
				columnFiltersTimeoutRef.current = setTimeout(() => {
					serverSideCallbacks.onColumnFiltersChange!({
						...getCurrentServerParams(),
						columnFilters: filters,
					});
				}, filterDebounceMs);
			}
		},
		[
			manualFiltering,
			serverSideCallbacks,
			getCurrentServerParams,
			filterDebounceMs,
		],
	);

	// Internal function to convert simple columns to TanStack table columns
	const convertToTableColumns = useMemo(() => {
		const columnHelper = createColumnHelper<TData>();
		const tableColumns: ColumnDef<TData, TValue>[] = [];

		// Add selection column if enabled
		if (showRowSelection || selectionOptions?.show) {
			const selectionColumn = columnHelper.display({
				id: selectionOptions?.columnId || "select",
				header: ({ table }) => (
					<Checkbox
						checked={
							table.getIsAllPageRowsSelected() ||
							(table.getIsSomePageRowsSelected() && "indeterminate")
						}
						onCheckedChange={(value) =>
							table.toggleAllPageRowsSelected(!!value)
						}
						aria-label="Select all"
					/>
				),
				cell: ({ row }) => (
					<Checkbox
						checked={row.getIsSelected()}
						onCheckedChange={(value) => row.toggleSelected(!!value)}
						aria-label="Select row"
					/>
				),
				enableSorting: false,
				enableHiding: false,
			});

			tableColumns.push(selectionColumn);
		}

		// Add actions column at the beginning if position is 'start'
		if (actionsOptions?.show && actionsOptions.position === "start") {
			tableColumns.push(createActionsColumn(columnHelper, actionsOptions));
		}

		// Process regular columns
		simpleColumns.forEach((simpleColumn) => {
			let column: ColumnDef<TData, TValue>;

			// Determine if we should use accessorKey or accessorFn
			if (simpleColumn.accessorKey) {
				column = columnHelper.accessor(simpleColumn.accessorKey as any, {
					header: simpleColumn.header,
					cell: simpleColumn.cell
						? ({ row }: CellContext<TData, any>) =>
								simpleColumn.cell!(row.original)
						: ({ getValue }) => getValue(),
					enableSorting: simpleColumn.enableSorting ?? true,
					enableColumnFilter: simpleColumn.enableFiltering ?? true,
					enableHiding: simpleColumn.enableHiding ?? true,
					meta: {
						className: simpleColumn.className,
						...simpleColumn.meta,
					},
				});
			} else if (simpleColumn.accessorFn) {
				column = columnHelper.accessor(simpleColumn.accessorFn as any, {
					id: simpleColumn.id,
					header: simpleColumn.header,
					cell: simpleColumn.cell
						? ({ row }: CellContext<TData, any>) =>
								simpleColumn.cell!(row.original)
						: ({ getValue }) => getValue(),
					enableSorting: simpleColumn.enableSorting ?? true,
					enableColumnFilter: simpleColumn.enableFiltering ?? true,
					enableHiding: simpleColumn.enableHiding ?? true,
					meta: {
						className: simpleColumn.className,
						...simpleColumn.meta,
					},
				});
			} else {
				// Display column for when no accessor is provided
				column = columnHelper.display({
					id: simpleColumn.id,
					header: simpleColumn.header as any,
					cell: ({ row }) =>
						simpleColumn.cell ? simpleColumn.cell(row.original) : null,
					enableSorting: simpleColumn.enableSorting ?? false,
					enableColumnFilter: simpleColumn.enableFiltering ?? false,
					enableHiding: simpleColumn.enableHiding ?? true,
					meta: {
						className: simpleColumn.className,
						...simpleColumn.meta,
					},
				});
			}

			tableColumns.push(column);
		});

		// Add actions column at the end if position is not 'start'
		if (actionsOptions?.show && actionsOptions.position !== "start") {
			tableColumns.push(createActionsColumn(columnHelper, actionsOptions));
		}

		return tableColumns;
	}, [simpleColumns, showRowSelection, selectionOptions, actionsOptions]);

	// Helper function to create actions column
	function createActionsColumn<TData extends RowData>(
		columnHelper: ReturnType<typeof createColumnHelper<TData>>,
		options: ActionsOptions<TData>,
	): ColumnDef<TData, TValue> {
		return columnHelper.display({
			id: options.columnId || "actions",
			header: options.dropdownLabel || "Hành động",
			cell: ({ row }) => {
				const rowData = row.original;

				// If actions should be in dropdown menu
				if (options.showInDropdown) {
					return (
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button variant="ghost" size="icon">
									<MoreHorizontal className="h-4 w-4" />
									<span className="sr-only">Mở menu</span>
								</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent align="end">
								<DropdownMenuLabel>
									{options.dropdownLabel || "Hành động"}
								</DropdownMenuLabel>
								{options.actions.map((action, index) => (
									<React.Fragment key={index}>
										{index > 0 && action.variant === "destructive" && (
											<DropdownMenuSeparator />
										)}
										<DropdownMenuItem
											onClick={() => action.onClick(rowData)}
											className={`flex items-center gap-2 ${action.variant === "destructive" ? "text-destructive focus:text-destructive" : ""} ${action.className || ""}`}
										>
											{action.icon}
											<span>{action.label}</span>
										</DropdownMenuItem>
									</React.Fragment>
								))}
							</DropdownMenuContent>
						</DropdownMenu>
					);
				}

				// Display actions as individual buttons
				return (
					<div className="flex items-center gap-2 justify-end">
						{options.actions.map((action, index) => (
							<Button
								key={index}
								variant={action.variant || "ghost"}
								size="icon"
								onClick={() => action.onClick(rowData)}
								className={action.className}
							>
								{action.icon}
								<span className="sr-only">{action.label}</span>
							</Button>
						))}
					</div>
				);
			},
			enableSorting: false,
			enableColumnFilter: false,
		});
	}

	// Enhanced handlers for server-side operations
	const handleSortingChange = useCallback(
		(updaterOrValue: any) => {
			const newSorting =
				typeof updaterOrValue === "function"
					? updaterOrValue(sorting)
					: updaterOrValue;

			setSorting(newSorting);

			if (manualSorting && serverSideCallbacks?.onSortingChange) {
				serverSideCallbacks.onSortingChange({
					...getCurrentServerParams(),
					sorting: newSorting,
				});
			}
		},
		[sorting, manualSorting, serverSideCallbacks, getCurrentServerParams],
	);

	const handlePaginationChange = useCallback(
		(updaterOrValue: any) => {
			const newPagination =
				typeof updaterOrValue === "function"
					? updaterOrValue(pagination)
					: updaterOrValue;

			setPagination(newPagination);

			if (manualPagination && serverSideCallbacks?.onPaginationChange) {
				serverSideCallbacks.onPaginationChange({
					...getCurrentServerParams(),
					pagination: newPagination,
				});
			}
		},
		[pagination, manualPagination, serverSideCallbacks, getCurrentServerParams],
	);

	const handleGlobalFilterChange = useCallback(
		(value: string) => {
			setGlobalFilter(value);

			if (manualFiltering) {
				handleServerSideGlobalFilter(value);
			}
		},
		[manualFiltering, handleServerSideGlobalFilter],
	);

	const handleColumnFiltersChange = useCallback(
		(updaterOrValue: any) => {
			const newFilters =
				typeof updaterOrValue === "function"
					? updaterOrValue(columnFilters)
					: updaterOrValue;

			setColumnFilters(newFilters);

			if (manualFiltering) {
				handleServerSideColumnFilters(newFilters);
			}
		},
		[columnFilters, manualFiltering, handleServerSideColumnFilters],
	);

	const handleRowSelectionChange = useCallback((updaterOrValue: any) => {
		setRowSelection(updaterOrValue);
	}, []);

	// Memoized data
	const tableData = useMemo(() => data, [data]);

	// Calculate total count for pagination
	const pageCount = useMemo(() => {
		if (manualPagination && totalCount !== undefined) {
			return Math.ceil(totalCount / pagination.pageSize);
		}
		return undefined;
	}, [manualPagination, totalCount, pagination.pageSize]);

	// TanStack Table instance
	const table = useReactTable({
		data: tableData,
		columns: convertToTableColumns,
		pageCount,
		state: {
			sorting,
			globalFilter,
			columnFilters,
			rowSelection,
			columnVisibility,
			pagination,
		},
		enableRowSelection: showRowSelection || selectionOptions?.show,
		onRowSelectionChange: handleRowSelectionChange,
		onSortingChange: handleSortingChange,
		onGlobalFilterChange: handleGlobalFilterChange,
		onColumnFiltersChange: handleColumnFiltersChange,
		onColumnVisibilityChange: setColumnVisibility,
		onPaginationChange: handlePaginationChange,
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: manualSorting ? undefined : getSortedRowModel(),
		getFilteredRowModel: manualFiltering ? undefined : getFilteredRowModel(),
		getPaginationRowModel: manualPagination
			? undefined
			: getPaginationRowModel(),
		manualPagination,
		manualSorting,
		manualFiltering,
		globalFilterFn: fuzzyFilter,
	});

	// Notify when selected rows change
	useEffect(() => {
		if (onRowSelectionChange && (showRowSelection || selectionOptions?.show)) {
			const selectedRows = table
				.getSelectedRowModel()
				.rows.map((row) => row.original);
			onRowSelectionChange(selectedRows);
		}
	}, [
		rowSelection,
		table,
		onRowSelectionChange,
		showRowSelection,
		selectionOptions,
	]);

	// Cleanup timeouts on unmount
	useEffect(() => {
		return () => {
			if (globalFilterTimeoutRef.current) {
				clearTimeout(globalFilterTimeoutRef.current);
			}
			if (columnFiltersTimeoutRef.current) {
				clearTimeout(columnFiltersTimeoutRef.current);
			}
		};
	}, []);

	return (
		<div className="w-full space-y-4">
			{/* Table controls */}
			<div className="flex flex-col md:flex-row items-center justify-between gap-4">
				{showGlobalFilter && (
					<div className="relative w-full md:w-64">
						<Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
						<Input
							placeholder="Tìm kiếm..."
							value={globalFilter ?? ""}
							onChange={(e) => handleGlobalFilterChange(String(e.target.value))}
							className="pl-8 w-full"
							disabled={loading}
						/>
						{globalFilter && (
							<Button
								variant="ghost"
								size="sm"
								className="absolute right-0 top-0 h-full rounded-l-none"
								onClick={() => handleGlobalFilterChange("")}
								disabled={loading}
							>
								<X className="h-4 w-4" />
								<span className="sr-only">Clear search</span>
							</Button>
						)}
					</div>
				)}

				<div className="flex flex-wrap items-center gap-2">
					{showColumnFilters && (
						<Button
							variant={showColumnFilterRow ? "secondary" : "outline"}
							size="sm"
							onClick={() => setShowColumnFilterRow(!showColumnFilterRow)}
							className="h-8 gap-1"
							disabled={loading}
						>
							<FilterIcon className="h-3.5 w-3.5" />
							<span>Lọc</span>
						</Button>
					)}

					{showColumnToggle && (
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button
									variant="outline"
									size="sm"
									className="h-8 gap-1"
									disabled={loading}
								>
									<Settings2 className="h-3.5 w-3.5" />
									<span>Cột</span>
								</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent align="end" className="w-[200px]">
								{table
									.getAllLeafColumns()
									.filter(
										(column) =>
											column.id !== (selectionOptions?.columnId || "select") &&
											column.id !== (actionsOptions?.columnId || "actions"),
									)
									.map((column) => {
										return (
											<DropdownMenuCheckboxItem
												key={column.id}
												className="capitalize"
												checked={column.getIsVisible()}
												onCheckedChange={(value) =>
													column.toggleVisibility(!!value)
												}
											>
												{column.columnDef.header?.toString()}
											</DropdownMenuCheckboxItem>
										);
									})}
							</DropdownMenuContent>
						</DropdownMenu>
					)}

					{(columnFilters.length > 0 || globalFilter) && (
						<Button
							variant="outline"
							size="sm"
							onClick={() => {
								handleColumnFiltersChange([]);
								handleGlobalFilterChange("");
							}}
							className="h-8 gap-1 text-destructive border-destructive hover:bg-destructive/10"
							disabled={loading}
						>
							<X className="h-3.5 w-3.5" />
							<span>Xóa bộ lọc</span>
						</Button>
					)}

					{loading && (
						<div className="flex items-center gap-1 text-sm text-muted-foreground">
							<Loader2 className="h-3.5 w-3.5 animate-spin" />
							<span>Đang tải...</span>
						</div>
					)}
				</div>
			</div>

			{/* Table */}
			<div className="rounded-md border">
				<Table>
					<TableHeader>
						{table.getHeaderGroups().map((headerGroup) => (
							<TableRow key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<TableHead key={header.id}>
										{header.isPlaceholder ? null : (
											<div
												className={
													header.column.getCanSort()
														? "cursor-pointer select-none flex items-center"
														: "flex items-center"
												}
												onClick={header.column.getToggleSortingHandler()}
											>
												{flexRender(
													header.column.columnDef.header,
													header.getContext(),
												)}

												{/* Sort indicator */}
												{header.column.getCanSort() && (
													<span className="ml-1">
														{{
															asc: <ChevronUp className="h-4 w-4" />,
															desc: <ChevronDown className="h-4 w-4" />,
														}[header.column.getIsSorted() as string] ?? (
															<ChevronsUpDown className="h-4 w-4 opacity-50" />
														)}
													</span>
												)}
											</div>
										)}
									</TableHead>
								))}
							</TableRow>
						))}

						{/* Column filter row */}
						{showColumnFilterRow && (
							<TableRow className="bg-muted/50">
								{table.getHeaderGroups()[0].headers.map((header) => (
									<TableHead key={`filter_${header.id}`} className="p-2">
										{!header.isPlaceholder && header.column.getCanFilter() ? (
											<Input
												type="text"
												value={(header.column.getFilterValue() as string) ?? ""}
												onChange={(e) =>
													header.column.setFilterValue(e.target.value)
												}
												placeholder={`Lọc...`}
												className="h-8 text-xs"
												disabled={loading}
											/>
										) : null}
									</TableHead>
								))}
							</TableRow>
						)}
					</TableHeader>
					<TableBody>
						{table.getRowModel().rows.length === 0 ? (
							<TableRow>
								<TableCell
									colSpan={table.getAllColumns().length}
									className="h-24 text-center"
								>
									{loading ? (
										<div className="flex items-center justify-center gap-2">
											<Loader2 className="h-4 w-4 animate-spin" />
											<span>Đang tải dữ liệu...</span>
										</div>
									) : (
										"Không tìm thấy dữ liệu"
									)}
								</TableCell>
							</TableRow>
						) : (
							table.getRowModel().rows.map((row) => (
								<TableRow
									key={row.id}
									data-state={row.getIsSelected() && "selected"}
									className={row.getIsSelected() ? "bg-primary/5" : undefined}
								>
									{row.getVisibleCells().map((cell) => (
										<TableCell key={cell.id}>
											{flexRender(
												cell.column.columnDef.cell,
												cell.getContext(),
											)}
										</TableCell>
									))}
								</TableRow>
							))
						)}
					</TableBody>
				</Table>
			</div>

			{/* Pagination */}
			{showPagination && (
				<div className="flex items-center flex-wrap gap-2 justify-between">
					<div className="flex-1 text-sm text-muted-foreground">
						{(manualPagination
							? totalCount
							: table.getFilteredRowModel().rows.length) > 0 && (
							<>
								Hiển thị{" "}
								{table.getState().pagination.pageIndex *
									table.getState().pagination.pageSize +
									1}{" "}
								đến{" "}
								{Math.min(
									(table.getState().pagination.pageIndex + 1) *
										table.getState().pagination.pageSize,
									manualPagination
										? totalCount!
										: table.getFilteredRowModel().rows.length,
								)}{" "}
								trong{" "}
								{manualPagination
									? totalCount
									: table.getFilteredRowModel().rows.length}{" "}
								kết quả
							</>
						)}
					</div>
					<div className="flex items-center space-x-6 lg:space-x-8">
						<div className="flex items-center space-x-2">
							<p className="text-sm font-medium">Số dòng</p>
							<Select
								value={`${table.getState().pagination.pageSize}`}
								onValueChange={(value) => {
									table.setPageSize(Number(value));
								}}
								disabled={loading}
							>
								<SelectTrigger className="h-8 w-[70px]">
									<SelectValue
										placeholder={table.getState().pagination.pageSize}
									/>
								</SelectTrigger>
								<SelectContent side="top">
									{pageSizeOptions.map((pageSize) => (
										<SelectItem key={pageSize} value={`${pageSize}`}>
											{pageSize}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</div>
						<div className="flex items-center space-x-2">
							<Button
								variant="outline"
								size="icon"
								className="h-8 w-8 p-0"
								onClick={() => table.setPageIndex(0)}
								disabled={!table.getCanPreviousPage() || loading}
							>
								<span className="sr-only">Trang đầu</span>
								<ChevronsLeft className="h-4 w-4" />
							</Button>
							<Button
								variant="outline"
								size="icon"
								className="h-8 w-8 p-0"
								onClick={() => table.previousPage()}
								disabled={!table.getCanPreviousPage() || loading}
							>
								<span className="sr-only">Trang trước</span>
								<ChevronLeft className="h-4 w-4" />
							</Button>
							<span className="flex items-center gap-1 text-sm">
								<Input
									className="h-8 w-12"
									type="number"
									min={1}
									max={table.getPageCount()}
									value={table.getState().pagination.pageIndex + 1}
									onChange={(e) => {
										const page = e.target.value
											? Number(e.target.value) - 1
											: 0;
										table.setPageIndex(page);
									}}
									disabled={loading}
								/>
								<span>/ {table.getPageCount()}</span>
							</span>
							<Button
								variant="outline"
								size="icon"
								className="h-8 w-8 p-0"
								onClick={() => table.nextPage()}
								disabled={!table.getCanNextPage() || loading}
							>
								<span className="sr-only">Trang tiếp</span>
								<ChevronRight className="h-4 w-4" />
							</Button>
							<Button
								variant="outline"
								size="icon"
								className="h-8 w-8 p-0"
								onClick={() => table.setPageIndex(table.getPageCount() - 1)}
								disabled={!table.getCanNextPage() || loading}
							>
								<span className="sr-only">Trang cuối</span>
								<ChevronsRight className="h-4 w-4" />
							</Button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}

export default DataTable;
