import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
import time
from security.api_key_manager import APIKeyManager

class TestAPIKeyManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.api_key_manager = APIKeyManager(api_keys_file=self.temp_file.name)
        
    def tearDown(self):
        # Clean up the temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if os.path.exists(f"{self.temp_file.name}.bak"):
            os.unlink(f"{self.temp_file.name}.bak")
    
    def test_generate_api_key(self):
        # Test generating an API key
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Verify the key was generated and stored
        self.assertIsNotNone(api_key)
        self.assertIn(api_key, self.api_key_manager.api_keys)
        
        # Verify the key properties
        key_info = self.api_key_manager.api_keys[api_key]
        self.assertEqual(key_info["user_id"], user_id)
        self.assertTrue(key_info["is_active"])
        self.assertEqual(key_info["scopes"], ["default"])
    
    def test_validate_api_key(self):
        # Generate a key for testing
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Test valid key validation
        validated_user_id = self.api_key_manager.validate_api_key(api_key)
        self.assertEqual(validated_user_id, user_id)
        
        # Test invalid key validation
        invalid_key = "invalid_key"
        self.assertIsNone(self.api_key_manager.validate_api_key(invalid_key))
    
    def test_revoke_api_key(self):
        # Generate a key for testing
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Revoke the key
        result = self.api_key_manager.revoke_api_key(api_key)
        self.assertTrue(result)
        
        # Verify the key is no longer valid
        self.assertIsNone(self.api_key_manager.validate_api_key(api_key))
        self.assertFalse(self.api_key_manager.api_keys[api_key]["is_active"])
    
    def test_rotate_api_key(self):
        # Generate a key for testing
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Rotate the key
        new_api_key = self.api_key_manager.rotate_api_key(api_key, user_id)
        
        # Verify the new key is valid and the old key is revoked
        self.assertIsNotNone(new_api_key)
        self.assertNotEqual(api_key, new_api_key)
        self.assertIsNone(self.api_key_manager.validate_api_key(api_key))
        self.assertEqual(self.api_key_manager.validate_api_key(new_api_key), user_id)
    
    def test_expired_key(self):
        # Generate a key that expires immediately
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id, expires_in_days=0)
        
        # Wait a moment to ensure expiration
        time.sleep(1)
        
        # Verify the key is expired
        self.assertIsNone(self.api_key_manager.validate_api_key(api_key))
    
    def test_scoped_keys(self):
        # Generate a key with specific scopes
        user_id = "test_user"
        scopes = ["read", "write"]
        api_key = self.api_key_manager.generate_api_key(user_id, scopes=scopes)
        
        # Verify scope validation
        self.assertEqual(self.api_key_manager.validate_api_key(api_key, "read"), user_id)
        self.assertEqual(self.api_key_manager.validate_api_key(api_key, "write"), user_id)
        self.assertIsNone(self.api_key_manager.validate_api_key(api_key, "admin"))
    
    def test_add_remove_scope(self):
        # Generate a key
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Add a scope
        result = self.api_key_manager.add_scope_to_key(api_key, "admin")
        self.assertTrue(result)
        self.assertIn("admin", self.api_key_manager.api_keys[api_key]["scopes"])
        
        # Remove a scope
        result = self.api_key_manager.remove_scope_from_key(api_key, "admin")
        self.assertTrue(result)
        self.assertNotIn("admin", self.api_key_manager.api_keys[api_key]["scopes"])
    
    def test_rate_limiting(self):
        # Generate a key
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Test rate limiting
        limit = 5
        for i in range(limit):
            self.assertTrue(self.api_key_manager.check_rate_limit(api_key, limit_per_minute=limit))
        
        # This should exceed the limit
        self.assertFalse(self.api_key_manager.check_rate_limit(api_key, limit_per_minute=limit))
    
    def test_usage_stats(self):
        # Generate a key
        user_id = "test_user"
        api_key = self.api_key_manager.generate_api_key(user_id)
        
        # Use the key a few times
        for _ in range(3):
            self.api_key_manager.validate_api_key(api_key)
        
        # Get usage stats
        stats = self.api_key_manager.get_key_usage_stats(api_key)
        self.assertEqual(stats["usage_count"], 3)
        self.assertIsNotNone(stats["last_used"])

if __name__ == "__main__":
    unittest.main()