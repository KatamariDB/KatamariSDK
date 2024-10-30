# KatamariIAM

**KatamariIAM** is a robust and feature-rich Identity and Access Management (IAM) module that provides secure authentication, authorization, and role-based access control (RBAC) for users and service accounts. It integrates with **KatamariMVCC** for multi-version concurrency control, allowing safe concurrent transactions and supporting OAuth2, JWT, and API key-based authentication. **KatamariIAM** uses **Argon2** for secure password hashing, ensuring that user credentials are stored with high resistance to brute-force attacks.

## Key Features

1. **Multiple Authentication Methods**:
   - **Password-Based Authentication (PBA)** using **Argon2** for password hashing.
   - **API Key-based Authentication** for service accounts.
   - **OAuth2** support with JWT tokens for stateless authentication.
   
2. **Service Accounts**:
   - Create and manage service accounts with API keys for automated access.
   - Service accounts can authenticate using API keys and receive JWT tokens.

3. **Role-Based Access Control (RBAC)**:
   - Assign roles to both users and service accounts with fine-grained access permissions.
   - Flexible and extendable roles and permissions model.

4. **JWT-based OAuth2 Authentication**:
   - Secure token-based authentication using **JWT** (JSON Web Tokens) with HMAC-SHA256.
   - Tokens contain expiration times, roles, and user-specific claims.
   - Support for refreshing OAuth2 tokens using refresh tokens.

5. **Session Management**:
   - Generate, validate, and refresh OAuth2 JWT tokens.
   - Expiration and revocation of tokens to control session lifetimes.

6. **Strong Password Security**:
   - **Argon2** password hashing for secure and modern password storage.
   - Resistant to side-channel attacks and brute-force attacks.

7. **Multi-Version Concurrency Control (MVCC)**:
   - All operations are performed within MVCC-backed transactions, ensuring consistency and safety in high-concurrency environments.

8. **Token Revocation and Validation**:
   - Session tokens can be revoked to invalidate access tokens and prevent misuse.
   - Efficient JWT validation for stateless authentication.

## Installation

### Dependencies

- Python 3.8+
- Install required Python libraries:

```bash
pip install argon2-cffi pyjwt
```

You will also need **KatamariDB** installed, as **KatamariIAM** relies on the **KatamariMVCC** transaction system for safe concurrency.

## Usage

### Initialize **KatamariIAM**

```python
from KatamariIAM import KatamariIAM

# Initialize KatamariIAM with a secret key for signing JWT tokens
iam = KatamariIAM(secret_key="your_secret_key")
```

### Creating a User

```python
# Create a new user with Argon2-hashed password
await iam.create_user('john_doe', 'super_secure_password', roles=['admin'])
```

### Authenticating a User with Password-Based Authentication (PBA)

```python
# Authenticate the user and receive an OAuth2 access token (JWT) and refresh token
auth_response = await iam.authenticate_user('john_doe', 'super_secure_password')
print(auth_response)  # Outputs: {'access_token': '<JWT>', 'refresh_token': '<UUID>'}

# Validate the access token
is_valid = iam.validate_jwt_token(auth_response['access_token'])
print(f"Is token valid? {is_valid}")
```

### Refreshing a Token

```python
# Refresh the access token using the refresh token
new_token = await iam.refresh_oauth_token(auth_response['refresh_token'])
print(new_token)  # Outputs: {'access_token': '<new JWT>'}
```

### Creating a Service Account

```python
# Create a service account with API key
api_key_response = await iam.create_service_account('service_account_1', roles=['service'])
print(api_key_response)  # Outputs: {'api_key': '<UUID>'}
```

### Authenticating a Service Account with API Key

```python
# Authenticate service account using API key and receive a JWT
service_auth_response = await iam.authenticate_service_account('service_account_1', api_key_response['api_key'])
print(service_auth_response)  # Outputs: {'access_token': '<JWT>'}
```

### Role-Based Access Control (RBAC)

#### Assigning a Role to a User

```python
# Assign a role to a user
await iam.assign_role_to_user('john_doe', 'admin')
```

#### Creating a Role

```python
# Create a new role with permissions
await iam.create_role('admin', permissions=['read', 'write', 'delete'])
```

### Revoking a Session Token

```python
# Revoke a session token
await iam.revoke_token(auth_response['access_token'])
```

## Configuration

- **Session Token Expiry**:
  - `self.token_expiry = timedelta(hours=1)` (default is 1 hour)
- **API Key Expiry**:
  - `self.api_key_expiry = timedelta(days=30)` (default is 30 days)
- **Refresh Token Expiry**:
  - `self.refresh_token_expiry = timedelta(days=7)` (default is 7 days)

You can modify these values within the **KatamariIAM** class to customize the duration of tokens.

## Security Considerations

1. **Password Hashing with Argon2**:
   - The module uses **Argon2**, the recommended algorithm for secure password hashing.
   - It is designed to be memory and CPU-intensive, making it resistant to brute-force attacks.
   
2. **JWT Security**:
   - JWTs are signed using **HMAC-SHA256** with a configurable secret key.
   - Tokens are stateless and expire based on the configuration, reducing risk if compromised.

3. **Role-Based Access Control**:
   - Roles provide fine-grained control over what actions users and service accounts can perform, reducing the risk of privilege escalation.

## Extensibility

1. **OAuth2 Grant Types**:
   - You can extend the module to support additional OAuth2 flows such as **Authorization Code Flow**, **Client Credentials**, and **Device Code Flow**.

2. **Multi-Factor Authentication (MFA)**:
   - The module can be enhanced to support **TOTP** (Time-based One-Time Passwords) for multi-factor authentication (MFA), adding an extra layer of security.

3. **Audit Logging**:
   - Add detailed audit logs to track user actions, including login attempts, token generation, and role changes.

4. **Custom Security Policies**:
   - Implement custom security policies for password complexity, token lifetime, and access controls, based on your organization's needs.

## Future Enhancements

- **Multi-Factor Authentication (MFA)**: Integration with TOTP-based MFA to secure user accounts.
- **OAuth2 Advanced Flows**: Expanding OAuth2 support to include more grant types and enhanced client scopes.
- **Audit Logging**: Detailed logging of all user activities for security and compliance.
- **Token Revocation List (TRL)**: Implement a token revocation list for handling compromised tokens.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**KatamariIAM** offers a flexible, scalable, and secure identity and access management system with modern features like OAuth2, JWT, Argon2-based password hashing, and service account management. With multi-version concurrency control (MVCC), it is suitable for high-concurrency and distributed environments.
