"""
Smart caching for event extraction results

Caches AI extraction results to avoid redundant API calls when users
submit the same schedule text. Uses SHA256 hashing with config fingerprinting.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from models import Event, Config


class ExtractionCache:
    """Manages caching of event extraction results"""
    
    def __init__(self, cache_dir: str = "cache", ttl_days: int = 30):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory to store cache files
            ttl_days: Cache time-to-live in days (default 30)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_days = ttl_days
        self.cache_dir.mkdir(exist_ok=True)
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def _get_config_fingerprint(self, config: Config) -> str:
        """
        Generate fingerprint of config to detect changes
        
        Config changes should invalidate cache since:
        - Location changes affect extraction
        - Default title affects results
        - Model version changes affect AI behavior
        
        Args:
            config: Application configuration
            
        Returns:
            SHA256 hash of relevant config fields
        """
        # Include fields that affect extraction
        config_data = {
            "locations": {name: loc.address for name, loc in config.locations.items()},
            "default_title": config.default_event_title,
            "model": config.gemini_model,
            "timezone": config.timezone
        }
        
        config_json = json.dumps(config_data, sort_keys=True)
        return hashlib.sha256(config_json.encode()).hexdigest()[:16]
    
    def _get_cache_key(self, text: str, config: Config) -> str:
        """
        Generate cache key from input text and config
        
        Args:
            text: Raw schedule text
            config: Application configuration
            
        Returns:
            SHA256 hash (first 32 chars) as cache key
        """
        # Normalize text (strip whitespace, lowercase for consistency)
        normalized_text = text.strip().lower()
        
        # Combine text + config fingerprint
        config_fp = self._get_config_fingerprint(config)
        combined = f"{normalized_text}||{config_fp}"
        
        # Generate hash
        hash_obj = hashlib.sha256(combined.encode())
        return hash_obj.hexdigest()[:32]
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_expired(self, cache_data: Dict) -> bool:
        """Check if cache entry is expired"""
        cached_at = datetime.fromisoformat(cache_data["cached_at"])
        age = datetime.now() - cached_at
        return age > timedelta(days=self.ttl_days)
    
    def get(self, text: str, config: Config) -> Optional[List[Event]]:
        """
        Get cached extraction results
        
        Args:
            text: Raw schedule text
            config: Application configuration
            
        Returns:
            List of cached Event objects if found and valid, None otherwise
        """
        cache_key = self._get_cache_key(text, config)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            self.misses += 1
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check expiration
            if self._is_expired(cache_data):
                cache_path.unlink()  # Delete expired cache
                self.misses += 1
                return None
            
            # Deserialize events
            events = []
            for event_dict in cache_data["events"]:
                event = Event.from_dict(event_dict, config.locations)
                events.append(event)
            
            self.hits += 1
            return events
            
        except Exception as e:
            # If cache is corrupted, delete it
            print(f"Warning: Cache read failed: {e}")
            if cache_path.exists():
                cache_path.unlink()
            self.misses += 1
            return None
    
    def set(self, text: str, config: Config, events: List[Event]) -> None:
        """
        Store extraction results in cache
        
        Args:
            text: Raw schedule text
            config: Application configuration
            events: Extracted events to cache
        """
        cache_key = self._get_cache_key(text, config)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Serialize events
            events_data = [event.to_dict() for event in events]
            
            cache_data = {
                "cached_at": datetime.now().isoformat(),
                "text_preview": text[:100] + "..." if len(text) > 100 else text,
                "event_count": len(events),
                "config_fingerprint": self._get_config_fingerprint(config),
                "events": events_data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Warning: Cache write failed: {e}")
    
    def clear(self) -> int:
        """
        Clear all cache files
        
        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        
        self.hits = 0
        self.misses = 0
        return count
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dict with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(cache_files),
            "total_size_kb": total_size / 1024,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "ttl_days": self.ttl_days
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries
        
        Returns:
            Number of expired entries removed
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if self._is_expired(cache_data):
                    cache_file.unlink()
                    count += 1
            except Exception:
                # If corrupted, delete it
                cache_file.unlink()
                count += 1
        
        return count
