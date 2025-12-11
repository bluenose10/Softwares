"""Usage tracking service for freemium model."""

import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta


class UsageTracker:
    """Track usage limits for free users (by IP address)."""

    def __init__(self, storage_path: str = "usage_data.json"):
        self.storage_path = Path(storage_path)
        self.free_daily_limit = 5  # Free users get 5 conversions per day
        self.free_file_size_limit_mb = 25  # Free users limited to 25MB
        self._load_data()

    def _load_data(self):
        """Load usage data from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
        else:
            self.data = {}

    def _save_data(self):
        """Save usage data to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.data, f)
        except Exception:
            pass

    def _cleanup_old_data(self):
        """Remove usage data older than 2 days."""
        cutoff_time = time.time() - (48 * 3600)  # 2 days ago

        to_remove = []
        for ip, data in self.data.items():
            if data.get('last_reset', 0) < cutoff_time:
                to_remove.append(ip)

        for ip in to_remove:
            del self.data[ip]

    def _get_user_data(self, ip_address: str) -> Dict:
        """Get or create user data for IP address."""
        if ip_address not in self.data:
            self.data[ip_address] = {
                'count': 0,
                'last_reset': time.time(),
                'is_pro': False
            }

        # Reset count if it's a new day
        user_data = self.data[ip_address]
        last_reset = user_data.get('last_reset', 0)
        hours_since_reset = (time.time() - last_reset) / 3600

        if hours_since_reset >= 24:
            user_data['count'] = 0
            user_data['last_reset'] = time.time()

        return user_data

    def can_process(self, ip_address: str, file_size_mb: float = 0) -> tuple[bool, str]:
        """
        Check if user can process another file.

        Returns:
            (can_process, reason_if_not)
        """
        self._cleanup_old_data()
        user_data = self._get_user_data(ip_address)

        # Pro users have unlimited access
        if user_data.get('is_pro', False):
            if file_size_mb > 500:
                return False, "File size exceeds 500MB limit (even for Pro users)"
            return True, ""

        # Free users: check file size limit
        if file_size_mb > self.free_file_size_limit_mb:
            return False, f"Free users limited to {self.free_file_size_limit_mb}MB files. Upgrade to Pro for 500MB limit."

        # Free users: check daily conversion limit
        if user_data['count'] >= self.free_daily_limit:
            hours_until_reset = 24 - ((time.time() - user_data['last_reset']) / 3600)
            return False, f"Free limit of {self.free_daily_limit} conversions per day reached. Upgrade to Pro for unlimited conversions or wait {int(hours_until_reset)} hours."

        return True, ""

    def increment_usage(self, ip_address: str):
        """Increment usage count for user."""
        user_data = self._get_user_data(ip_address)

        if not user_data.get('is_pro', False):
            user_data['count'] += 1
            self._save_data()

    def get_usage_stats(self, ip_address: str) -> Dict:
        """Get usage statistics for user."""
        user_data = self._get_user_data(ip_address)

        if user_data.get('is_pro', False):
            return {
                'is_pro': True,
                'conversions_used': 'unlimited',
                'conversions_remaining': 'unlimited',
                'max_file_size_mb': 500,
                'hours_until_reset': 0
            }

        hours_until_reset = 24 - ((time.time() - user_data['last_reset']) / 3600)

        return {
            'is_pro': False,
            'conversions_used': user_data['count'],
            'conversions_remaining': max(0, self.free_daily_limit - user_data['count']),
            'max_file_size_mb': self.free_file_size_limit_mb,
            'hours_until_reset': max(0, int(hours_until_reset))
        }

    def set_pro_status(self, ip_address: str, is_pro: bool = True):
        """Set Pro status for a user (after payment)."""
        user_data = self._get_user_data(ip_address)
        user_data['is_pro'] = is_pro
        self._save_data()


# Global instance
usage_tracker = UsageTracker()
