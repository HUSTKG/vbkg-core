import { UserAction } from "@vbkg/types";
import {
	Activity,
	BarChart3,
	Code,
	Edit,
	GitBranch,
	LogIn,
	LogOut,
	MessageSquare,
	Plus,
	Search,
	Trash2,
	Upload,
} from "lucide-react";
import { ReactNode } from "react";

export const getActivityIcon = (type: UserAction): ReactNode => {
	const iconMap = {
		user_login: <LogIn size={16} />,
		user_logout: <LogOut size={16} />,
		entity_create: <Plus size={16} />,
		entity_update: <Edit size={16} />,
		entity_delete: <Trash2 size={16} />,
		relationship_create: <GitBranch size={16} />,
		search_query: <Search size={16} />,
		visualization_create: <BarChart3 size={16} />,
		api_call: <Code size={16} />,
		file_upload: <Upload size={16} />,
		chat_message: <MessageSquare size={16} />,
	};
	return iconMap[type] || <Activity size={16} />;
};

export const getActivityColor = (type: UserAction) => {
	const colorMap = {
		user_login: "bg-green-100 text-green-600",
		user_logout: "bg-gray-100 text-gray-600",
		entity_create: "bg-blue-100 text-blue-600",
		entity_update: "bg-yellow-100 text-yellow-600",
		entity_delete: "bg-red-100 text-red-600",
		relationship_create: "bg-purple-100 text-purple-600",
		search_query: "bg-indigo-100 text-indigo-600",
		visualization_create: "bg-green-100 text-green-600",
		api_call: "bg-orange-100 text-orange-600",
		file_upload: "bg-teal-100 text-teal-600",
		chat_message: "bg-pink-100 text-pink-600",
	};
	return colorMap[type] || "bg-gray-100 text-gray-600";
};

export const getActivityLabel = (type: UserAction) => {
	const labelMap = {
		user_login: "Đăng nhập",
		user_logout: "Đăng xuất",
		entity_create: "Tạo thực thể mới",
		entity_update: "Cập nhật thực thể",
		entity_delete: "Xóa thực thể",
		relationship_create: "Tạo liên kết",
		search_query: "Tìm kiếm",
		visualization_create: "Tạo biểu đồ",
		api_call: "Gọi API",
		file_upload: "Tải File",
		chat_message: "Chat",
	};
	return labelMap[type] || "Không rõ";
};
