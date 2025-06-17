import { useLogout } from "@vbkg/api-client";
import { getSession, setSession } from "@vbkg/utils";
import {
	Network,
	PaintbrushIcon,
	Settings,
	UserIcon,
	Users,
} from "lucide-react";
import { Outlet, useNavigate } from "react-router";
import { queryClient } from "../App";
import AppLayout from "./main";

const UserLayout = () => {
	const session = getSession();
	const { mutateAsync: logout } = useLogout({});
	const navigate = useNavigate();
	return (
		<AppLayout
			menuItems={[
				{
					title: "Tìm kiếm",
					icon: <Network />,
					path: "/user/search",
				},
				{
					title: "Bảng biểu",
					icon: <PaintbrushIcon />,
					path: "/user/visualization",
				},
				{
					title: "API Access",
					icon: <UserIcon />,
					path: "/user/api-access",
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
			onNavigation={(path) => navigate(path)}
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

export default UserLayout;
