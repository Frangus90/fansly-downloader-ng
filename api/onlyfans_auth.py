"""OnlyFans Authentication & Signature Generation

Adapted from OF-Scraper (MIT License)
https://github.com/Frangus90/OF-Scraper

This module handles the complex dynamic signature system used by OnlyFans API.
Each API request requires a dynamically computed signature based on:
- Dynamic rules fetched from external endpoints
- SHA-1 hash of newline-separated: static param, timestamp, path, and user ID
- Checksum calculation using specific byte indexes from the hex hash string

Copyright (c) 2024 OF-Scraper contributors (MIT License)
Adapted for Fansly Downloader NG
"""

import time
import hashlib
import requests
from urllib.parse import urlparse
from typing import Optional, Dict
import json


class OnlyFansAuth:
    """
    OnlyFans authentication with dynamic signatures

    This implements the OF API's security system which requires:
    1. Fetching dynamic signing rules from external endpoints
    2. Computing SHA-1 based signatures for each request
    3. Including proper headers and cookies
    """

    # Rule provider endpoints (from OF-Scraper)
    # These endpoints provide the dynamic signing rules needed for API requests
    RULE_ENDPOINTS = [
        "https://raw.githubusercontent.com/DATAHOARDERS/dynamic-rules/main/onlyfans.json",
        "https://raw.githubusercontent.com/deviint/onlyfans-dynamic-rules/main/dynamicRules.json",
    ]

    def __init__(self, sess: str, auth_id: str, auth_uid: Optional[str],
                 user_agent: str, x_bc: str):
        """
        Initialize OF authentication

        Args:
            sess: Session cookie value
            auth_id: Authentication ID
            auth_uid: Authentication UID (only if 2FA enabled)
            user_agent: Browser user agent string
            x_bc: X-BC security token
        """
        self.sess = sess
        self.auth_id = auth_id
        self.auth_uid = auth_uid
        self.user_agent = user_agent
        self.x_bc = x_bc

        self.rules = None
        self.rules_cache_time = None
        self.CACHE_TTL = 30  # Cache rules for 30 seconds

    def get_dynamic_rules(self) -> Dict:
        """
        Fetch dynamic signing rules from external endpoints

        Rules are cached for 30 seconds to avoid excessive requests.
        Falls back through multiple endpoints if primary fails.

        Returns:
            Dict containing signing rules:
                - static_param: Static parameter for signature
                - format: Format string for final signature
                - checksum_indexes: Byte indexes for checksum calculation
                - checksum_constant: Constant added to checksum
                - app_token: App token for headers

        Raises:
            RuntimeError: If all endpoints fail
        """
        now = time.time()

        # Check cache
        if self.rules and self.rules_cache_time:
            if now - self.rules_cache_time < self.CACHE_TTL:
                return self.rules

        # Fetch from endpoints
        last_error = None
        for endpoint in self.RULE_ENDPOINTS:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    rules = response.json()

                    # Validate rules have required fields
                    required_fields = ['static_param', 'format', 'checksum_indexes',
                                     'checksum_constant', 'app_token']
                    if all(field in rules for field in required_fields):
                        self.rules = rules
                        self.rules_cache_time = now
                        return self.rules

            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(
            f"Could not fetch OF dynamic rules from any endpoint. "
            f"Last error: {last_error}"
        )

    def compute_signature(self, path: str, timestamp: int) -> str:
        """
        Compute OnlyFans API signature

        Based on OF-Scraper's implementation, this computes a signature using:
        1. SHA-1 hash of newline-separated: static_param, timestamp, path, user_id
        2. Checksum calculation using specific byte indexes from hex string
        3. Formatting according to the dynamic rule template

        Args:
            path: URL path (e.g., "/api2/v2/users/me")
            timestamp: Unix timestamp in milliseconds

        Returns:
            Computed signature string
        """
        rules = self.get_dynamic_rules()

        # Extract rule components
        static_param = rules.get('static_param', '')
        checksum_indexes = rules.get('checksum_indexes', [])
        checksum_constant = rules.get('checksum_constant', 0)
        format_template = rules.get('format', '{hash}:{checksum}')

        # Build message for hashing: NEWLINE separated components
        # This matches OF-Scraper's exact implementation
        components = [static_param, str(timestamp), path, self.auth_id]
        message = "\n".join(components)

        # Compute SHA-1 hash (NOT SHA-256!)
        hash_obj = hashlib.sha1(message.encode('utf-8'), usedforsecurity=False)
        hash_hex = hash_obj.hexdigest()
        hash_bytes = hash_hex.encode('ascii')

        # Compute checksum by summing specific bytes (from hex string, not digest)
        checksum = sum(hash_bytes[i] for i in checksum_indexes if i < len(hash_bytes))
        checksum += checksum_constant

        # Abs value to ensure positive
        checksum = abs(checksum)

        # Format signature according to template
        # Try both positional and named argument formatting
        try:
            # First try positional arguments (common in OF-Scraper)
            signature = format_template.format(hash_hex, checksum)
        except (IndexError, KeyError):
            try:
                # Fall back to named arguments
                signature = format_template.format(hash=hash_hex, checksum=checksum)
            except Exception:
                # Last resort: simple concatenation
                signature = f"{hash_hex}:{checksum}"

        return signature

    def get_headers(self, url: str) -> Dict[str, str]:
        """
        Get request headers with dynamic signature

        Generates all required headers for an OF API request:
        - Standard headers (accept, user-agent)
        - Authentication headers (user-id, x-bc)
        - Dynamic signature headers (sign, time, app-token)

        Args:
            url: Full URL of the API request

        Returns:
            Dictionary of HTTP headers
        """
        timestamp = int(time.time() * 1000)

        # Include query parameters in signature path
        parsed = urlparse(url)
        path = parsed.path
        if parsed.query:
            path = f"{path}?{parsed.query}"

        signature = self.compute_signature(path, timestamp)

        rules = self.get_dynamic_rules()

        return {
            "accept": "application/json, text/plain, */*",
            "app-token": rules.get('app_token', '33d57ade8c02dbc5a333db99ff9ae26a'),
            "user-agent": self.user_agent,
            "user-id": self.auth_id,
            "x-bc": self.x_bc,
            "referer": "https://onlyfans.com",
            "sign": signature,
            "time": str(timestamp),
        }

    def get_cookies(self) -> Dict[str, str]:
        """
        Get authentication cookies

        Returns:
            Dictionary of cookies for the request
        """
        cookies = {
            "sess": self.sess,
            "auth_id": self.auth_id,
        }

        # Only include auth_uid_ if provided (2FA users)
        # Cookie name has trailing underscore: auth_uid_
        # Use auth_uid if provided, otherwise fall back to auth_id
        if self.auth_uid:
            cookies["auth_uid_"] = self.auth_uid
        else:
            cookies["auth_uid_"] = self.auth_id

        return cookies
