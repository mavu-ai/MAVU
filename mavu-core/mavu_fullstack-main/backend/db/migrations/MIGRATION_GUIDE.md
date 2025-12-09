# Database Migrations Guide

This project uses Alembic for database schema migrations.

## Directory Structure

```
backend/
├── alembic.ini                 # Alembic configuration file
└── db/
    └── migrations/             # Migration scripts directory
        ├── env.py             # Alembic environment configuration
        ├── script.py.mako     # Migration template
        └── versions/          # Migration version files
            └── 6f6bdc38f2dc_initial_migration.py
```

## Configuration

The Alembic setup is already configured to:
- Read migrations from `backend/db/migrations/`
- Use database URL from `config.py` settings
- Auto-import all models from the `models/` package
- Support both online and offline migration modes

## Common Commands

All commands should be run from the `backend/` directory.

### Check Current Migration Status

```bash
# Show current database version
alembic current

# Check if database is up to date
alembic check

# Show migration history
alembic history
```

### Create New Migration

**Auto-generate migration (recommended):**
```bash
# Detects model changes automatically
alembic revision --autogenerate -m "Add user preferences table"
```

**Create empty migration:**
```bash
# For manual SQL or data migrations
alembic revision -m "Migrate legacy data"
```

### Apply Migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade to specific revision
alembic upgrade 6f6bdc38f2dc

# Upgrade one version forward
alembic upgrade +1
```

### Rollback Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 6f6bdc38f2dc

# Downgrade to base (remove all migrations)
alembic downgrade base
```

## Migration Workflow

### 1. Make Model Changes

Edit your SQLAlchemy models in `backend/models/`:

```python
# backend/models/user.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    # NEW: Add a field
    phone = Column(String, nullable=True)
```

### 2. Generate Migration

```bash
cd backend
alembic revision --autogenerate -m "Add phone field to users"
```

This creates a new file in `db/migrations/versions/` like:
```
abc123def456_add_phone_field_to_users.py
```

### 3. Review Migration

**IMPORTANT:** Always review auto-generated migrations!

```python
def upgrade() -> None:
    # Check these operations are correct
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))

def downgrade() -> None:
    # Verify rollback logic
    op.drop_column('users', 'phone')
```

### 4. Apply Migration

```bash
# In development
alembic upgrade head

# In production (via GitLab CI/CD)
# Migrations run automatically during deployment
```

## Production Deployment

Migrations are automatically applied during GitLab CI/CD deployment:

```yaml
# .gitlab-ci.yml
deploy:backend:
  script:
    - ssh $USER@$HOST "cd /root/mavuai && alembic upgrade head"
    - ssh $USER@$HOST "docker-compose up -d backend"
```

**Manual production migration:**
```bash
ssh root@147.45.245.105
cd /root/mavuai/backend
alembic upgrade head
```

## Best Practices

### ✅ DO

- Always use `--autogenerate` for schema changes
- Review generated migrations before applying
- Test migrations on development database first
- Write meaningful migration messages
- Keep migrations small and focused
- Commit migrations with the code changes

### ❌ DON'T

- Don't edit applied migrations (create a new one instead)
- Don't run migrations manually in production (use CI/CD)
- Don't skip migration review (auto-generate isn't perfect)
- Don't delete migration files
- Don't change migration order

## Troubleshooting

### Migration Already Applied

```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solution:** Run `alembic upgrade head`

### Model Changes Not Detected

```
INFO  [alembic.autogenerate.compare] Detected no changes
```

**Causes:**
1. Model not imported in `env.py` (check lines 36-39)
2. Changes already applied to database
3. Database tables created with `Base.metadata.create_all()` instead of migrations

**Solution:** Check your model is imported in `db/migrations/env.py`:
```python
from models import (
    User, Session, Chat, EmailVerification,
    FCMDevice, Threat, PromoCode, PaymeTransaction
)
```

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:** Check database is running and `.env` is configured:
```bash
# Check PostgreSQL
docker ps | grep postgres

# Verify .env has correct DATABASE_URL
cat .env | grep DATABASE_URL
```

### Conflicting Migrations

```
alembic.util.exc.CommandError: Multiple head revisions are present
```

**Solution:** Merge migrations:
```bash
alembic merge heads -m "Merge migrations"
```

## Migration File Example

```python
"""Add user phone field

Revision ID: abc123def456
Revises: 6f6bdc38f2dc
Create Date: 2025-12-07 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = '6f6bdc38f2dc'

def upgrade() -> None:
    op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    op.create_index('ix_users_phone', 'users', ['phone'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_column('users', 'phone')
```

## Replacing `init_db()` with Migrations

The old approach used `Base.metadata.create_all()`:

```python
# OLD: backend/dependencies/database.py
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
```

**New approach using migrations:**

```bash
# Instead of init_db(), use:
alembic upgrade head
```

**Benefits:**
- Version control for database schema
- Reversible changes (downgrade)
- Track schema history
- Safer production deployments
- Team collaboration on schema changes

## Current Migration Status

The project has one migration:

- **6f6bdc38f2dc** - Initial migration (removes `user_id` column from users table)

To apply this migration to your database:

```bash
cd backend
alembic upgrade head
```

---

**For more information:** https://alembic.sqlalchemy.org/en/latest/
