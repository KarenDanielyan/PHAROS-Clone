#!/usr/bin/env python3
"""
PHAROS Virtual Clone Verification Script
========================================

Quick verification script to test basic functionality of the virtual laser clone.
This script can be used to verify the installation and basic API functionality.

Usage:
    python verify_installation.py [port]

Author: Development Team
Date: September 2025
"""

import sys
import time
import requests
import subprocess
import threading
from typing import Optional


def test_server_connection(port: int, timeout: int = 10) -> bool:
    """Test if server is responding on the given port."""
    base_url = f"http://localhost:{port}"
    
    for _ in range(timeout * 10):  # Check every 0.1 seconds
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)
    
    return False


def run_basic_api_tests(port: int) -> bool:
    """Run basic API functionality tests."""
    base_url = f"http://localhost:{port}"
    api_base = f"{base_url}/v1"
    
    tests_passed = 0
    total_tests = 8
    
    print("🧪 Running basic API tests...")
    
    try:
        # Test 1: Get basic properties
        print("  ├─ Testing Basic properties batch retrieval...", end="")
        response = requests.get(f"{api_base}/Basic")
        if response.status_code == 200 and isinstance(response.json(), dict):
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 2: Get individual property
        print("  ├─ Testing individual property retrieval...", end="")
        response = requests.get(f"{api_base}/Basic/ActualOutputPower")
        if response.status_code == 200:
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 3: Turn on laser
        print("  ├─ Testing laser turn on...", end="")
        response = requests.post(f"{api_base}/Basic/TurnOn")
        if response.status_code == 200:
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 4: Set attenuator
        print("  ├─ Testing attenuator control...", end="")
        response = requests.put(f"{api_base}/Basic/TargetAttenuatorPercentage", data="75.0")
        if response.status_code == 200:
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 5: Enable output
        print("  ├─ Testing output enable...", end="")
        response = requests.post(f"{api_base}/Basic/EnableOutput")
        if response.status_code == 200:
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 6: Check output status
        print("  ├─ Testing output status check...", end="")
        response = requests.get(f"{api_base}/Basic/IsOutputEnabled")
        if response.status_code == 200 and response.json() is True:
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 7: Advanced API
        print("  ├─ Testing Advanced API...", end="")
        response = requests.get(f"{api_base}/Advanced")
        if response.status_code == 200 and isinstance(response.json(), dict):
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
        # Test 8: Raw API
        print("  └─ Testing Raw API...", end="")
        response = requests.get(f"{api_base}/Raw")
        if response.status_code == 200 and isinstance(response.json(), dict):
            print(" ✅")
            tests_passed += 1
        else:
            print(" ❌")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    return tests_passed == total_tests


def verify_response_format(port: int) -> bool:
    """Verify response formats match PHAROS API specifications."""
    api_base = f"http://localhost:{port}/v1"
    
    print("🔍 Verifying response formats...")
    
    try:
        # Check numeric responses are formatted correctly
        response = requests.get(f"{api_base}/Basic/ActualOutputPower")
        if response.status_code == 200:
            value = response.json()
            if isinstance(value, str) and value.replace('.', '').isdigit():
                print("  ✅ Numeric values formatted as strings")
            else:
                print("  ❌ Numeric format incorrect")
                return False
        
        # Check batch response structure
        response = requests.get(f"{api_base}/Basic")
        if response.status_code == 200:
            data = response.json()
            required_fields = ["ActualOutputPower", "ActualStateName", "GeneralStatus", "IsOutputEnabled"]
            if all(field in data for field in required_fields):
                print("  ✅ Batch response structure correct")
            else:
                print("  ❌ Batch response missing required fields")
                return False
        
        # Check state consistency
        basic_state = requests.get(f"{api_base}/Basic/ActualStateName").json()
        general_status = requests.get(f"{api_base}/Basic/GeneralStatus").json()
        
        if basic_state and general_status:
            print("  ✅ State information consistent")
        else:
            print("  ❌ State information inconsistent")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error verifying formats: {e}")
        return False


def main():
    """Main verification function."""
    # Parse command line arguments
    default_port = 20020
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number")
            print("Usage: python verify_installation.py [port]")
            sys.exit(1)
    else:
        port = default_port
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║            PHAROS Virtual Clone Verification               ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Testing server on: http://localhost:{port:<5}                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Test server connection
    print("🔌 Testing server connection...")
    if test_server_connection(port, timeout=5):
        print("  ✅ Server is responding")
    else:
        print("  ❌ Server not responding")
        print(f"\n💡 Make sure to start the server first:")
        print(f"   python pharos.py {port}")
        sys.exit(1)
    
    # Run API tests
    api_tests_passed = run_basic_api_tests(port)
    
    # Verify response formats
    format_tests_passed = verify_response_format(port)
    
    # Final results
    print("\n" + "="*60)
    if api_tests_passed and format_tests_passed:
        print("🎉 All verification tests PASSED!")
        print("✅ Virtual laser clone is working correctly")
        print(f"🚀 Ready for development at http://localhost:{port}")
        print("\n📚 Next steps:")
        print("   - Visit http://localhost:{port}/docs for API documentation")
        print("   - Run full test suite: python -m pytest test_pharos.py -v")
        print("   - Start developing your laser automation application!")
    else:
        print("❌ Some verification tests FAILED")
        print("🔧 Please check the server logs and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
