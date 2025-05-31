import { useState } from "react";
import { Link } from "react-router";
import {
  Card,
  Button,
  Input,
  ErrorNotification,
  SuccessNotification,
} from "@vbkg/ui";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setIsLoading(true);

    try {
      // Implement password reset logic here
      console.log("Password reset request for:", email);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setSuccess(true);
    } catch (err) {
      setError("Failed to send reset email. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Reset Password</h1>
          <p className="mt-2 text-gray-600">
            Enter your email to receive reset instructions
          </p>
        </div>

        <Card className="p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <ErrorNotification
                title="Error"
                message={error}
                onDelete={() => setError("")}
                id="error-notification"
                time={new Date().toLocaleTimeString()}
              />
            )}

            {success && (
              <SuccessNotification
                title="Success"
                message="If an account exists with this email, you will receive password reset instructions shortly."
                onDelete={() => setSuccess(false)}
                id="success-notification"
                time={new Date().toLocaleTimeString()}
              />
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="Enter your email"
                className="w-full"
              />
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Sending..." : "Send Reset Instructions"}
            </Button>
          </form>

          {success && (
            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600">
                Didn't receive the email? Check your spam folder or{" "}
                <button
                  onClick={handleSubmit}
                  className="text-blue-600 hover:text-blue-500"
                >
                  try again
                </button>
              </p>
            </div>
          )}
        </Card>

        <div className="mt-4 text-center space-x-4">
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 hover:text-blue-500"
          >
            Back to Login
          </Link>
          <span className="text-gray-400">|</span>
          <Link
            to="/register"
            className="text-sm font-medium text-blue-600 hover:text-blue-500"
          >
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
}
