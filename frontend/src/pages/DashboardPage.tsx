import { Link } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import StatusBadge from '@/components/ui/StatusBadge';
import { useProperties } from '@/hooks/useProperties';
import { useBills } from '@/hooks/useBilling';
import { useAuthStore } from '@/store/auth';

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const { data: properties, isLoading } = useProperties();
  const { data: overdueBills } = useBills({ status: 'overdue' });
  const { data: recentBills } = useBills({ ordering: '-created_at' });

  const totalUnits = properties?.results.reduce((sum, p) => sum + p.unit_count, 0) ?? 0;
  const occupiedUnits = properties?.results.reduce((sum, p) => sum + p.occupied_count, 0) ?? 0;
  const vacantUnits = totalUnits - occupiedUnits;

  return (
    <AppShell>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.first_name ? `, ${user.first_name}` : ''}
        </h1>
        <p className="text-gray-400 mt-1 text-sm">Here's an overview of your portfolio.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          {
            label: 'Properties', value: properties?.count ?? 0, href: '/properties',
            icon: (
              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            ),
            bg: 'bg-blue-50', color: 'text-blue-700',
          },
          {
            label: 'Total units', value: totalUnits, href: '/properties',
            icon: (
              <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            ),
            bg: 'bg-indigo-50', color: 'text-indigo-700',
          },
          {
            label: 'Vacant units', value: vacantUnits, href: '/properties',
            icon: (
              <svg className="h-5 w-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ),
            bg: 'bg-emerald-50', color: 'text-emerald-700',
          },
          {
            label: 'Overdue bills', value: overdueBills?.count ?? 0, href: '/billing?status=overdue',
            icon: (
              <svg className="h-5 w-5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ),
            bg: 'bg-rose-50', color: 'text-rose-700',
          },
        ].map(({ label, value, href, icon, bg, color }) => (
          <Link
            key={label}
            to={href}
            className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 hover:shadow-md hover:border-blue-100 transition-all group"
          >
            <div className={`inline-flex h-9 w-9 rounded-xl ${bg} items-center justify-center mb-3`}>
              {icon}
            </div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">{label}</p>
            {isLoading ? (
              <div className="h-8 w-16 bg-gray-100 animate-pulse rounded mt-1" />
            ) : (
              <p className={`text-3xl font-bold ${color}`}>{value}</p>
            )}
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent properties */}
        {!isLoading && properties && properties.results.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
              <h2 className="font-bold text-gray-900">Properties</h2>
              <Link to="/properties" className="text-xs font-medium text-blue-600 hover:underline">
                View all →
              </Link>
            </div>
            <div className="divide-y divide-gray-50">
              {properties.results.slice(0, 5).map((p) => {
                const occ = p.unit_count > 0 ? Math.round((p.occupied_count / p.unit_count) * 100) : 0;
                return (
                  <Link
                    key={p.id}
                    to={`/properties/${p.id}`}
                    className="flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50/80 transition-colors"
                  >
                    {p.cover_image ? (
                      <img src={p.cover_image} alt={p.name}
                        className="h-10 w-10 rounded-lg object-cover shrink-0 border border-gray-100" />
                    ) : (
                      <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center shrink-0">
                        <svg className="h-5 w-5 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-gray-900 truncate">{p.name}</p>
                      <p className="text-xs text-gray-400">{p.city}, {p.state}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs font-medium text-gray-700">{p.occupied_count}/{p.unit_count}</p>
                      <div className="w-16 h-1 rounded-full bg-gray-100 mt-1">
                        <div className="h-1 rounded-full bg-blue-500" style={{ width: `${occ}%` }} />
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent bills */}
        {recentBills && recentBills.results.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-50">
              <h2 className="font-bold text-gray-900">Recent bills</h2>
              <Link to="/billing" className="text-xs font-medium text-blue-600 hover:underline">View all →</Link>
            </div>
            <div className="divide-y divide-gray-50">
              {recentBills.results.slice(0, 5).map((b) => (
                <Link
                  key={b.id}
                  to={`/billing/${b.id}`}
                  className="flex items-center justify-between px-5 py-3.5 hover:bg-gray-50/80 transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900">{b.bill_number}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {b.lease_info.tenant_name || b.lease_info.tenant_email} · {b.lease_info.unit_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-medium text-gray-700">
                      ₹{Number(b.total_amount).toLocaleString('en-IN')}
                    </span>
                    <StatusBadge status={b.status} />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {!isLoading && properties?.count === 0 && (
        <div className="rounded-2xl border-2 border-dashed border-gray-200 p-16 text-center mt-4">
          <div className="h-16 w-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
            <svg className="h-8 w-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">No properties yet</h3>
          <p className="text-sm text-gray-500 mb-6">Start by adding your first property to manage rentals</p>
          <Link
            to="/properties"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
          >
            Add first property
          </Link>
        </div>
      )}
    </AppShell>
  );
}
