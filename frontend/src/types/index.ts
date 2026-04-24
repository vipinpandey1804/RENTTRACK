export interface Organization {
  id: string;
  name: string;
  slug: string;
  tier: 'shared' | 'pooled' | 'dedicated';
  primary_email: string;
  primary_phone?: string;
  gstin?: string;
  pan?: string;
}

export interface Membership {
  id: string;
  organization: Organization;
  role: 'owner' | 'property_manager' | 'accountant' | 'support' | 'tenant' | 'co_tenant';
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  phone_verified: boolean;
  email_verified: boolean;
  active_organization: Organization | null;
  memberships: Membership[];
}

export interface Property {
  id: string;
  name: string;
  property_type: 'residential' | 'commercial' | 'mixed';
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  electricity_rate_per_unit: string;
  cover_image: string | null;
  unit_count: number;
  occupied_count: number;
  created_at: string;
  updated_at: string;
}

export interface Unit {
  id: string;
  property: string;
  property_name: string;
  name: string;
  floor?: number | null;
  area_sqft?: string | null;
  bedrooms?: number | null;
  base_rent: string;
  security_deposit: string;
  electricity_meter_id?: string;
  status: 'vacant' | 'occupied' | 'maintenance';
  created_at: string;
  updated_at: string;
}

export interface Lease {
  id: string;
  unit: string;
  unit_name: string;
  property_name: string;
  tenant: string;
  tenant_email: string;
  start_date: string;
  end_date?: string | null;
  monthly_rent: string;
  security_deposit_held: string;
  billing_cycle: 'monthly' | 'quarterly' | 'yearly';
  billing_day_of_month: number;
  grace_period_days: number;
  late_fee_type: 'flat' | 'percentage' | 'none';
  late_fee_value: string;
  status: 'draft' | 'active' | 'ended' | 'terminated';
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: string | string[] | undefined;
}

export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced' | 'read';

export interface Notification {
  id: string;
  channel: 'email' | 'sms' | 'whatsapp' | 'in_app' | 'push';
  event_type: string;
  subject: string;
  body: string;
  status: NotificationStatus;
  sent_at: string | null;
  read_at: string | null;
  created_at: string;
}
