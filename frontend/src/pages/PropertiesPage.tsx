import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import AppShell from '@/components/layout/AppShell';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { toast } from '@/components/ui/Toast';
import { useProperties, useCreateProperty } from '@/hooks/useProperties';
import type { Property } from '@/types';

function PropertyCard({ property }: { property: Property }) {
  const occupancy =
    property.unit_count > 0
      ? Math.round((property.occupied_count / property.unit_count) * 100)
      : 0;

  return (
    <Link
      to={`/properties/${property.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-200 transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{property.name}</h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {property.city}, {property.state}
          </p>
        </div>
        <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-600 capitalize">
          {property.property_type}
        </span>
      </div>
      <p className="text-sm text-gray-500 mb-4 truncate">{property.address_line1}</p>
      <div className="flex items-center justify-between text-sm">
        <div className="text-gray-600">
          <span className="font-medium text-gray-900">{property.occupied_count}</span>
          /{property.unit_count} units occupied
        </div>
        <div className="flex items-center gap-2">
          <div className="w-24 h-1.5 rounded-full bg-gray-200">
            <div
              className="h-1.5 rounded-full bg-blue-500"
              style={{ width: `${occupancy}%` }}
            />
          </div>
          <span className="text-gray-500 text-xs">{occupancy}%</span>
        </div>
      </div>
    </Link>
  );
}

interface PropertyFormData {
  name: string;
  property_type: 'residential' | 'commercial' | 'mixed';
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
}

function AddPropertyModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const createProperty = useCreateProperty();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<PropertyFormData>();

  const onSubmit = async (data: PropertyFormData) => {
    try {
      await createProperty.mutateAsync(data);
      toast.success('Property created successfully');
      reset();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'Failed to create property';
      toast.error(msg);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add property" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <Input
              label="Property name"
              {...register('name', { required: 'Name is required' })}
              error={errors.name?.message}
            />
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              {...register('property_type', { required: true })}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="residential">Residential</option>
              <option value="commercial">Commercial</option>
              <option value="mixed">Mixed Use</option>
            </select>
          </div>
          <div className="col-span-2">
            <Input
              label="Address line 1"
              {...register('address_line1', { required: 'Address is required' })}
              error={errors.address_line1?.message}
            />
          </div>
          <div className="col-span-2">
            <Input label="Address line 2" {...register('address_line2')} />
          </div>
          <Input
            label="City"
            {...register('city', { required: 'City is required' })}
            error={errors.city?.message}
          />
          <Input
            label="State"
            {...register('state', { required: 'State is required' })}
            error={errors.state?.message}
          />
          <Input
            label="Postal code"
            {...register('postal_code', { required: 'Postal code is required' })}
            error={errors.postal_code?.message}
          />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createProperty.isPending}>
            Create property
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function PropertiesPage() {
  const [showAdd, setShowAdd] = useState(false);
  const { data, isLoading, isError } = useProperties();

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Properties</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.count ?? 0} propert{data?.count === 1 ? 'y' : 'ies'}
          </p>
        </div>
        <Button onClick={() => setShowAdd(true)}>+ Add property</Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-40 rounded-xl bg-gray-100 animate-pulse" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center text-sm text-red-700">
          Failed to load properties. Please refresh and try again.
        </div>
      )}

      {!isLoading && !isError && data?.results.length === 0 && (
        <div className="rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
          <p className="text-gray-500 mb-4">No properties yet</p>
          <Button onClick={() => setShowAdd(true)}>Add your first property</Button>
        </div>
      )}

      {!isLoading && !isError && data && data.results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.results.map((p) => (
            <PropertyCard key={p.id} property={p} />
          ))}
        </div>
      )}

      <AddPropertyModal open={showAdd} onClose={() => setShowAdd(false)} />
    </AppShell>
  );
}
