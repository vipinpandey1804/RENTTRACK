import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { format } from "date-fns";
import AppShell from "@/components/layout/AppShell";
import StatusBadge from "@/components/ui/StatusBadge";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import { useBill, useRecordPayment, useCancelBill } from "@/hooks/useBilling";
import type { PaymentRecord } from "@/types/billing";

const PAYMENT_METHODS = [
  { value: "upi", label: "UPI" },
  { value: "bank_transfer", label: "Bank Transfer" },
  { value: "cash", label: "Cash" },
  { value: "cheque", label: "Cheque" },
  { value: "card", label: "Card" },
];

function PaymentRow({ payment }: { payment: PaymentRecord }) {
  return (
    <tr className="border-b border-gray-100">
      <td className="py-2 px-4 text-sm text-gray-600">
        {payment.paid_at
          ? format(new Date(payment.paid_at), "dd MMM yyyy, HH:mm")
          : "—"}
      </td>
      <td className="py-2 px-4 text-sm font-medium text-gray-900">
        ₹{Number(payment.amount).toLocaleString("en-IN")}
      </td>
      <td className="py-2 px-4 text-sm text-gray-600 capitalize">
        {payment.method}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {payment.reference_number || "—"}
      </td>
      <td className="py-2 px-4 text-sm text-gray-500">
        {payment.recorded_by_email || "—"}
      </td>
    </tr>
  );
}

function RecordPaymentModal({
  open,
  onClose,
  billId,
  balanceDue,
}: {
  open: boolean;
  onClose: () => void;
  billId: string;
  balanceDue: number;
}) {
  const recordPayment = useRecordPayment(billId);
  const [amount, setAmount] = useState(String(balanceDue));
  const [method, setMethod] = useState("upi");
  const [reference, setReference] = useState("");
  const [notes, setNotes] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await recordPayment.mutateAsync({
        amount: parseFloat(amount),
        method,
        reference_number: reference,
        notes,
      });
      toast.success("Payment recorded");
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to record payment");
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Record payment">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Amount (₹)"
          type="number"
          step="0.01"
          min="0.01"
          max={balanceDue}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
          hint={`Balance due: ₹${balanceDue.toLocaleString("en-IN")}`}
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payment method <span className="text-red-500">*</span>
          </label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PAYMENT_METHODS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        <Input
          label="Reference / transaction ID"
          value={reference}
          onChange={(e) => setReference(e.target.value)}
          placeholder="UTR / cheque no. / transaction ID"
        />
        <Input
          label="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={recordPayment.isPending}>
            Record payment
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function BillDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [showRecord, setShowRecord] = useState(false);
  const { data: bill, isLoading } = useBill(id!);
  const cancelBill = useCancelBill(id!);

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this bill?")) return;
    try {
      await cancelBill.mutateAsync();
      toast.success("Bill cancelled");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to cancel bill");
    }
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-4 bg-gray-100 rounded w-72" />
        </div>
      </AppShell>
    );
  }

  if (!bill) {
    return (
      <AppShell>
        <p className="text-gray-500">Bill not found.</p>
      </AppShell>
    );
  }

  const balanceDue = Number(bill.balance_due);
  const canPay = ["issued", "partially_paid", "overdue"].includes(bill.status);
  const canCancel = ["draft", "issued"].includes(bill.status);

  return (
    <AppShell>
      <div className="mb-1">
        <Link
          to="/billing"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Billing
        </Link>
      </div>

      <div className="flex items-start justify-between mt-2 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              {bill.bill_number}
            </h1>
            <StatusBadge status={bill.status} />
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {bill.lease_info.tenant_name || bill.lease_info.tenant_email} ·{" "}
            {bill.lease_info.unit_name}, {bill.lease_info.property_name}
          </p>
        </div>
        <div className="flex gap-2">
          {canPay && (
            <Button onClick={() => setShowRecord(true)}>Record payment</Button>
          )}
          {canCancel && (
            <Button
              variant="danger"
              loading={cancelBill.isPending}
              onClick={handleCancel}
            >
              Cancel bill
            </Button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {[
          {
            label: "Total amount",
            value: `₹${Number(bill.total_amount).toLocaleString("en-IN")}`,
          },
          {
            label: "Amount paid",
            value: `₹${Number(bill.amount_paid).toLocaleString("en-IN")}`,
          },
          {
            label: "Balance due",
            value: `₹${balanceDue.toLocaleString("en-IN")}`,
            highlight: balanceDue > 0,
          },
          {
            label: "Due date",
            value: format(new Date(bill.due_date), "dd MMM yyyy"),
          },
        ].map(({ label, value, highlight }) => (
          <div
            key={label}
            className="bg-white rounded-xl border border-gray-200 p-4"
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              {label}
            </p>
            <p
              className={`text-xl font-bold mt-1 ${
                highlight ? "text-red-700" : "text-gray-900"
              }`}
            >
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Bill details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line items */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Line items</h2>
          </div>
          <table className="w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="py-2 px-4 text-left font-medium">Description</th>
                <th className="py-2 px-4 text-right font-medium">Qty</th>
                <th className="py-2 px-4 text-right font-medium">Amount</th>
              </tr>
            </thead>
            <tbody>
              {bill.line_items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-gray-100 last:border-0"
                >
                  <td className="py-2 px-4 text-sm text-gray-700">
                    {item.description}
                  </td>
                  <td className="py-2 px-4 text-sm text-gray-500 text-right">
                    {item.quantity}
                  </td>
                  <td className="py-2 px-4 text-sm font-medium text-gray-900 text-right">
                    ₹{Number(item.amount).toLocaleString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-gray-200 bg-gray-50">
              <tr>
                <td
                  colSpan={2}
                  className="py-2 px-4 text-sm font-semibold text-gray-700 text-right"
                >
                  Total
                </td>
                <td className="py-2 px-4 text-sm font-bold text-gray-900 text-right">
                  ₹{Number(bill.total_amount).toLocaleString("en-IN")}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Payments */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-gray-900">Payments</h2>
            {canPay && (
              <button
                onClick={() => setShowRecord(true)}
                className="text-sm text-blue-700 hover:underline"
              >
                + Record
              </button>
            )}
          </div>
          {bill.payments.length === 0 ? (
            <p className="p-6 text-sm text-gray-400 text-center">
              No payments recorded
            </p>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="py-2 px-4 text-left font-medium">Date</th>
                  <th className="py-2 px-4 text-left font-medium">Amount</th>
                  <th className="py-2 px-4 text-left font-medium">Method</th>
                  <th className="py-2 px-4 text-left font-medium">Ref</th>
                  <th className="py-2 px-4 text-left font-medium">By</th>
                </tr>
              </thead>
              <tbody>
                {bill.payments.map((p) => (
                  <PaymentRow key={p.id} payment={p} />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <RecordPaymentModal
        open={showRecord}
        onClose={() => setShowRecord(false)}
        billId={id!}
        balanceDue={balanceDue}
      />
    </AppShell>
  );
}
