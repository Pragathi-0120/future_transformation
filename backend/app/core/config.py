from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = Path(__file__).resolve().parents[2]
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    access_token_expire_minutes: int = 480
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', extra='ignore')
settings = Settings()
UPLOAD_DIR = BASE_DIR / 'uploads'; UPLOAD_DIR.mkdir(exist_ok=True)
VECTOR_DIR = BASE_DIR / 'chroma_store'; VECTOR_DIR.mkdir(exist_ok=True)
