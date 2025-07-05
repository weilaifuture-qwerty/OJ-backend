#!/usr/bin/env python
"""
Clean up duplicate migrations
"""

import os

# Remove the duplicate migration we created
migration_file = "/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/homework/migrations/0002_add_auto_grade.py"
if os.path.exists(migration_file):
    os.remove(migration_file)
    print(f"Removed {migration_file}")
else:
    print(f"File {migration_file} not found")

# Also remove the merge migration
merge_file = "/Users/weilai/Desktop/Fufu_website/website10/OJ/OnlineJudge/homework/migrations/0003_merge_20250629_0254.py"
if os.path.exists(merge_file):
    os.remove(merge_file)
    print(f"Removed {merge_file}")
else:
    print(f"File {merge_file} not found")

print("\nMigration cleanup complete!")