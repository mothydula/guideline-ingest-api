"""
Django models for the guideline ingest application.
"""
from django.db import models
import uuid


class JobStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'


class Job(models.Model):
    """Model to track guideline ingest jobs."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING
    )
    guideline_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # GPT chain results
    summary = models.TextField(blank=True, null=True)
    checklist = models.JSONField(blank=True, null=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'jobs'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Job {self.id} - {self.status}"
    
    @property
    def result(self):
        """Return the result data if job is completed."""
        if self.status == JobStatus.COMPLETED and self.summary and self.checklist:
            return {
                'summary': self.summary,
                'checklist': self.checklist
            }
        return None