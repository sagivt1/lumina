import threading

import time
import pika
from fastapi import FastAPI
from contextlib import asynccontextmanager


def run_consumer():

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
            channel = connection.channel()
            channel.queue_declare(queue="health_check", durable=False)


            def callback(ch, method, properties, body):
                print(f"[*] User A Received: {body.decode()}", flush=True)

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
