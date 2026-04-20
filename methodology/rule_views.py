"""Rule views — playbook-scoped CRUDLF (mirror skills)."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from methodology.models import Playbook, Rule
from methodology.services.rule_service import RuleService

logger = logging.getLogger(__name__)


def _get_playbook_or_deny(request, playbook_pk):
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    if playbook.source == 'owned' and playbook.author != request.user:
        logger.warning(
            'User %s denied access to playbook %s',
            request.user.username,
            playbook_pk,
        )
        messages.error(request, "You don't have permission to access this playbook.")
        return None
    return playbook


def _get_rule_in_playbook(playbook, rule_pk):
    return get_object_or_404(Rule, pk=rule_pk, playbook=playbook)


@login_required
def rule_list_global(request):
    """Global rules list for owned playbooks."""
    query = request.GET.get('q', '').strip()
    rules = RuleService.search_rules(query=query, user=request.user)
    total_count = RuleService.search_rules(query='', user=request.user).count()
    logger.info(
        'User %s viewing global rule list%s',
        request.user.username,
        f', query={query!r}' if query else '',
    )
    return render(
        request,
        'rules/list.html',
        {'rules': rules, 'query': query, 'total_count': total_count},
    )


@login_required
def rule_list(request, playbook_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')

    query = request.GET.get('q', '').strip()
    unlinked_only = request.GET.get('unlinked') == '1'
    rules = RuleService.list_rules_for_playbook(
        playbook_id=playbook_pk,
        search=query,
        unlinked_only=unlinked_only,
    )
    logger.info(
        'User %s listing rules in playbook %s',
        request.user.username,
        playbook_pk,
    )
    return render(
        request,
        'rules/playbook_list.html',
        {
            'playbook': playbook,
            'rules': rules,
            'query': query,
            'unlinked_only': unlinked_only,
            'can_edit': playbook.can_edit(request.user),
        },
    )


@login_required
def rule_create(request, playbook_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')
    if not playbook.can_edit(request.user):
        messages.error(request, "You don't have permission to create rules in this playbook.")
        return redirect('playbook_list')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        content = request.POST.get('content', '').strip()
        always_apply = request.POST.get('always_apply') == 'on'

        try:
            rule = RuleService.create_rule(
                playbook=playbook,
                title=title,
                content=content,
                slug=slug,
                always_apply=always_apply,
            )
            messages.success(request, f"Rule '{rule.title}' created successfully!")
            return redirect('rule_detail', playbook_pk=playbook_pk, rule_pk=rule.pk)
        except ValidationError as e:
            logger.warning('Rule create validation error: %s', e)
            err = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
            fd = request.POST.copy()
            fd['always_apply'] = request.POST.get('always_apply') == 'on'
            return _render_create_form(request, playbook, fd, {'title': err})

    return _render_create_form(request, playbook, {'always_apply': True}, {})


@login_required
def rule_detail(request, playbook_pk, rule_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')

    rule = _get_rule_in_playbook(playbook, rule_pk)
    activities = RuleService.get_activities_for_rule(rule_pk)

    return render(
        request,
        'rules/detail.html',
        {
            'playbook': playbook,
            'rule': rule,
            'activities': activities,
            'can_edit': playbook.can_edit(request.user),
        },
    )


@login_required
def rule_edit(request, playbook_pk, rule_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')
    if not playbook.can_edit(request.user):
        messages.error(request, "You don't have permission to edit rules in this playbook.")
        return redirect('playbook_list')

    rule = _get_rule_in_playbook(playbook, rule_pk)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        content = request.POST.get('content', '').strip()
        always_apply = request.POST.get('always_apply') == 'on'

        try:
            RuleService.update_rule(
                rule.pk,
                title=title,
                slug=slug,
                content=content,
                always_apply=always_apply,
            )
            messages.success(request, f"Rule '{title}' updated successfully!")
            return redirect('rule_detail', playbook_pk=playbook_pk, rule_pk=rule.pk)
        except ValidationError as e:
            err = e.messages[0] if hasattr(e, 'messages') and e.messages else str(e)
            return _render_edit_form(request, playbook, rule, request.POST, {'title': err})

    form_data = {
        'title': rule.title,
        'slug': rule.slug,
        'content': rule.content,
        'always_apply': rule.always_apply,
    }
    return _render_edit_form(request, playbook, rule, form_data, {})


@login_required
def rule_delete_confirm(request, playbook_pk, rule_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')

    rule = _get_rule_in_playbook(playbook, rule_pk)
    activities = RuleService.get_activities_for_rule(rule_pk)
    delete_url = reverse(
        'rule_delete',
        kwargs={'playbook_pk': playbook_pk, 'rule_pk': rule_pk},
    )
    return render(
        request,
        'rules/_delete_modal.html',
        {
            'playbook': playbook,
            'rule': rule,
            'activities': activities,
            'delete_url': delete_url,
        },
    )


@login_required
def rule_delete(request, playbook_pk, rule_pk):
    playbook = _get_playbook_or_deny(request, playbook_pk)
    if playbook is None:
        return redirect('playbook_list')
    if not playbook.can_edit(request.user):
        messages.error(request, "You don't have permission to delete rules in this playbook.")
        return redirect('playbook_list')

    rule = _get_rule_in_playbook(playbook, rule_pk)
    title = rule.title
    RuleService.delete_rule(rule.pk)
    messages.success(request, f"Rule '{title}' deleted.")
    return redirect('rule_list_playbook', playbook_pk=playbook_pk)


def _render_create_form(request, playbook, form_data, errors):
    return render(
        request,
        'rules/create.html',
        {'playbook': playbook, 'form_data': form_data, 'errors': errors},
    )


def _render_edit_form(request, playbook, rule, form_data, errors):
    return render(
        request,
        'rules/edit.html',
        {
            'playbook': playbook,
            'rule': rule,
            'form_data': form_data,
            'errors': errors,
        },
    )
