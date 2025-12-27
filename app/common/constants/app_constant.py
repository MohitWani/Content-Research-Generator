from app.core.config.environment_config import settings

title = settings.APP_NAME
version = settings.APP_VERSION
description = (
    'This server provides a suite of AI-powered services and endpoints, '
    'designed to enable seamless integration of AI capabilities '
    'into various applications. It serves as the central gateway for accessing.'
)

banner = f"""
    ╔═══════════════════════════════════════════════════════════════
    ║
    ║   {title}
    ║   Version: {version}
    ║   Status: Running
    ║   Host: {settings.APP_HOST}
    ║   Port: {settings.APP_PORT}
    ║
    ╚═══════════════════════════════════════════════════════════════
    """
