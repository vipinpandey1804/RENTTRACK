import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Bill, RecordPaymentPayload } from '@/types/billing';
import type { PaginatedResponse } from '@/types';

interface BillFilters {
  status?: string;
  lease?: string;
  bill_type?: string;
  ordering?: string;
}

export function useBills(filters: BillFilters = {}) {
  return useQuery({
    queryKey: ['bills', filters],
    queryFn: async () => {
      const params = new URLSearchParams(
        Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) as Record<string, string>,
      ).toString();
      const { data } = await api.get<PaginatedResponse<Bill>>(
        `/billing/bills/${params ? `?${params}` : ''}`,
      );
      return data;
    },
  });
}

export function useBill(id: string) {
  return useQuery({
    queryKey: ['bills', id],
    queryFn: async () => {
      const { data } = await api.get<Bill>(`/billing/bills/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function useGenerateBill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { lease_id: string; period_date: string }) =>
      api.post<Bill>('/billing/bills/generate/', payload).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bills'] }),
  });
}

export function useRecordPayment(billId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecordPaymentPayload) =>
      api.post<Bill>(`/billing/bills/${billId}/record_payment/`, payload).then((r) => r.data),
    onSuccess: (updatedBill) => {
      qc.setQueryData(['bills', billId], updatedBill);
      qc.invalidateQueries({ queryKey: ['bills'] });
    },
  });
}

export function useCancelBill(billId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post<Bill>(`/billing/bills/${billId}/cancel/`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['bills', billId] });
      qc.invalidateQueries({ queryKey: ['bills'] });
    },
  });
}
