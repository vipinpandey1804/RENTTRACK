import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { PaginatedResponse, Property, Unit, Lease } from '@/types';

export function useProperties() {
  return useQuery({
    queryKey: ['properties'],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Property>>('/properties/');
      return data;
    },
  });
}

export function useProperty(id: string) {
  return useQuery({
    queryKey: ['properties', id],
    queryFn: async () => {
      const { data } = await api.get<Property>(`/properties/${id}/`);
      return data;
    },
    enabled: !!id,
  });
}

export function usePropertyUnits(propertyId: string) {
  return useQuery({
    queryKey: ['properties', propertyId, 'units'],
    queryFn: async () => {
      const { data } = await api.get<Unit[]>(`/properties/${propertyId}/units/`);
      return data;
    },
    enabled: !!propertyId,
  });
}

export function useCreateProperty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Property>) => api.post('/properties/', payload).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['properties'] }),
  });
}

export function useUpdateProperty(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Property>) =>
      api.patch(`/properties/${id}/`, payload).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['properties'] });
      qc.invalidateQueries({ queryKey: ['properties', id] });
    },
  });
}

export function useDeleteProperty() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/properties/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['properties'] }),
  });
}

export function useUnits(propertyId?: string) {
  return useQuery({
    queryKey: ['units', { propertyId }],
    queryFn: async () => {
      const params = propertyId ? `?property=${propertyId}` : '';
      const { data } = await api.get<PaginatedResponse<Unit>>(`/properties/units/${params}`);
      return data;
    },
  });
}

export function useCreateUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Unit>) =>
      api.post('/properties/units/', payload).then((r) => r.data),
    onSuccess: (data: Unit) => {
      qc.invalidateQueries({ queryKey: ['units'] });
      qc.invalidateQueries({ queryKey: ['properties', data.property, 'units'] });
      qc.invalidateQueries({ queryKey: ['properties', data.property] });
    },
  });
}

export function useLeases(filters: { unit?: string; tenant?: string; status?: string } = {}) {
  return useQuery({
    queryKey: ['leases', filters],
    queryFn: async () => {
      const params = new URLSearchParams(filters as Record<string, string>).toString();
      const { data } = await api.get<PaginatedResponse<Lease>>(
        `/properties/leases/${params ? `?${params}` : ''}`,
      );
      return data;
    },
  });
}
