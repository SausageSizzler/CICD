"""
Configuration and settings for Health checker lambda
"""

# ────────────────────── Secrects manager settings ───────────────────

DATABASE_SECRET = "db_creds"

# ────────────────────── Notification settings ───────────────────────

ACCEPTABLE_ERROR_THRESHOLD = 0.8
EMAIL_TOPIC_ARN = "arn:aws:sns:ap-southeast-2:542726313726:Email_Alerts"

# ───────────────────────── AWS variables ───────────────────────────

SCHEDULE_NAME = "3_min_schedule"

# ────────────────────── Temporary vars ─────────────────────────────

FUNCTIONS_TO_CHECK = [
    "ENWL_power_scraper",
    "live_station_scraper",
]  # Could update to get all lmabdas with a certain tag programatically
