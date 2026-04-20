import { useAuthStore } from '@/store/auth';

export default function DashboardPage() {
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-brand-900">RentTrack</h1>
        <button
          onClick={logout}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          Sign out
        </button>
      </header>
      <main className="p-6 max-w-7xl mx-auto">
        <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
        <p className="text-gray-500">
          TODO: properties summary, outstanding dues, recent activity.
        </p>
      </main>
    </div>
  );
}
