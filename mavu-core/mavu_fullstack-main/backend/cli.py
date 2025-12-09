"""CLI for MavuAI - Superuser creation, promo code management, and RAG patterns."""
import asyncio
import re
import secrets
import click
from pathlib import Path
from sqlalchemy import select

from dependencies.database import SessionLocal
from models.user import User
from models.promo_code import PromoCode
from utils.password import hash_password
from config import settings


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Validate username format (3-30 chars, alphanumeric + underscores)."""
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None


@click.command("create-superuser")
@click.option("--email", "-e", help="Email address")
@click.option("--username", "-u", help="Username")
@click.option("--password", "-p", help="Password")
def create_superuser_command(email, username, password):
    """Create a superuser with admin access."""

    # Interactive prompts if not provided
    if not email:
        email = click.prompt("Email")

    if not validate_email(email):
        click.echo("Error: Invalid email format", err=True)
        raise click.Abort()

    if not username:
        username = click.prompt("Username")

    if not validate_username(username):
        click.echo("Error: Username must be 3-30 chars (alphanumeric + underscores)", err=True)
        raise click.Abort()

    if not password:
        password = click.prompt("Password", hide_input=True)
        confirm = click.prompt("Confirm Password", hide_input=True)

        if password != confirm:
            click.echo("Error: Passwords do not match", err=True)
            raise click.Abort()

    if len(password) < 8:
        click.echo("Error: Password must be at least 8 characters", err=True)
        raise click.Abort()

    # Create superuser
    try:
        db = SessionLocal()

        # Check if user exists (SQLAlchemy 2.0 syntax)
        stmt = select(User).where(
            (User.email == email) | (User.username == username)
        )
        existing = db.execute(stmt).scalars().first()

        if existing:
            click.echo("Error: User with this email or username already exists", err=True)
            db.close()
            raise click.Abort()

        # Create user
        user = User(
            email=email,
            username=username,
            name=username,  # Use username as name
            password_hash=hash_password(password),
            is_active=True,
            is_verified=True,
            is_admin=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        click.echo("\n✅ Superuser created successfully!")
        click.echo(f"Email: {user.email}")
        click.echo(f"Username: {user.username}")
        click.echo(f"Admin: Yes")
        click.echo(f"\nLogin at: http://localhost:8000/admin")

        db.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("create-promo-codes")
@click.option("--count", "-c", default=10, help="Number of promo codes to generate")
@click.option("--length", "-l", default=8, help="Length of each promo code")
@click.option("--prefix", "-p", default="MAVU", help="Prefix for promo codes")
def create_promo_codes_command(count, length, prefix):
    """Generate promo codes for user registration."""
    try:
        db = SessionLocal()

        click.echo(f"\nGenerating {count} promo codes...")

        created_codes = []
        for i in range(count):
            # Generate random code
            random_part = secrets.token_hex(length // 2).upper()[:length - len(prefix)]
            code = f"{prefix}{random_part}"

            # Check if code already exists (SQLAlchemy 2.0 syntax)
            stmt = select(PromoCode).where(PromoCode.code == code)
            existing = db.execute(stmt).scalars().first()
            if existing:
                click.echo(f"Skipping duplicate: {code}")
                continue

            # Create promo code
            promo_code = PromoCode(
                code=code,
                is_active=True
            )

            db.add(promo_code)
            created_codes.append(code)

        db.commit()

        click.echo(f"\n✅ Created {len(created_codes)} promo codes:")
        for code in created_codes:
            click.echo(f"  - {code}")

        db.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("list-promo-codes")
@click.option("--unused-only", "-u", is_flag=True, help="Show only unused promo codes")
def list_promo_codes_command(unused_only):
    """List all promo codes."""
    try:
        db = SessionLocal()

        # Build query (SQLAlchemy 2.0 syntax)
        stmt = select(PromoCode)
        if unused_only:
            stmt = stmt.where(PromoCode.is_active == True)

        codes = db.execute(stmt).scalars().all()

        if not codes:
            click.echo("No promo codes found.")
            db.close()
            return

        click.echo(f"\nPromo Codes ({len(codes)} total):")
        click.echo("-" * 60)

        for code in codes:
            status = "✓ Available" if code.is_active else "✗ Used"
            user_info = f" (User ID: {code.user_id})" if code.user_id else ""
            click.echo(f"{code.code:20s} {status:15s} {user_info}")

        db.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("setup-webhook")
def setup_webhook_command():
    """Setup Telegram webhook."""
    if not settings.telegram_bot_token:
        click.echo("Error: Telegram bot token not configured", err=True)
        raise click.Abort()

    if not settings.telegram_webhook_url:
        click.echo("Error: Telegram webhook URL not configured", err=True)
        raise click.Abort()

    async def _setup():
        from api.v1.endpoints.telegram import setup_webhook
        success = await setup_webhook()
        return success

    try:
        click.echo(f"Setting up Telegram webhook...")
        click.echo(f"Webhook URL: {settings.telegram_webhook_url}")
        success = asyncio.run(_setup())

        if success:
            click.echo("✅ Webhook configured successfully!")
        else:
            click.echo("❌ Failed to configure webhook", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("remove-webhook")
def remove_webhook_command():
    """Remove Telegram webhook."""
    if not settings.telegram_bot_token:
        click.echo("Error: Telegram bot token not configured", err=True)
        raise click.Abort()

    async def _remove():
        from api.v1.endpoints.telegram import remove_webhook
        success = await remove_webhook()
        return success

    try:
        click.echo("Removing Telegram webhook...")
        success = asyncio.run(_remove())

        if success:
            click.echo("✅ Webhook removed successfully!")
        else:
            click.echo("❌ Failed to remove webhook", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("webhook-info")
def webhook_info_command():
    """Get current Telegram webhook info."""
    if not settings.telegram_bot_token:
        click.echo("Error: Telegram bot token not configured", err=True)
        raise click.Abort()

    async def _get_info():
        from api.v1.endpoints.telegram import bot
        info = await bot.get_webhook_info()
        return info

    try:
        info = asyncio.run(_get_info())

        click.echo("\n📡 Telegram Webhook Info:")
        click.echo(f"  URL: {info.url or '(not set)'}")
        click.echo(f"  Pending updates: {info.pending_update_count}")
        click.echo(f"  Last error: {info.last_error_message or 'None'}")
        if info.last_error_date:
            click.echo(f"  Last error date: {info.last_error_date}")
        click.echo(f"  Max connections: {info.max_connections}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("upload-patterns")
@click.option("--dir", "-d", default="../patterns", help="Directory containing pattern files")
@click.option("--category", "-c", help="Filter by category (e.g., communication)")
def upload_patterns_command(dir, category):
    """Upload app pattern files to vector database (RAG)."""
    async def _upload():
        from scripts.upload_mavu_patterns import PatternUploader

        patterns_path = Path(dir)

        if not patterns_path.exists():
            click.echo(f"❌ Error: Directory not found: {dir}")
            click.echo("\n💡 Options:")
            click.echo(f"  1. Create directory: mkdir -p {dir}")
            click.echo("  2. Use custom path: --dir /path/to/patterns")
            return False

        # Count files
        pattern_files = list(patterns_path.glob("*.md")) + list(patterns_path.glob("*.txt"))

        if not pattern_files:
            click.echo(f"❌ No pattern files found in: {dir}")
            click.echo("\n💡 Pattern files should be:")
            click.echo("  - Markdown (.md) or text (.txt)")
            click.echo("  - Named like: pattern_01.md, guide.txt")
            return False

        click.echo(f"\n📦 Uploading Patterns to Vector Database")
        click.echo(f"   Directory: {dir}")
        click.echo(f"   Files: {len(pattern_files)}")
        if category:
            click.echo(f"   Category filter: {category}")
        click.echo()

        try:
            uploader = PatternUploader()
            result = await uploader.upload_patterns(
                patterns_dir=patterns_path,
                category_filter=category
            )

            click.echo(f"\n✅ Upload Complete!")
            click.echo(f"   Patterns: {result.get('patterns_processed', 0)}")
            click.echo(f"   Chunks: {result.get('chunks_created', 0)}")
            click.echo(f"   Time: {result.get('duration', 0):.2f}s")

            return True

        except Exception as e:
            click.echo(f"\n❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    try:
        success = asyncio.run(_upload())
        if not success:
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("list-patterns")
def list_patterns_command():
    """List patterns in vector database."""
    async def _list():
        try:
            from utils.weaviate_client import weaviate_client

            click.echo("\n📚 Patterns in Vector Database")
            click.echo("=" * 60)

            # Connect to Weaviate
            await weaviate_client.connect()

            # Get AppContext collection
            collection = weaviate_client.client.collections.get("AppContext")

            # Get total count
            response = collection.aggregate.over_all(
                total_count=True
            )

            if response.total_count and response.total_count > 0:
                click.echo(f"\n📊 Total app context chunks: {response.total_count}")

                # Try to fetch a sample to show categories
                sample = collection.query.fetch_objects(limit=5)
                if sample.objects:
                    click.echo("\n📝 Sample patterns:")
                    for obj in sample.objects:
                        props = obj.properties
                        category = props.get("category", "N/A")
                        pattern_id = props.get("pattern_id", "N/A")
                        click.echo(f"  • [{category}] {pattern_id}")
            else:
                click.echo("\n❌ No patterns found in vector database")
                click.echo("\n💡 To upload patterns:")
                click.echo("  python cli.py upload-patterns --dir ../patterns")

            # Close connection
            weaviate_client.client.close()

            return True

        except Exception as e:
            click.echo(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    try:
        success = asyncio.run(_list())
        if not success:
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.command("test-rag")
@click.argument("query")
def test_rag_command(query):
    """Test RAG retrieval with a query."""
    async def _test():
        try:
            from rag.pipeline import rag_pipeline
            from utils.weaviate_client import weaviate_client

            click.echo(f"\n🔍 Testing RAG Retrieval")
            click.echo(f"   Query: {query}")
            click.echo()

            # Connect to Weaviate
            await weaviate_client.connect()

            result = await rag_pipeline.retrieve_context(
                query=query,
                owner_id="test_user"
            )

            click.echo(f"✅ Results:")
            click.echo(f"   Method: {result.get('retrieval_method', 'N/A')}")

            user_ctx = result.get("user_context", [])
            app_ctx = result.get("app_context", [])

            if app_ctx:
                click.echo(f"\n   🎓 App Context ({len(app_ctx)}):")
                for i, ctx in enumerate(app_ctx[:3], 1):
                    text = ctx.get("text", "")[:120]
                    score = ctx.get("score", 0)
                    click.echo(f"      {i}. [Score: {score:.3f}] {text}...")

            if user_ctx:
                click.echo(f"\n   📚 User Context ({len(user_ctx)}):")
                for i, ctx in enumerate(user_ctx[:3], 1):
                    text = ctx.get("text", "")[:120]
                    score = ctx.get("score", 0)
                    click.echo(f"      {i}. [Score: {score:.3f}] {text}...")

            if not user_ctx and not app_ctx:
                click.echo("\n   ⚠️ No context retrieved")
                click.echo("\n   Possible reasons:")
                click.echo("      - No patterns uploaded")
                click.echo("      - Query doesn't match patterns")
                click.echo("      - Weaviate not configured")

            return True

        except Exception as e:
            click.echo(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    try:
        success = asyncio.run(_test())
        if not success:
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@click.group()
def cli():
    """MavuAI CLI - Manage users, promo codes, and RAG patterns."""
    pass


@click.command("delete-patterns")
@click.option("--category", "-c", help="Delete patterns by category")
@click.option("--confirm", is_flag=True, help="Confirm deletion without prompting")
def delete_patterns_command(category, confirm):
    """Delete patterns from vector database."""
    async def _delete():
        try:
            from utils.weaviate_client import weaviate_client

            click.echo("\n🗑️  Deleting Patterns from Vector Database")
            click.echo("=" * 60)

            # Connect to Weaviate
            await weaviate_client.connect()

            # Get AppContext collection
            collection = weaviate_client.client.collections.get("AppContext")

            # Get count before deletion
            before_count = collection.aggregate.over_all(total_count=True).total_count or 0

            if not confirm:
                if category:
                    click.echo(f"\n⚠️  This will delete all patterns in category: {category}")
                else:
                    click.echo(f"\n⚠️  This will delete ALL {before_count} patterns!")

                if not click.confirm("\nAre you sure you want to continue?"):
                    click.echo("Deletion cancelled.")
                    return False

            # Delete patterns
            if category:
                # Delete by category
                result = collection.data.delete_many(
                    where={
                        "path": ["category"],
                        "operator": "Equal",
                        "valueText": category
                    }
                )
                click.echo(f"\n✅ Deleted patterns in category: {category}")
            else:
                # Delete all
                result = collection.data.delete_many(
                    where={
                        "path": ["text_chunk"],
                        "operator": "IsNull",
                        "valueBoolean": False
                    }
                )
                click.echo(f"\n✅ Deleted all app context patterns")

            # Get count after deletion
            after_count = collection.aggregate.over_all(total_count=True).total_count or 0
            deleted = before_count - after_count

            click.echo(f"\n📊 Deletion Summary:")
            click.echo(f"   Before: {before_count} patterns")
            click.echo(f"   After: {after_count} patterns")
            click.echo(f"   Deleted: {deleted} patterns")

            # Close connection
            weaviate_client.client.close()

            return True

        except Exception as e:
            click.echo(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    try:
        success = asyncio.run(_delete())
        if not success:
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


cli.add_command(create_superuser_command)
cli.add_command(create_promo_codes_command)
cli.add_command(list_promo_codes_command)
cli.add_command(setup_webhook_command)
cli.add_command(remove_webhook_command)
cli.add_command(webhook_info_command)
cli.add_command(upload_patterns_command)
cli.add_command(list_patterns_command)
cli.add_command(test_rag_command)
cli.add_command(delete_patterns_command)


if __name__ == "__main__":
    cli()
