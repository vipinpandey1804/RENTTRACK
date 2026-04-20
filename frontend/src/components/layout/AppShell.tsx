import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';

const nav = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/properties', label: 'Properties' },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <span className="font-bold text-gray-900 text-lg">RentTrack</span>
          <nav className="flex items-center gap-1">
            {nav.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  location.pathname.startsWith(to)
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {user?.active_organization && (
            <span className="text-sm text-gray-500">{user.active_organization.name}</span>
          )}
          <div className="relative group">
            <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
              <span className="h-8 w-8 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs">
                {user?.first_name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? '?'}
              </span>
            </button>
            <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 hidden group-hover:block z-10">
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 px-6 py-8 max-w-6xl mx-auto w-full">{children}</main>
    </div>
  );
}
