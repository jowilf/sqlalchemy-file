from typing import Generator

from sqlmodel import Session

from .db import engine


def get_session() -> Generator[Session, None, None]:
    session: Session = Session(engine, expire_on_commit=False)
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
