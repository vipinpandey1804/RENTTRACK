"""
Data migration: register Celery beat schedules for daily billing tasks.

  - generate_daily_bills  → runs every day at 06:00 IST (00:30 UTC)
  - mark_overdue_bills_task → runs every day at 00:05 IST (18:35 UTC previous day)

IST = UTC+5:30, so:
  06:00 IST = 00:30 UTC
  00:05 IST = 18:35 UTC (previous calendar day)
"""
from django.db import migrations


def register_schedules(apps, schema_editor):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    # 06:00 IST = 00:30 UTC
    morning_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="30",
        hour="0",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        defaults={"timezone": "UTC"},
    )

    # 00:05 IST = 18:35 UTC (prior day)
    midnight_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="35",
        hour="18",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        defaults={"timezone": "UTC"},
    )

    PeriodicTask.objects.update_or_create(
        name="generate_daily_bills",
        defaults={
            "task": "apps.billing.tasks.generate_daily_bills",
            "crontab": morning_schedule,
            "enabled": True,
            "description": "Generate rent bills for leases due today (06:00 IST)",
        },
    )

    PeriodicTask.objects.update_or_create(
        name="mark_overdue_bills",
        defaults={
            "task": "apps.billing.tasks.mark_overdue_bills_task",
            "crontab": midnight_schedule,
            "enabled": True,
            "description": "Mark issued bills past due date as overdue (00:05 IST)",
        },
    )


def deregister_schedules(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(
        name__in=["generate_daily_bills", "mark_overdue_bills"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("django_celery_beat", "0018_improve_crontab_helptext"),
    ]

    operations = [
        migrations.RunPython(register_schedules, deregister_schedules),
    ]
