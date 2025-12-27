import os
from alembic import command
from alembic.config import Config


def run_migrations():
    """Run database migrations using Alembic"""
    try:
        # Get the absolute path to the alembic.ini file         # /app
        alembic_ini_path = os.path.join("", "alembic.ini")

        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini_path)
        # Explicitly set script_location relative to the current file
        # alembic_cfg.set_main_option("sqlalchemy.url", DatabaseService().get_sql_alchemy_url())

        # Run the migration
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        raise e
