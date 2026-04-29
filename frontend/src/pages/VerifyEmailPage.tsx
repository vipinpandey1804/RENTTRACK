import { useState, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

export default function VerifyEmailPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const fetchMe = useAuthStore((s) => s.fetchMe);

  const [status, setStatus] = useState<"verifying" | "success" | "error">(
    "verifying",
  );
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMsg("No token provided.");
      return;
    }
    api
      .post("/auth/verify-email/", { token })
      .then(async () => {
        // Refresh the user profile so email_verified flips to true in store
        await fetchMe();
        setStatus("success");
        setTimeout(() => navigate("/dashboard"), 3000);
      })
      .catch((err) => {
        setErrorMsg(
          err?.response?.data?.detail ??
            "Verification failed. The link may have expired.",
        );
        setStatus("error");
      });
  }, [token]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-10 text-center">
        {/* Logo */}
        <div className="inline-flex items-center gap-2 mb-8 justify-center">
          <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center">
            <svg
              className="h-6 w-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
          </div>
          <span className="text-xl font-bold text-gray-900">RentTrack</span>
        </div>

        {status === "verifying" && (
          <>
            <div className="h-16 w-16 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-4">
              <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Verifying your email…
            </h2>
            <p className="text-gray-500 text-sm">
              This will only take a moment.
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Email verified!
            </h2>
            <p className="text-gray-500 text-sm mb-6">
              Your email has been confirmed. Redirecting you to the dashboard…
            </p>
            <Link
              to="/dashboard"
              className="inline-block rounded-xl bg-blue-600 text-white text-sm font-semibold px-6 py-2.5 hover:bg-blue-700 transition"
            >
              Go to dashboard
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <svg
                className="h-8 w-8 text-red-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Verification failed
            </h2>
            <p className="text-gray-500 text-sm mb-6">{errorMsg}</p>
            <div className="flex flex-col gap-2 items-center">
              <Link
                to="/dashboard"
                className="text-sm font-medium text-blue-600 hover:underline"
              >
                Go to dashboard
              </Link>
              <span className="text-gray-300 text-xs">·</span>
              <Link
                to="/login"
                className="text-sm text-gray-500 hover:underline"
              >
                Sign in
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
