# Migrate Activity.skill FK → Activity.skills M2M with data preservation

from django.db import migrations, models


def copy_skill_fk_to_m2m(apps, schema_editor):
    Activity = apps.get_model('methodology', 'Activity')
    for activity in Activity.objects.exclude(skill_id__isnull=True).iterator():
        activity.skills.add(activity.skill_id)


def noop_reverse(apps, schema_editor):
    """M2M → FK reverse is lossy when multiple skills exist; leave skill NULL."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('methodology', '0018_alter_processimprovementproposal_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='skills',
            field=models.ManyToManyField(
                blank=True,
                help_text='Tech-specific skills linked to this activity (many-to-many)',
                related_name='activities',
                to='methodology.skill',
            ),
        ),
        migrations.RunPython(copy_skill_fk_to_m2m, noop_reverse),
        migrations.RemoveField(
            model_name='activity',
            name='skill',
        ),
    ]
