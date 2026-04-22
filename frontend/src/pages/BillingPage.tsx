import { useState, useCallback, useRef, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import AppShell from '@/components/layout/AppShell';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import { toast } from '@/components/ui/Toast';
import { useBills, useGenerateBill, type BillFilters } from '@/hooks/useBilling';
import { useLeases } from '@/hooks/useProperties';
import type { Bill, BillStatus } from '@/types/billing';

const STATUS_TABS: { label: string; value: BillStatus | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Issued', value: 'issued' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Paid', value: 'paid' },
  { label: 'Partial', value: 'partially_paid' },
  { label: 'Draft', value: 'draft' },
];

const PAGE_SIZE = 25;

function useDebounce<T>(value: T, delay = 400): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function BillRow({ bill }: { bill: Bill }) {
  const isDue = bill.status === 'overdue';
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4">
        <Link to={`/billing/${bill.id}`} className="text-sm font-medium text-blue-700 hover:underline">
          {bill.bill_number}
        </Link>
      </td>
      <td className="py-3 px-4 text-sm text-gray-700">
        {bill.lease_info.tenant_name || bill.lease_info.tenant_email}
      </td>
      <td className="py-3 px-4 text-sm text-gray-600">
        {bill.lease_info.unit_name} · {bill.lease_info.property_name}
      </td>
      <td className="py-3 px-4 text-sm text-gray-600">
        {format(new Date(bill.period_start), 'MMM yyyy')}
      </td>
      <td className={`py-3 px-4 text-sm font-medium ${isDue ? 'text-red-700' : 'text-gray-700'}`}>
        {format(new Date(bill.due_date), 'dd MMM yyyy')}
      </td>
      <td className="py-3 px-4 text-sm font-medium text-gray-900">
        ₹{Number(bill.total_amount).toLocaleString('en-IN')}
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">
        ₹{Number(bill.balance_due).toLocaleString('en-IN')}
      </td>
      <td className="py-3 px-4">
        <StatusBadge status={bill.status} />
      </td>
    </tr>
  );
}

function GenerateBillModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const generateBill = useGenerateBill();
  const { data: leases } = useLeases({ status: 'active' });
  const [leaseId, setLeaseId] = useState('');
  const [periodDate, setPeriodDate] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!leaseId) return;
    try {
      await generateBill.mutateAsync({ lease_id: leaseId, period_date: periodDate });
      toast.success('Bill generated successfully');
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to generate bill');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Generate rent bill">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Lease <span className="text-red-500">*</span>
          </label>
          <select
            value={leaseId}
            onChange={(e) => setLeaseId(e.target.value)}
            required
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a lease…</option>
            {leases?.results.map((l) => (
              <option key={l.id} value={l.id}>
                {l.tenant_email} — {l.unit_name} ({l.property_name})
              </option>
            ))}
          </select>
        </div>
        <Input
          label="Period (any day in the billing month)"
          type="date"
          value={periodDate}
          onChange={(e) => setPeriodDate(e.target.value)}
          required
        />
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={generateBill.isPending}>Generate</Button>
        </div>
      </form>
    </Modal>
  );
}

function Pagination({
  page,
  totalCount,
  pageSize,
  onChange,
}: {
  page: number;
  totalCount: number;
  pageSize: number;
  onChange: (p: number) => void;
}) {
  const totalPages = Math.ceil(totalCount / pageSize);
  if (totalPages <= 1) return null;

  const pages: (number | '…')[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push('…');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push('…');
    pages.push(totalPages);
  }

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
      <p className="text-sm text-gray-500">
        Showing {Math.min((page - 1) * pageSize + 1, totalCount)}–{Math.min(page * pageSize, totalCount)} of {totalCount}
      </p>
      <div className="flex gap-1">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page === 1}
          className="px-3 py-1 text-sm rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
        >
          Prev
        </button>
        {pages.map((p, i) =>
          p === '…' ? (
            <span key={`ellipsis-${i}`} className="px-2 py-1 text-sm text-gray-400">…</span>
          ) : (
            <button
              key={p}
              onClick={() => onChange(p as number)}
              className={`px-3 py-1 text-sm rounded border ${
                p === page
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
          )
        )}
        <button
          onClick={() => onChange(page + 1)}
          disabled={page === totalPages}
          className="px-3 py-1 text-sm rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default function BillingPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const activeStatus = (searchParams.get('status') ?? '') as BillStatus | '';
  const searchInput = searchParams.get('search') ?? '';
  const dueDateGte = searchParams.get('due_date__gte') ?? '';
  const dueDateLte = searchParams.get('due_date__lte') ?? '';
  const page = parseInt(searchParams.get('page') ?? '1', 10);

  const [localSearch, setLocalSearch] = useState(searchInput);
  const debouncedSearch = useDebounce(localSearch, 400);
  const prevDebounced = useRef(debouncedSearch);
  const isClearing = useRef(false);

  const [showGenerate, setShowGenerate] = useState(false);

  const updateParam = useCallback(
    (updates: Record<string, string>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        Object.entries(updates).forEach(([k, v]) => {
          if (v) next.set(k, v);
          else next.delete(k);
        });
        next.set('page', '1');
        return next;
      });
    },
    [setSearchParams],
  );

  // Sync debounced search to URL only when it actually changes and not during a clear
  useEffect(() => {
    if (isClearing.current || debouncedSearch === prevDebounced.current) return;
    prevDebounced.current = debouncedSearch;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (debouncedSearch) next.set('search', debouncedSearch);
      else next.delete('search');
      next.set('page', '1');
      return next;
    });
  }, [debouncedSearch, setSearchParams]);

  const filters: BillFilters = {
    ...(activeStatus && { status: activeStatus }),
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(dueDateGte && { due_date__gte: dueDateGte }),
    ...(dueDateLte && { due_date__lte: dueDateLte }),
    page,
    page_size: PAGE_SIZE,
  };

  const { data, isLoading, isError } = useBills(filters);

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing</h1>
          <p className="text-sm text-gray-500 mt-1">{data?.count ?? 0} bills</p>
        </div>
        <Button onClick={() => setShowGenerate(true)}>+ Generate bill</Button>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {STATUS_TABS.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => updateParam({ status: value })}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeStatus === value
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Search + date range filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex-1 min-w-48">
          <input
            type="search"
            placeholder="Search tenant, bill number…"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 whitespace-nowrap">Due from</label>
          <input
            type="date"
            value={dueDateGte}
            onChange={(e) => updateParam({ due_date__gte: e.target.value })}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 whitespace-nowrap">to</label>
          <input
            type="date"
            value={dueDateLte}
            onChange={(e) => updateParam({ due_date__lte: e.target.value })}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {(activeStatus || debouncedSearch || dueDateGte || dueDateLte) && (
          <Button
            variant="secondary"
            onClick={() => {
              isClearing.current = true;
              prevDebounced.current = '';
              setLocalSearch('');
              setSearchParams({});
              // Reset flag after debounce delay
              setTimeout(() => { isClearing.current = false; }, 500);
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {isError && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-sm text-red-700 text-center">
          Failed to load bills. Please refresh.
        </div>
      )}

      {!isLoading && !isError && data?.results.length === 0 && (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 mb-4">No bills found</p>
          {!activeStatus && !debouncedSearch && !dueDateGte && !dueDateLte && (
            <Button onClick={() => setShowGenerate(true)}>Generate first bill</Button>
          )}
        </div>
      )}

      {!isError && (data?.results.length ?? 0) > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="py-2 px-4 text-left font-medium">Bill #</th>
                <th className="py-2 px-4 text-left font-medium">Tenant</th>
                <th className="py-2 px-4 text-left font-medium">Unit</th>
                <th className="py-2 px-4 text-left font-medium">Period</th>
                <th className="py-2 px-4 text-left font-medium">Due</th>
                <th className="py-2 px-4 text-left font-medium">Amount</th>
                <th className="py-2 px-4 text-left font-medium">Balance</th>
                <th className="py-2 px-4 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(5)].map((_, i) => (
                    <tr key={i} className="border-b border-gray-100">
                      {[...Array(8)].map((_, j) => (
                        <td key={j} className="py-3 px-4">
                          <div className="h-4 bg-gray-100 animate-pulse rounded" />
                        </td>
                      ))}
                    </tr>
                  ))
                : data?.results.map((b) => <BillRow key={b.id} bill={b} />)}
            </tbody>
          </table>
          <Pagination
            page={page}
            totalCount={data?.count ?? 0}
            pageSize={PAGE_SIZE}
            onChange={(p) =>
              setSearchParams((prev) => {
                const next = new URLSearchParams(prev);
                next.set('page', String(p));
                return next;
              })
            }
          />
        </div>
      )}

      <GenerateBillModal open={showGenerate} onClose={() => setShowGenerate(false)} />
    </AppShell>
  );
}
