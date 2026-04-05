import redis
from typing import List, Tuple, Optional
from config import REDIS_URL

class JobQueue:
    """Redis-based job queue for job URLs"""

    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None
        self.queue_key = "job_applications"

    def add_job(self, job_url: str, priority: int = 0) -> bool:
        """Add job URL to queue"""
        if self.redis_client:
            # Use sorted set for priority queue
            return self.redis_client.zadd(self.queue_key, {job_url: priority}) > 0
        else:
            # Fallback to in-memory list (not persistent)
            if not hasattr(self, '_memory_queue'):
                self._memory_queue = []
            self._memory_queue.append((priority, job_url))
            return True

    def get_next_job(self) -> Optional[str]:
        """Get next job URL from queue"""
        if self.redis_client:
            # Get item with lowest score (highest priority)
            jobs = self.redis_client.zrange(self.queue_key, 0, 0, withscores=True)
            if jobs:
                job_url = jobs[0][0]
                self.redis_client.zrem(self.queue_key, job_url)
                return job_url.decode('utf-8') if isinstance(job_url, bytes) else job_url
        else:
            # Fallback to in-memory
            if hasattr(self, '_memory_queue') and self._memory_queue:
                self._memory_queue.sort(key=lambda x: x[0])  # Sort by priority
                priority, job_url = self._memory_queue.pop(0)
                return job_url

        return None

    def get_queue_size(self) -> int:
        """Get number of jobs in queue"""
        if self.redis_client:
            return self.redis_client.zcard(self.queue_key)
        else:
            return len(getattr(self, '_memory_queue', []))

    def clear_queue(self):
        """Clear all jobs from queue"""
        if self.redis_client:
            self.redis_client.delete(self.queue_key)
        else:
            if hasattr(self, '_memory_queue'):
                self._memory_queue.clear()