import json
import os
import threading
from contextlib import asynccontextmanager

import pika
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from sqlmodel import Session

from db import Document, DocumentChunk, engine, init_db

# Load Model once
model = None

def process_file(file_path: str, task_id: str, user_id: str, original_name: str):

    try:
        print(f" [AI] Starting processing for {original_name}...")

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        with Session(engine) as session:

            document = Document(
                filename=original_name, user_id=user_id, task_id=task_id
            )
            session.add(document)
            session.commit()
            session.refresh(document)

            chunk_size = 500
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

            print(f" [AI] Generated {len(chunks)} chunks. Generating Embeddings...", 
                  flush=True)

            for chunk_text in chunks:
                vector = model.encode(chunk_text).tolist()

                db_chunk = DocumentChunk(
                    document_id=document.id, content=chunk_text, embedding=vector
                )
                
                session.add(db_chunk)

            session.commit()
            print(f" [AI] Successfully indexed {original_name}", flush=True)

    except Exception as e:
        print(f" [!] Error: {e}", flush=True)
                
def run_consumer():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host="rabbitmq")
            )
            channel = connection.channel()
            channel.queue_declare(queue="task_queue", durable=True)

            def callback(ch, method, properties, body):

                data = json.loads(body)
                if os.path.exists(data['file_path']):
                    process_file(
                        file_path=data['file_path'],
                        task_id=data['task_id'],
                        user_id=data.get('user_id', {}),
                        original_name=data["original_name"]
                    )
                else:
                    print(f" [!] File not found: {data['file_path']}", flush=True)


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
    global model 
    init_db()

    print(" [AI] Loading model (this may take a moment)... ", flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(" [AI] Model loaded.", flush=True)


    t = threading.Thread(target=run_consumer, daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"service": "lumina backend", "status": "OK", "lifespan": "enabled"}
