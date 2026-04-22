"""Data migration: register Django Q schedules for daily billing tasks."""
from django.db import migrations


def register_schedules(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")

    Schedule.objects.update_or_create(
        name="generate_daily_bills",
        defaults={
            "func": "apps.billing.tasks.generate_daily_bills",
            "schedule_type": "C",
            "cron": "30 0 * * *",  # 00:30 UTC = 06:00 IST
            "repeats": -1,
        },
    )
    Schedule.objects.update_or_create(
        name="mark_overdue_bills",
        defaults={
            "func": "apps.billing.tasks.mark_overdue_bills_task",
            "schedule_type": "C",
            "cron": "35 18 * * *",  # 18:35 UTC = 00:05 IST
            "repeats": -1,
        },
    )


def deregister_schedules(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")
    Schedule.objects.filter(name__in=["generate_daily_bills", "mark_overdue_bills"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        ("django_q", "0018_task_success_index"),
    ]

    operations = [
        migrations.RunPython(register_schedules, deregister_schedules),
    ]
