import { Button } from "@vbkg/ui";
import { useNavigate } from "react-router";

export default function NotFound() {
	const navigate = useNavigate();

	return (
		<div className="min-h-screen flex items-center justify-center bg-gray-50">
			<div className="text-center">
				<h1 className="text-9xl font-bold text-gray-200">404</h1>
				<div className="mt-4">
					<h2 className="text-3xl font-bold text-gray-900">Page Not Found</h2>
					<p className="mt-2 text-gray-600">
						Sorry, we couldn't find the page you're looking for.
					</p>
				</div>
				<div className="mt-6 space-x-4">
					<Button onClick={() => navigate(-1)}>Go Back</Button>
					<Button variant="outline" onClick={() => navigate("/")}>
						Go to Dashboard
					</Button>
				</div>
			</div>
		</div>
	);
}
