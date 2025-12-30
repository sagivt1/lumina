import json
import threading
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI


def run_consumer():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="health_check", durable=False)

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body)

                user_id = data.get("user", {}).get("sub", "Unknown")

                print(f"[User A] Secure Task recived for user: {user_id}", flush=True)
                print(f"         Content: {data.get('content')}", flush=True)
            except json.JSONDecodeError:
                print("[!] Error: Received malformed JSON message.")

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue="health_check", on_message_callback=callback, auto_ack=True
        )
        print("[*] User A: waiting for messages...")
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError:
        print("[!] RabbitMQ not ready yet. Retrying in 5s...", flush=True)
    except Exception as e:
        print(f"[!] Connection faild: {e}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"service": "lumina backend", "status": "OK", "lifespan": "enabled"}
