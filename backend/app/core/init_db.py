from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.utils.security import get_password_hash
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def init_db(db: AsyncSession) -> None:
    """Initialize database with admin user if it doesn't exist"""
    try:
        result = await db.execute(
            select(User).filter(User.username == "admin")
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            logger.info("Creating admin user...")
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("admin"),  # Change this password in production!
                use_openai=True,
                enable_document_search=True,
                handle_urls=True,
                check_db=True
            )
            db.add(admin_user)
            await db.commit()
            logger.info("Admin user created successfully")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 