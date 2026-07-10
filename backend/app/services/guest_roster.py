"""
Guest roster and lightweight collection state for debate challengers.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from app.core.config import settings
from app.services.sage_persona import SAGES, get_sage


_collected_guests: set[str] = set()


def _guest_keys() -> List[str]:
    return [key for key in settings.DEBATE_EXTRA_SAGES if key in SAGES]


def list_guest_roster(active_session_participants: Optional[List[str]] = None) -> List[Dict[str, object]]:
    active = set(active_session_participants or [])
    guests = []
    for key in _guest_keys():
        sage = get_sage(key)
        guests.append(
            {
                "sage_key": key,
                "sage_name": sage.name,
                "era": sage.era,
                "core_thought": sage.core_thought,
                "unlocked": True,
                "collected": key in _collected_guests,
                "staying": key in active,
            }
        )
    return guests


def choose_random_guest(exclude: Optional[List[str]] = None) -> str:
    excluded = set(exclude or [])
    candidates = [key for key in _guest_keys() if key not in excluded]
    if not candidates:
        candidates = _guest_keys()
    if not candidates:
        raise ValueError("No guest sages available")
    return random.choice(candidates)


def mark_collected(sage_key: str) -> Dict[str, object]:
    if sage_key not in _guest_keys():
        raise ValueError(f"Unknown guest sage: {sage_key}")
    _collected_guests.add(sage_key)
    return next(guest for guest in list_guest_roster() if guest["sage_key"] == sage_key)
