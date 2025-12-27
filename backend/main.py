import threading

import pika
from fastapi import FastAPI
from contextlib import asynccontextmanager


app = FastAPI()

def run_consumer():


    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="health_check")


        def callback(ch, method, properties, body):
            print(f"User A Received: {body.decode()}")

        channel.basic_consume(
            queue="health_check", on_message_callback=callback, auto_ack=True
        )

        print("[*] User A: waiting for messages...")
        channel.start_consuming()
    except Exception as e:
        print(f"[!] Connection faild: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()

    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"service": "lumina backend", "status": "OK"}
