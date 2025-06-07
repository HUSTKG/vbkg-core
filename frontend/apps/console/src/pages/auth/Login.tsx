import { AppForm, Card, toast } from "@/components";
import { loginSchema } from "@vbkg/schemas";
import { Link, useNavigate } from "react-router";
import { useLoginJson } from "@vbkg/api-client";
import { getSession, setSession, isValidSession } from "@vbkg/utils";
import { useEffect } from "react";

export default function Login() {
	const navigate = useNavigate();
	const { mutate: login } = useLoginJson({
		onSuccess: (data) => {
			setSession({
				session: {
					accessToken: data.data.session.access_token,
					refreshToken: data.data.session.refresh_token,
				},
				user: {
					id: data.data.user.id,
					name: data.data.user.full_name,
					email: data.data.user.email,
					roles: data.data.user.roles,
				},
			});
			if (data.data.user.roles.includes("admin")) {
				navigate("/admin");
			} else if (data.data.user.roles.includes("expert")) {
				navigate("/expert");
			} else {
				navigate("/user");
			}
		},
		onError: (error) => {
			toast("Login failed " + error.message);
		},
	});

	useEffect(() => {
		const sessions = getSession();
		if (!sessions || !isValidSession(sessions)) return;
		if (sessions.user.roles.includes("admin")) {
			navigate("/admin");
		} else if (sessions.user.roles.includes("expert")) {
			navigate("/expert");
		} else {
			navigate("/user");
		}
	}, []);

	return (
		<div className="min-h-screen flex items-center justify-center bg-gray-50">
			<div className="w-full max-w-md">
				{/* Logo */}
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-gray-900">Console</h1>
					<p className="mt-2 text-gray-600">Đăng nhập tài khoản của bạn</p>
				</div>

				<Card className="p-8">
					<AppForm
						onSubmit={(values) => {
							login(values);
						}}
						schema={loginSchema}
						submitButtonText="Đăng nhập"
						fields={[
							{
								label: "Email",
								name: "email",
								placeholder: "Nhập địa ch email của bạn",
								type: "email",
							},
							{
								label: "Password",
								name: "password",
								placeholder: "Nhập mật khẩu của bạn",
								description: "Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường và số.",
								type: "password",
							},
						]}
					/>
				</Card>

				<p className="mt-4 text-center text-sm text-gray-600">
					Bạn chưa có tài khoản?{" "}
					<Link
						to="/register"
						className="font-medium text-blue-600 hover:text-blue-500"
					>
						Đăng ký
					</Link>
				</p>
			</div>
		</div>
	);
}
