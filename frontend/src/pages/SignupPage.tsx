import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

export default function SignupPage() {
  const navigate = useNavigate();
  const signup = useAuthStore((s) => s.signup);

  const [form, setForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    org_name: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);
    try {
      await signup(form);
      navigate('/dashboard');
    } catch (err: any) {
      const data = err?.response?.data ?? {};
      const mapped: Record<string, string> = {};
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? v[0] : String(v);
      }
      if (Object.keys(mapped).length === 0) {
        mapped.form = 'Something went wrong. Please try again.';
      }
      setErrors(mapped);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">RentTrack</h1>
          <p className="mt-1 text-gray-500">Create your landlord account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={onSubmit} className="space-y-5">
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="First name"
                value={form.first_name}
                onChange={set('first_name')}
                required
                autoComplete="given-name"
                error={errors.first_name}
              />
              <Input
                label="Last name"
                value={form.last_name}
                onChange={set('last_name')}
                autoComplete="family-name"
                error={errors.last_name}
              />
            </div>

            <Input
              label="Work email"
              type="email"
              value={form.email}
              onChange={set('email')}
              required
              autoComplete="email"
              error={errors.email}
            />

            <Input
              label="Password"
              type="password"
              value={form.password}
              onChange={set('password')}
              required
              autoComplete="new-password"
              hint="Minimum 10 characters"
              error={errors.password}
            />

            <Input
              label="Organization / Company name"
              value={form.org_name}
              onChange={set('org_name')}
              required
              placeholder="e.g. Sharma Properties"
              error={errors.org_name}
            />

            {errors.form && (
              <p className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {errors.form}
              </p>
            )}

            <Button type="submit" loading={loading} className="w-full" size="lg">
              Create account
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-blue-700 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
