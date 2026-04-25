import { useState, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

export default function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [invite, setInvite] = useState<{
    email: string;
    role: string;
    organization: string;
  } | null>(null);
  const [status, setStatus] = useState<"loading" | "valid" | "invalid">(
    "loading",
  );
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    password: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) {
      setStatus("invalid");
      return;
    }
    api
      .get(`/auth/invite/${token}/`)
      .then(({ data }) => {
        setInvite(data);
        setStatus("valid");
      })
      .catch(() => setStatus("invalid"));
  }, [token]);

  const set =
    (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitting(true);
    try {
      const payload: Record<string, string> = { token: token!, ...form };
      const { data } = await api.post("/auth/accept-invite/", payload);
      // Store tokens and user in auth store
      useAuthStore.setState({
        accessToken: data.access,
        refreshToken: data.refresh,
        user: data.user,
      });
      navigate("/dashboard");
    } catch (err: any) {
      const data = err?.response?.data ?? {};
      const mapped: Record<string, string> = {};
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? (v as string[])[0] : String(v);
      }
      if (!Object.keys(mapped).length)
        mapped.form = "Something went wrong. Please try again.";
      setErrors(mapped);
    } finally {
      setSubmitting(false);
    }
  };

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Validating your invitation…</p>
        </div>
      </div>
    );
  }

  if (status === "invalid") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 text-center">
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
            Invitation expired or invalid
          </h2>
          <p className="text-gray-500 text-sm mb-6">
            This invitation link is no longer valid. Please contact your
            landlord to send a new one.
          </p>
          <Link
            to="/login"
            className="text-sm font-medium text-blue-600 hover:underline"
          >
            Back to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-3">
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
            <span className="text-2xl font-bold text-gray-900">RentTrack</span>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-white/60 p-8">
          {/* Invite banner */}
          <div className="rounded-xl bg-blue-50 border border-blue-100 p-4 mb-6">
            <p className="text-sm font-semibold text-blue-800 mb-1">
              You've been invited to {invite?.organization}
            </p>
            <p className="text-sm text-blue-600">
              Joining as{" "}
              <span className="font-medium capitalize">
                {invite?.role?.replace("_", " ")}
              </span>{" "}
              · {invite?.email}
            </p>
          </div>

          <h1 className="text-xl font-bold text-gray-900 mb-1">
            Create your account
          </h1>
          <p className="text-sm text-gray-500 mb-6">
            Complete your details to accept the invitation
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="First name"
                value={form.first_name}
                onChange={set("first_name")}
                required
                autoComplete="given-name"
                error={errors.first_name}
              />
              <Input
                label="Last name"
                value={form.last_name}
                onChange={set("last_name")}
                autoComplete="family-name"
                error={errors.last_name}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                value={invite?.email ?? ""}
                disabled
                className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500 cursor-not-allowed"
              />
            </div>
            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={set("password")}
              required
              autoComplete="new-password"
              hint="Minimum 10 characters"
              error={errors.password}
            />

            {errors.form && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {errors.form}
              </div>
            )}
            {errors.detail && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {errors.detail}
              </div>
            )}

            <Button
              type="submit"
              loading={submitting}
              className="w-full"
              size="lg"
            >
              Accept invitation &amp; sign in
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-medium text-blue-600 hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
