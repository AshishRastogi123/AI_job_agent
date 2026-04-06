#!/usr/bin/env python3
"""
AI Job Application Agent - Main Runner
Complete end-to-end autonomous job application system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import JobApplicationAgent
from job_queue.manager import JobQueue
from utils.logging_config import get_logger
import argparse
import time

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description='AI Job Application Agent - End-to-End Autonomous Job Applications')
    parser.add_argument('--job-url', help='Single job URL to process')
    parser.add_argument('--user-id', type=int, default=1, help='User ID (default: 1)')
    parser.add_argument('--add-jobs', nargs='+', help='Add job URLs to queue')
    parser.add_argument('--process-queue', action='store_true', help='Process all jobs in queue')
    
    args = parser.parse_args()
    
    try:
        logger.info("Initializing AI Job Application Agent...")
        agent = JobApplicationAgent(user_id=args.user_id)
        queue = JobQueue()
        
        if args.add_jobs:
            logger.info(f"Adding {len(args.add_jobs)} jobs to queue...")
            for url in args.add_jobs:
                queue.add_job(url)
                print(f"✓ Added: {url}")
        
        if args.job_url:
            logger.info(f"Processing single job: {args.job_url}")
            result = agent.run_application(args.job_url)
            print(f"\n{'='*60}")
            print("APPLICATION RESULT")
            print(f"{'='*60}")
            print(f"Success: {result['success']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"ATS Platform: {result['ats_platform']}")
            print(f"Fields Filled: {result['filled_fields']}")
            print(f"Unanswered Fields: {len(result['unanswered_fields'])}")
            if result['unanswered_fields']:
                print("Unanswered field details:")
                for field in result['unanswered_fields']:
                    print(f"  - {field.get('label', 'Unknown')}: {field.get('type', 'unknown')}")
            if result['errors']:
                print(f"Errors: {result['errors']}")
            print(f"{'='*60}\n")
        
        elif args.process_queue:
            logger.info("Processing job queue...")
            count = 0
            max_jobs = 10  # Safety limit
            
            while queue.get_queue_size() > 0 and count < max_jobs:
                logger.info(f"\n[{count + 1}] Processing next job...")
                result = agent.run_application()
                
                if result['success']:
                    print(f"✓ {result['message']}")
                else:
                    print(f"✗ {result['message']}")
                
                count += 1
                time.sleep(2)  # Delay between applications
            
            logger.info(f"Processed {count} jobs from queue")
        
        elif not (args.add_jobs or args.job_url or args.process_queue):
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
