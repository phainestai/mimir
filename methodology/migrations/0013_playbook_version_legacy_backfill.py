# Data migration: normalize Decimal X.Y and backfill legacy release rows from S01 schema.

from decimal import Decimal

from django.db import migrations


def forwards(apps, schema_editor):
    PlaybookVersion = apps.get_model("methodology", "PlaybookVersion")

    for pv in PlaybookVersion.objects.iterator():
        updates = {}
        vn = pv.version_number
        if vn is None:
            continue
        normalized = Decimal(str(vn)).quantize(Decimal("0.1"))
        if pv.version_number != normalized:
            updates["version_number"] = normalized

        desc = (pv.description or "").strip()
        cs = (pv.change_summary or "").strip()
        if not desc and cs:
            updates["description"] = cs

        major_line = normalized >= Decimal("1.0")
        if major_line:
            if not pv.is_major:
                updates["is_major"] = True
            if pv.source == "author":
                updates["source"] = "release"

        if updates:
            for field, value in updates.items():
                setattr(pv, field, value)
            pv.save(update_fields=list(updates.keys()))


def backwards(apps, schema_editor):
    """Non-destructive: version history is not reverted."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("methodology", "0012_playbook_version_decimal_and_pip"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
