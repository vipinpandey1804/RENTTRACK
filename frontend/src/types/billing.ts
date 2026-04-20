export interface BillLineItem {
  id: string;
  description: string;
  quantity: string;
  unit_price: string;
  amount: string;
  tax_rate: string;
  metadata: Record<string, unknown>;
}

export interface PaymentRecord {
  id: string;
  amount: string;
  method: string;
  status: 'initiated' | 'pending' | 'success' | 'failed' | 'refunded';
  reference_number: string;
  paid_at: string | null;
  notes: string;
  recorded_by_email: string | null;
}

export interface LeaseInfo {
  id: string;
  tenant_email: string;
  tenant_name: string;
  unit_name: string;
  property_name: string;
}

export type BillStatus = 'draft' | 'issued' | 'paid' | 'partially_paid' | 'overdue' | 'cancelled';
export type BillType = 'rent' | 'electricity' | 'water' | 'maintenance' | 'combined';

export interface Bill {
  id: string;
  bill_number: string;
  bill_type: BillType;
  lease: string;
  lease_info: LeaseInfo;
  period_start: string;
  period_end: string;
  issue_date: string;
  due_date: string;
  subtotal: string;
  tax_amount: string;
  total_amount: string;
  amount_paid: string;
  balance_due: string;
  status: BillStatus;
  pdf_url?: string;
  notes?: string;
  line_items: BillLineItem[];
  payments: PaymentRecord[];
  created_at: string;
  updated_at: string;
}

export interface RecordPaymentPayload {
  amount: number;
  method: string;
  reference_number?: string;
  notes?: string;
}
