# Generated manually for Rule model + Activity M2M

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("methodology", "0010_add_phase_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="Short title for the rule", max_length=200)),
                ("slug", models.SlugField(help_text="Filename-safe identifier, unique per playbook", max_length=220)),
                (
                    "content",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Markdown body (exported after YAML front matter)",
                    ),
                ),
                (
                    "always_apply",
                    models.BooleanField(
                        default=True,
                        help_text="When True, exported .mdc includes alwaysApply in front matter",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "playbook",
                    models.ForeignKey(
                        help_text="Parent playbook owning this rule",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="methodology.playbook",
                    ),
                ),
            ],
            options={
                "verbose_name": "Rule",
                "verbose_name_plural": "Rules",
                "ordering": ["playbook", "slug"],
            },
        ),
        migrations.AddConstraint(
            model_name="rule",
            constraint=models.UniqueConstraint(fields=("playbook", "slug"), name="unique_rule_slug_per_playbook"),
        ),
        migrations.AddField(
            model_name="activity",
            name="rules",
            field=models.ManyToManyField(
                blank=True,
                help_text="IDE rules linked to this activity (many-to-many)",
                related_name="activities",
                to="methodology.rule",
            ),
        ),
    ]
