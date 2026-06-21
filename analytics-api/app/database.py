import os
import structlog
from databases import Database

logger = structlog.get_logger(__name__)

# Use environment variables injected by Vault / K8s
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "finsight_db")

# Fallback to sqlite if postgres is unavailable (useful for local dev)
if os.getenv("USE_SQLITE", "false").lower() == "true":
    DATABASE_URL = "sqlite:///./finsight.db"
else:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

database = Database(DATABASE_URL)

async def connect_db():
    try:
        await database.connect()
        logger.info("database_connected", url=DATABASE_URL)
        
        # Create table if not exists
        query = """
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(255) NOT NULL,
            amount FLOAT NOT NULL,
            currency VARCHAR(10) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            risk_score FLOAT NOT NULL,
            risk_level VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await database.execute(query=query)
        logger.info("database_table_ensured")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        # Don't crash the app if DB fails in demo, just log it.
        
async def disconnect_db():
    await database.disconnect()
    logger.info("database_disconnected")

async def save_transaction(tx_id: str, amount: float, currency: str, tx_type: str, risk_score: float, risk_level: str):
    if not database.is_connected:
        return
    query = """
    INSERT INTO transactions (transaction_id, amount, currency, transaction_type, risk_score, risk_level)
    VALUES (:tx_id, :amount, :currency, :tx_type, :risk_score, :risk_level)
    """
    values = {
        "tx_id": tx_id,
        "amount": amount,
        "currency": currency,
        "tx_type": tx_type,
        "risk_score": risk_score,
        "risk_level": risk_level
    }
    try:
        await database.execute(query=query, values=values)
    except Exception as e:
        logger.error("database_insert_failed", error=str(e))
