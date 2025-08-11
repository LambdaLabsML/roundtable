#!/usr/bin/env python3
"""
Script to run real integration tests with actual API keys.

This script provides a convenient way to run integration tests that use real API calls.
It checks for API key availability and provides helpful feedback.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_api_keys():
    """Check if required API keys are available"""
    required_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]
    missing_keys = []
    available_keys = []
    
    print("Checking API key availability...")
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower().replace('_api_key', '')}_api_key_here":
            missing_keys.append(key)
            print(f"  ❌ {key}: NOT SET")
        else:
            available_keys.append(key)
            # Only show first and last 4 characters for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            print(f"  ✅ {key}: {masked}")
    
    return available_keys, missing_keys

def main():
    """Main function"""
    print("🧪 Roundtable Real API Integration Tests")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("tests/test_real_integration.py").exists():
        print("Error: Please run this script from the roundtable root directory")
        sys.exit(1)
    
    # Check API keys
    available, missing = check_api_keys()
    
    if missing:
        print(f"\n⚠️  Missing API keys: {', '.join(missing)}")
        print("\nTo run real integration tests, you need to:")
        print("1. Copy .env.template to .env")
        print("2. Add your actual API keys to .env")
        print("3. Or set the environment variables directly")
        print("\nExample:")
        print("  export ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("  export OPENAI_API_KEY=sk-...")
        print("  export GOOGLE_API_KEY=...")
        print("\nTo run only mock tests instead:")
        print("  pytest tests/test_basic.py -v")
        sys.exit(1)
    
    print(f"\n✅ All {len(available)} API keys are available")
    print("\n🚀 Running real integration tests...")
    
    # Run the real tests
    try:
        cmd = ["python", "-m", "pytest", "tests/test_real_integration.py", "-v", "-m", "real_api"]
        result = subprocess.run(cmd, check=False)
        
        if result.returncode == 0:
            print("\n🎉 All real integration tests passed!")
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            print("\nThis could be due to:")
            print("- API rate limits")
            print("- Network connectivity issues") 
            print("- API service temporary issues")
            print("- Invalid API keys")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())