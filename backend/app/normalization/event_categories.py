"""
Event Categories Taxonomy & Enums — CyberTrace AI
"""
from app.models import EventCategory

# List of all supported categories
ALL_EVENT_CATEGORIES = [c.value for c in EventCategory]
