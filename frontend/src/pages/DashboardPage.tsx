import { Link } from 'react-router-dom';
import AppShell from '@/components/layout/AppShell';
import StatusBadge from '@/components/ui/StatusBadge';
import { useProperties } from '@/hooks/useProperties';
import { useBills } from '@/hooks/useBilling';
import { useAuthStore } from '@/store/auth';
import { format } from 'date-fns';

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
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.first_name ? `, ${user.first_name}` : ''}
        </h1>
        <p className="text-gray-500 mt-1">Here's an overview of your portfolio.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Properties', value: properties?.count ?? 0, href: '/properties' },
          { label: 'Total units', value: totalUnits, href: '/properties' },
          { label: 'Vacant units', value: vacantUnits, href: '/properties' },
          { label: 'Overdue bills', value: overdueBills?.count ?? 0, href: '/billing?status=overdue' },
        ].map(({ label, value, href }) => (
          <Link
            key={label}
            to={href}
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
          >
            <p className="text-sm text-gray-500">{label}</p>
            {isLoading ? (
              <div className="h-8 w-16 bg-gray-100 animate-pulse rounded mt-1" />
            ) : (
              <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
            )}
          </Link>
        ))}
      </div>

      {!isLoading && properties && properties.results.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Recent properties</h2>
            <Link to="/properties" className="text-sm text-blue-700 hover:underline">
              View all
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {properties.results.slice(0, 5).map((p) => (
              <Link
                key={p.id}
                to={`/properties/${p.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-gray-50"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{p.name}</p>
                  <p className="text-xs text-gray-500">{p.city}, {p.state}</p>
                </div>
                <span className="text-sm text-gray-500">
                  {p.occupied_count}/{p.unit_count} occupied
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent bills */}
      {recentBills && recentBills.results.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 mb-6">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Recent bills</h2>
            <Link to="/billing" className="text-sm text-blue-700 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-gray-100">
            {recentBills.results.slice(0, 5).map((b) => (
              <Link
                key={b.id}
                to={`/billing/${b.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-gray-50"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{b.bill_number}</p>
                  <p className="text-xs text-gray-500">
                    {b.lease_info.tenant_name || b.lease_info.tenant_email} · {b.lease_info.unit_name}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-700">
                    ₹{Number(b.total_amount).toLocaleString('en-IN')}
                  </span>
                  <StatusBadge status={b.status} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {!isLoading && properties?.count === 0 && (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 mb-4">No properties yet. Start by adding your first property.</p>
          <Link
            to="/properties"
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-700 text-white text-sm font-medium hover:bg-blue-800 transition-colors"
          >
            Go to Properties
          </Link>
        </div>
      )}
    </AppShell>
  );
}
