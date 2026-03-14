# Third party modules
import json
import logging
import redis
import asyncio
from redis import asyncio as aioredis
# Django modules
from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Listen to Redis 'comments' channel for new comment events (async)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting async Redis listener.."))
        asyncio.run(self.listen())

    async def listen(self):
        redis = aioredis.from_url(
            "redis://127.0.0.1:6379/0",
            encoding="utf-8",
            decode_responses=True,
        )

        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe("comments")
            self.stderr.write(
                self.style.SUCCESS(
                    "Subscribed to 'comments' channel. Waiting for messages..."
                )
            )
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self.handle.message(message["data"]) # type: ignore
        except KeyboardInterrupt:
            self.stdout.write("\nShutting down..")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error:{e}"))
        finally:
            await pubsub.unsubscribe("comments")
            await redis.close()
        
        async def handle_message(self, data: str):
            try:
                event = json.loads(data)
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(f"Event: {event.get('event')}")
                self.stdout.write(f"Post: {event.get('post_slug')}")
                self.stdout.write(f"Author: {event.get('author')}")
                self.stdout.write(f"Body: {event.get('body')}")
                self.stdout.write(f"Comment ID: {event.get('comment_id')}")
                self.stdout.write("=" * 60)

            except json.JSONDecodeError:
                self.stderr.write(f"Invalid JSON:{data}")
            except Exception as e:
                self.stderr.write(f"Error handling message: {e}")
        
