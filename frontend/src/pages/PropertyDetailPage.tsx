import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import AppShell from '@/components/layout/AppShell';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import { toast } from '@/components/ui/Toast';
import { useProperty, usePropertyUnits, useCreateUnit } from '@/hooks/useProperties';
import type { Unit } from '@/types';

const statusColors: Record<Unit['status'], string> = {
  vacant: 'bg-green-100 text-green-700',
  occupied: 'bg-blue-100 text-blue-700',
  maintenance: 'bg-yellow-100 text-yellow-700',
};

function UnitRow({ unit }: { unit: Unit }) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 px-4 text-sm font-medium text-gray-900">{unit.name}</td>
      <td className="py-3 px-4 text-sm text-gray-600">{unit.floor ?? '—'}</td>
      <td className="py-3 px-4 text-sm text-gray-600">{unit.bedrooms ?? '—'}</td>
      <td className="py-3 px-4 text-sm text-gray-600">
        ₹{Number(unit.base_rent).toLocaleString('en-IN')}
      </td>
      <td className="py-3 px-4">
        <span className={`text-xs font-medium px-2 py-1 rounded-full capitalize ${statusColors[unit.status]}`}>
          {unit.status}
        </span>
      </td>
    </tr>
  );
}

interface UnitFormData {
  name: string;
  floor: string;
  bedrooms: string;
  area_sqft: string;
  base_rent: string;
  security_deposit: string;
  electricity_meter_id: string;
}

function AddUnitModal({
  open,
  onClose,
  propertyId,
}: {
  open: boolean;
  onClose: () => void;
  propertyId: string;
}) {
  const createUnit = useCreateUnit();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<UnitFormData>();

  const onSubmit = async (data: UnitFormData) => {
    try {
      await createUnit.mutateAsync({
        property: propertyId,
        name: data.name,
        floor: data.floor ? Number(data.floor) : undefined,
        bedrooms: data.bedrooms ? Number(data.bedrooms) : undefined,
        area_sqft: data.area_sqft || undefined,
        base_rent: data.base_rent,
        security_deposit: data.security_deposit || '0',
        electricity_meter_id: data.electricity_meter_id,
      } as any);
      toast.success('Unit added');
      reset();
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to add unit');
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add unit">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Unit name"
          placeholder="e.g. Flat 3B"
          {...register('name', { required: 'Unit name is required' })}
          error={errors.name?.message}
        />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Floor" type="number" {...register('floor')} />
          <Input label="Bedrooms" type="number" {...register('bedrooms')} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Area (sqft)" type="number" {...register('area_sqft')} />
          <Input
            label="Monthly rent (₹)"
            type="number"
            {...register('base_rent', { required: 'Rent is required' })}
            error={errors.base_rent?.message}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Security deposit (₹)" type="number" {...register('security_deposit')} />
          <Input label="Electricity meter ID" {...register('electricity_meter_id')} />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createUnit.isPending}>
            Add unit
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [showAddUnit, setShowAddUnit] = useState(false);
  const { data: property, isLoading: propLoading } = useProperty(id!);
  const { data: units, isLoading: unitsLoading } = usePropertyUnits(id!);

  if (propLoading) {
    return (
      <AppShell>
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-4 bg-gray-100 rounded w-80" />
        </div>
      </AppShell>
    );
  }

  if (!property) {
    return (
      <AppShell>
        <p className="text-gray-500">Property not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-1">
        <Link to="/properties" className="text-sm text-gray-500 hover:text-gray-700">
          ← Properties
        </Link>
      </div>
      <div className="flex items-start justify-between mb-6 mt-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{property.name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {property.address_line1}
            {property.address_line2 ? `, ${property.address_line2}` : ''},{' '}
            {property.city}, {property.state} {property.postal_code}
          </p>
        </div>
        <span className="text-sm font-medium px-3 py-1 rounded-full bg-gray-100 text-gray-600 capitalize">
          {property.property_type}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Total units', value: property.unit_count },
          { label: 'Occupied', value: property.occupied_count },
          { label: 'Vacant', value: property.unit_count - property.occupied_count },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Units</h2>
          <Button size="sm" onClick={() => setShowAddUnit(true)}>
            + Add unit
          </Button>
        </div>

        {unitsLoading ? (
          <div className="p-8 text-center text-sm text-gray-400">Loading units…</div>
        ) : units && units.length > 0 ? (
          <table className="w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="py-2 px-4 text-left font-medium">Unit</th>
                <th className="py-2 px-4 text-left font-medium">Floor</th>
                <th className="py-2 px-4 text-left font-medium">Beds</th>
                <th className="py-2 px-4 text-left font-medium">Rent</th>
                <th className="py-2 px-4 text-left font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {units.map((u) => (
                <UnitRow key={u.id} unit={u} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500 text-sm mb-3">No units yet</p>
            <Button size="sm" onClick={() => setShowAddUnit(true)}>
              Add first unit
            </Button>
          </div>
        )}
      </div>

      <AddUnitModal
        open={showAddUnit}
        onClose={() => setShowAddUnit(false)}
        propertyId={id!}
      />
    </AppShell>
  );
}
