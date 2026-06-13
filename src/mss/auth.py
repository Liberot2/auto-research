"""Authentication management for MSS platform API access.

Reads credentials from config/mss_auth.yaml and provides session tokens.
Supports three auth types: login (API call), static token, environment variable.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Default paths (relative to project root)
DEFAULT_AUTH_PATH = Path("config/mss_auth.yaml")

# Token cache TTL: 25 minutes (most tokens expire in 30 min)
TOKEN_CACHE_TTL = 25 * 60


class AuthManager:
    """Manages authentication tokens for MSS platform API access."""

    def __init__(self, auth_path: Path | None = None) -> None:
        self._auth_path = auth_path or DEFAULT_AUTH_PATH
        self._profiles: dict[str, dict[str, Any]] = {}
        self._token_cache: dict[str, tuple[str, float]] = {}  # profile -> (token, expiry_time)
        self._load_config()

    def _load_config(self) -> None:
        """Load auth configuration from YAML file."""
        if not self._auth_path.exists():
            logger.warning("Auth config not found: %s", self._auth_path)
            return

        with open(self._auth_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        self._profiles = config.get("profiles", {})
        logger.info("Loaded %d auth profiles", len(self._profiles))

    def get_profile(self, profile_name: str) -> dict[str, Any]:
        """Get auth profile configuration."""
        if profile_name not in self._profiles:
            raise ValueError(f"Auth profile '{profile_name}' not found. Available: {list(self._profiles.keys())}")
        return self._profiles[profile_name]

    async def get_token(self, profile_name: str) -> str:
        """Obtain a valid authentication token for the given profile.

        Uses cached token if still valid, otherwise obtains a new one.
        """
        # Check cache
        if profile_name in self._token_cache:
            token, expiry = self._token_cache[profile_name]
            if time.time() < expiry:
                return token

        profile = self.get_profile(profile_name)
        auth_type = profile.get("auth_type", "token")

        if auth_type == "login":
            token = await self._login(profile)
        elif auth_type == "token":
            token = profile.get("static_token", "")
        elif auth_type == "env":
            env_var = profile.get("env_var", "MSS_API_TOKEN")
            token = os.environ.get(env_var, "")
            if not token:
                raise ValueError(f"Environment variable '{env_var}' not set")
        elif auth_type == "basic":
            # For basic auth, return base64 encoded credentials
            import base64
            username = profile.get("username", "")
            password = profile.get("password", "")
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
        else:
            raise ValueError(f"Unsupported auth_type: {auth_type}")

        # Cache the token
        self._token_cache[profile_name] = (token, time.time() + TOKEN_CACHE_TTL)
        return token

    async def _login(self, profile: dict[str, Any]) -> str:
        """Execute login API call to obtain session token."""
        import httpx

        base_url = profile.get("base_url", "")
        login_url = profile.get("login_url", "/api/v1/auth/login")
        login_body = profile.get("login_body", {})
        verify_ssl = profile.get("verify_ssl", True)
        url = f"{base_url}{login_url}"

        async with httpx.AsyncClient(timeout=30, verify=verify_ssl) as client:
            response = await client.post(url, json=login_body)
            response.raise_for_status()
            data = response.json()

        # Extract token using JSONPath-like expression
        token_path = profile.get("token_path", "$.data.token")
        token = self._extract_by_path(data, token_path)
        if not token:
            raise ValueError(f"Failed to extract token from login response using path '{token_path}'")

        logger.info("Login successful for profile '%s'", profile.get("base_url", ""))
        return str(token)

    @staticmethod
    def _extract_by_path(data: Any, path: str) -> Any:
        """Extract value from nested dict using dot-separated path.

        Supports: $.data.token, $.data.items[0].id
        """
        # Remove leading $. if present
        if path.startswith("$."):
            path = path[2:]

        parts = path.split(".")
        current = data
        for part in parts:
            # Handle array index: items[0]
            if "[" in part:
                key, idx_str = part.split("[", 1)
                idx = int(idx_str.rstrip("]"))
                current = current[key]
                current = current[idx]
            else:
                current = current[part]
        return current

    def build_auth_header(self, profile_name: str, token: str) -> dict[str, str]:
        """Build the authentication header dict for a profile."""
        profile = self.get_profile(profile_name)
        header_name = profile.get("token_header", "Authorization")
        prefix = profile.get("token_prefix", "Bearer ")
        return {header_name: f"{prefix}{token}"}
