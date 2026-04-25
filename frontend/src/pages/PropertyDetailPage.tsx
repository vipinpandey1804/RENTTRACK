import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import Modal from "@/components/ui/Modal";
import Input from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import {
  useProperty,
  usePropertyUnits,
  useCreateUnit,
} from "@/hooks/useProperties";
import type { Unit } from "@/types";

const statusColors: Record<Unit["status"], string> = {
  vacant: "bg-emerald-100 text-emerald-700",
  occupied: "bg-blue-100 text-blue-700",
  maintenance: "bg-amber-100 text-amber-700",
};

const statusDots: Record<Unit["status"], string> = {
  vacant: "bg-emerald-500",
  occupied: "bg-blue-500",
  maintenance: "bg-amber-500",
};

function UnitRow({ unit }: { unit: Unit }) {
  return (
    <tr className="border-b border-gray-50 hover:bg-blue-50/30 transition-colors">
      <td className="py-3.5 px-5">
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${statusDots[unit.status]}`} />
          <span className="text-sm font-semibold text-gray-900">
            {unit.name}
          </span>
        </div>
      </td>
      <td className="py-3.5 px-5 text-sm text-gray-500">{unit.floor ?? "—"}</td>
      <td className="py-3.5 px-5 text-sm text-gray-500">
        {unit.bedrooms ?? "—"}
      </td>
      <td className="py-3.5 px-5 text-sm font-medium text-gray-900">
        ₹{Number(unit.base_rent).toLocaleString("en-IN")}
      </td>
      <td className="py-3.5 px-5">
        <span
          className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${
            statusColors[unit.status]
          }`}
        >
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
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UnitFormData>();

  const onSubmit = async (data: UnitFormData) => {
    try {
      await createUnit.mutateAsync({
        property: propertyId,
        name: data.name,
        floor: data.floor ? Number(data.floor) : undefined,
        bedrooms: data.bedrooms ? Number(data.bedrooms) : undefined,
        area_sqft: data.area_sqft || undefined,
        base_rent: data.base_rent,
        security_deposit: data.security_deposit || "0",
        electricity_meter_id: data.electricity_meter_id,
      } as any);
      toast.success("Unit added");
      reset();
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to add unit");
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add unit">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Unit name"
          placeholder="e.g. Flat 3B"
          {...register("name", { required: "Unit name is required" })}
          error={errors.name?.message}
        />
        <div className="grid grid-cols-2 gap-4">
          <Input label="Floor" type="number" {...register("floor")} />
          <Input label="Bedrooms" type="number" {...register("bedrooms")} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Area (sqft)" type="number" {...register("area_sqft")} />
          <Input
            label="Monthly rent (₹)"
            type="number"
            {...register("base_rent", { required: "Rent is required" })}
            error={errors.base_rent?.message}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Security deposit (₹)"
            type="number"
            {...register("security_deposit")}
          />
          <Input
            label="Electricity meter ID"
            {...register("electricity_meter_id")}
          />
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

const PLACEHOLDER_GRADIENT = "from-blue-400 to-indigo-500";

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [showAddUnit, setShowAddUnit] = useState(false);
  const { data: property, isLoading: propLoading } = useProperty(id!);
  const { data: units, isLoading: unitsLoading } = usePropertyUnits(id!);

  if (propLoading) {
    return (
      <AppShell>
        <div className="animate-pulse space-y-4">
          <div className="h-56 rounded-2xl bg-gray-200" />
          <div className="h-6 bg-gray-200 rounded w-48" />
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

  const vacant = property.unit_count - property.occupied_count;

  return (
    <AppShell>
      {/* Breadcrumb */}
      <div className="mb-4">
        <Link
          to="/properties"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Properties
        </Link>
      </div>

      {/* Hero image */}
      <div className="relative h-56 rounded-2xl overflow-hidden mb-6 shadow-sm">
        {property.cover_image ? (
          <img
            src={property.cover_image}
            alt={property.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div
            className={`w-full h-full bg-gradient-to-br ${PLACEHOLDER_GRADIENT} flex items-center justify-center`}
          >
            <svg
              className="h-20 w-20 text-white/50"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
        )}
        {/* Overlay gradient for readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-6">
          <div className="flex items-end justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">
                {property.name}
              </h1>
              <p className="text-sm text-white/80">
                {property.address_line1}
                {property.address_line2
                  ? `, ${property.address_line2}`
                  : ""}, {property.city}, {property.state}{" "}
                {property.postal_code}
              </p>
            </div>
            <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-white/20 backdrop-blur-sm text-white border border-white/30 capitalize">
              {property.property_type}
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          {
            label: "Total units",
            value: property.unit_count,
            color: "text-gray-900",
            bg: "bg-white",
          },
          {
            label: "Occupied",
            value: property.occupied_count,
            color: "text-blue-700",
            bg: "bg-blue-50",
          },
          {
            label: "Vacant",
            value: vacant,
            color: "text-emerald-700",
            bg: "bg-emerald-50",
          },
        ].map(({ label, value, color, bg }) => (
          <div
            key={label}
            className={`${bg} rounded-2xl border border-gray-100 p-5 shadow-sm`}
          >
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
              {label}
            </p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Units table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">Units</h2>
          <Button size="sm" onClick={() => setShowAddUnit(true)}>
            + Add unit
          </Button>
        </div>

        {unitsLoading ? (
          <div className="p-10 text-center text-sm text-gray-400">
            Loading units…
          </div>
        ) : units && units.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50/80 text-xs text-gray-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-5 text-left font-semibold">Unit</th>
                  <th className="py-3 px-5 text-left font-semibold">Floor</th>
                  <th className="py-3 px-5 text-left font-semibold">Beds</th>
                  <th className="py-3 px-5 text-left font-semibold">Rent</th>
                  <th className="py-3 px-5 text-left font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {units.map((u) => (
                  <UnitRow key={u.id} unit={u} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="h-12 w-12 rounded-xl bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <svg
                className="h-6 w-6 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
            </div>
            <p className="font-medium text-gray-900 mb-1">No units yet</p>
            <p className="text-sm text-gray-400 mb-4">
              Add units to start assigning tenants
            </p>
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
