from sqlalchemy import Column, Integer, String, Boolean
from backend.database.database import Base


class BufferWorkspace(Base):
    __tablename__ = "buffer_workspaces"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    api_token = Column(String, nullable=False)

    active = Column(Boolean, default=False)