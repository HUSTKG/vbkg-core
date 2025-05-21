# debug_celery.py - Run this to test Celery setup
import os
import sys

# Add your project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_celery_connection():
    """Test basic Celery connection and task execution"""

    print("=== Testing Celery Connection ===")

    try:
        # Import Celery app
        from app.tasks.worker import celery_app, test_pipeline_task

        print(f"✓ Celery app imported successfully")
        print(f"✓ Broker URL: {celery_app.conf.broker_url}")
        print(f"✓ Result backend: {celery_app.conf.result_backend}")

        # Test broker connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            print(f"✓ Connected to broker - Found {len(stats)} workers")
            for worker, worker_stats in stats.items():
                print(f"  Worker: {worker}")
        else:
            print("✗ No workers found - Make sure you started the Celery worker")
            return False

        # Test simple task
        print("\n=== Testing Simple Task ===")
        result = test_pipeline_task.delay("Hello from debug script!")
        print(f"✓ Task submitted with ID: {result.id}")

        # Wait for result
        try:
            task_result = result.get(timeout=30)
            print(f"✓ Task completed: {task_result}")
        except Exception as e:
            print(f"✗ Task failed: {e}")
            return False

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False


def test_pipeline_task():
    """Test pipeline-specific tasks"""

    print("\n=== Testing Pipeline Tasks ===")

    try:
        from app.tasks.worker import test_pipeline_task

        # Test the pipeline test task
        result = test_pipeline_task.delay("Pipeline test message")
        print(f"✓ Pipeline task submitted with ID: {result.id}")

        task_result = result.get(timeout=30)
        print(f"✓ Pipeline task completed: {task_result}")

        return True

    except Exception as e:
        print(f"✗ Pipeline task error: {e}")
        return False


def check_redis_connection():
    """Check Redis connection independently"""

    print("\n=== Testing Redis Connection ===")

    try:
        import redis

        redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)

        # Test ping
        r.ping()
        print(f"✓ Redis connection successful: {redis_url}")

        # Test basic operations
        r.set("test_key", "test_value")
        value = r.get("test_key")
        r.delete("test_key")

        print(f"✓ Redis read/write successful")
        return True

    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("Make sure Redis is running on localhost:6379")
        return False


def check_environment():
    """Check environment and dependencies"""

    print("=== Environment Check ===")

    # Check environment variables
    env_vars = [
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
    ]

    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        print(f"{var}: {value}")

    # Check Python packages
    try:
        import celery

        print(f"✓ Celery version: {celery.__version__}")
    except ImportError:
        print("✗ Celery not installed")

    try:
        import redis

        print(f"✓ Redis package available")
    except ImportError:
        print("✗ Redis package not installed")


if __name__ == "__main__":
    print("Celery Debug Script")
    print("==================")

    # Step 1: Check environment
    check_environment()

    # Step 2: Check Redis
    if not check_redis_connection():
        print("\n❌ Redis connection failed. Please start Redis and try again.")
        sys.exit(1)

    # Step 3: Test Celery connection
    if not test_celery_connection():
        print(
            "\n❌ Celery connection failed. Please start Celery worker and try again."
        )
        print("\nTo start Celery worker, run:")
        print("celery -A app.celery_app worker --loglevel=info")
        sys.exit(1)

    # Step 4: Test pipeline tasks
    if test_pipeline_task():
        print("\n✅ All tests passed! Celery is working correctly.")
    else:
        print("\n⚠️ Basic Celery works, but pipeline tasks have issues.")

    print("\nNext steps:")
    print("1. Make sure your pipeline and step services are working")
    print("2. Test creating and running a simple pipeline")
    print("3. Check the Celery worker logs for any errors")
