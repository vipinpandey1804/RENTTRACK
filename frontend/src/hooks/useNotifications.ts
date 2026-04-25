import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Notification, PaginatedResponse } from "@/types";

const POLL_INTERVAL = 60_000;

export function useNotifications() {
  return useQuery<PaginatedResponse<Notification>>({
    queryKey: ["notifications"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Notification>>("/notifications/", {
          params: { page_size: 20 },
        })
        .then((r) => r.data),
    refetchInterval: POLL_INTERVAL,
    staleTime: 30_000,
  });
}

export function useUnreadCount() {
  const { data } = useNotifications();
  if (!data) return 0;
  return data.results.filter((n: Notification) => n.read_at === null).length;
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api
        .post<Notification>(`/notifications/${id}/mark_read/`)
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api
        .post<{ status: string }>("/notifications/mark_all_read/")
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

// ---------------------------------------------------------------------------
// Preferences
// ---------------------------------------------------------------------------

export interface NotificationPreferenceItem {
  event_type: string;
  channel: string;
  enabled: boolean;
}

export const PREFERENCE_EVENTS: { key: string; label: string }[] = [
  { key: "bill.issued", label: "Bill issued" },
  { key: "bill.overdue", label: "Bill overdue" },
  { key: "payment.received", label: "Payment received" },
];

export const PREFERENCE_CHANNELS: { key: string; label: string }[] = [
  { key: "email", label: "Email" },
  { key: "sms", label: "SMS" },
];

export function useNotificationPreferences() {
  return useQuery<NotificationPreferenceItem[]>({
    queryKey: ["notification-preferences"],
    queryFn: () =>
      api
        .get<NotificationPreferenceItem[]>("/notifications/preferences/")
        .then((r) => r.data),
  });
}

export function useUpdateNotificationPreferences() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (prefs: NotificationPreferenceItem[]) =>
      api
        .put<NotificationPreferenceItem[]>("/notifications/preferences/", prefs)
        .then((r) => r.data),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["notification-preferences"] }),
  });
}
