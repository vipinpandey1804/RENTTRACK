import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import AppShell from '@/components/layout/AppShell';
import StatusBadge from '@/components/ui/StatusBadge';
import { useAuthStore } from '@/store/auth';
import { useLeases } from '@/hooks/useProperties';
import { useBills } from '@/hooks/useBilling';
import type { Lease } from '@/types';
import type { Bill } from '@/types/billing';

function LeaseCard({ lease }: { lease: Lease }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">{lease.unit_name}</h2>
          <p className="text-sm text-gray-500">{lease.property_name}</p>
        </div>
        <StatusBadge status={lease.status} />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt className="text-gray-500">Monthly Rent</dt>
          <dd className="font-medium text-gray-900">₹{Number(lease.monthly_rent).toLocaleString('en-IN')}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Security Deposit</dt>
          <dd className="font-medium text-gray-900">₹{Number(lease.security_deposit_held).toLocaleString('en-IN')}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Start Date</dt>
          <dd className="font-medium text-gray-900">{format(new Date(lease.start_date), 'dd MMM yyyy')}</dd>
        </div>
        {lease.end_date && (
          <div>
            <dt className="text-gray-500">End Date</dt>
            <dd className="font-medium text-gray-900">{format(new Date(lease.end_date), 'dd MMM yyyy')}</dd>
          </div>
        )}
        <div>
          <dt className="text-gray-500">Billing Cycle</dt>
          <dd className="font-medium text-gray-900 capitalize">{lease.billing_cycle}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Bill Generated On</dt>
          <dd className="font-medium text-gray-900">Day {lease.billing_day_of_month}</dd>
        </div>
      </dl>
    </div>
  );
}

function OutstandingBillRow({ bill }: { bill: Bill }) {
  const isOverdue = bill.status === 'overdue';
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4">
        <Link to={`/billing/${bill.id}`} className="text-sm font-medium text-blue-700 hover:underline">
          {bill.bill_number}
        </Link>
      </td>
      <td className="py-3 px-4 text-sm text-gray-600">
        {format(new Date(bill.period_start), 'MMM yyyy')}
      </td>
      <td className={`py-3 px-4 text-sm font-medium ${isOverdue ? 'text-red-700' : 'text-gray-700'}`}>
        {format(new Date(bill.due_date), 'dd MMM yyyy')}
      </td>
      <td className="py-3 px-4 text-sm font-semibold text-gray-900">
        ₹{Number(bill.balance_due).toLocaleString('en-IN')}
      </td>
      <td className="py-3 px-4">
        <StatusBadge status={bill.status} />
      </td>
      <td className="py-3 px-4">
        <Link
          to={`/billing/${bill.id}`}
          className="inline-block rounded-lg bg-blue-600 text-white text-xs font-medium px-3 py-1.5 hover:bg-blue-700"
        >
          View bill
        </Link>
      </td>
    </tr>
  );
}

export default function TenantDashboardPage() {
  const user = useAuthStore((s) => s.user);

  // Fetch leases for the current tenant
  const { data: leasesData, isLoading: leasesLoading } = useLeases({
    tenant: user?.id,
    status: 'active',
  });

  // Fetch outstanding bills (issued + overdue)
  const { data: issuedBills } = useBills({ status: 'issued', page_size: 10 });
  const { data: overdueBills } = useBills({ status: 'overdue', page_size: 10 });

  const outstandingBills: Bill[] = [
    ...(overdueBills?.results ?? []),
    ...(issuedBills?.results ?? []),
  ];

  const activeLease = leasesData?.results?.[0];

  return (
    <AppShell>
      {/* Welcome header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.first_name || user?.email}
        </h1>
        <p className="text-sm text-gray-500 mt-1">Your tenant portal</p>
      </div>

      {/* Email verification banner */}
      {user && !user.email_verified && (
        <div className="mb-6 rounded-xl bg-amber-50 border border-amber-200 p-4 flex items-start gap-3">
          <span className="text-amber-500 mt-0.5">⚠</span>
          <div>
            <p className="text-sm font-medium text-amber-800">Email not verified</p>
            <p className="text-sm text-amber-700 mt-0.5">
              Please check your inbox and verify your email address to receive bill notifications.
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: lease info */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-base font-semibold text-gray-700">Your Tenancy</h2>
          {leasesLoading ? (
            <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-4 bg-gray-100 rounded w-3/4" />
              ))}
            </div>
          ) : activeLease ? (
            <LeaseCard lease={activeLease} />
          ) : (
            <div className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-8 text-center text-sm text-gray-500">
              No active lease found.
              <br />
              Contact your landlord for details.
            </div>
          )}

          {/* Account settings quick link */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-sm font-medium text-gray-700 mb-3">Account</p>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Email</dt>
                <dd className="text-gray-900">{user?.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Phone</dt>
                <dd className="text-gray-900">{user?.phone || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Email verified</dt>
                <dd className={user?.email_verified ? 'text-green-600' : 'text-amber-600'}>
                  {user?.email_verified ? 'Yes' : 'No'}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Right column: outstanding bills */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-gray-700">
              Outstanding Bills
              {outstandingBills.length > 0 && (
                <span className="ml-2 inline-flex items-center justify-center rounded-full bg-red-100 text-red-700 text-xs font-bold px-2 py-0.5">
                  {outstandingBills.length}
                </span>
              )}
            </h2>
            <Link to="/billing" className="text-sm text-blue-600 hover:underline">
              View all bills →
            </Link>
          </div>

          {outstandingBills.length === 0 ? (
            <div className="bg-white rounded-xl border-2 border-dashed border-gray-200 p-12 text-center">
              <p className="text-3xl mb-3">✓</p>
              <p className="text-gray-500 font-medium">All caught up!</p>
              <p className="text-sm text-gray-400 mt-1">No outstanding bills at the moment.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
                  <tr>
                    <th className="py-2 px-4 text-left font-medium">Bill #</th>
                    <th className="py-2 px-4 text-left font-medium">Period</th>
                    <th className="py-2 px-4 text-left font-medium">Due</th>
                    <th className="py-2 px-4 text-left font-medium">Balance</th>
                    <th className="py-2 px-4 text-left font-medium">Status</th>
                    <th className="py-2 px-4 text-left font-medium" />
                  </tr>
                </thead>
                <tbody>
                  {outstandingBills.map((b) => (
                    <OutstandingBillRow key={b.id} bill={b} />
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Meter reading placeholder */}
          <div className="mt-4 bg-white rounded-xl border border-dashed border-gray-200 p-5 text-center">
            <p className="text-sm font-medium text-gray-600">Meter Reading Submission</p>
            <p className="text-xs text-gray-400 mt-1">
              Electricity meter reading submission coming in Phase 2.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
