import { useState } from 'react';
import AppShell from '@/components/layout/AppShell';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { toast } from '@/components/ui/Toast';
import { useAuthStore } from '@/store/auth';
import { api } from '@/lib/api';

function ProfileForm() {
  const { user, setUser } = useAuthStore();
  const [firstName, setFirstName] = useState(user?.first_name ?? '');
  const [lastName, setLastName] = useState(user?.last_name ?? '');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [saving, setSaving] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { data } = await api.patch('/auth/me/', { first_name: firstName, last_name: lastName, phone });
      setUser(data);
      toast.success('Profile updated');
    } catch {
      toast.error('Failed to update profile');
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
        value={user?.email ?? ''}
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
        <Button type="submit" loading={saving}>Save changes</Button>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${user?.email_verified ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
          Email {user?.email_verified ? 'verified ✓' : 'not verified'}
        </span>
      </div>
    </form>
  );
}

function ChangePasswordForm() {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (next !== confirm) {
      setError('New passwords do not match');
      return;
    }
    setSaving(true);
    try {
      await api.post('/auth/me/change-password/', { current_password: current, new_password: next });
      toast.success('Password changed');
      setCurrent(''); setNext(''); setConfirm('');
    } catch (err: any) {
      const msg = err?.response?.data?.current_password?.[0]
        ?? err?.response?.data?.new_password?.[0]
        ?? err?.response?.data?.detail
        ?? 'Failed to change password';
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
      <Button type="submit" loading={saving}>Change password</Button>
    </form>
  );
}

export default function ProfilePage() {
  const { user } = useAuthStore();
  const initials = [user?.first_name, user?.last_name]
    .filter(Boolean)
    .map((s) => s![0].toUpperCase())
    .join('') || user?.email?.[0]?.toUpperCase() || '?';

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
          <h2 className="text-base font-semibold text-gray-700 mb-4">Personal information</h2>
          <ProfileForm />
        </div>

        {/* Memberships */}
        {(user?.memberships?.length ?? 0) > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-base font-semibold text-gray-700 mb-4">Organizations</h2>
            <ul className="divide-y divide-gray-100">
              {user!.memberships.map((m) => (
                <li key={m.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{m.organization.name}</p>
                    <p className="text-xs text-gray-500">{m.organization.primary_email}</p>
                  </div>
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-blue-50 text-blue-700 capitalize">
                    {m.role.replace('_', ' ')}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Change password */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Change password</h2>
          <ChangePasswordForm />
        </div>
      </div>
    </AppShell>
  );
}
