"""
Configuration management with persistence
"""

import json
import logging
from pathlib import Path
from typing import Optional
from models import Config
from settings import DEFAULT_CONFIG_PATH


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with file persistence"""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[Config] = None
    
    def load(self) -> Config:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = Config.from_dict(data)
                return self.config
            except Exception as e:
                logger.warning("Failed to load config from %s: %s", self.config_path, e)
                logger.warning("Using default configuration")
        
        # Create default config
        self.config = Config.get_default_config()
        self.save()
        return self.config
    
    def save(self) -> None:
        """Save configuration to file"""
        if self.config is None:
            return
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning("Failed to save config to %s: %s", self.config_path, e)
