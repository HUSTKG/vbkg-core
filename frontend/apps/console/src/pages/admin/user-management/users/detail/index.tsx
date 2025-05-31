import { useState, useEffect } from "react";
import * as z from "zod";
import {
  ArrowLeft,
  Shield,
  Key,
  CheckCircle2,
  XCircle,
  Trash2,
} from "lucide-react";
import {
  AppForm,
  Avatar,
  AvatarFallback,
  AvatarImage,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  ConfirmDialog,
  DataTable,
  Dialog,
  FieldConfig,
  Input,
  Label,
  Separator,
  SimpleColumnDef,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast,
} from "@vbkg/ui";
import { useNavigate, useParams } from "react-router";

// Types for our data
interface User {
  id: string;
  email: string;
  full_name?: string;
  department?: string;
  position?: string;
  bio?: string;
  avatar_url?: string;
  is_active: boolean;
  roles: string[];
  last_sign_in_at?: Date;
  created_at: Date;
  updated_at: Date;
}

interface Role {
  id: number;
  name: string;
  description?: string;
  created_at: Date;
  permissions?: string[];
}

interface UserActivity {
  id: string;
  user_id: string;
  activity_type: string;
  details: string;
  ip_address?: string;
  created_at: Date;
}

// Mock data
const mockUsers: User[] = [
  {
    id: "1",
    email: "admin@example.com",
    full_name: "Admin User",
    department: "IT",
    position: "System Administrator",
    bio: "Experienced system administrator with over 10 years in IT infrastructure management.",
    is_active: true,
    roles: ["admin"],
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=admin",
    created_at: new Date("2024-01-01"),
    updated_at: new Date("2024-01-01"),
    last_sign_in_at: new Date("2024-05-18"),
  },
  {
    id: "2",
    email: "john.doe@example.com",
    full_name: "John Doe",
    department: "Engineering",
    position: "Senior Developer",
    bio: "Full-stack developer with expertise in React, Node.js, and cloud infrastructure.",
    is_active: true,
    roles: ["developer", "viewer"],
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=john",
    created_at: new Date("2024-01-15"),
    updated_at: new Date("2024-02-10"),
    last_sign_in_at: new Date("2024-05-17"),
  },
  {
    id: "3",
    email: "jane.smith@example.com",
    full_name: "Jane Smith",
    department: "Data Science",
    position: "Data Analyst",
    bio: "Data analyst focused on deriving insights from large datasets using Python and machine learning.",
    is_active: true,
    roles: ["analyst", "viewer"],
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=jane",
    created_at: new Date("2024-02-01"),
    updated_at: new Date("2024-02-01"),
    last_sign_in_at: new Date("2024-05-15"),
  },
  {
    id: "4",
    email: "mark.wilson@example.com",
    full_name: "Mark Wilson",
    department: "Marketing",
    position: "Marketing Manager",
    bio: "Marketing professional with extensive experience in digital campaigns and brand management.",
    is_active: false,
    roles: ["viewer"],
    avatar_url: "https://api.dicebear.com/7.x/avataaars/svg?seed=mark",
    created_at: new Date("2024-02-15"),
    updated_at: new Date("2024-03-01"),
    last_sign_in_at: new Date("2024-04-10"),
  },
];

const mockRoles: Role[] = [
  {
    id: 1,
    name: "admin",
    description: "Full system access with all permissions",
    created_at: new Date("2024-01-01"),
    permissions: ["all:read", "all:write", "all:delete", "all:admin"],
  },
  {
    id: 2,
    name: "developer",
    description: "Access to development tools and APIs",
    created_at: new Date("2024-01-01"),
    permissions: [
      "pipelines:read",
      "pipelines:write",
      "data:read",
      "data:write",
    ],
  },
  {
    id: 3,
    name: "analyst",
    description: "Access to data and analytics",
    created_at: new Date("2024-01-01"),
    permissions: ["data:read", "analytics:read", "analytics:write"],
  },
  {
    id: 4,
    name: "viewer",
    description: "Read-only access to the system",
    created_at: new Date("2024-01-01"),
    permissions: ["data:read", "pipelines:read", "analytics:read"],
  },
];

// Mock user activities
const mockUserActivities: UserActivity[] = [
  {
    id: "act1",
    user_id: "1",
    activity_type: "login",
    details: "User logged in successfully",
    ip_address: "192.168.1.1",
    created_at: new Date("2024-05-18T08:30:00"),
  },
  {
    id: "act2",
    user_id: "1",
    activity_type: "data_access",
    details: "Accessed sales dashboard",
    ip_address: "192.168.1.1",
    created_at: new Date("2024-05-18T09:15:00"),
  },
  {
    id: "act3",
    user_id: "1",
    activity_type: "admin_action",
    details: "Created new user john.doe@example.com",
    ip_address: "192.168.1.1",
    created_at: new Date("2024-05-17T14:20:00"),
  },
  {
    id: "act4",
    user_id: "1",
    activity_type: "login",
    details: "User logged in successfully",
    ip_address: "192.168.1.1",
    created_at: new Date("2024-05-17T08:25:00"),
  },
];

// Mock API functions
const fetchUser = async (id: string): Promise<User | undefined> => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      const user = mockUsers.find((u) => u.id === id);
      resolve(user);
    }, 500);
  });
};

const fetchRoles = async (): Promise<Role[]> => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockRoles);
    }, 500);
  });
};

const fetchUserActivities = async (userId: string): Promise<UserActivity[]> => {
  // Simulate API call
  return new Promise((resolve) => {
    setTimeout(() => {
      const activities = mockUserActivities.filter((a) => a.user_id === userId);
      resolve(activities);
    }, 500);
  });
};

// Password change dialog
const PasswordChangeDialog = ({
  isOpen,
  onClose,
  onChangePassword,
  userId,
}: {
  isOpen: boolean;
  onClose: () => void;
  onChangePassword: (userId: string, newPassword: string) => void;
  userId: string;
}) => {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (isOpen) {
      // Reset form
      setPassword("");
      setConfirmPassword("");
      setError("");
    }
  }, [isOpen]);

  const handleSubmit = () => {
    // Validate
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    onChangePassword(userId, password);
    onClose();
  };

  return (
    <Dialog
      title="Change Password"
      description="Enter a new password for this user."
      primaryActionText="Change Password"
      onPrimaryAction={handleSubmit}
      open={isOpen}
      showFooter={false}
      onOpenChange={onClose}
    >
      <div className="space-y-4 py-2">
        <div className="space-y-2">
          <Label htmlFor="new-password">New Password</Label>
          <Input
            id="new-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New password"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirm-password">Confirm Password</Label>
          <Input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
          />
        </div>

        {error && <div className="text-sm text-red-500">{error}</div>}
      </div>
    </Dialog>
  );
};

// Delete user dialog
const DeleteUserDialog = ({
  isOpen,
  onClose,
  onConfirm,
  user,
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  user: User | null;
}) => {
  if (!user) return null;

  return (
    <ConfirmDialog
      title="Delete User"
      message="Are you sure you want to delete this user? This action cannot be undone."
      onConfirm={onConfirm}
      onCancel={onClose}
      isOpen={isOpen}
    />
  );
};

// User role management dialog
const UserRolesDialog = ({
  isOpen,
  onClose,
  onUpdateRoles,
  user,
  allRoles,
}: {
  isOpen: boolean;
  onClose: () => void;
  onUpdateRoles: (userId: string, roles: string[]) => void;
  user: User | null;
  allRoles: Role[];
}) => {
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  useEffect(() => {
    if (user && isOpen) {
      setSelectedRoles(user.roles || []);
    }
  }, [user, isOpen]);

  if (!user) return null;

  const handleToggleRole = (roleName: string) => {
    setSelectedRoles((prev) => {
      if (prev.includes(roleName)) {
        return prev.filter((r) => r !== roleName);
      } else {
        return [...prev, roleName];
      }
    });
  };

  const handleSubmit = () => {
    onUpdateRoles(user.id, selectedRoles);
    onClose();
  };

  return (
    <Dialog
      title="Manage User Roles"
      description="Assign roles to this user."
      onPrimaryAction={handleSubmit}
      primaryActionText="Save Roles"
      onClose={onClose}
      open={isOpen}
      onOpenChange={onClose}
    >
      <div className="py-4">
        <div className="space-y-4">
          {allRoles.map((role) => (
            <div key={role.id} className="flex items-start space-x-2">
              <input
                type="checkbox"
                id={`role-${role.id}`}
                checked={selectedRoles.includes(role.name)}
                onChange={() => handleToggleRole(role.name)}
                className="mt-1"
              />
              <div>
                <label
                  htmlFor={`role-${role.id}`}
                  className="font-medium cursor-pointer"
                >
                  {role.name}
                </label>
                <p className="text-sm text-muted-foreground">
                  {role.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Dialog>
  );
};

// Form schema
const userSchema = z.object({
  full_name: z.string().optional(),
  department: z.string().optional(),
  position: z.string().optional(),
  bio: z.string().optional(),
  avatar_url: z.string().optional(),
});

export default function UserDetailsPage() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [user, setUser] = useState<User | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [activities, setActivities] = useState<UserActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRolesDialog, setShowRolesDialog] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;

      try {
        setLoading(true);

        const [userData, rolesData, activitiesData] = await Promise.all([
          fetchUser(id as string),
          fetchRoles(),
          fetchUserActivities(id as string),
        ]);

        if (userData) {
          setUser(userData);
          setActivities(activitiesData);
          setRoles(rolesData);
        } else {
          toast("Error", {
            description: "User not found",
            className: "bg-red-500 text-white",
          });
          navigate("/users");
        }
      } catch (error) {
        console.error("Failed to load user data:", error);
        toast("Error", {
          description: "Failed to load user data. Please try again.",
          className: "bg-red-500 text-white",
        });
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, navigate]);

  // Form fields for editing user details
  const userFormFields: FieldConfig[] = [
    {
      name: "full_name",
      label: "Full Name",
      type: "text",
      placeholder: "Enter full name",
      description: "The user's full name",
    },
    {
      name: "department",
      label: "Department",
      type: "text",
      placeholder: "Enter department",
      description: "The user's department within the organization",
    },
    {
      name: "position",
      label: "Position",
      type: "text",
      placeholder: "Enter position",
      description: "The user's job title or position",
    },
    {
      name: "bio",
      label: "Biography",
      type: "textarea",
      placeholder: "Enter user bio",
      description: "A brief description of the user and their role",
    },
    {
      name: "avatar_url",
      label: "Avatar URL",
      type: "text",
      placeholder: "https://example.com/avatar.jpg",
      description: "URL to the user's profile image",
    },
  ];

  const handleUpdateUser = async (data: z.infer<typeof userSchema>) => {
    if (!user) return;

    try {
      // In a real app, make API call to update user
      // Here we just update the local state
      const updatedUser = {
        ...user,
        ...data,
        updated_at: new Date(),
      };

      setUser(updatedUser);

      toast("Success", {
        description: "User information updated successfully",
      });
    } catch (error) {
      console.error("Failed to update user:", error);
      toast("Error", {
        description: "Failed to update user. Please try again.",
        className: "bg-red-500 text-white",
      });
    }
  };

  const handleChangePassword = async (userId: string, newPassword: string) => {
    try {
      // In a real app, make API call to change password

      toast("Success", {
        description: "Password changed successfully",
      });
    } catch (error) {
      console.error("Failed to change password:", error);
      toast("Error", {
        description: "Failed to change password. Please try again.",
        className: "bg-red-500 text-white",
      });
    }
  };

  const handleToggleStatus = async () => {
    if (!user) return;

    try {
      // In a real app, make API call to toggle status
      const updatedUser = {
        ...user,
        is_active: !user.is_active,
        updated_at: new Date(),
      };

      setUser(updatedUser);

      toast("Success", {
        description: `User ${user.is_active ? "deactivated" : "activated"} successfully`,
      });
    } catch (error) {
      console.error("Failed to toggle user status:", error);
      toast("Error", {
        description: "Failed to update user status. Please try again.",
        className: "bg-red-500 text-white",
      });
    }
  };

  const handleDeleteUser = async () => {
    if (!user) return;

    try {
      // In a real app, make API call to delete user

      toast("Success", {
        description: "User deleted successfully",
      });

      navigate("/users");
    } catch (error) {
      console.error("Failed to delete user:", error);
      toast("Error", {
        description: "Failed to delete user. Please try again.",
        className: "bg-red-500 text-white",
      });
    } finally {
      setShowDeleteDialog(false);
    }
  };

  const handleUpdateRoles = async (userId: string, roles: string[]) => {
    if (!user) return;

    try {
      // In a real app, make API call to update roles
      const updatedUser = {
        ...user,
        roles,
        updated_at: new Date(),
      };

      setUser(updatedUser);

      toast("Success", {
        description: "User roles updated successfully",
      });
    } catch (error) {
      console.error("Failed to update user roles:", error);
      toast("Error", {
        description: "Failed to update user roles. Please try again.",
        className: "bg-red-500 text-white",
      });
    }
  };

  // Activity columns
  const activityColumns: SimpleColumnDef<UserActivity, any>[] = [
    {
      header: "Activity",
      accessorKey: "activity_type",
      cell: (row) => (
        <div className="font-medium capitalize">
          {row?.activity_type.replace("_", " ")}
        </div>
      ),
    },
    {
      header: "Details",
      accessorKey: "details",
      cell: (row) => <div>{row?.details}</div>,
    },
    {
      header: "IP Address",
      accessorKey: "ip_address",
      cell: (row) => (
        <div className="font-mono text-xs">{row?.ip_address || "—"}</div>
      ),
    },
    {
      header: "Date/Time",
      accessorKey: "created_at",
      cell: (row) => (
        <div className="text-sm">
          {row?.created_at ? new Date(row.created_at).toLocaleString() : "—"}
        </div>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center">
          <Button size="sm" onClick={() => navigate("/users")}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Users
          </Button>
        </div>
        <Card>
          <CardContent className="py-10">
            <div className="flex justify-center">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <div className="flex items-center">
          <Button size="sm" onClick={() => navigate("/users")}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Users
          </Button>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <h2 className="text-xl font-semibold mb-2">User Not Found</h2>
            <p className="text-muted-foreground">
              The requested user could not be found.
            </p>
            <Button className="mt-4" onClick={() => navigate("/users")}>
              Return to User List
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center mb-4">
        <Button size="sm" onClick={() => navigate("/users")}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Users
        </Button>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start gap-4 md:items-center">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={user.avatar_url} />
            <AvatarFallback className="text-lg">
              {user.full_name
                ?.split(" ")
                .map((n) => n[0])
                .join("") || user.email[0].toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {user.full_name || user.email}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge
                className={
                  user.is_active
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }
              >
                {user.is_active ? "Active" : "Inactive"}
              </Badge>
              {user.roles.map((role) => (
                <Badge key={role} variant="outline">
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          <Button
            variant={user.is_active ? "info" : "default"}
            onClick={handleToggleStatus}
            className={
              user.is_active
                ? "border-amber-200 text-amber-700"
                : "bg-green-100 text-green-800 hover:bg-green-200 border-green-200"
            }
          >
            {user.is_active ? (
              <>
                <XCircle className="mr-2 h-4 w-4" /> Deactivate User
              </>
            ) : (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" /> Activate User
              </>
            )}
          </Button>
          <Button onClick={() => setShowPasswordDialog(true)}>
            <Key className="mr-2 h-4 w-4" /> Change Password
          </Button>
          <Button onClick={() => setShowRolesDialog(true)}>
            <Shield className="mr-2 h-4 w-4" /> Manage Roles
          </Button>
          <Button variant="warning" onClick={() => setShowDeleteDialog(true)}>
            <Trash2 className="mr-2 h-4 w-4" /> Delete User
          </Button>
        </div>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="activity">Activity Log</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>User Profile</CardTitle>
              <CardDescription>
                Manage user's profile information and settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6">
                <div className="space-y-2">
                  <h3 className="text-lg font-medium">Account Information</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm text-muted-foreground">
                        Email
                      </Label>
                      <div className="font-medium">{user.email}</div>
                    </div>
                    <div>
                      <Label className="text-sm text-muted-foreground">
                        Account Created
                      </Label>
                      <div>
                        {new Date(user.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm text-muted-foreground">
                        Last Updated
                      </Label>
                      <div>
                        {new Date(user.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm text-muted-foreground">
                        Last Login
                      </Label>
                      <div>
                        {user.last_sign_in_at
                          ? new Date(user.last_sign_in_at).toLocaleString()
                          : "Never"}
                      </div>
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-medium mb-4">Edit Profile</h3>
                  <AppForm
                    fields={userFormFields}
                    schema={userSchema}
                    onSubmit={handleUpdateUser}
                    defaultValues={{
                      full_name: user.full_name || "",
                      department: user.department || "",
                      position: user.position || "",
                      bio: user.bio || "",
                      avatar_url: user.avatar_url || "",
                    }}
                    submitButtonText="Save Changes"
                    resetButton={true}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle>Activity Log</CardTitle>
              <CardDescription>
                Recent user activity and system interactions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable<UserActivity, any>
                data={activities}
                columns={activityColumns}
                showPagination={true}
                showGlobalFilter={true}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Password Change Dialog */}
      <PasswordChangeDialog
        isOpen={showPasswordDialog}
        onClose={() => setShowPasswordDialog(false)}
        onChangePassword={handleChangePassword}
        userId={user.id}
      />

      {/* Delete User Dialog */}
      <DeleteUserDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteUser}
        user={user}
      />

      {/* User Roles Dialog */}
      <UserRolesDialog
        isOpen={showRolesDialog}
        onClose={() => setShowRolesDialog(false)}
        onUpdateRoles={handleUpdateRoles}
        user={user}
        allRoles={roles}
      />
    </div>
  );
}
