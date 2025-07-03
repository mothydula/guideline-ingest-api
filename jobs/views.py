"""
Django views for the guideline ingest API.
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import get_object_or_404

from .models import Job, JobStatus
from .serializers import (
    JobCreateSerializer, 
    JobCreateResponseSerializer,
    JobStatusResponseSerializer,
    JobSerializer
)
from .tasks import process_guideline_task

@extend_schema(
    request=JobCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=JobCreateResponseSerializer,
            description="Job created successfully"
        ),
        400: OpenApiResponse(description="Invalid request data"),
    },
    summary="Create a new guideline ingest job",
    description="Creates a new job to process guideline text through GPT chain analysis"
)
@api_view(['POST'])
def create_job(request):
    """
    Create a new guideline ingest job.
    
    Places a job on the queue for processing and returns an event_id.
    """
    serializer = JobCreateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create job in database
    job = Job.objects.create(
        guideline_text=serializer.validated_data['guideline_text'],
        status=JobStatus.PENDING
    )
    
    # Queue the processing task
    process_guideline_task.delay(str(job.id))
    
    # Return response
    response_data = {
        'event_id': job.id,
        'status': job.status
    }
    
    return Response(
        response_data,
        status=status.HTTP_201_CREATED
    )

@extend_schema(
    responses={
        200: OpenApiResponse(
            response=JobStatusResponseSerializer,
            description="Job status retrieved successfully"
        ),
        404: OpenApiResponse(description="Job not found"),
    },
    summary="Get job status and results",
    description="Retrieves the current status and results (if available) for a job"
)
@api_view(['GET'])
def get_job_status(request, event_id):
    """
    Get the status and results of a job.
    
    Returns job status and result data if the job is completed.
    """
    job = get_object_or_404(Job, id=event_id)
    
    serializer = JobSerializer(job)
    
    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )