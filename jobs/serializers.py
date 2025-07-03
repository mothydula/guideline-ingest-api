"""
Django REST Framework serializers for the guideline ingest API.
"""
from rest_framework import serializers
from .models import Job, JobStatus


class JobCreateSerializer(serializers.Serializer):
    """Serializer for creating new jobs."""
    
    guideline_text = serializers.CharField(
        max_length=50000,
        help_text="The guideline text to process (max 50,000 characters)"
    )
    
    def validate_guideline_text(self, value):
        """Validate that guideline text is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Guideline text cannot be empty.")
        return value.strip()


class JobCreateResponseSerializer(serializers.Serializer):
    """Serializer for job creation response."""
    
    event_id = serializers.UUIDField(
        help_text="Unique identifier for the created job"
    )
    status = serializers.ChoiceField(
        choices=JobStatus.choices,
        help_text="Current status of the job"
    )


class JobResultSerializer(serializers.Serializer):
    """Serializer for job result data."""
    
    summary = serializers.CharField(
        help_text="Summary of the guideline text"
    )
    checklist = serializers.JSONField(
        help_text="Generated checklist based on the guidelines"
    )


class JobStatusResponseSerializer(serializers.Serializer):
    """Serializer for job status response."""
    
    event_id = serializers.UUIDField(
        help_text="Unique identifier for the job"
    )
    status = serializers.ChoiceField(
        choices=JobStatus.choices,
        help_text="Current status of the job"
    )
    result = JobResultSerializer(
        required=False,
        allow_null=True,
        help_text="Job result data (only present when status is 'completed')"
    )
    error_message = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Error message if job failed"
    )
    created_at = serializers.DateTimeField(
        help_text="When the job was created"
    )
    updated_at = serializers.DateTimeField(
        help_text="When the job was last updated"
    )


class JobSerializer(serializers.ModelSerializer):
    """Main serializer for Job model."""
    
    event_id = serializers.UUIDField(source='id', read_only=True)
    result = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'event_id', 
            'status', 
            'result', 
            'error_message',
            'created_at', 
            'updated_at'
        ]
    
    def get_result(self, obj):
        """Get the result data for completed jobs."""
        return obj.result