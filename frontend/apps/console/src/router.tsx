import { Suspense, lazy } from "react";
import { Navigate, type RouteObject, createBrowserRouter } from "react-router";

// Layouts
import { getSession, isValidSession } from "@vbkg/utils";
import AdminLayout from "./layouts/AdminLayout";
import AuthLayout from "./layouts/AuthLayout";
import AdvancedErrorElement from "./pages/Error";
import NotFound from "./pages/NotFound";
import ExpertLayout from "./layouts/ExpertLayout";
import UserLayout from "./layouts/UserLayout";

// Auth Pages
const LoginPage = lazy(() => import("./pages/auth/Login"));
const RegisterPage = lazy(() => import("./pages/auth/Register"));
const ForgotPasswordPage = lazy(() => import("./pages/auth/ForgotPassword"));

// Admin Pages
const AdminDashboard = lazy(() => import("./pages/admin/dashboard"));
const ManageUser = lazy(() => import("./pages/admin/user-management/users"));
const UserDetail = lazy(
  () => import("./pages/admin/user-management/users/detail"),
);
const RoleManagement = lazy(
  () => import("./pages/admin/user-management/roles"),
);

const ConfigureDataSource = lazy(
  () => import("./pages/common/data-management/sources"),
);
const DataSourceDetail = lazy(
  () => import("./pages/common/data-management/sources/detail"),
);
const ConfigureDataPipeline = lazy(
  () => import("./pages/common/data-management/pipelines"),
);
const DataPipelineDetail = lazy(
  () => import("./pages/common/data-management/pipelines/detail"),
);
const KGOverview = lazy(
  () => import("./pages/common/knowledge-graph/overview"),
);
const KGEntities = lazy(
  () => import("./pages/common/knowledge-graph/entities"),
);
const KGRelationships = lazy(
  () => import("./pages/common/knowledge-graph/relationship"),
);
const KGExplorer = lazy(
  () => import("./pages/common/knowledge-graph/explorer"),
);
const QualityDashboard = lazy(
  () => import("./pages/common/quality-management/dashboard"),
);
const QualityConflicts = lazy(
  () => import("./pages/common/quality-management/conflicts"),
);

// Expert Pages
const ExpertConflict = lazy(() => import("./pages/expert/conflicts"));
const ExpertKGRelationship = lazy(
  () => import("./pages/common/knowledge-graph/relationship"),
);
const ExpertKGEntity = lazy(
  () => import("./pages/common/knowledge-graph/entities"),
);
const ExpertKGExplorer = lazy(
  () => import("./pages/common/knowledge-graph/explorer"),
);
const DomainManagement = lazy(
  () => import("./pages/expert/domain-management/domain"),
);
const DomainEntityTypes = lazy(
  () => import("./pages/expert/domain-management/entity-types"),
);
const DomainRelationshipTypes = lazy(
  () => import("./pages/expert/domain-management/relationship-types"),
);

const DomainFibo = lazy(() => import("./pages/expert/domain-management/fibo"));
const DomainFiboMapping = lazy(
  () => import("./pages/expert/domain-management/fibo-mapping"),
);
const DomainExtractionTemplate = lazy(
  () => import("./pages/expert/domain-management/extraction-templates"),
);

// User Pages
const UserSearch = lazy(() => import("./pages/user/search"));
const UserChatBot = lazy(() => import("./pages/user/chatbot"));
const UserVisualization = lazy(() => import("./pages/user/visualization"));
const UserAPIAccess = lazy(() => import("./pages/user/api-access"));

// Loading Component
const PageLoading = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
  </div>
);

// Role Guard Component
const RoleGuard = ({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles: string[];
}) => {
  const session = getSession();
  const userRole = session?.user?.roles;
  if (
    !userRole ||
    !allowedRoles.some((role) => userRole?.includes(role)) ||
    !isValidSession(session)
  ) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// Route Definitions
const routes: RouteObject[] = [
  // Auth Routes
  {
    path: "/",
    element: <AuthLayout />,
    children: [
      {
        path: "",
        index: true,
        element: (
          <Suspense fallback={<PageLoading />}>
            <Navigate to="/login" replace />
          </Suspense>
        ),
      },
      {
        path: "login",
        element: (
          <Suspense fallback={<PageLoading />}>
            <LoginPage />
          </Suspense>
        ),
      },
      {
        path: "register",
        element: (
          <Suspense fallback={<PageLoading />}>
            <RegisterPage />
          </Suspense>
        ),
      },
      {
        path: "forgot-password",
        element: (
          <Suspense fallback={<PageLoading />}>
            <ForgotPasswordPage />
          </Suspense>
        ),
      },
    ],
  },

  // Business Routes
  {
    path: "/user",
    element: (
      <RoleGuard allowedRoles={["user"]}>
        <UserLayout />
      </RoleGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="search" replace />,
      },
      {
        path: "search",
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserSearch />
          </Suspense>
        ),
      },
      {
        path: "chatbot",
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserChatBot />
          </Suspense>
        ),
      },
      {
        path: "visualization",
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserVisualization />
          </Suspense>
        ),
      },
      {
        path: "api-access",
        element: (
          <Suspense fallback={<PageLoading />}>
            <UserAPIAccess />
          </Suspense>
        ),
      },
    ],
  },
  {
    path: "/expert",
    element: (
      <RoleGuard allowedRoles={["expert"]}>
        <ExpertLayout />
      </RoleGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/expert/conflicts" replace />,
      },
      {
        path: "conflicts",
        element: (
          <Suspense fallback={<PageLoading />}>
            <ExpertConflict />
          </Suspense>
        ),
      },
      {
        path: "kg",
        children: [
          {
            path: "explorer",
            element: (
              <Suspense fallback={<PageLoading />}>
                <ExpertKGExplorer />
              </Suspense>
            ),
          },
          {
            path: "relationships",
            element: (
              <Suspense fallback={<PageLoading />}>
                <ExpertKGRelationship />
              </Suspense>
            ),
          },
          {
            path: "entities",
            element: (
              <Suspense fallback={<PageLoading />}>
                <ExpertKGEntity />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: "domain",
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainManagement />
              </Suspense>
            ),
          },
          {
            path: "entity-types",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainEntityTypes />
              </Suspense>
            ),
          },
          {
            path: "relationship-types",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainRelationshipTypes />
              </Suspense>
            ),
          },
          {
            path: "fibo",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainFibo />
              </Suspense>
            ),
          },
          {
            path: "fibo-mapping",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainFiboMapping />
              </Suspense>
            ),
          },
          {
            path: "extraction-templates",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DomainExtractionTemplate />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },

  // Admin Routes
  {
    path: "/admin",
    element: (
      <RoleGuard allowedRoles={["admin"]}>
        <AdminLayout />
      </RoleGuard>
    ),
    errorElement: <AdvancedErrorElement />,
    children: [
      {
        index: true,
        element: <Navigate to="/admin/dashboard" replace />,
      },
      {
        path: "dashboard",
        element: (
          <Suspense fallback={<PageLoading />}>
            <AdminDashboard />
          </Suspense>
        ),
      },
      {
        path: "users",
        children: [
          {
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <ManageUser />
              </Suspense>
            ),
          },
          {
            path: "user/:id",
            element: (
              <Suspense fallback={<PageLoading />}>
                <UserDetail />
              </Suspense>
            ),
          },
          {
            path: "roles",
            element: (
              <Suspense fallback={<PageLoading />}>
                <RoleManagement />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: "data/sources",
        children: [
          {
            path: "",
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <ConfigureDataSource />
              </Suspense>
            ),
          },
          {
            path: ":id",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DataSourceDetail />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: "data/pipelines",
        children: [
          {
            path: "",
            index: true,
            element: (
              <Suspense fallback={<PageLoading />}>
                <ConfigureDataPipeline />
              </Suspense>
            ),
          },
          {
            path: ":id",
            element: (
              <Suspense fallback={<PageLoading />}>
                <DataPipelineDetail />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: "kg",
        children: [
          {
            path: "overview",
            element: (
              <Suspense fallback={<PageLoading />}>
                <KGOverview />
              </Suspense>
            ),
          },
          {
            path: "entities",
            element: (
              <Suspense fallback={<PageLoading />}>
                <KGEntities />
              </Suspense>
            ),
          },
          {
            path: "relationships",
            element: (
              <Suspense fallback={<PageLoading />}>
                <KGRelationships />
              </Suspense>
            ),
          },
          {
            path: "explorer",
            element: (
              <Suspense fallback={<PageLoading />}>
                <KGExplorer />
              </Suspense>
            ),
          },
        ],
      },
      {
        path: "quality",
        children: [
          {
            path: "dashboard",
            element: (
              <Suspense fallback={<PageLoading />}>
                <QualityDashboard />
              </Suspense>
            ),
          },
          {
            path: "conflicts",
            element: (
              <Suspense fallback={<PageLoading />}>
                <QualityConflicts />
              </Suspense>
            ),
          },
        ],
      },
    ],
  },

  // 404 Route
  {
    path: "*",
    element: (
      <Suspense fallback={<PageLoading />}>
        <NotFound />
      </Suspense>
    ),
  },
];

export const router = createBrowserRouter(routes);

// Export route paths for programmatic navigation
export const ROUTES = {
  // Auth Routes
  LOGIN: "/login",
  REGISTER: "/register",
  FORGOT_PASSWORD: "/forgot-password",

  // Business Routes
  DASHBOARD: "/dashboard",
  PROJECTS: "/projects",
  TEAM: "/team",
  INTEGRATION: "/integration",
  USAGE: "/usage",
  BILLING: "/billing",

  // Admin Routes
  ADMIN_DASHBOARD: "/admin/dashboard",
  ADMIN_USERS: "/admin/users",
  ADMIN_DATA_SOURCES: "/admin/data-sources",
  ADMIN_DATA_PIPELINES: "/admin/data-pipelines",
  ADMIN_MONITORING: "/admin/monitoring",
  ADMIN_SETTINGS: "/admin/settings",

  // Shared Features
  API_KEYS: "/api-keys",
  VISUALIZATIONS: "/visualizations",
  PROFILE: "/profile",
} as const;
