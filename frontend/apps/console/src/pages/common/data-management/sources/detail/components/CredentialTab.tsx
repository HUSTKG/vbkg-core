import {
	X,
	Eye,
	EyeOff,
	Plus,
} from "lucide-react";
import {
	Button,
	Input,
	Label,
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components";
import { Shield } from "lucide-react";
import { useState } from "react";
import { formatDate } from "@vbkg/utils";

interface CredentialTabProps {
	credentials: Record<string, string>;
	isEditing: boolean;
	updateCredential: (key: string, value: string) => void;
	updateFormField: (field: any, value: any) => void;
	isActive?: boolean;
	handleToggleActive?: () => void;
}

export const CredentialTab = ({
	credentials,
	isEditing,
	updateCredential,
	updateFormField,
}: CredentialTabProps) => {
	const [showPassword, setShowPassword] = useState(false);
	const creds = credentials;

	if (!creds || Object.keys(creds).length === 0) {
		return (
			<div className="py-8 text-center">
				<div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
					<Shield className="h-6 w-6 text-muted-foreground" />
				</div>
				<h3 className="mb-1 text-lg font-semibold">
					Chưa có thông tin xác thực
				</h3>
				<p className="text-sm text-muted-foreground mb-4">
					Thêm thông tin xác thực để kết nối đến nguồn dữ liệu này
				</p>
				{isEditing && (
					<Button
						variant="outline"
						onClick={() => updateCredential("auth_type", "api_key")}
					>
						<Plus className="mr-2 h-4 w-4" />
						Thêm thông tin xác thực
					</Button>
				)}
			</div>
		);
	}

	return (
		<div className="space-y-4">
			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div className="space-y-2">
					<Label>Loại xác thực</Label>
					<Select
						value={creds.auth_type}
						onValueChange={(value) => updateCredential("auth_type", value)}
						disabled={!isEditing}
					>
						<SelectTrigger>
							<SelectValue placeholder="Chọn loại xác thực" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="api_key">API Key</SelectItem>
							<SelectItem value="oauth">OAuth 2.0</SelectItem>
							<SelectItem value="basic">Basic Auth</SelectItem>
							<SelectItem value="token">Token</SelectItem>
							<SelectItem value="certificate">Certificate</SelectItem>
						</SelectContent>
					</Select>
				</div>
			</div>

			<div className="border rounded-md overflow-hidden">
				<Table>
					<TableHeader>
						<TableRow>
							<TableHead>Key</TableHead>
							<TableHead>Value</TableHead>
							{isEditing && <TableHead className="w-16"></TableHead>}
						</TableRow>
					</TableHeader>
					<TableBody>
						{Object.entries(creds).map(([key, value]) => (
							<TableRow key={key}>
								<TableCell>
									{isEditing ? (
										<Input
											value={key}
											onChange={(e) => {
												const newCreds = { ...creds };
												delete newCreds[key];
												newCreds[e.target.value] = value;
												updateFormField("credentials", newCreds);
											}}
										/>
									) : (
										key
									)}
								</TableCell>
								<TableCell>
									{key.toLowerCase().includes("password") ||
										key.toLowerCase().includes("secret") ||
										key.toLowerCase().includes("key") ? (
										<div className="flex items-center">
											<Input
												type={showPassword ? "text" : "password"}
												value={value as string}
												onChange={(e) =>
													updateCredential(key, e.target.value)
												}
												readOnly={!isEditing}
												className="font-mono"
											/>
											<Button
												size="icon"
												variant="outline"
												onClick={() => setShowPassword(!showPassword)}
												className="ml-2"
											>
												{showPassword ? (
													<EyeOff className="h-4 w-4" />
												) : (
													<Eye className="h-4 w-4" />
												)}
											</Button>
										</div>
									) : (
										<Input
											value={value as string}
											onChange={(e) => updateCredential(key, e.target.value)}
											readOnly={!isEditing}
										/>
									)}
								</TableCell>
								{isEditing && (
									<TableCell>
										<Button
											size="sm"
											variant="ghost"
											onClick={() => {
												const newCreds = { ...creds };
												delete newCreds[key];
												updateFormField("credentials", newCreds);
											}}
										>
											<X className="h-4 w-4" />
										</Button>
									</TableCell>
								)}
							</TableRow>
						))}
					</TableBody>
				</Table>
			</div>

			{isEditing && (
				<Button
					size="sm"
					variant="outline"
					onClick={() => updateCredential("", "")}
				>
					<Plus className="h-4 w-4 mr-1" />
					Thêm credential
				</Button>
			)}

			<div className="flex justify-end">
				<p className="text-sm text-muted-foreground">
					Cập nhật lần cuối: {formatDate(credentials?.updated_at)}
				</p>
			</div>
		</div>
	);
};

