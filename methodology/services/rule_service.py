"""Service layer for playbook-scoped Rule operations."""

import logging
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Count, Q, QuerySet
from django.utils.text import slugify

from methodology.models import Rule

logger = logging.getLogger(__name__)


class RuleService:
    """Playbook-scoped rules (IDE-style), M2M with activities."""

    MAX_TITLE_LENGTH = 200
    ALLOWED_UPDATE_FIELDS = {'title', 'content', 'slug', 'always_apply'}

    @staticmethod
    def create_rule(
        playbook,
        title: str,
        content: str = '',
        slug: str = '',
        always_apply: bool = True,
    ):
        """Create a rule in a playbook."""
        RuleService._validate_title(title)
        slug_clean = RuleService._normalize_slug(slug, title, playbook.id)
        rule = Rule.objects.create(
            playbook=playbook,
            title=title.strip(),
            slug=slug_clean,
            content=content.strip() if content else '',
            always_apply=always_apply,
        )
        logger.info(
            "Created rule '%s' (id=%s, slug=%s) in playbook %s",
            rule.title, rule.id, rule.slug, playbook.id,
        )
        return rule

    @staticmethod
    def get_rule(rule_id: int):
        """Get rule by ID with playbook prefetched."""
        return Rule.objects.select_related('playbook').get(pk=rule_id)

    @staticmethod
    def list_rules_for_playbook(
        playbook_id: int,
        search: str = '',
        unlinked_only: bool = False,
    ) -> QuerySet:
        """List rules with optional search and unlinked-only filter."""
        qs = Rule.objects.filter(playbook_id=playbook_id).select_related('playbook').annotate(
            activity_count=Count('activities', distinct=True)
        )
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(slug__icontains=search)
                | Q(content__icontains=search)
            )
        if unlinked_only:
            qs = qs.filter(activity_count=0)
        return qs.order_by('slug')

    @staticmethod
    def search_rules(query: str, user=None) -> QuerySet:
        """Global search for rules in owned playbooks."""
        qs = Rule.objects.select_related('playbook')
        if user is not None:
            qs = qs.filter(playbook__author=user, playbook__source='owned')
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(slug__icontains=query)
                | Q(content__icontains=query)
            )
        return qs.order_by('playbook__name', 'slug')

    @staticmethod
    def update_rule(rule_id: int, **kwargs):
        """Update allowed fields on a rule."""
        rule = Rule.objects.get(pk=rule_id)
        unknown = set(kwargs.keys()) - RuleService.ALLOWED_UPDATE_FIELDS
        if unknown:
            raise ValidationError(f'Cannot update fields: {unknown}')
        if 'title' in kwargs:
            RuleService._validate_title(kwargs['title'])
            kwargs['title'] = kwargs['title'].strip()
        if 'content' in kwargs:
            kwargs['content'] = kwargs['content'].strip() if kwargs['content'] else ''
        if 'slug' in kwargs:
            kwargs['slug'] = RuleService._normalize_slug(
                kwargs['slug'], kwargs.get('title', rule.title), rule.playbook_id, exclude_pk=rule.pk
            )
        for field, value in kwargs.items():
            setattr(rule, field, value)
        rule.save()
        logger.info('Updated rule %s: %s', rule_id, ', '.join(kwargs.keys()))
        return rule

    @staticmethod
    def delete_rule(rule_id: int) -> None:
        """Delete rule (M2M cleared by Django)."""
        rule = Rule.objects.get(pk=rule_id)
        title, rid = rule.title, rule.id
        rule.delete()
        logger.info('Deleted rule id=%s title=%s', rid, title)

    @staticmethod
    def get_activities_for_rule(rule_id: int):
        """Activities linked to this rule."""
        from methodology.models import Activity

        return (
            Activity.objects.filter(rules__id=rule_id)
            .select_related('workflow')
            .order_by('workflow__name', 'order', 'name')
        )

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise ValidationError('Rule title cannot be empty')
        if len(title) > RuleService.MAX_TITLE_LENGTH:
            raise ValidationError(f'Rule title cannot exceed {RuleService.MAX_TITLE_LENGTH} characters')

    @staticmethod
    def _normalize_slug(slug: str, title: str, playbook_id: int, exclude_pk: Optional[int] = None) -> str:
        """Build unique slug within playbook."""
        raw = (slug or '').strip()
        if not raw:
            raw = slugify(title)[:200] or 'rule'
        base = slugify(raw)[:200] or 'rule'
        candidate = base
        n = 2
        qs = Rule.objects.filter(playbook_id=playbook_id, slug=candidate)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        while qs.exists():
            suffix = f'-{n}'
            candidate = (base[: (220 - len(suffix))] + suffix) if len(base) + len(suffix) > 220 else base + suffix
            candidate = candidate.strip('-')[:220]
            qs = Rule.objects.filter(playbook_id=playbook_id, slug=candidate)
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            n += 1
        return candidate
