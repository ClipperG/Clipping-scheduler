from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from backend.database.database import Base

class BufferAccount(Base):
    __tablename__ = "buffer_accounts"

    id = Column(Integer, primary_key=True, index=True)

    workspace_id = Column(
        Integer,
        ForeignKey("buffer_workspaces.id"),
        nullable=False
    )

    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    channel_id = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)