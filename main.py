import uvicorn
from dotenv import load_dotenv

from app.core.config.environment_config import settings
from app.main_app import create_app

load_dotenv()  # Loads from `.env` in project root by default

app = create_app()

if __name__ == '__main__':
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
