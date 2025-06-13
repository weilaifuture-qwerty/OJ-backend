"""
Patch for Django PostgreSQL UTC timezone issue.
This patches the utc_tzinfo_factory to be more lenient with timezone offsets.
"""
from django.utils.timezone import utc
import logging

logger = logging.getLogger(__name__)

def patched_utc_tzinfo_factory(offset):
    """
    Patched version of utc_tzinfo_factory that handles timezone offset issues more gracefully.
    """
    # Handle both integer and timedelta offsets
    from datetime import timedelta
    
    if isinstance(offset, timedelta):
        offset_seconds = offset.total_seconds()
    else:
        offset_seconds = offset
    
    if offset_seconds != 0:
        logger.warning(f"Database connection timezone offset is {offset}, expected 0 (UTC). Forcing UTC.")
    return utc

def apply_timezone_patch():
    """
    Apply the timezone patch to Django's PostgreSQL backend.
    """
    try:
        from django.db.backends.postgresql import utils as pg_utils
        original_factory = pg_utils.utc_tzinfo_factory
        pg_utils.utc_tzinfo_factory = patched_utc_tzinfo_factory
        logger.info("Applied PostgreSQL UTC timezone patch")
        return True
    except Exception as e:
        logger.error(f"Failed to apply timezone patch: {e}")
        return False