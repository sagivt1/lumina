import json
import os
import threading
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI


def run_consumer():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            channel = connection.channel()
            channel.queue_declare(queue="task_queue", durable=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    file_path = data.get("file_path")

                    print(f" [User A] Recived Task: {data['task_id']}", flush=True)

                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        print(f" File Found : {file_path}", flush=True)
                        print(f" Size       : {size / 1024:.2f} KB", flush=True)
                    else:
                        print(f" Error : File not found at {file_path}", flush=True)
                except json.JSONDecodeError:
                    print(" [!] Error: Received malformed JSON message.", flush=True)

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue="task_queue", on_message_callback=callback, auto_ack=True
            )
            print(" [*] User A: Listening on 'task_queue'...", flush=True)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not ready yet. Retrying in 5s...", flush=True)
        except Exception as e:
            print(f" [!] Connection faild: {e}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"service": "lumina backend", "status": "OK", "lifespan": "enabled"}
