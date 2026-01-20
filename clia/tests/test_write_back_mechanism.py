"""Test the write_back mechanism without requiring LLM API"""
from pathlib import Path
from clia.agents import tools as tool_funcs

# Create a test file with buggy code
test_file = "test_buggy_code.py"
original_content = """def add_numbers(a, b):
    return a + b + c  # Error: 'c' is not defined

result = add_numbers(5, 3)
print(result)
"""

# Write original file
tool_funcs.write_file_safe(test_file, original_content, backup=False)
print(f"[PASS] Created {test_file}")

# Simulate fixed code (what the LLM would generate)
fixed_content = """def add_numbers(a, b):
    return a + b  # Fixed: removed undefined 'c'

result = add_numbers(5, 3)
print(result)
"""

# Test write_back with backup (default behavior)
print(f"\n[TEST] Testing write_back with backup=True...")
tool_funcs.write_file_safe(test_file, fixed_content, backup=True)

# Check if backup was created
backup_file = f"{test_file}.bak"
if Path(backup_file).exists():
    print(f"[PASS] Backup created: {backup_file}")
    backup_content = tool_funcs.read_file_safe(backup_file, max_chars=1000)
    if backup_content == original_content:
        print("[PASS] Backup contains original content")
    else:
        print("[FAIL] Backup content mismatch!")
else:
    print("[FAIL] Backup file not created!")

# Check if main file was updated
current_content = tool_funcs.read_file_safe(test_file, max_chars=1000)
if current_content == fixed_content:
    print(f"[PASS] {test_file} updated with fixed content")
else:
    print(f"[FAIL] {test_file} content mismatch!")

# Verify the fixed code runs without error
print(f"\n[TEST] Testing if fixed code runs...")
import subprocess
result = subprocess.run(["python", test_file], capture_output=True, text=True)
if result.returncode == 0:
    print(f"[PASS] Fixed code runs successfully!")
    print(f"  Output: {result.stdout.strip()}")
else:
    print(f"[FAIL] Fixed code failed: {result.stderr}")

print("\n[PASS] Write-back mechanism test completed!")
