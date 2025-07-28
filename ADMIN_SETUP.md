# Admin Setup Guide

This guide provides instructions for creating admin accounts and managing the database setup for the AI Consultancy Platform.

## Prerequisites

- Docker and Docker Compose installed
- Project running with `docker-compose up -d`
- Database service (PostgreSQL) is healthy

## Database Setup

### Initialize Database Tables

If the database tables don't exist yet (fresh installation), run:

```bash
# Navigate to project directory
cd "/Users/1kpier/Agentic Framework"

# Create database tables
docker-compose exec backend python3 -c "from src.database.connection import create_tables; create_tables(); print('Database tables created successfully!')"
```

### Verify Database Connection

Check if the database is accessible:

```bash
# Test database connection
docker-compose exec backend python3 -c "from src.database.connection import SessionLocal; db = SessionLocal(); print('Database connection successful!'); db.close()"
```

## Creating Admin Accounts

### Using the Admin Creation Script

The `create_admin.py` script is located in the project root and can create admin users with full privileges.

#### Basic Usage

```bash
docker-compose exec backend python3 /app/create_admin.py \
  --email "admin@example.com" \
  --username "admin" \
  --password "secure_password_123" \
  --full-name "Admin User"
```

#### Script Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--email` | Yes | Admin's email address | `admin@company.com` |
| `--username` | Yes | Admin's username | `admin` |
| `--password` | Yes | Admin's password | `SecurePass123!` |
| `--full-name` | No | Admin's full name | `John Admin` |

#### Example Commands

**Create main admin account:**
```bash
docker-compose exec backend python3 /app/create_admin.py \
  --email "admin@yourcompany.com" \
  --username "admin" \
  --password "YourSecurePassword123!" \
  --full-name "System Administrator"
```

**Create additional admin users:**
```bash
# IT Admin
docker-compose exec backend python3 /app/create_admin.py \
  --email "it-admin@yourcompany.com" \
  --username "it_admin" \
  --password "ITSecurePass456!" \
  --full-name "IT Administrator"

# Support Admin
docker-compose exec backend python3 /app/create_admin.py \
  --email "support@yourcompany.com" \
  --username "support_admin" \
  --password "SupportPass789!" \
  --full-name "Support Administrator"
```

### Admin User Properties

Admin users created with this script have the following properties:

- **Role**: `admin`
- **Subscription Tier**: `enterprise`
- **Subscription Status**: `active`
- **Account Status**: `is_active = True`
- **Email Verification**: `is_verified = True`
- **Password**: Securely hashed with bcrypt

## Troubleshooting

### Common Issues and Solutions

#### 1. "relation 'users' does not exist"

**Problem**: Database tables haven't been created yet.

**Solution**:
```bash
docker-compose exec backend python3 -c "from src.database.connection import create_tables; create_tables()"
```

#### 2. "User already exists"

**Problem**: Trying to create a user with an email or username that already exists.

**Solution**: Either use different credentials or delete the existing user first.

#### 3. Container not running

**Problem**: Backend container is not running.

**Solution**:
```bash
# Check container status
docker-compose ps

# Start services if not running
docker-compose up -d

# Check logs if container fails to start
docker-compose logs backend
```

#### 4. Database connection issues

**Problem**: Cannot connect to the database.

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database service
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

## Security Best Practices

### Password Requirements

- Use strong passwords (minimum 12 characters)
- Include uppercase, lowercase, numbers, and special characters
- Avoid common passwords or dictionary words
- Consider using a password manager

### Admin Account Management

1. **Limit admin accounts**: Only create admin accounts for users who need administrative privileges
2. **Regular password changes**: Update admin passwords periodically
3. **Monitor admin activity**: Keep track of admin logins and actions
4. **Remove unused accounts**: Deactivate or delete admin accounts that are no longer needed

### Environment Security

- Never use default passwords in production
- Ensure `.env` file contains secure values
- Use HTTPS in production environments
- Enable proper logging and monitoring

## Verification

### Check if Admin User was Created

```bash
# Verify admin user exists in database
docker-compose exec backend python3 -c "
from src.database.connection import SessionLocal
from src.database.models import User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    print(f'Admin user found: {admin.email} ({admin.role})')
else:
    print('Admin user not found')
db.close()
"
```

### List All Admin Users

```bash
# List all users with admin role
docker-compose exec backend python3 -c "
from src.database.connection import SessionLocal
from src.database.models import User
db = SessionLocal()
admins = db.query(User).filter(User.role == 'admin').all()
print(f'Found {len(admins)} admin users:')
for admin in admins:
    print(f'  - {admin.username} ({admin.email}) - {admin.subscription_tier}')
db.close()
"
```

## Quick Reference Commands

```bash
# Navigate to project
cd "/Users/1kpier/Agentic Framework"

# Start services
docker-compose up -d

# Create database tables (if needed)
docker-compose exec backend python3 -c "from src.database.connection import create_tables; create_tables()"

# Create admin user
docker-compose exec backend python3 /app/create_admin.py \
  --email "your@email.com" \
  --username "yourusername" \
  --password "yourpassword" \
  --full-name "Your Name"

# Verify admin creation
docker-compose exec backend python3 -c "
from src.database.connection import SessionLocal
from src.database.models import User
db = SessionLocal()
admin = db.query(User).filter(User.username == 'yourusername').first()
print(f'User created: {admin.email if admin else \"Not found\"}')
db.close()
"
```

## Notes

- The bcrypt warning during user creation is normal and doesn't affect functionality
- Admin users have access to all platform features and administrative functions
- Keep this guide updated when making changes to the admin creation process
- Always test admin account creation in development before running in production

## Support

If you encounter issues not covered in this guide:

1. Check the application logs: `docker-compose logs backend`
2. Verify database connectivity: `docker-compose logs postgres`
3. Ensure all environment variables are properly set in `.env`
4. Restart services: `docker-compose restart`

---

*Last updated: [Current Date]*
*For technical support, contact the development team.* 