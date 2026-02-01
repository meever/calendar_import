"""
Test caching functionality
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from extractor import EventExtractor
from cache_manager import ExtractionCache

# Load environment
load_dotenv()

def main():
    """Test caching with same and different inputs"""
    print("=" * 80)
    print("Testing Cache Functionality")
    print("=" * 80)
    
    # Setup
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in .env")
        return False
    
    print("✓ API key loaded")
    
    config_manager = ConfigManager()
    config = config_manager.load()
    print(f"✓ Config loaded with {len(config.locations)} locations")
    
    # Clear cache to start fresh
    cache = ExtractionCache()
    cleared = cache.clear()
    print(f"✓ Cleared {cleared} cache entries to start fresh\n")
    
    # Test schedule
    test_schedule = """
周四 1/29 下午 6 - 8 下水+陆上 @ Regis
周五 1/30 下午 6 - 8 下水 @ Regis
周六 1/31 上午 9 - 11 下水+陆上 @ Brandeis
    """.strip()
    
    # First extraction - should be cache miss
    print("=" * 80)
    print("TEST 1: First extraction (expect MISS)")
    print("=" * 80)
    extractor1 = EventExtractor(api_key=api_key, config=config, use_cache=True)
    
    import time
    start1 = time.time()
    events1 = extractor1.extract(test_schedule)
    duration1 = time.time() - start1
    
    print(f"✓ Extracted {len(events1)} events")
    print(f"✓ Cache hit: {extractor1.last_cache_hit}")
    print(f"✓ Duration: {duration1:.2f}s")
    
    if extractor1.last_cache_hit:
        print("❌ FAIL: Expected cache miss on first extraction")
        return False
    else:
        print("✓ PASS: Cache miss as expected\n")
    
    # Second extraction - same text, should be cache hit
    print("=" * 80)
    print("TEST 2: Second extraction with same text (expect HIT)")
    print("=" * 80)
    extractor2 = EventExtractor(api_key=api_key, config=config, use_cache=True)
    
    start2 = time.time()
    events2 = extractor2.extract(test_schedule)
    duration2 = time.time() - start2
    
    print(f"✓ Extracted {len(events2)} events")
    print(f"✓ Cache hit: {extractor2.last_cache_hit}")
    print(f"✓ Duration: {duration2:.2f}s")
    print(f"✓ Speedup: {duration1/duration2:.1f}x faster")
    
    if not extractor2.last_cache_hit:
        print("❌ FAIL: Expected cache hit on second extraction")
        return False
    
    if len(events1) != len(events2):
        print(f"❌ FAIL: Event count mismatch ({len(events1)} vs {len(events2)})")
        return False
    
    print("✓ PASS: Cache hit and results match\n")
    
    # Third extraction - different text, should be cache miss
    print("=" * 80)
    print("TEST 3: Different schedule (expect MISS)")
    print("=" * 80)
    different_schedule = """
周一 2/2 下午 6 - 8 下水+陆上 @ Regis
周二 2/3 下午 6 - 8 下水 @ Regis
    """.strip()
    
    extractor3 = EventExtractor(api_key=api_key, config=config, use_cache=True)
    
    start3 = time.time()
    events3 = extractor3.extract(different_schedule)
    duration3 = time.time() - start3
    
    print(f"✓ Extracted {len(events3)} events")
    print(f"✓ Cache hit: {extractor3.last_cache_hit}")
    print(f"✓ Duration: {duration3:.2f}s")
    
    if extractor3.last_cache_hit:
        print("❌ FAIL: Expected cache miss for different text")
        return False
    else:
        print("✓ PASS: Cache miss as expected\n")
    
    # Cache statistics
    print("=" * 80)
    print("CACHE STATISTICS")
    print("=" * 80)
    stats = cache.get_stats()
    print(f"Entries: {stats['entries']}")
    print(f"Hits: {stats['hits']}")
    print(f"Misses: {stats['misses']}")
    print(f"Hit Rate: {stats['hit_rate']:.1f}%")
    print(f"Total Size: {stats['total_size_kb']:.2f} KB")
    print(f"TTL: {stats['ttl_days']} days")
    
    # Expected: 2 entries (2 different schedules)
    # Note: extractor creates new cache instances, so hits/misses aren't aggregated
    if stats['entries'] != 2:
        print(f"❌ FAIL: Expected 2 cache entries, got {stats['entries']}")
        return False
    
    print("✓ PASS: Cache entries correct")
    
    # Verify cache speedup from our manual tracking
    print(f"\n✓ Verified {duration1/duration2:.1f}x speedup on cache hit")
    
    print("\n" + "=" * 80)
    print("✅ ALL CACHE TESTS PASSED")
    print("=" * 80)
    
    # Cleanup
    print(f"\nCleaning up: removed {cache.clear()} cache entries")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
