import { DataTable, SimpleColumnDef } from "@/components";
import { UserActivity } from "@vbkg/types";
import { getActivityColor, getActivityIcon } from "./utils";

interface ActivityTableProps {
	setSelectedActivity: (activity: UserActivity) => void;
	activities: UserActivity[];
}

export default function ActivityTable() {
	const activityColumns: SimpleColumnDef<any, any>[] = [
		{
			header: "Activity",
			accessorKey: "title",
			cell: (row) => (
				<div className="flex items-center space-x-3">
					<div className={`p-2 rounded-full ${getActivityColor(row.type)}`}>
						{getActivityIcon(row.type)}
					</div>
					<div>
						<div className="font-medium text-sm">{row.title}</div>
						<div className="text-xs text-gray-500">{row.description}</div>
					</div>
				</div>
			),
		},
		{
			header: "User",
			accessorKey: "user",
			cell: (row) => (
				<div className="flex items-center space-x-2">
					<User size={16} className="text-gray-400" />
					<span className="text-sm">{row.user}</span>
				</div>
			),
		},
		{
			header: "Time",
			accessorKey: "timestamp",
			cell: (row) => (
				<div className="text-sm text-gray-600">
					{new Date(row.timestamp).toLocaleString()}
				</div>
			),
		},
		{
			header: "IP Address",
			accessorKey: "ip_address",
			cell: (row) => (
				<code className="text-xs bg-gray-100 p-1 rounded">
					{row.ip_address}
				</code>
			),
		},
		{
			header: "Actions",
			cell: (row) => (
				<button
					onClick={() => setSelectedActivity(row)}
					className="p-1 hover:bg-gray-100 rounded"
					title="View Details"
				>
					<Eye size={16} />
				</button>
			),
		},
	];

	return (
		<div className="bg-white rounded-lg border shadow-sm">
			<div className="p-6 border-b">
				<h2 className="text-lg font-semibold">Activity Table</h2>
			</div>
			<div className="p-6">
				<DataTable
					data={activities}
					columns={activityColumns}
					showGlobalFilter={true}
				/>
			</div>
		</div>
	);
}
