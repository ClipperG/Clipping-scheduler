from sqlalchemy import Column, Integer, String, DateTime
from backend.database.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=False)

    status = Column(String, default="waiting")

    platform = Column(String, nullable=True)
    account = Column(String, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)

    r2_url = Column(String, nullable=True)

    instagram_buffer_id = Column(String, nullable=True)
    youtube_buffer_id = Column(String, nullable=True)