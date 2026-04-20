import type { BillStatus } from '@/types/billing';

const configs: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-gray-100 text-gray-600' },
  issued: { label: 'Issued', className: 'bg-blue-100 text-blue-700' },
  paid: { label: 'Paid', className: 'bg-green-100 text-green-700' },
  partially_paid: { label: 'Partial', className: 'bg-yellow-100 text-yellow-700' },
  overdue: { label: 'Overdue', className: 'bg-red-100 text-red-700' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-400' },
  // Unit statuses
  vacant: { label: 'Vacant', className: 'bg-green-100 text-green-700' },
  occupied: { label: 'Occupied', className: 'bg-blue-100 text-blue-700' },
  maintenance: { label: 'Maintenance', className: 'bg-yellow-100 text-yellow-700' },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const cfg = configs[status] ?? { label: status, className: 'bg-gray-100 text-gray-500' };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cfg.className} ${className}`}>
      {cfg.label}
    </span>
  );
}
