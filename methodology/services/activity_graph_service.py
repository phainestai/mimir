"""
Activity Graph Service for Graphviz visualization.

Generates SVG flow diagrams of activities within workflows using Graphviz.
Supports phase grouping, clickable nodes, and status-based styling.
"""

import logging
import graphviz
from django.conf import settings
from django.urls import reverse
from methodology.models import Activity

logger = logging.getLogger(__name__)


def _graphviz_fontname():
    """Return Graphviz fontname for the active UI brand pack.

    :returns: Font family name string for Graphviz ``fontname``.
    """
    brand = (getattr(settings, 'UI_BRAND', '') or '').strip().lower()
    if brand == 'professional':
        return 'IBM Plex Sans'
    return 'Montserrat'


class ActivityGraphService:
    """
    Service for generating Graphviz-based activity flow diagrams.
    
    Provides visual representation of activities with:
    - Sequential flow arrows
    - Phase grouping (if phases exist)
    - Clickable nodes linking to activity detail
    - Dependency indicators
    
    Note: Activities are static reference material (like a book).
    No status tracking - work tracking happens in external systems.
    """
    
    def generate_activities_graph(self, workflow, playbook):
        """
        Generate Graphviz flow diagram of activities in a workflow.
        
        Creates an SVG representation showing:
        - Activities as nodes with name
        - Sequential flow based on order field
        - Phase grouping using Graphviz subgraph clusters
        - Clickable nodes with href to activity detail
        
        :param workflow: Workflow instance containing activities
        :type workflow: methodology.models.Workflow
        :param playbook: Playbook instance (parent of workflow, used for URL generation)
        :type playbook: methodology.models.Playbook
        :return: SVG markup as string, or None if no activities exist
        :rtype: str or None
        :raises graphviz.backend.ExecutableNotFound: If Graphviz is not installed on system
        
        Example usage:
            >>> service = ActivityGraphService()
            >>> svg = service.generate_activities_graph(workflow, playbook)
            >>> # Returns: "<svg width='800' height='600'>...</svg>"
        
        Example with no activities:
            >>> svg = service.generate_activities_graph(empty_workflow, playbook)
            >>> # Returns: None
        """
        logger.info(f"Generating activity graph for workflow {workflow.pk}")
        
        # Fetch activities for workflow
        activities = Activity.objects.filter(workflow=workflow).order_by('order')
        
        if not activities.exists():
            logger.info(f"No activities found for workflow {workflow.pk}")
            return None
        
        try:
            # Graphviz font follows UI brand (stock Montserrat / professional IBM Plex).
            graph_font = _graphviz_fontname()
            logger.info(
                "Activity graph font set to %s for workflow %s (ui_brand=%s)",
                graph_font,
                workflow.pk,
                getattr(settings, 'UI_BRAND', ''),
            )
            dot = graphviz.Digraph(comment=f'{workflow.name} Activities')
            dot.attr(rankdir='LR', fontname=graph_font)  # Left to right; graph/cluster labels
            dot.attr('node', shape='box', style='filled,rounded', fontname=graph_font)
            dot.attr('edge', fontname=graph_font)
            
            # Check if activities have phases
            has_phases = self._has_phases(activities)
            
            if has_phases:
                # Group activities by phase
                phase_groups = self._group_activities_by_phase(activities)
                
                # Create subgraph cluster for each phase
                for phase_name, phase_activities in phase_groups.items():
                    cluster_name = f'cluster_{phase_name.lower().replace(" ", "_")}'
                    with dot.subgraph(name=cluster_name) as subg:
                        subg.attr(
                            label=phase_name,
                            style='filled',
                            color='lightgrey',
                            fontname=graph_font,
                        )
                        
                        # Add activity nodes within this phase
                        for activity in phase_activities:
                            self._add_activity_node(subg, activity, playbook, workflow)
            else:
                # No phases - add all activities directly
                for activity in activities:
                    self._add_activity_node(dot, activity, playbook, workflow)
            
            # Add edges based on predecessor relationships (source of truth for flow order).
            # The successor FK is rarely populated; predecessor_id is always set by set_predecessor.
            for activity in activities:
                if activity.predecessor_id:
                    dot.edge(
                        f'activity_{activity.predecessor_id}',
                        f'activity_{activity.pk}',
                        label='',
                        color='blue',
                        penwidth='2.0'
                    )
                    logger.debug(f"Added edge: {activity.predecessor.reference_name} -> {activity.reference_name}")
            
            # Generate SVG
            svg_bytes = dot.pipe(format='svg')
            svg_str = svg_bytes.decode('utf-8')
            
            logger.info(f"Generated SVG graph for workflow {workflow.pk} with {activities.count()} activities")
            return svg_str
            
        except Exception as e:
            logger.error(f"Error generating activity graph for workflow {workflow.pk}: {str(e)}")
            raise
    
    
    def _create_activity_node_label(self, activity):
        """
        Create formatted label for activity node.
        
        Format: "{reference_name}\\n{activity.name}"
        
        :param activity: Activity instance
        :type activity: methodology.models.Activity
        :return: Formatted label string
        :rtype: str
        
        Example:
            >>> label = service._create_activity_node_label(activity)
            >>> # Returns: "DFS1\\nDesign Component"
        """
        # Include reference name (e.g., "DFS1") in label
        label = f"{activity.reference_name}\\n{activity.name}"
        return label
    
    def _get_activity_detail_url(self, activity, playbook, workflow):
        """
        Generate URL to activity detail page.
        
        :param activity: Activity instance
        :type activity: methodology.models.Activity
        :param playbook: Playbook instance
        :type playbook: methodology.models.Playbook
        :param workflow: Workflow instance
        :type workflow: methodology.models.Workflow
        :return: Full URL path to activity detail
        :rtype: str
        
        Example:
            >>> url = service._get_activity_detail_url(activity, playbook, workflow)
            >>> # Returns: "/playbooks/1/workflows/2/activities/3/"
        """
        return reverse('activity_detail', kwargs={
            'playbook_pk': playbook.pk,
            'workflow_pk': workflow.pk,
            'activity_pk': activity.pk
        })
    
    def _has_phases(self, activities):
        """
        Check if any activity has a phase assigned.
        
        :param activities: QuerySet or list of Activity instances
        :type activities: django.db.models.QuerySet or list
        :return: True if at least one activity has phase field set
        :rtype: bool
        
        Example:
            >>> service._has_phases([activity1, activity2])
            True  # If any has phase != None
        """
        return any(activity.phase for activity in activities)
    
    def _group_activities_by_phase(self, activities):
        """
        Group activities by their phase field.
        
        Returns dict with phase names as keys and lists of activities as values.
        Activities without phase go into 'Unassigned' group.
        
        :param activities: QuerySet or list of Activity instances
        :type activities: django.db.models.QuerySet or list
        :return: Dict mapping phase names to activity lists
        :rtype: dict
        
        Example:
            >>> groups = service._group_activities_by_phase(activities)
            >>> # Returns: {'Planning': [act1, act2], 'Execution': [act3]}
        """
        phase_groups = {}
        for activity in activities:
            phase_name = activity.phase.name if activity.phase else 'Unassigned'
            if phase_name not in phase_groups:
                phase_groups[phase_name] = []
            phase_groups[phase_name].append(activity)
        return phase_groups
    
    def _add_activity_node(self, graph, activity, playbook, workflow):
        """
        Add activity node to Graphviz graph with styling and href.
        
        :param graph: Graphviz graph or subgraph instance
        :param activity: Activity instance to add
        :param playbook: Playbook instance for URL generation
        :param workflow: Workflow instance for URL generation
        """
        node_id = f'activity_{activity.pk}'
        label = self._create_activity_node_label(activity)
        url = self._get_activity_detail_url(activity, playbook, workflow)
        
        # Use uniform color - activities are static reference material
        graph.node(
            node_id,
            label=label,
            fillcolor='lightblue',  # Uniform color for all activities
            href=url,
            target='_top'  # Opens in full page, not iframe
        )
