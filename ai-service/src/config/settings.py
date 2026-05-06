# ============================================
# Nexus-Graph AI Service — Settings
# ============================================

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Centralised configuration loaded from environment variables."""

    # Service
    ai_service_port: int = 8001
    ai_service_host: str = "0.0.0.0"
    log_level: str = "INFO"
    ai_grpc_host: str = "0.0.0.0"
    ai_grpc_port: int = 50051

    # Redis
    redis_url: str = "redis://localhost:6379"

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/nexus_graph"
    mongodb_db_name: str = "nexus_graph"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "nexus_graph_2026"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # LLM
    gemini_api_key: str = ""
    deepseek_api_key: str = ""

    # Redis channels
    channel_slack: str = "slack-events"
    channel_github: str = "github-events"
    channel_jira: str = "jira-events"
    channel_decisions: str = "decision-events"
    channel_conflicts: str = "conflict-events"
    channel_graph_updates: str = "graph-updates"
    channel_timeline: str = "timeline-events"
    channel_orchestration: str = "orchestration-events"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
