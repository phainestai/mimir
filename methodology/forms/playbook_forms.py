"""
Forms for Playbook creation wizard.

Three-step wizard:
- Step 1: Basic Information (name, description, category, tags, visibility)
- Step 2: Add Workflows (optional workflow creation)
- Step 3: Publishing (status selection and final review)
"""

from django import forms
from methodology.models import Playbook, Workflow


class PlaybookBasicInfoForm(forms.ModelForm):
    """
    Step 1: Basic Information form.
    
    Collects name, description, category, tags, and visibility.
    All fields except tags are required.
    """
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter tags separated by commas',
            'data-testid': 'tags-input'
        }),
        help_text='Comma-separated tags (optional)'
    )
    
    class Meta:
        model = Playbook
        fields = ['name', 'description', 'category', 'visibility']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter playbook name (3-100 characters)',
                'data-testid': 'name-input'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Enter playbook description (10-500 characters)',
                'data-testid': 'description-input'
            }),
            'category': forms.Select(attrs={
                'data-testid': 'category-select'
            }),
            'visibility': forms.Select(attrs={
                'data-testid': 'visibility-select'
            }),
        }
        error_messages = {
            'name': {
                'required': 'Name is required. Must be 3-100 characters.',
            },
            'description': {
                'required': 'Description is required. Must be 10-500 characters.',
            },
            'category': {
                'required': 'Please select a category.',
            },
        }
    
    def clean_name(self):
        """Validate name length and uniqueness."""
        name = self.cleaned_data.get('name', '')
        
        if not name:
            raise forms.ValidationError(
                'Name is required. Must be 3-100 characters.'
            )
        
        # Length validation
        if len(name) < 3:
            raise forms.ValidationError(
                'Name is required. Must be 3-100 characters.'
            )
        if len(name) > 100:
            raise forms.ValidationError(
                'Name is required. Must be 3-100 characters.'
            )
        
        return name
    
    def clean_description(self):
        """Validate description length."""
        description = self.cleaned_data.get('description', '')
        
        if not description or len(description) < 10:
            raise forms.ValidationError(
                'Description is required. Must be 10-500 characters.'
            )
        if len(description) > 500:
            raise forms.ValidationError(
                'Description is required. Must be 10-500 characters.'
            )
        
        return description
    
    def clean_tags(self):
        """Parse and clean tags from comma-separated string."""
        tags_str = self.cleaned_data.get('tags', '')
        
        if not tags_str:
            return []
        
        # Split by comma and clean each tag
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        return tags


class PlaybookWorkflowForm(forms.Form):
    """
    Step 2: Add Workflows form.
    
    Optional form for adding first workflow inline.
    User can skip this step.
    """
    
    workflow_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter workflow name',
            'data-testid': 'workflow-name-input'
        }),
        help_text='Name of the workflow (optional)'
    )
    
    workflow_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Enter workflow description',
            'data-testid': 'workflow-description-input'
        }),
        help_text='Brief description of the workflow (optional)'
    )
    
    skip = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    def clean(self):
        """Validate that if name is provided, it's not empty."""
        cleaned_data = super().clean()
        workflow_name = cleaned_data.get('workflow_name', '').strip()
        skip = cleaned_data.get('skip', False)
        
        # If not skipping and name provided, ensure it's valid
        if not skip and workflow_name and len(workflow_name) < 3:
            raise forms.ValidationError(
                'Workflow name must be at least 3 characters if provided.'
            )
        
        return cleaned_data


class PlaybookPublishingForm(forms.Form):
    """
    Step 3: Publishing form.

    Draft (v0.1) is editable via GUI/MCP; released (v1.0) is read-only except PIP.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('released', 'Released'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial='draft',
        widget=forms.RadioSelect(attrs={
            'data-testid': 'status-radio',
        }),
        help_text='Draft playbooks are editable; released playbooks require a PIP for changes.',
    )

    def clean_status(self):
        """Validate status choice."""
        status = self.cleaned_data.get('status')

        if status not in ('draft', 'released'):
            raise forms.ValidationError('Invalid status selected.')

        return status
