from sqlalchemy import Column, Integer, String, DateTime

from backend.database.database import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, index=True)

    video_id = Column(Integer, nullable=False)

    channel = Column(String, nullable=False, default="ALL")

    scheduled_time = Column(DateTime, nullable=False)

    status = Column(String, default="scheduled")