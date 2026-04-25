import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import {
  PREFERENCE_CHANNELS,
  PREFERENCE_EVENTS,
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  type NotificationPreferenceItem,
} from "@/hooks/useNotifications";

function ProfileForm() {
  const { user, setUser } = useAuthStore();
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [saving, setSaving] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { data } = await api.patch("/auth/me/", {
        first_name: firstName,
        last_name: lastName,
        phone,
      });
      setUser(data);
      toast.success("Profile updated");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          label="First name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
        />
        <Input
          label="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
        />
      </div>
      <Input
        label="Email"
        type="email"
        value={user?.email ?? ""}
        disabled
        hint="Email cannot be changed"
      />
      <Input
        label="Phone"
        type="tel"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        placeholder="+91 98765 43210"
      />
      <div className="flex items-center gap-3">
        <Button type="submit" loading={saving}>
          Save changes
        </Button>
        <span
          className={`text-xs px-2 py-1 rounded-full font-medium ${
            user?.email_verified
              ? "bg-green-100 text-green-700"
              : "bg-amber-100 text-amber-700"
          }`}
        >
          Email {user?.email_verified ? "verified ✓" : "not verified"}
        </span>
      </div>
    </form>
  );
}

function ChangePasswordForm() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (next !== confirm) {
      setError("New passwords do not match");
      return;
    }
    setSaving(true);
    try {
      await api.post("/auth/me/change-password/", {
        current_password: current,
        new_password: next,
      });
      toast.success("Password changed");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err: any) {
      const msg =
        err?.response?.data?.current_password?.[0] ??
        err?.response?.data?.new_password?.[0] ??
        err?.response?.data?.detail ??
        "Failed to change password";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Input
        label="Current password"
        type="password"
        value={current}
        onChange={(e) => setCurrent(e.target.value)}
        required
      />
      <Input
        label="New password"
        type="password"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        required
      />
      <Input
        label="Confirm new password"
        type="password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        required
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Button type="submit" loading={saving}>
        Change password
      </Button>
    </form>
  );
}

function NotificationPreferencesSection() {
  const { data: prefs, isLoading } = useNotificationPreferences();
  const update = useUpdateNotificationPreferences();

  const isEnabled = (eventKey: string, channelKey: string) => {
    if (!prefs) return true;
    return (
      prefs.find((p) => p.event_type === eventKey && p.channel === channelKey)
        ?.enabled ?? true
    );
  };

  const toggle = (eventKey: string, channelKey: string) => {
    if (!prefs) return;
    const current = isEnabled(eventKey, channelKey);
    const updated: NotificationPreferenceItem[] = PREFERENCE_EVENTS.flatMap(
      (evt) =>
        PREFERENCE_CHANNELS.map((ch) => ({
          event_type: evt.key,
          channel: ch.key,
          enabled:
            evt.key === eventKey && ch.key === channelKey
              ? !current
              : isEnabled(evt.key, ch.key),
        })),
    );
    update.mutate(updated, {
      onError: () => toast.error("Failed to update preferences"),
    });
  };

  if (isLoading) {
    return <p className="text-sm text-gray-400">Loading preferences…</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left font-medium text-gray-500 pb-3 pr-6">
              Event
            </th>
            {PREFERENCE_CHANNELS.map((ch) => (
              <th
                key={ch.key}
                className="text-center font-medium text-gray-500 pb-3 px-4 w-24"
              >
                {ch.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {PREFERENCE_EVENTS.map((evt) => (
            <tr key={evt.key}>
              <td className="py-3 pr-6 text-gray-700 font-medium">
                {evt.label}
              </td>
              {PREFERENCE_CHANNELS.map((ch) => {
                const on = isEnabled(evt.key, ch.key);
                return (
                  <td key={ch.key} className="py-3 px-4 text-center">
                    <button
                      onClick={() => toggle(evt.key, ch.key)}
                      disabled={update.isPending}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 ${
                        on ? "bg-blue-600" : "bg-gray-200"
                      }`}
                      role="switch"
                      aria-checked={on}
                      aria-label={`${evt.label} via ${ch.label}`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                          on ? "translate-x-4" : "translate-x-1"
                        }`}
                      />
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuthStore();
  const initials =
    [user?.first_name, user?.last_name]
      .filter(Boolean)
      .map((s) => s![0].toUpperCase())
      .join("") ||
    user?.email?.[0]?.toUpperCase() ||
    "?";

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-blue-100 text-blue-700 font-bold text-2xl flex items-center justify-center">
            {initials}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {user?.first_name} {user?.last_name}
            </h1>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>

        {/* Profile info */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Personal information
          </h2>
          <ProfileForm />
        </div>

        {/* Memberships */}
        {(user?.memberships?.length ?? 0) > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-700 mb-4">
              Organizations
            </h2>
            <ul className="divide-y divide-gray-100">
              {user!.memberships.map((m) => (
                <li
                  key={m.id}
                  className="py-3 flex items-center justify-between"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {m.organization.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {m.organization.primary_email}
                    </p>
                  </div>
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-blue-50 text-blue-700 capitalize">
                    {m.role.replace("_", " ")}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Notification preferences */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-1">
            Notification preferences
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Choose which notifications you receive and how.
          </p>
          <NotificationPreferencesSection />
        </div>

        {/* Change password */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Change password
          </h2>
          <ChangePasswordForm />
        </div>
      </div>
    </AppShell>
  );
}
