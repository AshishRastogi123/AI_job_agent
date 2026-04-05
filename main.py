#!/usr/bin/env python3
"""
AI Job Application Agent - Main Runner
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.orchestrator import JobApplicationAgent
from queue.manager import JobQueue
from db.queries import insert_job
import argparse

def main():
    parser = argparse.ArgumentParser(description='AI Job Application Agent')
    parser.add_argument('--job-url', help='Single job URL to process')
    parser.add_argument('--user-id', type=int, default=1, help='User ID (default: 1)')
    parser.add_argument('--add-jobs', nargs='+', help='Add job URLs to queue')
    parser.add_argument('--process-queue', action='store_true', help='Process all jobs in queue')

    args = parser.parse_args()

    agent = JobApplicationAgent(user_id=args.user_id)
    queue = JobQueue()

    if args.add_jobs:
        for url in args.add_jobs:
            queue.add_job(url)
            print(f"Added job to queue: {url}")

    if args.job_url:
        print(f"Processing single job: {args.job_url}")
        result = agent.run_application(args.job_url)
        print(f"Result: {result}")

    if args.process_queue:
        print("Processing job queue...")
        while queue.get_queue_size() > 0:
            result = agent.run_application()
            print(f"Processed job: {result}")
            if not result.get('success'):
                break  # Stop on failure for safety

if __name__ == "__main__":
    main()