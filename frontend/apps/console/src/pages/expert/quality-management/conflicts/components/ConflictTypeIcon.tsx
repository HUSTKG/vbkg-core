import {
	AlertTriangle,
	XCircle,
	RefreshCw,
	Calendar,
	ArrowUpDown,
	FileText,
	GitMerge,
} from "lucide-react";

import { ConflictType } from "@vbkg/types";

interface ConflictTypeIconProps {
	type: ConflictType
}

export const ConflictTypeIcon = ({ type }: ConflictTypeIconProps) => {
	const iconMap: any = {
		duplicate_entity: <GitMerge className="h-4 w-4 text-purple-500" />,
		attribute_mismatch: <FileText className="h-4 w-4 text-blue-500" />,
		contradictory_relationship: (
			<ArrowUpDown className="h-4 w-4 text-red-500" />
		),
		temporal_conflict: <Calendar className="h-4 w-4 text-orange-500" />,
		source_conflict: <RefreshCw className="h-4 w-4 text-indigo-500" />,
		schema_mismatch: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
		missing_relationship: <XCircle className="h-4 w-4 text-gray-500" />,
	};

	return iconMap[type] || <AlertTriangle className="h-4 w-4 text-gray-500" />;
};
