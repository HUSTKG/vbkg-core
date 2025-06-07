import { useState } from "react";
import {
  Users,
  UserPlus,
  Edit,
  Trash2,
  Shield,
  ShieldCheck,
  ShieldX,
  Eye,
} from "lucide-react";
import {
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
  AppForm,
  SimpleColumnDef,
  toast,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  FieldConfig,
} from "@/components";
import { useNavigate } from "react-router";
import { User, UserUpdate } from "@vbkg/types";
import {
  useUsers,
  useUpdateUser,
  useDeleteUser,
  useAssignRole,
  useRemoveRole,
  useRoles,
} from "@vbkg/api-client";
import * as z from "zod";

// Form schemas
const updateUserSchema = z.object({
  full_name: z.string().optional(),
  department: z.string().optional(),
  position: z.string().optional(),
  bio: z.string().optional(),
  avatar_url: z.string().url().optional().or(z.literal("")),
});

// Edit User Dialog
const EditUserDialog = ({
  isOpen,
  onClose,
  user,
}: {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
}) => {
  const updateUserMutation = useUpdateUser();

  if (!user) return null;

  const fields: FieldConfig[] = [
    {
      name: "full_name",
      label: "Full Name",
      type: "text",
      placeholder: "Enter full name",
    },
    {
      name: "department",
      label: "Department",
      type: "text",
      placeholder: "Enter department",
    },
    {
      name: "position",
      label: "Position",
      type: "text",
      placeholder: "Enter position",
    },
    {
      name: "bio",
      label: "Bio",
      type: "textarea",
      placeholder: "Enter bio",
    },
    {
      name: "avatar_url",
      label: "Avatar URL",
      type: "text",
      placeholder: "Enter avatar URL",
    },
  ];

  const handleSubmit = async (data: z.infer<typeof updateUserSchema>) => {
    try {
      await updateUserMutation.mutateAsync({
        user_id: user.id,
        data: data as UserUpdate,
      });
      toast("Success", {
        description: "User updated successfully",
      });
      onClose();
    } catch (error) {
      toast("Error", {
        description: "Failed to update user",
        className: "bg-red-500 text-white",
      });
    }
  };

  return (
    <Dialog
      title="Edit User"
      description="Update user information"
      open={isOpen}
      onOpenChange={onClose}
    >
      <AppForm
        fields={fields}
        schema={updateUserSchema}
        onSubmit={handleSubmit}
        defaultValues={{
          full_name: user.full_name || "",
          department: user.department || "",
          position: user.position || "",
          bio: user.bio || "",
          avatar_url: user.avatar_url || "",
        }}
        submitButtonText="Update User"
        loading={updateUserMutation.isPending}
        buttons={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={updateUserMutation.isPending}>
              Update User
            </Button>
          </div>
        }
      />
    </Dialog>
  );
};

// Role Management Dialog
const RoleManagementDialog = ({
  isOpen,
  onClose,
  user,
}: {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
}) => {
  const [selectedRole, setSelectedRole] = useState("");
  const { data: rolesData } = useRoles();
  const assignRoleMutation = useAssignRole();
  const removeRoleMutation = useRemoveRole();

  if (!user) return null;

  const availableRoles =
    rolesData?.data?.filter((role) => !user.roles.includes(role.name)) || [];

  const handleAssignRole = async () => {
    if (!selectedRole) return;

    try {
      await assignRoleMutation.mutateAsync({
        user_id: user.id,
        role_name: selectedRole,
      });
      toast("Success", {
        description: `Role "${selectedRole}" assigned successfully`,
      });
      setSelectedRole("");
    } catch (error) {
      toast("Error", {
        description: "Failed to assign role",
        className: "bg-red-500 text-white",
      });
    }
  };

  const handleRemoveRole = async (roleName: string) => {
    try {
      await removeRoleMutation.mutateAsync({
        user_id: user.id,
        role_name: roleName,
      });
      toast("Success", {
        description: `Role "${roleName}" removed successfully`,
      });
    } catch (error) {
      toast("Error", {
        description: "Failed to remove role",
        className: "bg-red-500 text-white",
      });
    }
  };

  return (
    <Dialog
      title="Manage User Roles"
      description={`Manage roles for ${user.full_name || user.email}`}
      open={isOpen}
      onOpenChange={onClose}
    >
      <div className="space-y-6">
        {/* Current Roles */}
        <div>
          <h4 className="font-medium mb-3">Current Roles</h4>
          {user.roles.length === 0 ? (
            <p className="text-muted-foreground text-sm">No roles assigned</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {user.roles.map((role) => (
                <Badge key={role} className="flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" />
                  {role}
                  <button
                    onClick={() => handleRemoveRole(role)}
                    className="ml-1 hover:text-red-600"
                    disabled={removeRoleMutation.isPending}
                  >
                    <ShieldX className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Assign New Role */}
        <div>
          <h4 className="font-medium mb-3">Assign New Role</h4>
          <div className="flex gap-2">
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                {availableRoles.map((role) => (
                  <SelectItem key={role.name} value={role.name}>
                    {role.name} - {role.description}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={handleAssignRole}
              disabled={!selectedRole || assignRoleMutation.isPending}
              loading={assignRoleMutation.isPending}
            >
              Assign
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
};

export default function UserManagementPage() {
  const navigate = useNavigate();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [filters, setFilters] = useState({
    role_filter: "",
    department_filter: "",
  });

  // Queries
  const { data: usersData, isLoading } = useUsers(filters);
  const deleteUserMutation = useDeleteUser();

  const users = usersData?.data || [];

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    try {
      await deleteUserMutation.mutateAsync({ user_id: selectedUser.id });
      toast("Success", {
        description: "User deleted successfully",
      });
      setShowDeleteDialog(false);
      setSelectedUser(null);
    } catch (error) {
      toast("Error", {
        description: "Failed to delete user",
        className: "bg-red-500 text-white",
      });
    }
  };

  // Table columns
  const columns: SimpleColumnDef<User, any>[] = [
    {
      header: "User",
      accessorKey: "email",
      cell: (row) => (
        <div className="flex items-center space-x-3">
          <Avatar>
            <AvatarImage src={row?.avatar_url} />
            <AvatarFallback>
              {row?.full_name
                ?.split(" ")
                .map((n) => n[0])
                .join("") || row?.email[0].toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-medium">{row?.full_name || "No name"}</div>
            <div className="text-sm text-muted-foreground">{row?.email}</div>
          </div>
        </div>
      ),
    },
    {
      header: "Department",
      accessorKey: "department",
      cell: (row) => row?.department || "—",
    },
    {
      header: "Position",
      accessorKey: "position",
      cell: (row) => row?.position || "—",
    },
    {
      header: "Status",
      accessorKey: "is_active",
      cell: (row) => (
        <Badge
          className={
            row?.is_active
              ? "bg-green-100 text-green-800"
              : "bg-gray-100 text-gray-800"
          }
        >
          {row?.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
    },
    {
      header: "Roles",
      accessorKey: "roles",
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {row?.roles?.map((role) => (
            <Badge key={role} variant="outline">
              {role}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      header: "Last Sign In",
      accessorKey: "last_sign_in_at",
      cell: (row) =>
        row?.last_sign_in_at
          ? new Date(row.last_sign_in_at).toLocaleDateString()
          : "Never",
    },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center">
            <Users className="mr-2 h-7 w-7" />
            User Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage user accounts, roles, and permissions.
          </p>
        </div>
      </div>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
          <CardDescription>{users.length} users found</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <DataTable<User, any>
              data={users}
              columns={columns}
              showGlobalFilter={true}
              showColumnFilters={true}
              showPagination={true}
              actionsOptions={{
                show: true,
                position: "end",
                actions: [
                  {
                    label: "View",
                    icon: <Eye className="h-4 w-4" />,
                    onClick: (user) => navigate(`/admin/users/${user.id}`),
                    variant: "ghost",
                  },
                  {
                    label: "Edit",
                    icon: <Edit className="h-4 w-4" />,
                    onClick: (user) => {
                      setSelectedUser(user);
                      setShowEditDialog(true);
                    },
                    variant: "outline",
                  },
                  {
                    label: "Manage Roles",
                    icon: <Shield className="h-4 w-4" />,
                    onClick: (user) => {
                      setSelectedUser(user);
                      setShowRoleDialog(true);
                    },
                    variant: "outline",
                  },
                  {
                    label: "Delete",
                    icon: <Trash2 className="h-4 w-4" />,
                    onClick: (user) => {
                      setSelectedUser(user);
                      setShowDeleteDialog(true);
                    },
                    variant: "outline",
                    className: "text-red-600 hover:text-red-700",
                  },
                ],
                showInDropdown: true,
                dropdownLabel: "Actions",
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <EditUserDialog
        isOpen={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        user={selectedUser}
      />

      {/* Role Management Dialog */}
      <RoleManagementDialog
        isOpen={showRoleDialog}
        onClose={() => setShowRoleDialog(false)}
        user={selectedUser}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        title="Delete User"
        message={`Are you sure you want to delete the user "${selectedUser?.full_name || selectedUser?.email}"? This action cannot be undone.`}
        onConfirm={handleDeleteUser}
        onCancel={() => setShowDeleteDialog(false)}
        isOpen={showDeleteDialog}
        loading={deleteUserMutation.isPending}
      />
    </div>
  );
}
