"""
Integration tests for group-based playbook sharing.

Tests that group membership grants read access to shared playbooks.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from methodology.models import Playbook

User = get_user_model()


@pytest.mark.django_db
class TestGroupBasedSharing:
    """Test group-based playbook sharing."""

    def test_owner_can_share_playbook_with_group(self):
        """Owner should be able to share playbook with groups."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=owner)
        
        # Create a group
        group = Group.objects.create(name='Team Alpha')
        
        # Create playbook
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Share with group
        response = client.put(f'/api/playbooks/{playbook.id}/share/', {
            'group_ids': [group.id]
        }, format='json')
        
        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['shared_with_groups'][0]['id'] == group.id
        
        # Verify in DB
        playbook.refresh_from_db()
        assert list(playbook.shared_with_groups.all()) == [group]

    def test_non_owner_cannot_share_playbook(self):
        """Non-owner should not be able to share playbook."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=other_user)
        
        group = Group.objects.create(name='Team Alpha')
        
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Try to share (should fail)
        response = client.put(f'/api/playbooks/{playbook.id}/share/', {
            'group_ids': [group.id]
        }, format='json')
        
        assert response.status_code == 404  # Not in queryset

    def test_group_member_can_read_shared_playbook(self):
        """Group member should be able to read shared playbook."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=member)
        
        # Create group and add member
        group = Group.objects.create(name='Team Alpha')
        member.groups.add(group)
        
        # Create playbook and share with group
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        playbook.shared_with_groups.add(group)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Member should see playbook in list
        response = client.get('/api/playbooks/')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == playbook.id
        
        # Member should be able to retrieve playbook
        response = client.get(f'/api/playbooks/{playbook.id}/')
        assert response.status_code == 200
        assert response.data['id'] == playbook.id

    def test_group_member_cannot_modify_shared_playbook(self):
        """Group member should NOT be able to modify shared playbook."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=member)
        
        # Create group and add member
        group = Group.objects.create(name='Team Alpha')
        member.groups.add(group)
        
        # Create playbook and share with group
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        playbook.shared_with_groups.add(group)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Try to update (should fail)
        response = client.patch(f'/api/playbooks/{playbook.id}/', {
            'name': 'Modified Name'
        }, format='json')
        
        assert response.status_code == 403
        assert 'error' in response.data or 'detail' in response.data

    def test_non_group_member_cannot_see_shared_playbook(self):
        """User not in group should NOT see shared playbook."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        outsider = User.objects.create_user(
            username='outsider',
            email='outsider@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=outsider)
        
        # Create group (outsider not a member)
        group = Group.objects.create(name='Team Alpha')
        
        # Create playbook and share with group
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        playbook.shared_with_groups.add(group)
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Outsider should NOT see playbook in list
        response = client.get('/api/playbooks/')
        assert response.status_code == 200
        assert len(response.data['results']) == 0
        
        # Outsider should NOT be able to retrieve playbook
        response = client.get(f'/api/playbooks/{playbook.id}/')
        assert response.status_code == 404

    def test_share_with_multiple_groups(self):
        """Owner should be able to share with multiple groups."""
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='pass123'
        )
        token = Token.objects.create(user=owner)
        
        # Create multiple groups
        group1 = Group.objects.create(name='Team Alpha')
        group2 = Group.objects.create(name='Team Beta')
        
        playbook = Playbook.objects.create(
            author=owner,
            name='Shared Playbook',
            description='Test',
            category='development',
            status='draft',
            version='0.1'
        )
        
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Share with both groups
        response = client.put(f'/api/playbooks/{playbook.id}/share/', {
            'group_ids': [group1.id, group2.id]
        }, format='json')
        
        assert response.status_code == 200
        assert response.data['count'] == 2
        
        # Verify in DB
        playbook.refresh_from_db()
        shared_groups = list(playbook.shared_with_groups.all())
        assert len(shared_groups) == 2
        assert group1 in shared_groups
        assert group2 in shared_groups
