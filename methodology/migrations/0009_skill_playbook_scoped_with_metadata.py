# Custom migration: Skill model changes from activity-scoped (1:1) to playbook-scoped (1:N)
#
# Changes:
# 1. Skill: Remove 'activity' OneToOneField
# 2. Skill: Add 'playbook' ForeignKey (non-nullable)
# 3. Skill: Add 'capability_domain' CharField
# 4. Skill: Add 'technology_stack' CharField
# 5. Activity: Add 'skill' ForeignKey (nullable)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('methodology', '0008_activity_agent_field'),
    ]

    operations = [
        # 1. Remove old activity 1:1 link from Skill
        migrations.RemoveField(
            model_name='skill',
            name='activity',
        ),

        # 2. Add playbook FK to Skill (non-nullable — no existing rows in practice)
        migrations.AddField(
            model_name='skill',
            name='playbook',
            field=models.ForeignKey(
                default=1,  # one-off default; no existing rows in practice
                help_text='Parent playbook owning this skill',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='skills',
                to='methodology.playbook',
            ),
            preserve_default=False,
        ),

        # 3. Add capability_domain to Skill
        migrations.AddField(
            model_name='skill',
            name='capability_domain',
            field=models.CharField(
                blank=True,
                default='',
                help_text='What capability this skill covers (e.g., GUI_FORM, API_CRUD, DB_MIGRATION)',
                max_length=100,
            ),
        ),

        # 4. Add technology_stack to Skill
        migrations.AddField(
            model_name='skill',
            name='technology_stack',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Technology used (e.g., React+Redux, Django+HTMX, FastAPI)',
                max_length=100,
            ),
        ),

        # 5. Add skill FK on Activity (nullable — activities may not have a skill)
        migrations.AddField(
            model_name='activity',
            name='skill',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional skill providing tech-specific guidance for this activity',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='activities',
                to='methodology.skill',
            ),
        ),
    ]
