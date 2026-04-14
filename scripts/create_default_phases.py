#!/usr/bin/env python
"""
One-time script to create 5 standard lifecycle phases for a playbook.

Usage:
    python scripts/create_default_phases.py <playbook_id>

Example:
    python scripts/create_default_phases.py 1
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimir.settings')
django.setup()

from methodology.services.phase_service import PhaseService


# Standard 5 phases for software development lifecycle
STANDARD_PHASES = [
    {
        'name': 'Planning',
        'description': 'Initial planning, requirements gathering, and design phase',
        'order': 1
    },
    {
        'name': 'Foundation',
        'description': 'Setup infrastructure, architecture, and foundational components',
        'order': 2
    },
    {
        'name': 'Implementation',
        'description': 'Core development and feature implementation',
        'order': 3
    },
    {
        'name': 'Testing',
        'description': 'Quality assurance, testing, and validation',
        'order': 4
    },
    {
        'name': 'Deployment',
        'description': 'Release preparation, deployment, and go-live activities',
        'order': 5
    }
]


def create_default_phases(playbook_id: int):
    """
    Create 5 standard phases for a playbook.
    
    :param playbook_id: Playbook ID
    """
    from methodology.models import Playbook
    
    # Get playbook and its owner
    try:
        playbook = Playbook.objects.get(id=playbook_id)
        user = playbook.author
    except Playbook.DoesNotExist:
        print(f"✗ Error: Playbook {playbook_id} not found")
        return []
    
    print(f"Creating 5 standard phases for playbook {playbook_id} (owner: {user.username})...")
    
    created_phases = []
    for phase_data in STANDARD_PHASES:
        try:
            phase = PhaseService.create_phase(
                playbook_id=playbook_id,
                name=phase_data['name'],
                description=phase_data['description'],
                order=phase_data['order'],
                user=user
            )
            created_phases.append(phase)
            print(f"✓ Created phase: {phase.name} (ID: {phase.id})")
        except Exception as e:
            print(f"✗ Failed to create phase '{phase_data['name']}': {str(e)}")
    
    print(f"\nSuccessfully created {len(created_phases)} phases!")
    return created_phases


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python scripts/create_default_phases.py <playbook_id>")
        print("Example: python scripts/create_default_phases.py 1")
        sys.exit(1)
    
    try:
        playbook_id = int(sys.argv[1])
    except ValueError:
        print("Error: playbook_id must be an integer")
        sys.exit(1)
    
    create_default_phases(playbook_id)
