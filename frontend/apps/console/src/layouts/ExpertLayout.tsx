import { useLogout } from "@vbkg/api-client";
import { getSession, setSession } from "@vbkg/utils";
import {
	Construction,
	DatabaseIcon,
	Edit3,
	GitGraphIcon,
	Settings,
	Users,
} from "lucide-react";
import { Outlet, useNavigate } from "react-router";
import { queryClient } from "../App";
import AppLayout from "./main";

const ExpertLayout = () => {
	const session = getSession();
	const { mutateAsync: logout } = useLogout({});
	const navigate = useNavigate();
	return (
		<AppLayout
			menuItems={[
				{
					title: "Quản lý miền",
					icon: <Edit3 />,
					submenu: [
						{
							title: "🌐 Domain",
							path: "/expert/domain",
						},
						{
							title: "🏛️ Ontology",
							path: "/expert/domain/ontology",
						},
						{
							title: "🗺️ Khớp Ontology",
							path: "/expert/domain/fibo-mapping",
						},
					],
				},
				{
					title: "Xử lý dữ liệu",
					icon: <DatabaseIcon />,
					submenu: [
						{
							title: "🔌 Nguồn Dữ Liệu",
							path: "/expert/data/sources",
						},
						{
							title: "⚙️ Pipeline",
							path: "/expert/data/pipelines",
						},
					],
				},
				{
					title: "Quản lý chất lượng",
					icon: <Construction />,
					submenu: [
						{
							title: "🛠️ Xử lý xung đột",
							path: "/expert/quality/conflicts",
						},
						{
							title: "✅ Hoàn thiện đồ thị",
							path: "/expert/quality/completion",
						},
					],
				},
				{
					title: "Đồ thị tri thức",
					icon: <GitGraphIcon />,
					submenu: [
						{
							title: "🔍 Tra cứu",
							path: "/expert/kg/explorer",
						},
						{
							title: "🏢 Quản lý thực thể",
							path: "/expert/kg/entities",
						},
						{
							title: "🔗 Quản lý mối quan hệ",
							path: "/expert/kg/relationships",
						},
					],
				},
			]}
			userEmail={session?.user?.email}
			userName={session?.user?.name}
			userAvatar={""}
			onNavigation={(path) => navigate(path)}
			onLogout={async () => {
				await logout();
				queryClient.removeQueries();
				setSession(null);
				navigate("/login");
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

export default ExpertLayout;
