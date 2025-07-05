#!/usr/bin/env python3
"""Check token hash"""

import hashlib

# The token in the judge server container
judge_token = "CHANGE_THIS_TOKEN"

# Calculate SHA256 hash
hashed = hashlib.sha256(judge_token.encode("utf-8")).hexdigest()

print(f"Judge server token: {judge_token}")
print(f"SHA256 hash: {hashed}")
print()
print("The Django system should be using the UNHASHED token.")
print("The judge dispatcher will hash it before sending.")