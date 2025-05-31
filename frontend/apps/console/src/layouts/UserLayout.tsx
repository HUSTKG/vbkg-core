import { useLogout } from "@vbkg/api-client";
import { getSession, setSession } from "@vbkg/utils";
import {
  Bot,
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
          title: "Knowledge Search",
          icon: <Network />,
          path: "/user/search",
        },
        {
          title: "Chatbot",
          path: "/user/chatbot",
          icon: <Bot />,
        },
        {
          title: "Visualization",
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
