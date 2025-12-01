"""
Configuration settings for the AI Customer Service application.

This module provides type-safe, validated configuration management using Pydantic Settings.
All settings can be overridden via environment variables.

Usage :
    from config import settings

    api_key = settings.llm.claude.api_key
    db_url = settings.database.url

"""

from email.policy import default
from enum import Enum
from os import path
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, SecretStr, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================
# ENUMS
# ============================================================

class Environment(str, Enum):
    """ Application Environment """
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LLMProvider(str, Enum):
    """ LLM provider options. """
    CLAUDE = "claude"
    OPENAI = "openai"
    BOTH = "both" # Claude primary, OpenAI fallback

class VectorDBProvider(str, Enum):
    """ Vector database provider. """
    CHROMADB = "chromadb" # local environment
    QDRANT = "qdrant" # production

# ============================================================
# LLM Configuration
# ============================================================

class ClaudeSettings(BaseSettings):
    """ Anthropic Claude configuration. """

    api_key: SecretStr = Field(
        ...,
        description = "Anthropic API Key"
    )
    model: str = Field(
        default = "claude-sonnet-4-20250514",
        description = "Claude model to use"
    )
    max_tokens: int = Field(
        default = 4096,
        ge = 1,
        le = 200000,
        description = "Maximum tokens in response"
    )
    temperature: float = Field(
        default = 0.7,
        ge = 0.0,
        le = 1.0,
        description = "Sampling temperature"
    )
    timeout: int = Field(
        default = 60,
        ge = 1,
        description = "Request timeout in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix = "LLM__CLAUDE__",
        case_sensitive = False
    )

class OpenAISettings(BaseSettings):
    """ OpenAI configuration """

    api_key: SecretStr = Field(
        ...,
        description = "OpenAI API key"
    )
    model: str = Field(
        default = "gpt-4-turbo-preview",
        description = "OpenAI model to use"
    )
    max_tokens: int = Field(
        default = 4096,
        ge = 1,
        le = 128000,
        description = "Maximum tokens in response"
    )
    temperature: float = Field(
        default = 0.7,
        ge = 0.0,
        le = 2.0,
        description = "Sampling temperatrure"
    )
    timeout: int = Field(
        default = 60,
        ge = 1,
        description = "Request timeout in seconds"
    )
    embedding_model: str = Field(
        default = "text-embedding-3-small",
        description = "Embedding model for vectors"
    )
    embedding_dimensions: int = Field(
        default = 1536,
        description = "Embedding vector dimensions"
    )
    
    model_config = SettingsConfigDict(
        env_prefix = "LLM__OPENAI__",
        case_sensitive = False
    )

class LLMSettings(BaseSettings):
    """ LLM provider configuration. """

    provider: LLMProvider = Field(
        default = LLMProvider.BOTH,
        description = "Which LLM provider(s) to use"
    )
    claude: ClaudeSettings
    openai: OpenAISettings

    fallback_enabled: bool = Field(
        default = True,
        description = "Enable fallback to secondary provider"
    )
    max_retries: int = Field(
        default = 3,
        ge = 0,
        description = "Maximum retry attempts"
    )
    retry_delay: float = Field(
        default = 1.0,
        ge = 0.0,
        description = "Delay between retries in seconds"
    )

    model_config = SettingsConfigDict(
        env_prefix = "LLM__",
        case_sensitive = False
    )

# ==================================================================
# DATABASE CONFIGURATION
# ==================================================================

class DatabaseSettings(BaseSettings):
    """ PostgresSQL database configuration. """

    url: str = Field(
        default = "postgresql+asyncpg://user:password@localhost:5432/customer_service",
        description = "Database connection URL"
    )
    pool_size: int = Field(
        default = 10,
        ge = 1,
        le = 100,
        description = "Connection pool size"
    )
    max_overflow: int = Field(
        default = 20,
        ge = 0,
        description = "Maximum overflow connections."
    )
    pool_timeout: int = Field(
        default = 30,
        ge = 1,
        description = "Pool checkout timeout in seconds"
    )
    echo: bool = Field(
        default = False,
        description = "Log all SQL statements"
    )

    model_config = SettingsConfigDict(
        env_prefix = "DATABASE__",
        case_sensitive = False
    )

    @property
    def url_safe(self) -> str:
        """ Get URL with password masked for logging. """
        if "@" in self.url:
            parts = self.url.split("@")
            if "://" in parts[0]:
                protocol, credentials = parts[0].split("://")
                if ":" in credentials:
                    user, _ = credentials.split(":", 1)
                    return f"{protocol}://{user}:****@{parts[1]}"
        return self.url

class RedisSettings(BaseSettings):
    """ Redis configuration for caching and state management. """

    url: str = Field(
        default = "redis://localhost:6379/0",
        description = "Redis connection URL"
    )
    max_connections: int = Field(
        default = 50,
        ge = 1,
        description = "Maximum connection pool size"
    )
    socket_timeout: int = Field(
        default = 5,
        ge = 1,
        description = "Socket timeout in seconds"
    )
    socket_connect_timeout: int = Field(
        default = 5,
        ge = 1,
        description = "Socket connect timeout in seconds"
    )
    decode_response: bool = Field(
        default = True,
        description = "Decode byte responses to strings"
    )

    model_config = SettingsConfigDict(
        env_prefix = "REDIS__",
        case_sensitive = False
    )

# ===========================================================
# Vector Database Configuration 
# ===========================================================

class ChromaDBSettings(BaseSettings):
    """ ChromaDB configuration (for local development) """

    path: str = Field(
        default = "./data/chroma",
        description = "Path to ChromaDB storage"
    )
    collection_name: str = Field(
        default = "customer_service_kb",
        description = "Collection name for knowledge base"
    )

    model_config = SettingsConfigDict(
        env_prefix = "VECTOR_DB__CHROMADB__",
        case_sensitive = False
    )

class QdrantSettings(BaseSettings):
    """ Qdrant configuration (for production). """

    url: str = Field(
        ...,
        description = "Qdrant server URL"
    )
    api_key: Optional[SecretStr] = Field(
        None,
        description = "Qdrant API key for (for cloud)"
    )
    collection_name: str = Field(
        default = "customer_service_kb",
        description = "Collection name for knowledge base"
    )
    vector_size: int = Field(
        default = 1536,
        description = "Vector dimensions (must match embedding model)"
    )

    model_config = SettingsConfigDict(
        env_prefix = "VECTOR_DB__QDRANT__",
        case_sensitive = False
    )

class VectorDBSettings(BaseSettings):
    """ Vector database configuration. """

    provider: VectorDBProvider = Field(
        default = VectorDBProvider.CHROMADB,
        description = "Vector DB provider"
    )
    chromadb: Optional[ChromaDBSettings] = None
    qdrant: Optional[QdrantSettings] = None

    top_k: int = Field(
        default = 5,
        ge = 1,
        le = 50,
        description = "Number of results to retrieve"
    )
    similarity_threshold: float = Field(
        default = 0.7,
        ge = 0.0,
        le = 1.0,
        description = "Minimum similarity score for results"
    )

    model_config = SettingsConfigDict(
        env_prefix = "VECTOR_DB__",
        case_sensitive = False
    )

    @field_validator('chormadb', 'qdrant', mode = 'before')
    @classmethod
    def validate_provider_config(cls, v, info):
        """ Ensure the selected provider has configuration. """
        provider = info.data.get("provider")
        field_name = info.field_name

        # If this field matches the provider, it must be configured.
        if provider == VectorDBProvider.CHROMADB and field_name == 'chromadb':
            return v or ChromaDBSettings()
        elif provider == VectorDBProvider.QDRANT and field_name == 'qdrant':
            if v is None:
                raise ValueError("Qdrant configuration required when using Qdrant provider")
        return v

# ============================================================================
# Agent Configuration
# ============================================================================

class AgentSettings(BaseSettings):
    """ Agent behaviour configuration . """

    # Escalation settings
    
