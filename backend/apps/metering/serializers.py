"""Metering serializers."""

from decimal import Decimal

from rest_framework import serializers

from apps.metering.models import MeterReading
from apps.properties.models import Unit


class MeterReadingSerializer(serializers.ModelSerializer):
    unit_name = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()

    class Meta:
        model = MeterReading
        fields = [
            "id",
            "unit",
            "unit_name",
            "property_name",
            "meter_type",
            "period_month",
            "previous_reading",
            "current_reading",
            "units_consumed",
            "reading_photo_url",
            "ocr_extracted_value",
            "status",
            "notes",
            "submitted_by",
            "confirmed_by",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "previous_reading",
            "units_consumed",
            "status",
            "submitted_by",
            "confirmed_by",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]

    def get_unit_name(self, obj):
        return obj.unit.name

    def get_property_name(self, obj):
        return obj.unit.property.name

    def validate(self, data):
        unit: Unit = data["unit"]
        meter_type = data["meter_type"]
        period_month = data["period_month"]
        current_reading = data["current_reading"]

        # period_month must be the first of the month
        if period_month.day != 1:
            raise serializers.ValidationError(
                {"period_month": "Must be the first day of the month (e.g. 2026-04-01)."}
            )

        # Cannot submit for a locked period
        locked = MeterReading.objects.filter(
            unit=unit,
            meter_type=meter_type,
            period_month=period_month,
            status=MeterReading.Status.LOCKED,
        ).exists()
        if locked:
            raise serializers.ValidationError(
                {"period_month": "A locked reading already exists for this period."}
            )

        # Cannot duplicate an existing non-locked reading
        existing = MeterReading.objects.filter(
            unit=unit,
            meter_type=meter_type,
            period_month=period_month,
        ).first()
        if existing and existing.status != MeterReading.Status.LOCKED:
            raise serializers.ValidationError(
                {"period_month": "A reading already exists for this period. Delete it first."}
            )

        # Look up the previous reading for this unit/meter_type
        prev = (
            MeterReading.objects.filter(
                unit=unit,
                meter_type=meter_type,
                period_month__lt=period_month,
            )
            .order_by("-period_month")
            .first()
        )
        previous_reading = prev.current_reading if prev else Decimal("0")

        if current_reading < previous_reading:
            raise serializers.ValidationError(
                {
                    "current_reading": (
                        f"Current reading ({current_reading}) cannot be less than "
                        f"the previous reading ({previous_reading})."
                    )
                }
            )

        data["previous_reading"] = previous_reading
        return data

    def create(self, validated_data):
        validated_data["submitted_by"] = self.context["request"].user
        # period_month must be first of month (already validated)
        return super().create(validated_data)


class ConfirmReadingSerializer(serializers.Serializer):
    """Empty body — confirmation requires no extra input."""

    pass
