import { useState } from "react";
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Plus,
  Edit,
  Trash2,
  Users,
  Eye,
  ChevronDown,
} from "lucide-react";
import {
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
  FieldConfig,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Checkbox,
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@vbkg/ui";
import { Role, Permission } from "@vbkg/types";
import { useRoles, usePermissions } from "@vbkg/api-client";
import * as z from "zod";

// Mock data for demonstration (replace with actual API calls)
const mockCreateRole = async (data: any) => {
  console.log("Creating role:", data);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

const mockUpdateRole = async (id: number, data: any) => {
  console.log("Updating role:", id, data);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

const mockDeleteRole = async (id: number) => {
  console.log("Deleting role:", id);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

const mockCreatePermission = async (data: any) => {
  console.log("Creating permission:", data);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

const mockUpdatePermission = async (id: number, data: any) => {
  console.log("Updating permission:", id, data);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

const mockDeletePermission = async (id: number) => {
  console.log("Deleting permission:", id);
  await new Promise((resolve) => setTimeout(resolve, 1000));
};

// Schemas
const roleSchema = z.object({
  name: z.string().min(1, "Role name is required"),
  description: z.string().min(1, "Description is required"),
  permissions: z.array(z.string()).optional(),
});

const permissionSchema = z.object({
  name: z.string().min(1, "Permission name is required"),
  description: z.string().min(1, "Description is required"),
});

// Role Dialog Component
const RoleDialog = ({
  isOpen,
  onClose,
  role,
  permissions,
}: {
  isOpen: boolean;
  onClose: () => void;
  role?: Role;
  permissions: Permission[];
}) => {
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>(
    role?.permissions || [],
  );
  const [loading, setLoading] = useState(false);
  const isEditMode = !!role;

  // Group permissions by category
  const groupedPermissions = permissions.reduce(
    (acc, permission) => {
      const category = permission.name.split(":")[0]; // Extract category from permission name
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(permission);
      return acc;
    },
    {} as Record<string, Permission[]>,
  );

  const fields: FieldConfig[] = [
    {
      name: "name",
      label: "Role Name",
      type: "text",
      required: true,
      placeholder: "e.g., Data Analyst",
      disabled: isEditMode,
    },
    {
      name: "description",
      label: "Description",
      type: "textarea",
      required: true,
      placeholder: "Describe what this role can do",
    },
  ];

  const handleSubmit = async (data: z.infer<typeof roleSchema>) => {
    setLoading(true);
    try {
      const roleData = {
        ...data,
        permissions: selectedPermissions,
      };

      if (isEditMode) {
        await mockUpdateRole(role.id, roleData);
        toast("Success", {
          description: "Role updated successfully",
        });
      } else {
        await mockCreateRole(roleData);
        toast("Success", {
          description: "Role created successfully",
        });
      }
      onClose();
    } catch (error) {
      toast("Error", {
        description: `Failed to ${isEditMode ? "update" : "create"} role`,
        className: "bg-red-500 text-white",
      });
    }
    setLoading(false);
  };

  const handlePermissionToggle = (permissionName: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionName)
        ? prev.filter((p) => p !== permissionName)
        : [...prev, permissionName],
    );
  };

  const handleCategoryToggle = (
    category: string,
    categoryPermissions: Permission[],
  ) => {
    const categoryPermissionNames = categoryPermissions.map((p) => p.name);
    const allSelected = categoryPermissionNames.every((name) =>
      selectedPermissions.includes(name),
    );

    if (allSelected) {
      setSelectedPermissions((prev) =>
        prev.filter((p) => !categoryPermissionNames.includes(p)),
      );
    } else {
      setSelectedPermissions((prev) => [
        ...new Set([...prev, ...categoryPermissionNames]),
      ]);
    }
  };

  return (
    <Dialog
      title={isEditMode ? "Edit Role" : "Create Role"}
      description={
        isEditMode
          ? "Update role details and permissions"
          : "Create a new role with specific permissions"
      }
      open={isOpen}
      onOpenChange={onClose}
    >
      <div className="space-y-6">
        <AppForm
          fields={fields}
          schema={roleSchema.omit({ permissions: true })}
          onSubmit={handleSubmit}
          defaultValues={
            role
              ? {
                  name: role.name,
                  description: role.description || "",
                }
              : undefined
          }
          submitButtonText={isEditMode ? "Update Role" : "Create Role"}
          loading={loading}
          hideSubmitButton={true}
        />

        {/* Permissions Selection */}
        <div>
          <h4 className="font-medium mb-3">Permissions</h4>
          <div className="border rounded-md p-4 max-h-96 overflow-y-auto">
            <div className="space-y-4">
              {Object.entries(groupedPermissions).map(
                ([category, categoryPermissions]) => {
                  const allSelected = categoryPermissions.every((p) =>
                    selectedPermissions.includes(p.name),
                  );
                  const someSelected = categoryPermissions.some((p) =>
                    selectedPermissions.includes(p.name),
                  );

                  return (
                    <Collapsible key={category} defaultOpen={true}>
                      <CollapsibleTrigger className="flex items-center justify-between w-full p-2 hover:bg-muted rounded">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={allSelected}
                            indeterminate={someSelected && !allSelected}
                            onCheckedChange={() =>
                              handleCategoryToggle(
                                category,
                                categoryPermissions,
                              )
                            }
                          />
                          <span className="font-medium capitalize">
                            {category}
                          </span>
                          <Badge variant="outline">
                            {categoryPermissions.length}
                          </Badge>
                        </div>
                        <ChevronDown className="h-4 w-4" />
                      </CollapsibleTrigger>
                      <CollapsibleContent className="pl-6 pt-2">
                        <div className="space-y-2">
                          {categoryPermissions.map((permission) => (
                            <div
                              key={permission.name}
                              className="flex items-start space-x-2"
                            >
                              <Checkbox
                                id={permission.name}
                                checked={selectedPermissions.includes(
                                  permission.name,
                                )}
                                onCheckedChange={() =>
                                  handlePermissionToggle(permission.name)
                                }
                              />
                              <div className="flex-1">
                                <label
                                  htmlFor={permission.name}
                                  className="text-sm font-medium cursor-pointer"
                                >
                                  {permission.name}
                                </label>
                                {permission.description && (
                                  <p className="text-xs text-muted-foreground">
                                    {permission.description}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  );
                },
              )}
            </div>
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Selected {selectedPermissions.length} of {permissions.length}{" "}
            permissions
          </p>
        </div>

        <div className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() =>
              handleSubmit({
                name: role?.name || "",
                description: role?.description || "",
              })
            }
            loading={loading}
          >
            {isEditMode ? "Update Role" : "Create Role"}
          </Button>
        </div>
      </div>
    </Dialog>
  );
};

// Permission Dialog Component
const PermissionDialog = ({
  isOpen,
  onClose,
  permission,
}: {
  isOpen: boolean;
  onClose: () => void;
  permission?: Permission;
}) => {
  const [loading, setLoading] = useState(false);
  const isEditMode = !!permission;

  const fields: FieldConfig[] = [
    {
      name: "name",
      label: "Permission Name",
      type: "text",
      required: true,
      placeholder: "resource:action (e.g., users:read)",
      disabled: isEditMode,
      description: "Format: resource:action",
    },
    {
      name: "description",
      label: "Description",
      type: "textarea",
      required: true,
      placeholder: "Describe what this permission allows",
    },
  ];

  const handleSubmit = async (data: z.infer<typeof permissionSchema>) => {
    setLoading(true);
    try {
      if (isEditMode) {
        await mockUpdatePermission(permission.id, data);
        toast("Success", {
          description: "Permission updated successfully",
        });
      } else {
        await mockCreatePermission(data);
        toast("Success", {
          description: "Permission created successfully",
        });
      }
      onClose();
    } catch (error) {
      toast("Error", {
        description: `Failed to ${isEditMode ? "update" : "create"} permission`,
        className: "bg-red-500 text-white",
      });
    }
    setLoading(false);
  };

  return (
    <Dialog
      title={isEditMode ? "Edit Permission" : "Create Permission"}
      description={
        isEditMode
          ? "Update permission details"
          : "Create a new system permission"
      }
      open={isOpen}
      onOpenChange={onClose}
    >
      <AppForm
        fields={fields}
        schema={permissionSchema}
        onSubmit={handleSubmit}
        defaultValues={
          permission
            ? {
                name: permission.name,
                description: permission.description || "",
              }
            : undefined
        }
        submitButtonText={
          isEditMode ? "Update Permission" : "Create Permission"
        }
        loading={loading}
        buttons={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={loading}>
              {isEditMode ? "Update Permission" : "Create Permission"}
            </Button>
          </div>
        }
      />
    </Dialog>
  );
};

export default function RolesPermissionsManagementPage() {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [selectedPermission, setSelectedPermission] =
    useState<Permission | null>(null);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [showDeleteRoleDialog, setShowDeleteRoleDialog] = useState(false);
  const [showDeletePermissionDialog, setShowDeletePermissionDialog] =
    useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Queries
  const { data: rolesData, isLoading: rolesLoading } = useRoles();
  const { data: permissionsData, isLoading: permissionsLoading } =
    usePermissions();

  const roles = rolesData?.data || [];
  const permissions = permissionsData?.data || [];

  const handleDeleteRole = async () => {
    if (!selectedRole) return;

    setDeleteLoading(true);
    try {
      await mockDeleteRole(selectedRole.id);
      toast("Success", {
        description: "Role deleted successfully",
      });
      setShowDeleteRoleDialog(false);
      setSelectedRole(null);
    } catch (error) {
      toast("Error", {
        description: "Failed to delete role",
        className: "bg-red-500 text-white",
      });
    }
    setDeleteLoading(false);
  };

  const handleDeletePermission = async () => {
    if (!selectedPermission) return;

    setDeleteLoading(true);
    try {
      await mockDeletePermission(selectedPermission.id);
      toast("Success", {
        description: "Permission deleted successfully",
      });
      setShowDeletePermissionDialog(false);
      setSelectedPermission(null);
    } catch (error) {
      toast("Error", {
        description: "Failed to delete permission",
        className: "bg-red-500 text-white",
      });
    }
    setDeleteLoading(false);
  };

  // Role columns
  const roleColumns: SimpleColumnDef<Role, any>[] = [
    {
      header: "Role Name",
      accessorKey: "name",
      cell: (row) => (
        <div>
          <div className="font-medium capitalize">{row?.name}</div>
          {row?.description && (
            <div className="text-sm text-muted-foreground">
              {row.description}
            </div>
          )}
        </div>
      ),
    },
    {
      header: "Permissions",
      accessorKey: "permissions",
      cell: (row) => (
        <Badge variant="outline">
          {row?.permissions?.length || 0} permissions
        </Badge>
      ),
    },
    {
      header: "Created",
      accessorKey: "created_at",
      cell: (row) =>
        row?.created_at ? new Date(row.created_at).toLocaleDateString() : "—",
    },
  ];

  // Permission columns
  const permissionColumns: SimpleColumnDef<Permission, any>[] = [
    {
      header: "Permission",
      accessorKey: "name",
      cell: (row) => (
        <div>
          <div className="font-mono text-sm font-medium">{row?.name}</div>
          {row?.description && (
            <div className="text-sm text-muted-foreground">
              {row.description}
            </div>
          )}
        </div>
      ),
    },
    {
      header: "Category",
      accessorKey: "name",
      cell: (row) => {
        const category = row?.name?.split(":")[0] || "unknown";
        return (
          <Badge variant="outline" className="capitalize">
            {category}
          </Badge>
        );
      },
    },
    {
      header: "Used in Roles",
      accessorKey: "name",
      cell: (row) => {
        const usageCount = roles.filter((role) =>
          role.permissions?.includes(row?.name || ""),
        ).length;
        return (
          <div className="flex items-center">
            <Users className="h-4 w-4 mr-1" />
            {usageCount} role{usageCount !== 1 ? "s" : ""}
          </div>
        );
      },
    },
    {
      header: "Created",
      accessorKey: "created_at",
      cell: (row) =>
        row?.created_at ? new Date(row.created_at).toLocaleDateString() : "—",
    },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center">
          <Shield className="mr-2 h-7 w-7" />
          Roles & Permissions
        </h1>
      </div>

      <Tabs defaultValue="roles" className="space-y-4">
        <TabsList className="grid grid-cols-2">
          <TabsTrigger value="roles" className="flex items-center">
            <ShieldCheck className="mr-2 h-4 w-4" />
            Roles
          </TabsTrigger>
          <TabsTrigger value="permissions" className="flex items-center">
            <ShieldAlert className="mr-2 h-4 w-4" />
            Permissions
          </TabsTrigger>
        </TabsList>

        {/* Roles Tab */}
        <TabsContent value="roles" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Roles Management</h2>
              <p className="text-muted-foreground">
                Create and manage user roles with specific permissions.
              </p>
            </div>
            <Button onClick={() => setShowRoleDialog(true)}>
              <Plus className="mr-2 h-4 w-4" /> Create Role
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Roles</CardTitle>
              <CardDescription>{roles.length} roles configured</CardDescription>
            </CardHeader>
            <CardContent>
              {rolesLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
                </div>
              ) : (
                <DataTable<Role, any>
                  data={roles}
                  columns={roleColumns}
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
                        onClick: (role) => {
                          setSelectedRole(role);
                          setShowRoleDialog(true);
                        },
                        variant: "ghost",
                      },
                      {
                        label: "Edit",
                        icon: <Edit className="h-4 w-4" />,
                        onClick: (role) => {
                          setSelectedRole(role);
                          setShowRoleDialog(true);
                        },
                        variant: "outline",
                      },
                      {
                        label: "Delete",
                        icon: <Trash2 className="h-4 w-4" />,
                        onClick: (role) => {
                          setSelectedRole(role);
                          setShowDeleteRoleDialog(true);
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
        </TabsContent>

        {/* Permissions Tab */}
        <TabsContent value="permissions" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">Permissions Management</h2>
              <p className="text-muted-foreground">
                Define granular permissions for system resources.
              </p>
            </div>
            <Button onClick={() => setShowPermissionDialog(true)}>
              <Plus className="mr-2 h-4 w-4" /> Create Permission
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Permissions</CardTitle>
              <CardDescription>
                {permissions.length} permissions available
              </CardDescription>
            </CardHeader>
            <CardContent>
              {permissionsLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"></div>
                </div>
              ) : (
                <DataTable<Permission, any>
                  data={permissions}
                  columns={permissionColumns}
                  showGlobalFilter={true}
                  showColumnFilters={true}
                  showPagination={true}
                  actionsOptions={{
                    show: true,
                    position: "end",
                    actions: [
                      {
                        label: "Edit",
                        icon: <Edit className="h-4 w-4" />,
                        onClick: (permission) => {
                          setSelectedPermission(permission);
                          setShowPermissionDialog(true);
                        },
                        variant: "outline",
                      },
                      {
                        label: "Delete",
                        icon: <Trash2 className="h-4 w-4" />,
                        onClick: (permission) => {
                          setSelectedPermission(permission);
                          setShowDeletePermissionDialog(true);
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
        </TabsContent>
      </Tabs>

      {/* Role Dialog */}
      <RoleDialog
        isOpen={showRoleDialog}
        onClose={() => {
          setShowRoleDialog(false);
          setSelectedRole(null);
        }}
        role={selectedRole || undefined}
        permissions={permissions}
      />

      {/* Permission Dialog */}
      <PermissionDialog
        isOpen={showPermissionDialog}
        onClose={() => {
          setShowPermissionDialog(false);
          setSelectedPermission(null);
        }}
        permission={selectedPermission || undefined}
      />

      {/* Delete Role Confirmation */}
      <ConfirmDialog
        title="Delete Role"
        message={`Are you sure you want to delete the role "${selectedRole?.name}"? Users with this role will lose their associated permissions.`}
        onConfirm={handleDeleteRole}
        onCancel={() => setShowDeleteRoleDialog(false)}
        isOpen={showDeleteRoleDialog}
        loading={deleteLoading}
      />

      {/* Delete Permission Confirmation */}
      <ConfirmDialog
        title="Delete Permission"
        message={`Are you sure you want to delete the permission "${selectedPermission?.name}"? This will remove it from all roles that currently have it.`}
        onConfirm={handleDeletePermission}
        onCancel={() => setShowDeletePermissionDialog(false)}
        isOpen={showDeletePermissionDialog}
        loading={deleteLoading}
      />
    </div>
  );
}
