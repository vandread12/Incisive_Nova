"""
Configuración de la base de datos (PostgreSQL vía SQLAlchemy).

Usa SQLAlchemy síncrono con el driver psycopg v3. La conexión se determina por
la variable de entorno DATABASE_URL:

    postgresql://user:pass@host:5432/db  ->  postgresql+psycopg://...

Si DATABASE_URL no está definida (tests, desarrollo local sin Postgres), el
motor no se crea y `is_db_enabled()` devuelve False; los repositorios usan
entonces su fallback en memoria.
"""

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base declarativa para los modelos ORM."""


_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def _normalize_url(url: str) -> str:
    """Normaliza el DATABASE_URL al driver psycopg v3 de SQLAlchemy."""
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def _init_engine() -> None:
    """Inicializa el engine y el sessionmaker si hay DATABASE_URL."""
    global _engine, _SessionLocal
    if _engine is not None:
        return
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return
    normalized = _normalize_url(database_url)
    # Los argumentos de pool (pool_size/max_overflow) solo aplican a backends
    # con QueuePool (p. ej. PostgreSQL); SQLite usa otro pool y los rechaza.
    engine_kwargs = {"pool_pre_ping": True, "future": True}
    if not normalized.startswith("sqlite"):
        engine_kwargs.update(pool_size=5, max_overflow=10)
    _engine = create_engine(normalized, **engine_kwargs)
    _SessionLocal = sessionmaker(
        bind=_engine, class_=Session, expire_on_commit=False, future=True
    )


def is_db_enabled() -> bool:
    """True si hay una base de datos configurada y disponible."""
    _init_engine()
    return _engine is not None


def get_engine() -> Optional[Engine]:
    _init_engine()
    return _engine


def get_session() -> Session:
    """Devuelve una nueva sesión. Requiere que la BD esté habilitada."""
    _init_engine()
    if _SessionLocal is None:
        raise RuntimeError("La base de datos no está configurada (DATABASE_URL)")
    return _SessionLocal()


def init_db() -> bool:
    """Crea las tablas si la BD está disponible. Devuelve True si se inicializó.

    Importa los modelos para registrarlos en la metadata antes de crear tablas.
    """
    if not is_db_enabled():
        return False
    # Import diferido para evitar ciclos y registrar los modelos en Base.metadata.
    from . import models  # noqa: F401

    engine = get_engine()
    assert engine is not None
    Base.metadata.create_all(engine)
    return True
