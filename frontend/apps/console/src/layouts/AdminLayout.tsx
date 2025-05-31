import { useLogout } from "@vbkg/api-client";
import { getSession, setSession } from "@vbkg/utils";
import {
  DatabaseIcon,
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
          title: "Dashboard",
          path: "/admin/dashboard",
          icon: <HomeIcon />,
        },
        {
          title: "Knowledge Graph",
          icon: <NetworkIcon />,
          submenu: [
            {
              title: "📊 Overview",
              path: "/admin/kg/overview",
            },
            {
              title: "🏢 Entities",
              path: "/admin/kg/entities",
            },
            {
              title: "🔗 Relationships",
              path: "/admin/kg/relationships",
            },
            {
              title: "🔍 Graph Explorer",
              path: "/admin/kg/explorer",
            },
          ],
        },
        {
          title: "Quality Management",
          icon: <ShieldCheckIcon />,
          submenu: [
            {
              title: "📈 Quality Dashboard",
              path: "/admin/quality/dashboard",
            },
            {
              title: "⚠️ Conflicts",
              path: "/admin/quality/conflicts",
            },
          ],
        },
        {
          title: "Data Management",
          icon: <DatabaseIcon />,
          submenu: [
            {
              title: "🔌 Data Sources",
              path: "/admin/data/sources",
            },
            {
              title: "⚙️ Pipelines",
              path: "/admin/data/pipelines",
            },
          ],
        },
        {
          title: "User Management",
          icon: <UsersIcon />,
          submenu: [
            {
              title: "👤 Users",
              path: "/admin/users",
            },
            {
              title: "🔐 Roles & Permissions",
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
