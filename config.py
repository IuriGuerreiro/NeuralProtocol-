"""
Simple configuration for Gemini chat application.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChatConfig(BaseModel):
    """Chat configuration."""
    model: str = Field(default="gemini-2.0-flash", description="Gemini model to use")
    max_tokens: int = Field(default=1000, description="Maximum tokens per response")
    temperature: float = Field(default=0.7, description="Response creativity (0.0-1.0)")
    memory_size: int = Field(default=10, description="Number of messages to keep in memory")


class Config(BaseModel):
    """Main configuration class."""
    google_api_key: Optional[str] = Field(default=None, description="Google API key for Gemini")
    chat: ChatConfig = Field(default_factory=ChatConfig)

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            google_api_key=os.getenv("GEMINI_API_KEY"),
            chat=ChatConfig(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                memory_size=int(os.getenv("MEMORY_SIZE", "10"))
            )
        )


# Global configuration instance
config = Config.from_env()
