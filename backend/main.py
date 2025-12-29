import threading
import time   # ← חדש
import json
import pika
from fastapi import FastAPI
from contextlib import asynccontextmanager


def run_consumer():
    """
    Background task to listen for RabbitMQ messages.
    Keeps retrying until RabbitMQ is ready.
    """
    while True:
        try:
            print(" [*] User A: trying to connect to RabbitMQ...", flush=True)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            channel = connection.channel()
            channel.queue_declare(queue="health_check", durable=False)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    user_info = data.get("user", {})
                    user_id = user_info.get("sub", "Unknown")

                    print(
                        f" [User A] 🔒 Secure Task received for User: {user_id}",
                        flush=True,
                    )
                    print(f"          Content: {data.get('content')}", flush=True)
                except json.JSONDecodeError:
                    print(" [!] Error: Received malformed JSON", flush=True)

            # 🔴 חשוב – מחוץ ל-callback (כמו שדיברנו קודם)
            channel.basic_consume(
                queue="health_check", on_message_callback=callback, auto_ack=True
            )
            print(" [*] User A: waiting for messages on 'health_check'...", flush=True)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not ready yet. Retrying in 5s...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f" [!] RabbitMQ error: {e}", flush=True)
            time.sleep(5)



@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"service": "lumina backend", "status": "OK", "lifespan": "enabled"}
