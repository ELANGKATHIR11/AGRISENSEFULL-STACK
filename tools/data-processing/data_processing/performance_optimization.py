#!/usr/bin/env python3
"""
AgriSense Performance Optimization and Health Check
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

def get_system_info():
    """Get system performance information"""
    try:
        import psutil
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('.').percent,
            'python_version': sys.version.split()[0],
            'platform': sys.platform
        }
    except ImportError:
        return {
            'python_version': sys.version.split()[0],
            'platform': sys.platform,
            'note': 'Install psutil for detailed system metrics'
        }

def check_dependencies():
    """Check all key dependencies are installed"""
    dependencies = [
        'fastapi', 'uvicorn', 'pydantic', 'numpy', 'pandas', 
        'scikit-learn', 'tensorflow', 'torch', 'transformers',
        'sentence-transformers', 'faiss-cpu', 'lightgbm',
        'requests', 'python-multipart', 'python-dotenv',
        'pyyaml', 'joblib', 'pytest'
    ]
    
    installed = []
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            installed.append(dep)
        except ImportError:
            missing.append(dep)
    
    return installed, missing

def optimize_python_environment():
    """Apply Python optimizations"""
    optimizations = []
    
    # Check for __pycache__ cleanup
    pycache_dirs = list(Path('.').rglob('__pycache__'))
    if pycache_dirs:
        for cache_dir in pycache_dirs:
            try:
                import shutil
                shutil.rmtree(cache_dir)
                optimizations.append(f"Cleaned {cache_dir}")
            except:
                pass
    
    # Check for .pyc files
    pyc_files = list(Path('.').rglob('*.pyc'))
    if pyc_files:
        for pyc_file in pyc_files:
            try:
                pyc_file.unlink()
                optimizations.append(f"Removed {pyc_file}")
            except:
                pass
    
    return optimizations

def check_file_sizes():
    """Check large files that might affect performance"""
    large_files = []
    total_size = 0
    
    for file_path in Path('.').rglob('*'):
        if file_path.is_file():
            try:
                size = file_path.stat().st_size
                total_size += size
                if size > 50 * 1024 * 1024:  # Files larger than 50MB
                    large_files.append({
                        'path': str(file_path),
                        'size_mb': size / (1024 * 1024)
                    })
            except:
                pass
    
    return large_files, total_size / (1024 * 1024)

def check_git_status():
    """Check git repository status"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        untracked_files = len([line for line in result.stdout.split('\n') if line.strip()])
        
        # Get commit info
        commit_result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                     capture_output=True, text=True, cwd='.')
        latest_commit = commit_result.stdout.strip()
        
        return {
            'untracked_files': untracked_files,
            'latest_commit': latest_commit,
            'is_clean': untracked_files == 0
        }
    except:
        return {'error': 'Git not available or not a git repository'}

def main():
    print("🔧 AgriSense Performance Optimization & Health Check")
    print("=" * 60)
    
    # System Information
    print("\n💻 System Information:")
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"   {key}: {value}")
    
    # Dependencies Check
    print("\n📦 Dependencies Check:")
    installed, missing = check_dependencies()
    print(f"   ✅ Installed: {len(installed)} packages")
    if missing:
        print(f"   ❌ Missing: {', '.join(missing)}")
    else:
        print("   ✅ All key dependencies are installed")
    
    # Python Environment Optimization
    print("\n🧹 Python Environment Optimization:")
    optimizations = optimize_python_environment()
    if optimizations:
        for opt in optimizations[:5]:  # Show first 5
            print(f"   ✅ {opt}")
        if len(optimizations) > 5:
            print(f"   ... and {len(optimizations) - 5} more")
    else:
        print("   ✅ Environment already optimized")
    
    # File Size Analysis
    print("\n📁 File Size Analysis:")
    large_files, total_size = check_file_sizes()
    print(f"   Total project size: {total_size:.1f} MB")
    if large_files:
        print("   Large files (>50MB):")
        for file_info in large_files[:3]:
            print(f"     - {file_info['path']}: {file_info['size_mb']:.1f} MB")
    else:
        print("   ✅ No unusually large files found")
    
    # Git Status
    print("\n🔄 Git Repository Status:")
    git_status = check_git_status()
    if 'error' in git_status:
        print(f"   ⚠️ {git_status['error']}")
    else:
        print(f"   Latest commit: {git_status['latest_commit']}")
        if git_status['is_clean']:
            print("   ✅ Repository is clean")
        else:
            print(f"   ⚠️ {git_status['untracked_files']} untracked changes")
    
    # Performance Recommendations
    print("\n🚀 Performance Recommendations:")
    recommendations = []
    
    if 'memory_percent' in system_info and isinstance(system_info['memory_percent'], (int, float)) and system_info['memory_percent'] > 80:
        recommendations.append("High memory usage detected - consider restarting or optimizing")
    
    if 'cpu_percent' in system_info and isinstance(system_info['cpu_percent'], (int, float)) and system_info['cpu_percent'] > 80:
        recommendations.append("High CPU usage detected - check for background processes")
    
    if total_size > 1000:  # > 1GB
        recommendations.append("Large project size - consider cleaning up unused files")
    
    if missing:
        recommendations.append(f"Install missing dependencies: {', '.join(missing)}")
    
    if not recommendations:
        recommendations.append("✅ System is well optimized!")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # Test Performance
    print("\n⚡ Quick Performance Test:")
    start_time = time.time()
    
    # Import test
    try:
        from agrisense_app.backend.main import app
        import_time = time.time() - start_time
        print(f"   Backend import: {import_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Backend import failed: {e}")
        return
    
    # Simple calculation test
    calc_start = time.time()
    import numpy as np
    _ = np.random.random((1000, 1000)).sum()
    calc_time = time.time() - calc_start
    print(f"   NumPy calculation: {calc_time:.3f}s")
    
    # Overall health score
    health_score = 100
    if 'memory_percent' in system_info and isinstance(system_info['memory_percent'], (int, float)) and system_info['memory_percent'] > 80:
        health_score -= 10
    if 'cpu_percent' in system_info and isinstance(system_info['cpu_percent'], (int, float)) and system_info['cpu_percent'] > 80:
        health_score -= 10
    if missing:
        health_score -= len(missing) * 5
    if total_size > 1000:
        health_score -= 5
    
    print(f"\n🏥 Overall Health Score: {health_score}/100")
    
    if health_score >= 90:
        print("🎉 EXCELLENT: System is in excellent condition!")
    elif health_score >= 75:
        print("👍 GOOD: System is performing well")
    elif health_score >= 60:
        print("⚠️ MODERATE: Some optimizations recommended")
    else:
        print("🚨 POOR: Significant optimizations needed")
    
    # Save optimization report
    report = {
        'timestamp': time.time(),
        'system_info': system_info,
        'dependencies': {'installed': installed, 'missing': missing},
        'file_analysis': {'total_size_mb': total_size, 'large_files': large_files},
        'git_status': git_status,
        'health_score': health_score,
        'recommendations': recommendations
    }
    
    with open('optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Optimization report saved to optimization_report.json")
    
    return health_score >= 75

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)