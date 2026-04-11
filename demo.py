#!/usr/bin/env python3
"""
Email Triage Environment - Automated Demo Script

This script demonstrates how to use the Email Triage Environment
for evaluating AI agents on email handling tasks.

The script automatically starts the server, runs demos, and cleans up.

Usage:
    python demo.py
"""

import sys
import time
import subprocess
from email_triage_env import EmailAction, EmailTriageEnv


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print a formatted section."""
    print(f"\n--- {text} ---")


def start_server():
    """Start the FastAPI server in a subprocess."""
    print_section("Starting server")
    print("Launching uvicorn server on http://localhost:7860...")
    
    try:
        # Start server process
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start (check for up to 10 seconds)
        print("Waiting for server to start", end="", flush=True)
        for i in range(20):
            time.sleep(0.5)
            print(".", end="", flush=True)
            
            # Check if server is ready
            try:
                import httpx
                response = httpx.get("http://localhost:7860/health", timeout=1.0)
                if response.status_code == 200:
                    print(" ✓")
                    print("Server started successfully!")
                    return process
            except:
                pass
        
        print(" ✗")
        print("Warning: Server may not have started properly")
        return process
        
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        return None


def stop_server(process):
    """Stop the server process."""
    if process:
        print_section("Stopping server")
        print("Shutting down server...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✓ Server stopped successfully")
        except:
            process.kill()
            print("✓ Server forcefully stopped")


def demo_easy_task(env: EmailTriageEnv):
    """Demonstrate the easy task (spam classification)."""
    print_header("DEMO 1: Easy Task - Spam Classification")
    
    # Reset environment
    print_section("Resetting environment with 'easy' task")
    obs = env.reset(task_id="easy")
    
    print(f"Task ID: {obs.task_id}")
    print(f"Instructions: {obs.instructions}")
    print(f"\nEmail to classify:")
    print(f"  From: {obs.email.get('sender', 'N/A')}")
    print(f"  Subject: {obs.email.get('subject', 'N/A')}")
    print(f"  Body: {obs.email.get('body', 'N/A')[:100]}...")
    
    # Take action
    print_section("Taking action: classify as 'spam'")
    action = EmailAction(action_type="classify", value="spam")
    result = env.step(action)
    
    print(f"Reward: {result.reward:.2f}")
    print(f"Done: {result.done}")
    print(f"Step: {result.observation.step_num}")
    
    # Get final state
    state = env.state()
    print_section("Final state")
    print(f"Cumulative score: {state.cumulative_score:.2f}")
    print(f"Episode done: {state.done}")


def demo_medium_task(env: EmailTriageEnv):
    """Demonstrate the medium task (priority assignment)."""
    print_header("DEMO 2: Medium Task - Priority Assignment")
    
    # Reset environment
    print_section("Resetting environment with 'medium' task")
    obs = env.reset(task_id="medium")
    
    print(f"Task ID: {obs.task_id}")
    print(f"Instructions: {obs.instructions}")
    print(f"\nEmail to prioritize:")
    print(f"  From: {obs.email.get('sender', 'N/A')}")
    print(f"  Subject: {obs.email.get('subject', 'N/A')}")
    print(f"  Body: {obs.email.get('body', 'N/A')[:100]}...")
    
    # Take action
    print_section("Taking action: prioritize as 'high'")
    action = EmailAction(action_type="prioritize", value="high")
    result = env.step(action)
    
    print(f"Reward: {result.reward:.2f}")
    print(f"Done: {result.done}")
    print(f"Step: {result.observation.step_num}")
    
    # Get final state
    state = env.state()
    print_section("Final state")
    print(f"Cumulative score: {state.cumulative_score:.2f}")
    print(f"Episode done: {state.done}")


def demo_hard_task(env: EmailTriageEnv):
    """Demonstrate the hard task (reply generation)."""
    print_header("DEMO 3: Hard Task - Reply Generation")
    
    # Reset environment
    print_section("Resetting environment with 'hard' task")
    obs = env.reset(task_id="hard")
    
    print(f"Task ID: {obs.task_id}")
    print(f"Instructions: {obs.instructions}")
    print(f"\nEmail to reply to:")
    print(f"  From: {obs.email.get('sender', 'N/A')}")
    print(f"  Subject: {obs.email.get('subject', 'N/A')}")
    print(f"  Body: {obs.email.get('body', 'N/A')}")
    
    # Take action
    reply_text = (
        "Thank you for reaching out. I have reviewed your message and "
        "understand your request. I will get back to you with a detailed "
        "response by the end of the business day. Please let me know if "
        "you have any urgent concerns in the meantime."
    )
    
    print_section("Taking action: draft reply")
    print(f"Reply: {reply_text}")
    
    action = EmailAction(action_type="reply", value=reply_text)
    result = env.step(action)
    
    print(f"\nReward: {result.reward:.2f}")
    print(f"Done: {result.done}")
    print(f"Step: {result.observation.step_num}")
    
    # Get final state
    state = env.state()
    print_section("Final state")
    print(f"Cumulative score: {state.cumulative_score:.2f}")
    print(f"Episode done: {state.done}")


def demo_multi_step_episode(env: EmailTriageEnv):
    """Demonstrate a multi-step episode."""
    print_header("DEMO 4: Multi-Step Episode")
    
    # Reset environment
    print_section("Resetting environment with 'medium' task")
    obs = env.reset(task_id="medium")
    
    print(f"Email to prioritize:")
    print(f"  Subject: {obs.email.get('subject', 'N/A')}")
    
    # Try multiple actions
    priorities = ["low", "medium", "high", "critical"]
    
    for i, priority in enumerate(priorities, 1):
        if obs.step_num >= 5:  # MAX_STEPS
            print("\nReached maximum steps!")
            break
        
        print_section(f"Step {i}: Trying priority '{priority}'")
        action = EmailAction(action_type="prioritize", value=priority)
        result = env.step(action)
        
        print(f"Reward: {result.reward:.2f}")
        print(f"Done: {result.done}")
        
        if result.done:
            print(f"\nEpisode completed after {i} step(s)!")
            break
        
        obs = result.observation
    
    # Get final state
    state = env.state()
    print_section("Final state")
    print(f"Total steps: {state.step_num}")
    print(f"Cumulative score: {state.cumulative_score:.2f}")
    print(f"Episode done: {state.done}")


def main():
    """Run all demos with automatic server management."""
    print_header("Email Triage Environment - Automated Demo")
    print("\nThis demo automatically starts the server and runs all demonstrations.")
    print("Press Ctrl+C at any time to exit.\n")
    
    server_process = None
    
    try:
        # Start server
        server_process = start_server()
        if not server_process:
            print("\n✗ Failed to start server. Please start it manually:")
            print("  uvicorn server.app:app --host 0.0.0.0 --port 7860")
            sys.exit(1)
        
        # Give server a moment to fully initialize
        time.sleep(1)
        
        # Connect to environment
        print_section("Connecting to environment")
        base_url = "http://localhost:7860"
        print(f"Base URL: {base_url}")
        
        with EmailTriageEnv(base_url=base_url) as env:
            print("✓ Connected successfully!")
            
            # Run demos
            demo_easy_task(env)
            input("\nPress Enter to continue to next demo...")
            
            demo_medium_task(env)
            input("\nPress Enter to continue to next demo...")
            
            demo_hard_task(env)
            input("\nPress Enter to continue to next demo...")
            
            demo_multi_step_episode(env)
            
            print_header("Demo Complete!")
            print("\nAll demos completed successfully!")
            print("\nNext steps:")
            print("  1. Explore the Swagger UI at http://localhost:7860/docs")
            print("  2. Run inference.py to test with an LLM")
            print("  3. Build your own agent using the EmailTriageEnv client")
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except ConnectionError as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nThe server may not have started properly.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always stop the server
        if server_process:
            stop_server(server_process)


if __name__ == "__main__":
    main()
