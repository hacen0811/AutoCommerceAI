from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import DATABASE_PATH


DATABASE_FILE = Path(DATABASE_PATH).resolve()

print(
    "######## DATABASE PATH UTF8 TRACE ########",
    flush=True,
)
print(
    "[DATABASE PATH]",
    repr(str(DATABASE_FILE)),
    flush=True,
)
print(
    "[DATABASE EXISTS]",
    DATABASE_FILE.exists(),
    flush=True,
)
print(
    "[DATABASE SIZE]",
    DATABASE_FILE.stat().st_size if DATABASE_FILE.exists() else 0,
    flush=True,
)

engine = create_engine(
    f"sqlite:///{DATABASE_FILE.as_posix()}",
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)