import { useState } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import AppShell from '@/components/layout/AppShell';
import StatusBadge from '@/components/ui/StatusBadge';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import { toast } from '@/components/ui/Toast';
import { useBills, useGenerateBill } from '@/hooks/useBilling';
import { useLeases } from '@/hooks/useProperties';
import type { Bill, BillStatus } from '@/types/billing';

const STATUS_TABS: { label: string; value: BillStatus | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Issued', value: 'issued' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Paid', value: 'paid' },
  { label: 'Partial', value: 'partially_paid' },
];

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

export default function BillingPage() {
  const [activeStatus, setActiveStatus] = useState<BillStatus | ''>('');
  const [showGenerate, setShowGenerate] = useState(false);
  const { data, isLoading, isError } = useBills(activeStatus ? { status: activeStatus } : {});

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
            onClick={() => setActiveStatus(value)}
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

      {isError && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-sm text-red-700 text-center">
          Failed to load bills. Please refresh.
        </div>
      )}

      {!isLoading && !isError && data?.results.length === 0 && (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 mb-4">No bills yet</p>
          <Button onClick={() => setShowGenerate(true)}>Generate first bill</Button>
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
        </div>
      )}

      <GenerateBillModal open={showGenerate} onClose={() => setShowGenerate(false)} />
    </AppShell>
  );
}
