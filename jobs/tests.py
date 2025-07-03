"""
Unit tests for the guideline ingest application.
"""
import json
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Job, JobStatus
from .tasks import GPTChainProcessor, process_guideline_task


class JobModelTest(TestCase):
    """Test cases for the Job model."""
    
    def setUp(self):
        self.job = Job.objects.create(
            guideline_text="Test guideline text",
            status=JobStatus.PENDING
        )
    
    def test_job_creation(self):
        """Test that a job is created correctly."""
        self.assertEqual(self.job.guideline_text, "Test guideline text")
        self.assertEqual(self.job.status, JobStatus.PENDING)
        self.assertIsNotNone(self.job.id)
        self.assertIsNotNone(self.job.created_at)
        self.assertIsNotNone(self.job.updated_at)
    
    def test_job_str_method(self):
        """Test the string representation of a job."""
        expected = f"Job {self.job.id} - {self.job.status}"
        self.assertEqual(str(self.job), expected)
    
    def test_job_result_property_pending(self):
        """Test that result is None for pending jobs."""
        self.assertIsNone(self.job.result)
    
    def test_job_result_property_completed(self):
        """Test that result is returned for completed jobs."""
        self.job.status = JobStatus.COMPLETED
        self.job.summary = "Test summary"
        self.job.checklist = [{"item": "Test item", "description": "Test description"}]
        self.job.save()
        
        expected_result = {
            'summary': "Test summary",
            'checklist': [{"item": "Test item", "description": "Test description"}]
        }
        self.assertEqual(self.job.result, expected_result)


class JobAPITest(APITestCase):
    """Test cases for the Job API endpoints."""
    
    def setUp(self):
        self.create_job_url = reverse('jobs:create_job')
        self.job_data = {
            'guideline_text': 'This is a test guideline text for processing.'
        }
    
    def test_create_job_success(self):
        """Test successful job creation."""
        response = self.client.post(self.create_job_url, self.job_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('event_id', response.data)
        self.assertEqual(response.data['status'], JobStatus.PENDING)
        
        # Verify job was created in database
        job = Job.objects.get(id=response.data['event_id'])
        self.assertEqual(job.guideline_text, self.job_data['guideline_text'])
        self.assertEqual(job.status, JobStatus.PENDING)
    
    def test_create_job_invalid_data(self):
        """Test job creation with invalid data."""
        invalid_data = {'guideline_text': ''}
        response = self.client.post(self.create_job_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guideline_text', response.data)
    
    def test_create_job_missing_data(self):
        """Test job creation with missing required data."""
        response = self.client.post(self.create_job_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('guideline_text', response.data)
    
    def test_get_job_status_success(self):
        """Test successful job status retrieval."""
        # Create a job
        job = Job.objects.create(
            guideline_text="Test guideline",
            status=JobStatus.COMPLETED,
            summary="Test summary",
            checklist=[{"item": "Test item", "description": "Test description"}]
        )
        
        url = reverse('jobs:get_job_status', kwargs={'event_id': job.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], str(job.id))
        self.assertEqual(response.data['status'], JobStatus.COMPLETED)
        self.assertIsNotNone(response.data['result'])
        self.assertIn('summary', response.data['result'])
        self.assertIn('checklist', response.data['result'])
    
    def test_get_job_status_not_found(self):
        """Test job status retrieval for non-existent job."""
        non_existent_id = uuid.uuid4()
        url = reverse('jobs:get_job_status', kwargs={'event_id': non_existent_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_job_status_pending(self):
        """Test job status retrieval for pending job."""
        job = Job.objects.create(
            guideline_text="Test guideline",
            status=JobStatus.PENDING
        )
        
        url = reverse('jobs:get_job_status', kwargs={'event_id': job.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], JobStatus.PENDING)
        self.assertIsNone(response.data['result'])


class GPTChainProcessorTest(TestCase):
    """Test cases for the GPTChainProcessor."""
    
    @patch('jobs.tasks.OpenAI')
    def test_summarize_guideline_success(self, mock_openai):
        """Test successful guideline summarization."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is a test summary."
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        processor = GPTChainProcessor()
        result = processor.summarize_guideline("Test guideline text")
        
        self.assertEqual(result, "This is a test summary.")
        mock_openai.return_value.chat.completions.create.assert_called_once()
    
    @patch('jobs.tasks.OpenAI')
    def test_generate_checklist_success(self, mock_openai):
        """Test successful checklist generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            {"item": "Test item 1", "description": "Test description 1"},
            {"item": "Test item 2", "description": "Test description 2"}
        ])
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        processor = GPTChainProcessor()
        result = processor.generate_checklist("Test summary")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['item'], "Test item 1")
        self.assertEqual(result[1]['item'], "Test item 2")
    
    @patch('jobs.tasks.OpenAI')
    def test_generate_checklist_invalid_json(self, mock_openai):
        """Test checklist generation with invalid JSON response."""
        # Mock OpenAI response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        processor = GPTChainProcessor()
        result = processor.generate_checklist("Test summary")
        
        # Should fallback to simple structure
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['item'], "Review guidelines")
        self.assertEqual(result[0]['description'], "Invalid JSON response")


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ProcessGuidelineTaskTest(TestCase):
    """Test cases for the process_guideline_task."""
    
    def setUp(self):
        self.job = Job.objects.create(
            guideline_text="Test guideline text for processing",
            status=JobStatus.PENDING
        )
    
    @patch('jobs.tasks.GPTChainProcessor')
    def test_process_guideline_task_success(self, mock_processor_class):
        """Test successful guideline processing task."""
        # Mock processor
        mock_processor = MagicMock()
        mock_processor.summarize_guideline.return_value = "Test summary"
        mock_processor.generate_checklist.return_value = [
            {"item": "Test item", "description": "Test description"}
        ]
        mock_processor_class.return_value = mock_processor
        
        # Execute task
        result = process_guideline_task(str(self.job.id))
        
        # Verify result
        self.assertEqual(result['status'], 'completed')
        self.assertIn('job_id', result)
        
        # Verify job was updated
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.COMPLETED)
        self.assertEqual(self.job.summary, "Test summary")
        self.assertIsNotNone(self.job.checklist)
    
    @patch('jobs.tasks.GPTChainProcessor')
    def test_process_guideline_task_failure(self, mock_processor_class):
        """Test guideline processing task failure."""
        # Mock processor to raise exception
        mock_processor = MagicMock()
        mock_processor.summarize_guideline.side_effect = Exception("API Error")
        mock_processor_class.return_value = mock_processor
        
        # Execute task (should handle exception)
        with self.assertRaises(Exception):
            process_guideline_task(str(self.job.id))
        
        # Verify job was marked as failed
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.FAILED)
        self.assertIsNotNone(self.job.error_message)
    
    def test_process_guideline_task_nonexistent_job(self):
        """Test processing task with non-existent job."""
        non_existent_id = str(uuid.uuid4())
        
        with self.assertRaises(Job.DoesNotExist):
            process_guideline_task(non_existent_id)


class JobStatusChoicesTest(TestCase):
    """Test cases for JobStatus choices."""
    
    def test_job_status_choices(self):
        """Test that all job status choices are valid."""
        valid_statuses = [choice[0] for choice in JobStatus.choices]
        expected_statuses = ['pending', 'processing', 'completed', 'failed']
        
        self.assertEqual(set(valid_statuses), set(expected_statuses))
    
    def test_job_status_labels(self):
        """Test job status labels."""
        self.assertEqual(JobStatus.PENDING.label, 'Pending')
        self.assertEqual(JobStatus.PROCESSING.label, 'Processing')
        self.assertEqual(JobStatus.COMPLETED.label, 'Completed')
        self.assertEqual(JobStatus.FAILED.label, 'Failed')


class SerializerTest(TestCase):
    """Test cases for serializers."""
    
    def test_job_create_serializer_valid(self):
        """Test JobCreateSerializer with valid data."""
        from .serializers import JobCreateSerializer
        
        data = {'guideline_text': 'This is a valid guideline text.'}
        serializer = JobCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['guideline_text'], data['guideline_text'])
    
    def test_job_create_serializer_empty_text(self):
        """Test JobCreateSerializer with empty text."""
        from .serializers import JobCreateSerializer
        
        data = {'guideline_text': '   '}
        serializer = JobCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('guideline_text', serializer.errors)
    
    def test_job_serializer(self):
        """Test JobSerializer."""
        from .serializers import JobSerializer
        
        job = Job.objects.create(
            guideline_text="Test guideline",
            status=JobStatus.COMPLETED,
            summary="Test summary",
            checklist=[{"item": "Test item", "description": "Test description"}]
        )
        
        serializer = JobSerializer(job)
        data = serializer.data
        
        self.assertEqual(data['event_id'], str(job.id))
        self.assertEqual(data['status'], JobStatus.COMPLETED)
        self.assertIsNotNone(data['result'])
        self.assertIn('summary', data['result'])
        self.assertIn('checklist', data['result'])