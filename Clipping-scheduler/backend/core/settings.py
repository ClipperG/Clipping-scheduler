import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    APP_NAME: str = "Clipping Scheduler"

    DATABASE_URL: str
    BUFFER_API_KEY: str

    GOOGLE_DRIVE_FOLDER_ID: str = ""

    INSTAGRAM_CHANNEL_ID: str
    YOUTUBE_CHANNEL_ID: str

    R2_BUCKET_NAME: str
    R2_ENDPOINT: str
    R2_ACCESS_KEY: str
    R2_SECRET_KEY: str
    R2_PUBLIC_URL: str

    POST_TIMES: str = "09:00,13:00,18:00"
    TIMEZONE: str = "Europe/Tirane"

    @property
    def post_times(self):
        return [t.strip() for t in self.POST_TIMES.split(",")]


settings = Settings()