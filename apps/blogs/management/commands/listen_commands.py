# Third party modules
import json
import logging
import redis
# Django modules
from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Connecting to REDIS"))

        try:
            r = redis.Redis(
                host="127.0.0.1", port=6379, db=0, decode_responses=True
            )
            r.ping()
        except redis.ConnectionError:
            self.stderr.write(self.style.ERROR(
                "Can't connect to REDIS at 127.0.0.1:6379.\n"
                "Start Redis: docker run -p 6379:6379 redis:alpine"
            ))
            return
        
        pubsub = r.pubsub()
        pubsub.subscribe("comments")

        self.stdout.write(self.style.SUCCESS("Subscribed to channel 'comments'"))

        for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
                self.stdout.write(
                    f"\n{'-' * 40}\n"
                    f"Event : {data.get('event')}\n"
                    f"Post : {data.get("post_slug")}\n"
                    f"Author : {data.get("author")}\n"
                    f"Body : {data.get("body")}\n"
                    f"ID : {data.get("comment_id")}\n" 
                )
            except (json.JSONDecodeError, KeyError) as exc:
                self.stderr.write(f"Bad message: {message["data"]} - {exc}")
