"""Serializers for properties, units, and leases."""
from rest_framework import serializers

from apps.properties.models import Lease, Property, Unit


class PropertySerializer(serializers.ModelSerializer):
    unit_count = serializers.SerializerMethodField()
    occupied_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "name",
            "property_type",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "electricity_rate_per_unit",
            "unit_count",
            "occupied_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_unit_count(self, obj):
        return obj.units.filter(is_deleted=False).count()

    def get_occupied_count(self, obj):
        return obj.units.filter(is_deleted=False, status=Unit.Status.OCCUPIED).count()


class UnitSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source="property.name", read_only=True)

    class Meta:
        model = Unit
        fields = [
            "id",
            "property",
            "property_name",
            "name",
            "floor",
            "area_sqft",
            "bedrooms",
            "base_rent",
            "security_deposit",
            "electricity_meter_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "property_name", "created_at", "updated_at"]

    def validate_property(self, value):
        request = self.context.get("request")
        if request and value.organization_id != request.user.active_organization_id:
            raise serializers.ValidationError("Property does not belong to your organization.")
        return value


class LeaseSerializer(serializers.ModelSerializer):
    tenant_email = serializers.EmailField(source="tenant.email", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True)
    property_name = serializers.CharField(source="unit.property.name", read_only=True)

    class Meta:
        model = Lease
        fields = [
            "id",
            "unit",
            "unit_name",
            "property_name",
            "tenant",
            "tenant_email",
            "start_date",
            "end_date",
            "monthly_rent",
            "security_deposit_held",
            "billing_cycle",
            "billing_day_of_month",
            "grace_period_days",
            "late_fee_type",
            "late_fee_value",
            "status",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant_email",
            "unit_name",
            "property_name",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_unit(self, value):
        request = self.context.get("request")
        if request and value.organization_id != request.user.active_organization_id:
            raise serializers.ValidationError("Unit does not belong to your organization.")
        return value

    def validate(self, data):
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and end <= start:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        day = data.get("billing_day_of_month", 1)
        if not (1 <= day <= 28):
            raise serializers.ValidationError(
                {"billing_day_of_month": "Billing day must be between 1 and 28."}
            )
        return data
