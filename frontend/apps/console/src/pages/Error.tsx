import { useState } from "react";
import {
  isRouteErrorResponse,
  Link,
  useNavigate,
  useRouteError,
} from "react-router";

// Mock error reporting service - replace with your actual error reporting
const reportError = (error: any, errorInfo: any) => {
  // In a real app, you would send this to a service like Sentry, LogRocket, etc.
  console.error("Reported error:", error);
  console.error("Error info:", errorInfo);
  return Promise.resolve({
    errorId: "ERR" + Math.random().toString(36).substr(2, 9),
  });
};

const AdvancedErrorElement = () => {
  const error = useRouteError();
  const navigate = useNavigate();
  const [errorId, setErrorId] = useState<string>("");
  const [reported, setReported] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [feedback, setFeedback] = useState("");

  // Determine if it's a route error response (404, 500, etc.)
  const isRouteError = isRouteErrorResponse(error);

  // Default values
  let status = "Error";
  let title = "Something went wrong";
  let message = "An unexpected error occurred. Please try again later.";
  let retryable = false;

  // Handle route errors differently based on status
  if (isRouteError) {
    status = error.status.toString();

    if (error.status === 404) {
      title = "Page not found";
      message = "The page you are looking for doesn't exist or has been moved.";
    } else if (error.status === 401) {
      title = "Unauthorized";
      message = "You need to be logged in to access this page.";
      retryable = true;
    } else if (error.status === 403) {
      title = "Forbidden";
      message = "You don't have permission to access this page.";
    } else if (error.statusText) {
      // Use the status text if available
      message = error.statusText;
      retryable = error.status < 500;
    } else if (error.status >= 500) {
      title = "Server error";
      message = "There was a problem with the server. Please try again later.";
      retryable = true;
    }
  } else if (error instanceof Error) {
    // Handle JavaScript errors
    title = error.name || "Error";
    message = error.message;
    retryable = !(
      error instanceof ReferenceError || error instanceof SyntaxError
    );
  }

  // Report error to monitoring service
  const handleReportError = async () => {
    try {
      const result = await reportError(error, {
        path: window.location.pathname,
        userFeedback: feedback,
      });

      setErrorId(result.errorId);
      setReported(true);
    } catch (reportingError) {
      console.error("Failed to report error:", reportingError);
    }
  };

  // Submit user feedback
  const handleSubmitFeedback = (e: any) => {
    e.preventDefault();
    setFeedbackSubmitted(true);
    handleReportError();
  };

  // Retry the current route
  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-8">
        <div className="text-center">
          <h1 className="text-9xl font-extrabold text-gray-900">{status}</h1>
          <h2 className="mt-4 text-3xl font-bold text-gray-900">{title}</h2>
          <p className="mt-2 text-base text-gray-500">{message}</p>

          {/* Show error details in development environment */}
          {process.env.NODE_ENV === "development" &&
            !isRouteError &&
            error instanceof Error && (
              <div className="mt-4 p-4 bg-red-50 rounded-md">
                <p className="text-sm text-red-800 font-mono overflow-auto whitespace-pre-wrap">
                  {error.stack}
                </p>
              </div>
            )}

          {/* User feedback form */}
          {!feedbackSubmitted && !reported && (
            <div className="mt-8 bg-white p-6 rounded-lg shadow-sm">
              <h3 className="text-lg font-medium text-gray-900">
                Help us improve
              </h3>
              <p className="text-sm text-gray-500">
                Tell us what happened so we can fix the issue
              </p>
              <form onSubmit={handleSubmitFeedback} className="mt-4">
                <textarea
                  className="w-full h-24 px-3 py-2 text-base border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="What were you trying to do when this error occurred?"
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                ></textarea>
                <button
                  type="submit"
                  className="mt-2 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
                >
                  Submit Feedback
                </button>
              </form>
            </div>
          )}

          {/* Error reporting confirmation */}
          {(reported || errorId) && (
            <div className="mt-6 p-4 bg-blue-50 text-blue-700 rounded-md">
              <p>
                This error has been reported{" "}
                {errorId ? `with ID: ${errorId}` : ""}. Our team has been
                notified.
              </p>
            </div>
          )}

          {/* Navigation buttons */}
          <div className="mt-8 flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
            >
              Go to Home
            </Link>

            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-md transition-colors"
            >
              Go Back
            </button>

            {retryable && (
              <button
                onClick={handleRetry}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-md transition-colors"
              >
                Retry
              </button>
            )}

            {!reported && !feedbackSubmitted && (
              <button
                onClick={handleReportError}
                className="px-4 py-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-800 font-medium rounded-md transition-colors"
              >
                Report Issue
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedErrorElement;
