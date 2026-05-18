"""Async SQLAlchemy engine + session factory for HITL service."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = structlog.get_logger()

_engine = None
_session_factory: async_sessionmaker | None = None

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def init_db() -> None:
    global _engine, _session_factory

    _engine = create_async_engine(
        settings.get_db_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    logger.info("db_connected", url=settings.get_db_url.split("@")[-1])

    await _run_migrations()


async def _run_migrations() -> None:
    """Run pending SQL migrations on startup for all envs (local, beta, prod).

    Tracks applied migrations in {schema}.schema_migrations table.
    SQL files: db/migrations/{env}/V{n}__{description}.sql
    {schema} placeholder is replaced at runtime from DB_SCHEMA env var.
    """
    env = settings.env.lower()
    schema = settings.db_schema
    migration_dir = _MIGRATIONS_DIR / env

    if not migration_dir.exists():
        logger.warning("migrations_dir_not_found", path=str(migration_dir))
        return

    sql_files = sorted(
        migration_dir.glob("V*.sql"),
        key=lambda f: int(f.stem.split("__")[0].lstrip("V")),
    )

    if not sql_files:
        logger.info("no_migrations_found", env=env)
        return

    async with _engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema}".schema_migrations (
                version     VARCHAR(200) PRIMARY KEY,
                applied_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """))

        for sql_file in sql_files:
            version = sql_file.stem
            result = await conn.execute(
                text(f'SELECT 1 FROM "{schema}".schema_migrations WHERE version = :v'),
                {"v": version},
            )
            if result.scalar_one_or_none():
                continue

            sql = sql_file.read_text(encoding="utf-8-sig").replace("{schema}", schema)
            # asyncpg cannot execute multiple statements in one call — split by ;
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            for stmt in statements:
                await conn.execute(text(stmt))
            await conn.execute(
                text(f'INSERT INTO "{schema}".schema_migrations (version) VALUES (:v)'),
                {"v": version},
            )
            logger.info("migration_applied", version=version, schema=schema, env=env)


async def close_db() -> None:
    if _engine:
        await _engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:  # type: ignore[misc]
        yield session
