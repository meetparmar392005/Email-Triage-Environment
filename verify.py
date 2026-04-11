#!/usr/bin/env python3
"""
Pre-Submission Verification Script
Run this to verify everything is working before Phase 2 submission.
"""

import sys
import os

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    try:
        from email_triage_env import EmailAction, EmailObservation, EmailState, EmailTriageEnv
        print("  ✅ email_triage_env imports OK")
    except Exception as e:
        print(f"  ❌ email_triage_env imports FAILED: {e}")
        return False
    
    try:
        from server.app import app
        print("  ✅ server.app imports OK")
    except Exception as e:
        print(f"  ❌ server.app imports FAILED: {e}")
        return False
    
    try:
        from server.tasks import TASKS
        print("  ✅ server.tasks imports OK")
    except Exception as e:
        print(f"  ❌ server.tasks imports FAILED: {e}")
        return False
    
    try:
        from server.email_environment import EmailEnvironment
        print("  ✅ server.email_environment imports OK")
    except Exception as e:
        print(f"  ❌ server.email_environment imports FAILED: {e}")
        return False
    
    return True


def test_tasks():
    """Test task definitions."""
    print("\nTesting tasks...")
    try:
        from server.tasks import TASKS
        
        if len(TASKS) != 3:
            print(f"  ❌ Expected 3 tasks, found {len(TASKS)}")
            return False
        print(f"  ✅ 3 tasks defined: {list(TASKS.keys())}")
        
        for task_id in ["easy", "medium", "hard"]:
            if task_id not in TASKS:
                print(f"  ❌ Task '{task_id}' not found")
                return False
        print("  ✅ All required tasks present")
        
        return True
    except Exception as e:
        print(f"  ❌ Task test FAILED: {e}")
        return False


def test_graders():
    """Test grader functions."""
    print("\nTesting graders...")
    try:
        from server.tasks import TASKS
        from email_triage_env.models import EmailAction
        
        # Test easy grader
        task = TASKS["easy"]
        email = task.sample_email()
        action = EmailAction(action_type="classify", value="spam")
        score, reason = task.grade(action, email)
        
        if not (0.0 <= score <= 1.0):
            print(f"  ❌ Easy grader score out of range: {score}")
            return False
        print(f"  ✅ Easy grader OK (score={score:.2f})")
        
        # Test medium grader
        task = TASKS["medium"]
        email = task.sample_email()
        action = EmailAction(action_type="prioritize", value="high")
        score, reason = task.grade(action, email)
        
        if not (0.0 <= score <= 1.0):
            print(f"  ❌ Medium grader score out of range: {score}")
            return False
        print(f"  ✅ Medium grader OK (score={score:.2f})")
        
        # Test hard grader
        task = TASKS["hard"]
        email = task.sample_email()
        action = EmailAction(action_type="reply", value="Thank you for your message. I will respond shortly.")
        score, reason = task.grade(action, email)
        
        if not (0.0 <= score <= 1.0):
            print(f"  ❌ Hard grader score out of range: {score}")
            return False
        print(f"  ✅ Hard grader OK (score={score:.2f})")
        
        return True
    except Exception as e:
        print(f"  ❌ Grader test FAILED: {e}")
        return False


def test_environment():
    """Test environment logic."""
    print("\nTesting environment...")
    try:
        from server.email_environment import EmailEnvironment
        from email_triage_env.models import EmailAction
        
        env = EmailEnvironment()
        
        # Test reset
        obs = env.reset("easy")
        if obs.task_id != "easy":
            print(f"  ❌ Reset failed: wrong task_id")
            return False
        if obs.step_num != 0:
            print(f"  ❌ Reset failed: step_num should be 0")
            return False
        print("  ✅ Reset OK")
        
        # Test step
        action = EmailAction(action_type="classify", value="spam")
        obs, reward, done = env.step(action)
        
        if not (0.0 <= reward <= 1.0):
            print(f"  ❌ Step failed: reward out of range: {reward}")
            return False
        if obs.step_num != 1:
            print(f"  ❌ Step failed: step_num should be 1")
            return False
        print(f"  ✅ Step OK (reward={reward:.2f}, done={done})")
        
        # Test state
        state = env.state()
        if state.task_id != "easy":
            print(f"  ❌ State failed: wrong task_id")
            return False
        print("  ✅ State OK")
        
        # Test grader_result
        result = env.grader_result()
        if "normalized_score" not in result:
            print(f"  ❌ Grader result missing normalized_score")
            return False
        if not (0.0 <= result["normalized_score"] <= 1.0):
            print(f"  ❌ Normalized score out of range: {result['normalized_score']}")
            return False
        print(f"  ✅ Grader result OK (normalized_score={result['normalized_score']:.2f})")
        
        return True
    except Exception as e:
        print(f"  ❌ Environment test FAILED: {e}")
        return False


def test_pyproject():
    """Test pyproject.toml configuration."""
    print("\nTesting pyproject.toml...")
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
        
        if 'server = "server.app:main"' not in content:
            print("  ❌ Missing correct server entry point")
            return False
        print("  ✅ Server entry point correct")
        
        if "httpx" not in content:
            print("  ❌ Missing httpx dependency")
            return False
        print("  ✅ httpx dependency present")
        
        if "openenv-core" not in content:
            print("  ❌ Missing openenv-core dependency")
            return False
        print("  ✅ openenv-core dependency present")
        
        return True
    except Exception as e:
        print(f"  ❌ pyproject.toml test FAILED: {e}")
        return False


def test_inference():
    """Test inference.py structure."""
    print("\nTesting inference.py...")
    try:
        with open("inference.py", "r") as f:
            content = f.read()
        
        if "API_BASE_URL" not in content:
            print("  ❌ Missing API_BASE_URL")
            return False
        print("  ✅ API_BASE_URL present")
        
        if "MODEL_NAME" not in content:
            print("  ❌ Missing MODEL_NAME")
            return False
        print("  ✅ MODEL_NAME present")
        
        if "HF_TOKEN" not in content:
            print("  ❌ Missing HF_TOKEN")
            return False
        print("  ✅ HF_TOKEN present")
        
        if "[START]" not in content:
            print("  ❌ Missing [START] log")
            return False
        print("  ✅ [START] log present")
        
        if "[STEP]" not in content:
            print("  ❌ Missing [STEP] log")
            return False
        print("  ✅ [STEP] log present")
        
        if "[END]" not in content:
            print("  ❌ Missing [END] log")
            return False
        print("  ✅ [END] log present")
        
        if '.replace("\\n", " ")' not in content:
            print("  ❌ Missing newline replacement in action logging")
            return False
        print("  ✅ Newline replacement present")
        
        return True
    except Exception as e:
        print(f"  ❌ inference.py test FAILED: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("PRE-SUBMISSION VERIFICATION")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Tasks", test_tasks),
        ("Graders", test_graders),
        ("Environment", test_environment),
        ("pyproject.toml", test_pyproject),
        ("inference.py", test_inference),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! READY FOR PHASE 2! 🎉")
        print("\n✅ You can submit with 100% confidence.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Fix issues before submitting.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
