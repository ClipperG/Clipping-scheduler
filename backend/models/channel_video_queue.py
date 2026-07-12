from sqlalchemy import Boolean, Column, ForeignKey, Integer

from backend.database.database import Base


class ChannelVideoQueue(Base):
    __tablename__ = "channel_video_queue"

    id = Column(Integer, primary_key=True, index=True)

    channel_id = Column(
        Integer,
        ForeignKey("buffer_accounts.id"),
        nullable=False,
    )

    video_id = Column(
        Integer,
        ForeignKey("videos.id"),
        nullable=False,
    )

    queue_position = Column(Integer, nullable=False)

    posted = Column(Boolean, default=False, nullable=False)