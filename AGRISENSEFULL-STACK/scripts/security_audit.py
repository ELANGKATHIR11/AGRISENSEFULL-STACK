"""
Security Audit Script for AgriSense
Runs dependency vulnerability scans and security checks
"""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run comprehensive security audit"""
    print(f"\n🔒 AgriSense Security Audit")
    print(f"Started: {datetime.now().isoformat()}")
    
    results = {}
    
    # 1. pip-audit on main requirements
    print("\n1️⃣  Checking main dependencies...")
    results['pip_audit_main'] = run_command(
        "pip-audit --requirement agrisense_app/backend/requirements.txt --format json > security_audit_main.json",
        "pip-audit on requirements.txt"
    )
    
    # 2. pip-audit on dev requirements
    print("\n2️⃣  Checking development dependencies...")
    results['pip_audit_dev'] = run_command(
        "pip-audit --requirement agrisense_app/backend/requirements-dev.txt --format json > security_audit_dev.json",
        "pip-audit on requirements-dev.txt"
    )
    
    # 3. Safety check
    print("\n3️⃣  Running Safety check...")
    results['safety_check'] = run_command(
        "safety check --json > security_safety.json",
        "Safety vulnerability database check"
    )
    
    # 4. Check for secrets in code
    print("\n4️⃣  Checking for hardcoded secrets...")
    patterns = [
        "password",
        "api_key",
        "secret",
        "token",
        "private_key"
    ]
    
    results['secret_scan'] = True
    for pattern in patterns:
        result = subprocess.run(
            f'grep -r --include="*.py" -i "{pattern} = " agrisense_app/ --exclude-dir=__pycache__',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout:
            print(f"⚠️  Found potential {pattern} in code:")
            print(result.stdout[:500])
            results['secret_scan'] = False
    
    # 5. Check npm vulnerabilities
    print("\n5️⃣  Checking frontend dependencies...")
    results['npm_audit'] = run_command(
        "cd agrisense_app/frontend/farm-fortune-frontend-main && npm audit --production --json > ../../../security_npm_audit.json",
        "npm audit for frontend"
    )
    
    # Generate summary report
    print("\n\n" + "="*60)
    print("📊 SECURITY AUDIT SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "passed": passed,
        "total": total,
        "score": (passed / total) * 100
    }
    
    with open("security_audit_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Detailed reports saved:")
    print("   - security_audit_main.json")
    print("   - security_audit_dev.json")
    print("   - security_safety.json")
    print("   - security_npm_audit.json")
    print("   - security_audit_summary.json")
    
    # Exit with error if any check failed
    if passed < total:
        print("\n⚠️  Some security checks failed. Please review the reports.")
        sys.exit(1)
    else:
        print("\n✅ All security checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
