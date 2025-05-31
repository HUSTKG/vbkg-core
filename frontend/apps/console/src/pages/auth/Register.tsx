import { useRegister } from "@vbkg/api-client";
import { registerSchema } from "@vbkg/schemas";
import { AppForm, Card } from "@vbkg/ui";
import { Link } from "react-router";

export default function Register() {
  const { mutate: register } = useRegister({
    onSuccess: () => {
      console.log("Registration successful");
    },
    onError: (error) => {
      console.error("Registration failed", error);
    },
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Create Account</h1>
          <p className="mt-2 text-gray-600">Register your organization</p>
        </div>

        <Card className="p-8">
          <AppForm
            fields={[
              {
                label: "Email",
                name: "email",
                type: "email",
                placeholder: "Enter your email",
                required: true,
              },
              {
                label: "Password",
                name: "password",
                type: "password",
                placeholder: "Enter your password",
                required: true,
              },
              {
                label: "Confirm Password",
                name: "confirmPassword",
                type: "password",
                placeholder: "Confirm your password",
                required: true,
              },
              {
                label: "Full Name",
                name: "fullname",
                type: "text",
                placeholder: "Enter your full name",
                required: true,
              },
            ]}
            onSubmit={(values) => {
              register({
                email: values.email,
                password: values.password,
				full_name: values.fullname,
                roles: ["admin"],
              });
            }}
            schema={registerSchema}
          />
        </Card>

        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-blue-600 hover:text-blue-500"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
