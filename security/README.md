# Security Module

## API Key Manager

The API Key Manager provides a secure way to generate, validate, and manage API keys for your application. It includes features for key rotation, scoping, rate limiting, and usage tracking.

### Features

- **Secure Key Generation**: Creates cryptographically secure API keys
- **Key Validation**: Validates keys with expiration and scope checking
- **Key Rotation**: Safely rotates keys while preserving scopes
- **Scoped Access**: Limit API keys to specific operations
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Usage Tracking**: Monitor key usage with detailed statistics
- **Audit Logging**: Log all key operations for security auditing

### Usage

#### Basic Usage

```python
from security.api_key_manager import APIKeyManager

# Initialize the manager
manager = APIKeyManager()

# Generate a new API key
api_key = manager.generate_api_key(user_id="user123")

# Validate an API key
user_id = manager.validate_api_key(api_key)
if user_id:
    print(f"Valid key for user: {user_id}")
else:
    print("Invalid or expired key")

# Revoke an API key
manager.revoke_api_key(api_key)
```

#### Advanced Usage

```python
# Generate a key with specific scopes and expiration
api_key = manager.generate_api_key(
    user_id="user123",
    expires_in_days=30,
    scopes=["read:users", "write:posts"]
)

# Validate with scope checking
user_id = manager.validate_api_key(api_key, required_scope="read:users")

# Add a new scope to an existing key
manager.add_scope_to_key(api_key, "read:metrics")

# Check rate limits
if manager.check_rate_limit(api_key, limit_per_minute=100):
    # Process the request
    pass
else:
    # Return rate limit exceeded error
    pass

# Get usage statistics
stats = manager.get_key_usage_stats(api_key)
print(f"Key used {stats['usage_count']} times")
```

### Command Line Interface

The module includes a command-line interface for managing API keys:

```bash
# Generate a new API key
python api_key_cli.py generate --user user123 --expires 90 --scopes read:users write:posts

# Validate an API key
python api_key_cli.py validate --key YOUR_API_KEY --scope read:users

# List all keys for a user
python api_key_cli.py list --user user123

# Get usage statistics
python api_key_cli.py stats --key YOUR_API_KEY
```

### Security Best Practices

1. **Store Keys Securely**: API keys should be treated as sensitive credentials
2. **Use HTTPS**: Always transmit API keys over secure connections
3. **Rotate Keys Regularly**: Use the rotation feature to change keys periodically
4. **Limit Scopes**: Apply the principle of least privilege with scoped keys
5. **Monitor Usage**: Regularly review the audit logs for suspicious activity
6. **Set Expirations**: Use short expiration times for sensitive operations

### Implementation Details

The API Key Manager uses a JSON file to store key information. In production environments, consider using a database backend for better scalability and security.

All key operations are logged to `logs/security-audit.log` for security auditing purposes.