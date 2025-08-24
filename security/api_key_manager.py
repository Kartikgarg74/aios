import os
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

class APIKeyManager:
    def __init__(self, api_keys_file: str = "api_keys.json"):
        self.api_keys_file = api_keys_file
        self.api_keys: Dict[str, Dict[str, any]] = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, Dict[str, any]]:
        if os.path.exists(self.api_keys_file):
            with open(self.api_keys_file, "r") as f:
                return json.load(f)
        return {}

    def _save_api_keys(self):
        with open(self.api_keys_file, "w") as f:
            json.dump(self.api_keys, f, indent=4)

    def generate_api_key(self, user_id: str, expires_in_days: int = 365) -> str:
        api_key = secrets.token_urlsafe(32)
        expiration_date = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
        self.api_keys[api_key] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiration_date,
            "is_active": True
        }
        self._save_api_keys()
        return api_key

    def validate_api_key(self, api_key: str) -> Optional[str]:
        key_info = self.api_keys.get(api_key)
        if not key_info or not key_info.get("is_active"):
            return None
        
        expires_at = datetime.fromisoformat(key_info["expires_at"])
        if datetime.now() > expires_at:
            key_info["is_active"] = False # Mark as expired
            self._save_api_keys()
            return None
        
        return key_info["user_id"]

    def revoke_api_key(self, api_key: str) -> bool:
        if api_key in self.api_keys:
            self.api_keys[api_key]["is_active"] = False
            self._save_api_keys()
            return True
        return False

    def rotate_api_key(self, old_api_key: str, user_id: str, expires_in_days: int = 365) -> Optional[str]:
        if not self.validate_api_key(old_api_key) or self.api_keys.get(old_api_key, {}).get("user_id") != user_id:
            return None

        # Revoke the old key
        self.revoke_api_key(old_api_key)

        # Generate a new key
        new_api_key = self.generate_api_key(user_id, expires_in_days)
        return new_api_key

    def get_user_api_keys(self, user_id: str) -> Dict[str, Dict[str, any]]:
        return {key: info for key, info in self.api_keys.items() if info.get("user_id") == user_id}

    def activate_api_key(self, api_key: str) -> bool:
        if api_key in self.api_keys:
            self.api_keys[api_key]["is_active"] = True
            self._save_api_keys()
            return True
        return False