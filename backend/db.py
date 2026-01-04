from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Session, SQLModel, create_engine, text

# Database URL
DATABASE_URL = "postgresql+psycopg://lumina:password@db:5432/luminadb"

engine = create_engine(DATABASE_URL)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    user_id: str
    task_id: str


class DocumentChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    content: str
    embedding: List[float] = Field(sa_column=Column(Vector(384)))
    
def init_db():

    with Session(engine) as session:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        session.commit()

    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session