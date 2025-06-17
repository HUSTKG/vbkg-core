import { UserAction, UserActivity } from "@vbkg/types";
import { formatTimeAgo } from "@vbkg/utils";
import { Globe2, Monitor } from "lucide-react";
import { getActivityColor, getActivityIcon, getActivityLabel } from "./utils";

export const ActivityTimeline = ({
	activities,
	onActivityClick,
}: {
	activities: UserActivity[];
	onActivityClick: (activity: UserActivity) => void;
}) => {
	return (
		<div className="space-y-4">
			{activities.map((activity) => (
				<div
					key={activity.id}
					className="flex items-start space-x-4 p-4 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
					onClick={() => onActivityClick?.(activity)}
				>
					<div
						className={`p-2 rounded-full ${getActivityColor(activity.action)}`}
					>
						{getActivityIcon(activity.action)}
					</div>

					<div className="flex-1 min-w-0">
						<div className="flex items-center justify-between">
							<h4 className="text-sm font-medium text-gray-900 truncate">
								{getActivityLabel(activity.action)}
							</h4>
							<time className="text-xs text-gray-500 flex-shrink-0">
								{formatTimeAgo(new Date(activity.created_at).getTime())}
							</time>
						</div>

						<div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
							{/* <div className="flex items-center space-x-1"> */}
							{/* 	<User size={12} /> */}
							{/* 	<span>{activity.user}</span> */}
							{/* </div> */}
							{activity.ip_address && (
								<div className="flex items-center space-x-1">
									<Globe2 size={12} />
									<span>{activity.ip_address}</span>
								</div>
							)}
							{activity.user_agent && (
								<div className="flex items-center space-x-1">
									<Monitor size={12} />
									<span>{activity.user_agent.split(" ")[0]}</span>
								</div>
							)}
						</div>

						{activity.details && Object.keys(activity.details).length > 0 && (
							<div className="mt-2 p-2 bg-gray-50 rounded text-xs">
								<details>
									<summary className="cursor-pointer text-gray-600">
										Additional Details
									</summary>
									<div className="mt-1 space-y-1">
										{Object.entries(activity.details).map(([key, value]) => (
											<div key={key} className="flex justify-between">
												<span className="font-medium">{key}:</span>
												<span>{String(value)}</span>
											</div>
										))}
									</div>
								</details>
							</div>
						)}
					</div>
				</div>
			))}
		</div>
	);
};
