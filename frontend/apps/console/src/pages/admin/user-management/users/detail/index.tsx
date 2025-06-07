import { useState, useEffect } from "react";
import * as z from "zod";
import {
	ArrowLeft,
	Shield,
	CheckCircle2,
	XCircle,
	Trash2,
} from "lucide-react";
import {
	AppForm,
	Badge,
	Button,
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
	DataTable,
	Dialog,
	FieldConfig,
	Label,
	Separator,
	SimpleColumnDef,
	Tabs,
	TabsContent,
	TabsList,
	TabsTrigger,
	toast,
} from "@/components";
import { useNavigate, useParams } from "react-router";
import {
	useRoles,
	useUpdateUser,
	useUser,
	useUserActivity,
} from "@vbkg/api-client";
import { Role, User, UserActivity } from "@vbkg/types";

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

	const { data: userResponse, isFetching: loading } = useUser(
		{
			user_id: id!,
		},
		{
			enabled: !!id,
		},
	);
	const user = userResponse?.data;
	const { data: roles } = useRoles();
	const { data: activitiesResponse } = useUserActivity(
		{
			user_id: id!,
		},
		{
			enabled: !!id,
		},
	);
	const activities = activitiesResponse?.data || [];
	// const [showDeleteDialog, setShowDeleteDialog] = useState(false);
	const [showRolesDialog, setShowRolesDialog] = useState(false);

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

	const { mutate: updateUser } = useUpdateUser({
		onSuccess: () => {
			toast.success("User updated successfully");
		},
		onError: (error) => {
			toast.error("Failed to update user: " + error.message);
		},
	});

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

			updateUser({
				user_id: user.id,
				data: updatedUser,
			});

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

	const handleToggleStatus = async () => {
		if (!user) return;

		try {
			// In a real app, make API call to toggle status
			const updatedUser = {
				user_id: user.id,
				data: {
					...user,
					is_active: !user.is_active,
					updated_at: new Date(),
				},
			};

			updateUser(updatedUser);

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

	// const handleDeleteUser = async () => {
	// 	if (!user) return;
	//
	// 	try {
	// 		// In a real app, make API call to delete user
	//
	// 		toast("Success", {
	// 			description: "User deleted successfully",
	// 		});
	//
	// 		navigate("/users");
	// 	} catch (error) {
	// 		console.error("Failed to delete user:", error);
	// 		toast("Error", {
	// 			description: "Failed to delete user. Please try again.",
	// 			className: "bg-red-500 text-white",
	// 		});
	// 	} finally {
	// 		setShowDeleteDialog(false);
	// 	}
	// };

	const handleUpdateRoles = async (userId: string, roles: string[]) => {
		if (!user) return;

		try {
			const updatedUser = {
				...user,
				roles,
				updated_at: new Date(),
			};

			// handle update
			updateUser({
				user_id: userId,
				data: updatedUser,
			});

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
			accessorKey: "action",
			cell: (row) => (
				<div className="font-medium capitalize">
					{row?.action.replace("_", " ")}
				</div>
			),
		},
		{
			header: "Details",
			accessorKey: "details",
			cell: (row) => <div className="line-clamp-1 w-40">{JSON.stringify(row?.details)}</div>,
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
					<Button
						size="sm"
						onClick={() => navigate("/admin/users")}
						variant="outline"
					>
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
					<Button
						size="sm"
						onClick={() => navigate("/admin/users")}
						variant={"outline"}
					>
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
				<Button size="sm" onClick={() => navigate("/admin/users")} variant="outline">
					<ArrowLeft className="mr-2 h-4 w-4" /> Back to Users
				</Button>
			</div>

			<div className="flex flex-col md:flex-row justify-between items-start gap-4 md:items-center">
				<div className="flex items-center gap-4">
					<div>
						<h1 className="text-3xl font-bold tracking-tight">
							{user?.full_name || user?.email}
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
						variant={user.is_active ? "secondary" : "default"}
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
					<Button variant="outline" onClick={() => setShowRolesDialog(true)}>
						<Shield className="mr-2 h-4 w-4" /> Manage Roles
					</Button>
					{/* <Button */}
					{/* 	variant="destructive" */}
					{/* 	onClick={() => setShowDeleteDialog(true)} */}
					{/* > */}
					{/* 	<Trash2 className="mr-2 h-4 w-4" /> Delete User */}
					{/* </Button> */}
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

			{/* Delete User Dialog */}
			{/* <DeleteUserDialog */}
			{/* 	isOpen={showDeleteDialog} */}
			{/* 	onClose={() => setShowDeleteDialog(false)} */}
			{/* 	onConfirm={handleDeleteUser} */}
			{/* 	user={user} */}
			{/* /> */}

			{/* User Roles Dialog */}
			<UserRolesDialog
				isOpen={showRolesDialog}
				onClose={() => setShowRolesDialog(false)}
				onUpdateRoles={handleUpdateRoles}
				user={user}
				allRoles={roles?.data || []}
			/>
		</div>
	);
}
