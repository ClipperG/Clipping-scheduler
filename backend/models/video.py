from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.database.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    r2_url = Column(String, nullable=True)              # standard variant (YouTube / TikTok)
    r2_url_instagram = Column(String, nullable=True)     # variant with the Roobet logo burned in

    status = Column(String, default="new")

    assigned_channel_id = Column(
        Integer,
        ForeignKey("buffer_accounts.id"),
        nullable=True,
    )
    assigned_date = Column(DateTime, nullable=True)
    scheduled_for = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
