#!/usr/bin/env python3
"""
Simple test script to verify web interface structure
"""
import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    base_dir = Path(__file__).parent
    
    required_files = [
        'web/index.html',
        'web/terminal.css', 
        'web/terminal.js',
        'web/server.py',
        'web/web_ui.py',
        'web_main.py'
    ]
    
    print("Testing file structure...")
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            return False
    
    return True

def test_imports():
    """Test that imports work correctly"""
    print("\nTesting imports...")
    
    # Test basic Python imports
    try:
        import json
        import asyncio
        import logging
        print("✓ Standard library imports")
    except ImportError as e:
        print(f"✗ Standard library import error: {e}")
        return False
    
    # Test existing roundtable imports
    try:
        from models.discussion import DiscussionState, Round, Message, Role
        print("✓ Models import")
    except ImportError as e:
        print(f"✗ Models import error: {e}")
        return False
    
    try:
        from storage.session_logger import SessionLogger
        print("✓ Storage import")
    except ImportError as e:
        print(f"✗ Storage import error: {e}")
        return False
    
    return True

def test_html_structure():
    """Test HTML file structure"""
    print("\nTesting HTML structure...")
    
    html_file = Path(__file__).parent / 'web' / 'index.html'
    
    if not html_file.exists():
        print("✗ index.html not found")
        return False
    
    content = html_file.read_text()
    
    required_elements = [
        '<div id="terminal">',
        '<div id="output">',
        '<input type="text" id="command-input"',
        'terminal.css',
        'terminal.js'
    ]
    
    for element in required_elements:
        if element in content:
            print(f"✓ Found: {element}")
        else:
            print(f"✗ Missing: {element}")
            return False
    
    return True

def main():
    print("=" * 60)
    print("ROUNDTABLE WEB INTERFACE STRUCTURE TEST")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Python Imports", test_imports),
        ("HTML Structure", test_html_structure)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            result = test_func()
            if result:
                print(f"\n✓ {test_name} PASSED")
            else:
                print(f"\n✗ {test_name} FAILED")
                all_passed = False
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Web interface structure is ready!")
        print("\nTo start the web server:")
        print("  python web_main.py")
        print("\nThen open: http://localhost:8080")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())