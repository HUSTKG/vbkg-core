# debug_your_project.py - Debug script specifically for your project structure
# Save this in your PROJECT ROOT (same directory as main.py)

import os
import sys
import redis
import time

def test_your_celery_setup():
    """Test your existing Celery setup"""
    
    print("=== Testing Your Celery Setup ===")
    
    try:
        # Test import of your worker
        from app.tasks.worker import celery_app
        print("✓ Successfully imported app.tasks.worker.celery_app")
        
        # Show configuration
        print(f"✓ Broker: {celery_app.conf.broker_url}")
        print(f"✓ Backend: {celery_app.conf.result_backend}")
        print(f"✓ Eager mode: {celery_app.conf.task_always_eager}")
        
        # Check registered tasks
        tasks = list(celery_app.tasks.keys())
        print(f"✓ Registered tasks: {len(tasks)}")
        
        # Show your specific tasks
        your_tasks = [t for t in tasks if not t.startswith('celery.')]
        if your_tasks:
            print("Your custom tasks:")
            for task in your_tasks:
                print(f"  - {task}")
        
        return celery_app
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Check if app/tasks/worker.py exists and exports 'celery_app'")
        return None
    except Exception as e:
        print(f"❌ Other error: {e}")
        return None

def test_your_pipeline_tasks():
    """Test your specific pipeline tasks"""
    
    print("\n=== Testing Your Pipeline Tasks ===")
    
    try:
        # Import your specific tasks
        from app.tasks.worker import run_pipeline_task
        
        print("✓ Successfully imported pipeline tasks")
        
        # Test submitting a pipeline task
        print("📤 Submitting test pipeline task...")
        result = run_pipeline_task.delay(
            pipeline_id="debug-test-123",
            run_id="debug-run-123",
            user_id="debug-user"
        )
        
        print(f"✓ Pipeline task submitted: {result.id}")
        print(f"✓ Task state: {result.state}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_your_queues():
    """Check Redis queues for your project"""
    
    print("\n=== Checking Your Redis Queues ===")
    
    try:
        # Connect to Redis using your config
        from app.core.config import settings
        
        redis_url = settings.CELERY_BROKER_URL
        r = redis.from_url(redis_url)
        
        print(f"✓ Connected to Redis: {redis_url}")
        
        # Check your specific queues (from your worker.py)
        queues = ['celery', 'pipeline', 'steps']
        
        print("\nQueue status:")
        total_tasks = 0
        for queue in queues:
            length = r.llen(queue)
            total_tasks += length
            status = "📨" if length > 0 else "✓"
            print(f"  {status} {queue}: {length} tasks")
        
        if total_tasks > 0:
            print(f"\n🎯 Total tasks in queues: {total_tasks}")
            print("Tasks are being submitted! Check if worker is consuming them.")
        else:
            print("\n📭 No tasks in queues")
            print("Submit some tasks to test the flow")
        
        return r
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None

def test_your_services():
    """Test your pipeline service"""
    
    print("\n=== Testing Your Pipeline Service ===")
    
    try:
        from app.services.pipeline import PipelineService
        
        print("✓ Successfully imported PipelineService")
        
        # Note: Don't actually execute since it needs real data
        print("⚠️  Skipping actual service test (needs database)")
        print("Your service layer imports work correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Service import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_worker_status():
    """Check if your worker is running"""
    
    print("\n=== Checking Worker Status ===")
    
    try:
        from app.tasks.worker import celery_app
        
        # Check worker connection
        inspect = celery_app.control.inspect()
        
        # Get active workers
        stats = inspect.stats()
        if stats:
            print(f"✓ Found {len(stats)} active workers:")
            for worker_name, worker_stats in stats.items():
                print(f"  - {worker_name}")
                pool_info = worker_stats.get('pool', {})
                print(f"    Processes: {pool_info.get('processes', 'unknown')}")
                print(f"    Pool: {pool_info.get('implementation', 'unknown')}")
        else:
            print("❌ No active workers found")
            print("\nStart worker with:")
            print("  celery -A app.tasks.worker worker --loglevel=info")
            print("Or use your existing script:")
            print("  ./scripts/start_celery.sh")
            return False
        
        # Check registered tasks on workers
        registered = inspect.registered()
        if registered:
            print(f"\n📋 Tasks registered on workers:")
            for worker, tasks in registered.items():
                your_tasks = [t for t in tasks if 'pipeline' in t or 'run_' in t]
                if your_tasks:
                    print(f"  {worker}: {len(your_tasks)} pipeline tasks")
                    for task in your_tasks[:3]:
                        print(f"    - {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker status check failed: {e}")
        return False

def monitor_task_flow():
    """Monitor your task flow"""
    
    print("\n=== Monitoring Task Flow ===")
    print("Watching for 30 seconds... submit tasks in another terminal")
    print("Use: python -c \"from app.tasks.worker import run_pipeline_task; print(run_pipeline_task.delay('test', 'test', 'test'))\"")
    print("-" * 60)
    
    try:
        from app.core.config import settings
        r = redis.from_url(settings.CELERY_BROKER_URL)
        
        queues = ['celery', 'pipeline', 'steps']
        initial_state = {q: r.llen(q) for q in queues}
        
        for i in range(30):
            current_state = {q: r.llen(q) for q in queues}
            
            # Check for changes
            changes = []
            for queue in queues:
                if current_state[queue] != initial_state[queue]:
                    change = current_state[queue] - initial_state[queue]
                    changes.append(f"{queue}: {change:+d}")
            
            timestamp = time.strftime('%H:%M:%S')
            
            if changes:
                print(f"{timestamp} 📊 Changes: {', '.join(changes)}")
                initial_state = current_state
            else:
                # Show current state
                summary = ', '.join([f"{q}:{current_state[q]}" for q in queues])
                print(f"\r{timestamp} - {summary}", end="", flush=True)
            
            time.sleep(1)
        
        print(f"\n\nFinal state:")
        for queue in queues:
            print(f"  {queue}: {r.llen(queue)} tasks")
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring stopped")
    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")

if __name__ == "__main__":
    print("Debug Script for Your Knowledge Graph Project")
    print("=" * 60)
    
    # Test 1: Celery setup
    celery_app = test_your_celery_setup()
    if not celery_app:
        print("\n❌ Fix Celery setup first!")
        sys.exit(1)
    
    # Test 2: Redis queues
    redis_conn = check_your_queues()
    
    # Test 3: Your services
    test_your_services()
    
    # Test 4: Pipeline tasks
    test_your_pipeline_tasks()
    
    # Test 5: Worker status
    worker_running = check_worker_status()
    
    # Test 6: Monitor if requested
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"- Celery app: {'✓' if celery_app else '❌'}")
    print(f"- Redis connection: {'✓' if redis_conn else '❌'}")
    print(f"- Worker running: {'✓' if worker_running else '❌'}")
    
    if celery_app and redis_conn:
        print(f"\n✅ Basic setup is working!")
        if not worker_running:
            print("Start your worker with: ./scripts/start_celery.sh")
        
        monitor_choice = input("\nMonitor task flow? (y/n): ").lower()
        if monitor_choice == 'y':
            monitor_task_flow()
    else:
        print(f"\n❌ Fix the issues above first")
