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
          title: "Conflicts",
          icon: <Construction />,
          path: "/expert/conflicts",
        },
        {
          title: "Knowledge Graph",
          icon: <GitGraphIcon />,
          submenu: [
            {
              title: "🔍 Graph Explorer",
              path: "/expert/kg/explorer",
            },
            {
              title: "🏢 Entity Management",
              path: "/expert/kg/entities",
            },
            {
              title: "🔗 Relationship Management",
              path: "/expert/kg/relationships",
            },
          ],
        },
        {
          title: "Data Management",
          icon: <DatabaseIcon />,
          submenu: [
            {
              title: "🔌 Data Sources",
              path: "/expert/data/sources",
            },
            {
              title: "⚙️ Pipeline Management",
              path: "/expert/data/pipelines",
            },
          ],
        },
        {
          title: "Domain Customization",
          icon: <Edit3 />,
          submenu: [
            {
              title: "🌐 Domain Management",
              path: "/expert/domain",
            },
            {
              title: "🏷️ Entity Types",
              path: "/expert/domain/entity-types",
            },
            {
              title: "🔗 Relationship Types",
              path: "/expert/domain/relationship-types",
            },
            {
              title: "🏛️ FIBO",
              path: "/expert/domain/fibo",
            },
            {
              title: "🗺️ FIBO Mapping",
              path: "/expert/domain/fibo-mapping",
            },
            {
              title: "📑 Extraction Templates",
              path: "/expert/domain/extraction-templates",
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
