import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { toast } from "@/components/ui/Toast";
import { useProperties, useCreateProperty } from "@/hooks/useProperties";
import type { Property } from "@/types";

const TYPE_BADGE: Record<Property["property_type"], string> = {
  residential: "bg-emerald-100 text-emerald-700",
  commercial: "bg-violet-100 text-violet-700",
  mixed: "bg-amber-100 text-amber-700",
};

const TYPE_LABEL: Record<Property["property_type"], string> = {
  residential: "Residential",
  commercial: "Commercial",
  mixed: "Mixed Use",
};

const PLACEHOLDER_COLORS = [
  "from-blue-400 to-indigo-500",
  "from-emerald-400 to-teal-500",
  "from-violet-400 to-purple-500",
  "from-amber-400 to-orange-500",
  "from-rose-400 to-pink-500",
];

function PropertyCard({
  property,
  index,
}: {
  property: Property;
  index: number;
}) {
  const occupancy =
    property.unit_count > 0
      ? Math.round((property.occupied_count / property.unit_count) * 100)
      : 0;
  const color = PLACEHOLDER_COLORS[index % PLACEHOLDER_COLORS.length];

  return (
    <Link
      to={`/properties/${property.id}`}
      className="block bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all overflow-hidden group"
    >
      {/* Cover image */}
      <div className="relative h-44 overflow-hidden">
        {property.cover_image ? (
          <img
            src={property.cover_image}
            alt={property.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div
            className={`w-full h-full bg-gradient-to-br ${color} flex items-center justify-center`}
          >
            <svg
              className="h-14 w-14 text-white/60"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
        )}
        <span
          className={`absolute top-3 right-3 text-xs font-semibold px-2.5 py-1 rounded-full backdrop-blur-sm bg-white/90 border border-white/60 ${
            TYPE_BADGE[property.property_type]
          }`}
        >
          {TYPE_LABEL[property.property_type]}
        </span>
      </div>

      {/* Card body */}
      <div className="p-5">
        <h3 className="font-bold text-gray-900 text-base leading-snug mb-0.5 group-hover:text-blue-700 transition-colors">
          {property.name}
        </h3>
        <p className="text-sm text-gray-500 mb-4 truncate">
          {property.city}, {property.state}
        </p>

        <div className="flex items-center justify-between">
          <div className="flex gap-4 text-sm">
            <div className="text-center">
              <p className="font-bold text-gray-900 text-lg leading-none">
                {property.unit_count}
              </p>
              <p className="text-gray-400 text-xs mt-0.5">units</p>
            </div>
            <div className="text-center">
              <p className="font-bold text-gray-900 text-lg leading-none">
                {property.occupied_count}
              </p>
              <p className="text-gray-400 text-xs mt-0.5">occupied</p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1.5 justify-end mb-1">
              <div className="w-20 h-1.5 rounded-full bg-gray-100">
                <div
                  className={`h-1.5 rounded-full ${
                    occupancy >= 80
                      ? "bg-emerald-500"
                      : occupancy >= 40
                        ? "bg-blue-500"
                        : "bg-amber-500"
                  }`}
                  style={{ width: `${occupancy}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 font-medium w-8 text-right">
                {occupancy}%
              </span>
            </div>
            <p className="text-xs text-gray-400">occupancy</p>
          </div>
        </div>
      </div>
    </Link>
  );
}

interface PropertyFormData {
  name: string;
  property_type: "residential" | "commercial" | "mixed";
  address_line1: string;
  address_line2: string;
  city: string;
  state: string;
  postal_code: string;
}

function AddPropertyModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const createProperty = useCreateProperty();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PropertyFormData>();
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const onSubmit = async (data: PropertyFormData) => {
    try {
      await createProperty.mutateAsync({
        ...data,
        cover_image_file: imageFile ?? undefined,
      } as any);
      toast.success("Property created successfully");
      reset();
      setImageFile(null);
      setImagePreview(null);
      onClose();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Failed to create property");
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add property" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Image upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Cover photo (optional)
          </label>
          <div
            onClick={() => fileRef.current?.click()}
            className="cursor-pointer rounded-xl border-2 border-dashed border-gray-200 hover:border-blue-400 transition-colors overflow-hidden"
          >
            {imagePreview ? (
              <div className="relative h-40">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                  <span className="text-white text-sm font-medium">
                    Change photo
                  </span>
                </div>
              </div>
            ) : (
              <div className="h-32 flex flex-col items-center justify-center gap-2 text-gray-400">
                <svg
                  className="h-8 w-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <span className="text-sm">Click to upload photo</span>
              </div>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="hidden"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <Input
              label="Property name"
              {...register("name", { required: "Name is required" })}
              error={errors.name?.message}
            />
          </div>
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              {...register("property_type", { required: true })}
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
              {...register("address_line1", {
                required: "Address is required",
              })}
              error={errors.address_line1?.message}
            />
          </div>
          <div className="col-span-2">
            <Input label="Address line 2" {...register("address_line2")} />
          </div>
          <Input
            label="City"
            {...register("city", { required: "City is required" })}
            error={errors.city?.message}
          />
          <Input
            label="State"
            {...register("state", { required: "State is required" })}
            error={errors.state?.message}
          />
          <Input
            label="Postal code"
            {...register("postal_code", {
              required: "Postal code is required",
            })}
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
  const count = data?.count ?? 0;

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Properties</h1>
          <p className="text-sm text-gray-500 mt-1">
            {count} propert{count === 1 ? "y" : "ies"} in your portfolio
          </p>
        </div>
        <Button onClick={() => setShowAdd(true)} className="shadow-sm">
          + Add property
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="rounded-2xl overflow-hidden border border-gray-100 shadow-sm"
            >
              <div className="h-44 bg-gray-100 animate-pulse" />
              <div className="p-5 space-y-3">
                <div className="h-4 bg-gray-100 animate-pulse rounded w-3/4" />
                <div className="h-3 bg-gray-100 animate-pulse rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl bg-red-50 border border-red-200 p-6 text-center text-sm text-red-700">
          Failed to load properties. Please refresh and try again.
        </div>
      )}

      {!isLoading && !isError && data?.results.length === 0 && (
        <div className="rounded-2xl border-2 border-dashed border-gray-200 p-16 text-center">
          <div className="h-16 w-16 rounded-2xl bg-blue-50 flex items-center justify-center mx-auto mb-4">
            <svg
              className="h-8 w-8 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900 mb-1">
            No properties yet
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Add your first property to start managing rentals
          </p>
          <Button onClick={() => setShowAdd(true)}>
            Add your first property
          </Button>
        </div>
      )}

      {!isLoading && !isError && data && data.results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.results.map((p, i) => (
            <PropertyCard key={p.id} property={p} index={i} />
          ))}
        </div>
      )}

      <AddPropertyModal open={showAdd} onClose={() => setShowAdd(false)} />
    </AppShell>
  );
}
