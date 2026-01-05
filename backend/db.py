from typing import List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, text
from sqlmodel import Field, Session, SQLModel, create_engine

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

def search_documents(session: Session, query_vector:list, user_id: str, limit: int = 3):
    query = text(
        """
        SELECT 
            c.content,
            d.filename
        FROM 
            DocumentChunk c
        JOIN 
            Document d ON c.document_id = d.id
        WHERE
            d.user_id = :uid
        ORDER BY 
            c.embedding <-> :query_vector
        LIMIT :limit
        """
    )

    result = session.execute(
        query,
        params = {
            "uid": user_id,
            "query_vector": str(query_vector),
            "limit": limit
        }
    ).all()

    return result