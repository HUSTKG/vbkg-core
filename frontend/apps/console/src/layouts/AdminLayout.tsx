import { useLogout } from "@vbkg/api-client";
import { getSession, setSession } from "@vbkg/utils";
import {
	DatabaseIcon,
	Edit3,
	HomeIcon,
	NetworkIcon,
	Settings,
	ShieldCheckIcon,
	Users,
	UsersIcon,
} from "lucide-react";
import { Outlet, useNavigate } from "react-router";
import { queryClient } from "../App";
import AppLayout from "./main";

const AdminLayout = () => {
	const session = getSession();
	const { mutateAsync: logout } = useLogout({});
	const navigate = useNavigate();
	return (
		<AppLayout
			menuItems={[
				{
					title: "Tổng Quan",
					path: "/admin/dashboard",
					icon: <HomeIcon />,
				},
				{
					title: "Xử lý dữ liệu",
					icon: <DatabaseIcon />,
					submenu: [
						{
							title: "🔌 Nguồn dữ liệu",
							path: "/admin/data/sources",
						},
						{
							title: "⚙️ Pipelines",
							path: "/admin/data/pipelines",
						},
					],
				},
				{
					title: "Đồ thị tri thức",
					icon: <NetworkIcon />,
					submenu: [
						{
							title: "📊 Tổng quan",
							path: "/admin/kg/overview",
						},
						{
							title: "🏢 Thực thể",
							path: "/admin/kg/entities",
						},
						{
							title: "🔗 Mối quan hệ ",
							path: "/admin/kg/relationships",
						},
						{
							title: "🔍 Tra cứu đồ thị",
							path: "/admin/kg/explorer",
						},
					],
				},
				{
					title: "Quản lý chất lượng",
					icon: <ShieldCheckIcon />,
					submenu: [
						{
							title: "📈 Tổng quan",
							path: "/admin/quality/dashboard",
						},
						{
							title: "⚠️ Xung đột",
							path: "/admin/quality/conflicts",
						},
						{
							title: "💯 Hoàn thiện đồ thị",
							path: "/admin/quality/completion",
						},
					],
				},
				{
					title: "Quản lý miền",
					icon: <Edit3 />,
					submenu: [
						{
							title: "🌐 Domain",
							path: "/admin/domain",
						},
						{
							title: "🏛️ Ontology",
							path: "/admin/domain/fibo",
						},
						{
							title: "🗺️ Khớp Ontology",
							path: "/admin/domain/fibo-mapping",
						},
					],
				},
				{
					title: "Quản trị người dùng",
					icon: <UsersIcon />,
					submenu: [
						{
							title: "👤 Người dùng",
							path: "/admin/users",
						},
						{
							title: "🔐 Vai trò & Quyền",
							path: "/admin/users/roles",
						},
					],
				},
			]}
			userEmail={session?.user?.email}
			userName={session?.user?.name}
			userAvatar={""}
			onLogout={async () => {
				await logout();
				queryClient.removeQueries();
				setSession(null);
				navigate("/login");
			}}
			onNavigation={(path) => {
				navigate(path);
			}}
			profileMenuItems={[
				{
					icon: <Users />,
					label: "Profile",
					onClick: () => {
						// Handle profile click
					},
				},
				{
					icon: <Settings />,
					label: "Settings",
					onClick: () => {
						// Handle settings click
					},
				},
			]}
		>
			<Outlet />
		</AppLayout>
	);
};

export default AdminLayout;
