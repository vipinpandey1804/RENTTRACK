import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';

const nav = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    to: '/properties',
    label: 'Properties',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    to: '/billing',
    label: 'Billing',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-7-7 7V5a2 2 0 012-2h10a2 2 0 012 2v16z" />
      </svg>
    ),
  },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const initials = user?.first_name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? '?';
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-100 shadow-sm px-6 py-0 flex items-stretch justify-between sticky top-0 z-20">
        {/* Logo */}
        <div className="flex items-center gap-8 py-3">
          <Link to="/dashboard" className="flex items-center gap-2 group">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm group-hover:bg-blue-700 transition-colors">
              <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
            <span className="font-bold text-gray-900 text-base tracking-tight">RentTrack</span>
          </Link>

          <nav className="flex items-stretch gap-0.5">
            {nav.map(({ to, label, icon }) => {
              const active = location.pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-1.5 px-3 py-0 text-sm font-medium transition-colors border-b-2 my-0 h-full ${
                    active
                      ? 'text-blue-700 border-blue-600'
                      : 'text-gray-500 border-transparent hover:text-gray-900 hover:border-gray-300'
                  }`}
                >
                  {icon}
                  {label}
                </Link>
              );
            })}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/dashboard" className="font-bold text-gray-900 text-lg">RentTrack</Link>
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

        {/* Right side */}
        <div className="flex items-center gap-3 py-3">
          {user?.active_organization && (
            <span className="hidden sm:block text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-full px-3 py-1">
              {user.active_organization.name}
            </span>
          )}
          <div className="relative group">
            <button className="flex items-center gap-2 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold text-xs shadow-sm">
                {initials}
              </div>
              <svg className="h-3.5 w-3.5 text-gray-400 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl shadow-lg border border-gray-100 py-1.5 hidden group-hover:block z-10">
              <div className="px-4 py-2.5 border-b border-gray-100">
                <p className="text-sm font-medium text-gray-900 truncate">{fullName}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 mt-0.5 flex items-center gap-2"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen((o) => !o)}
              className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900"
            >
              <span className="h-8 w-8 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-xs">
                {user?.first_name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? '?'}
              </span>
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                <Link
                  to="/profile"
                  onClick={() => setMenuOpen(false)}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Profile
                </Link>
                <hr className="my-1 border-gray-100" />
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 px-4 sm:px-6 py-8 max-w-7xl mx-auto w-full">{children}</main>
    </div>
  );
}
