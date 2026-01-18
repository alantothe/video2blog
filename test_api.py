#!/usr/bin/env python3
"""
Simple test script to verify the article types API logic works.
"""
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, 'apps/backend')
sys.path.insert(0, 'packages/shared/src')
sys.path.insert(0, 'packages/utils/src')

# Set up environment
os.environ['DATA_DIR'] = 'data'

try:
    from app.storage.file_store import read_article_types
    from app.config import DB_PATH

    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {DB_PATH.exists()}")

    types = read_article_types()
    print(f"Found {len(types)} article types")

    if types:
        print("Sample article types:")
        for i, t in enumerate(types[:3]):
            print(f"  {i+1}. {t['name']}: {t['definition'][:60]}...")

    # Test what the API should return
    import json
    response_data = types
    print(f"\nAPI response would be: {len(json.dumps(response_data))} characters")
    print("First 500 chars of response:")
    print(json.dumps(response_data)[:500] + "...")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()