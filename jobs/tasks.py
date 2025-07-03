"""
Celery tasks for processing guideline documents with GPT chains.
"""
import json
import logging
from typing import Dict, List

from celery import shared_task
from django.conf import settings
from openai import OpenAI

from .models import Job, JobStatus

logger = logging.getLogger(__name__)


class GPTChainProcessor:
    """Handles the two-step GPT chain processing."""
    
    def __init__(self):
        # Correct OpenAI client initialization
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def summarize_guideline(self, text: str) -> str:
        """Step 1: Summarize the guideline text."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that summarizes guideline documents. "
                            "Create a concise but comprehensive summary that captures the key "
                            "points, requirements, and important details from the text."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following guideline text:\n\n{text}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error in summarize_guideline: {str(e)}")
            raise
    
    def generate_checklist(self, summary: str) -> List[Dict[str, str]]:
        """Step 2: Generate a checklist based on the summary."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that creates actionable checklists. "
                            "Based on the provided summary, create a practical checklist with "
                            "specific, actionable items. Return the response as a JSON array "
                            "where each item is an object with 'item' and 'description' fields."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Based on this summary, create a practical checklist:\n\n{summary}\n\n"
                            "Return as JSON array with objects containing 'item' and 'description' fields."
                        )
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                checklist = json.loads(content)
                if isinstance(checklist, list):
                    return checklist
                else:
                    # If not a list, wrap in a list
                    return [checklist]
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple structure
                return [{"item": "Review guidelines", "description": content}]
                
        except Exception as e:
            logger.error(f"Error in generate_checklist: {str(e)}")
            raise


@shared_task(bind=True, max_retries=3)
def process_guideline_task(self, job_id: str):
    """
    Process a guideline text through the GPT chain.
    """
    try:
        # Get the job
        job = Job.objects.get(id=job_id)
        
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.save()
        
        logger.info(f"Starting processing for job {job_id}")
        
        # Initialize GPT processor
        processor = GPTChainProcessor()
        
        # Step 1: Summarize
        logger.info(f"Summarizing guideline for job {job_id}")
        summary = processor.summarize_guideline(job.guideline_text)
        
        # Step 2: Generate checklist
        logger.info(f"Generating checklist for job {job_id}")
        checklist = processor.generate_checklist(summary)
        
        # Update job with results
        job.summary = summary
        job.checklist = checklist
        job.status = JobStatus.COMPLETED
        job.save()
        
        logger.info(f"Successfully completed processing for job {job_id}")
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'summary_length': len(summary),
            'checklist_items': len(checklist)
        }
        
    except Job.DoesNotExist:
        logger.error(f"Job {job_id} not found")
        raise
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        
        # Update job status to failed
        try:
            job = Job.objects.get(id=job_id)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.save()
        except Job.DoesNotExist:
            pass
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)
        else:
            logger.error(f"Max retries exceeded for job {job_id}")
            raise