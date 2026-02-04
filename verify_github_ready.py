#!/usr/bin/env python3
"""
Verification script to ensure GiftsChart is GitHub-ready.
Checks for all required files and configurations.
"""
import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file(filepath, description):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"{GREEN}✓{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {filepath} {RED}MISSING{RESET}")
        return False

def check_directory(dirpath, description):
    """Check if a directory exists."""
    if os.path.isdir(dirpath):
        print(f"{GREEN}✓{RESET} {description}: {dirpath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {dirpath} {RED}MISSING{RESET}")
        return False

def main():
    """Run all verification checks."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}GiftsChart GitHub-Ready Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    checks_passed = 0
    checks_total = 0
    
    # Documentation files
    print(f"\n{YELLOW}📚 Documentation Files{RESET}")
    docs = [
        ("README.md", "Main README"),
        ("CONTRIBUTING.md", "Contribution guidelines"),
        ("LICENSE", "License file"),
        ("CHANGELOG.md", "Changelog"),
        ("SECURITY.md", "Security policy"),
    ]
    for file, desc in docs:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # GitHub configuration
    print(f"\n{YELLOW}🔧 GitHub Configuration{RESET}")
    github_files = [
        (".github/workflows/python-tests.yml", "Python tests workflow"),
        (".github/workflows/docker-build.yml", "Docker build workflow"),
        (".github/workflows/security-scan.yml", "Security scan workflow"),
        (".github/workflows/code-quality.yml", "Code quality workflow"),
        (".github/ISSUE_TEMPLATE/bug_report.md", "Bug report template"),
        (".github/ISSUE_TEMPLATE/feature_request.md", "Feature request template"),
        (".github/PULL_REQUEST_TEMPLATE.md", "PR template"),
        (".github/CODE_OF_CONDUCT.md", "Code of conduct"),
        (".github/dependabot.yml", "Dependabot config"),
        (".github/FUNDING.yml", "Funding config"),
    ]
    for file, desc in github_files:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Development tools
    print(f"\n{YELLOW}🛠️ Development Tools{RESET}")
    dev_files = [
        ("pyproject.toml", "Python project config"),
        ("Makefile", "Development commands"),
        (".editorconfig", "Editor config"),
        (".gitattributes", "Git attributes"),
        (".pre-commit-config.yaml", "Pre-commit hooks"),
        (".env.example", "Environment template"),
    ]
    for file, desc in dev_files:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Test structure
    print(f"\n{YELLOW}🧪 Test Structure{RESET}")
    test_files = [
        ("tests/__init__.py", "Test package init"),
        ("tests/test_gift_cards.py", "Gift card tests"),
        ("tests/test_sticker_integration.py", "Sticker tests"),
        ("tests/test_rate_limiter.py", "Rate limiter tests"),
        ("tests/README.md", "Test documentation"),
    ]
    for file, desc in test_files:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Core directories
    print(f"\n{YELLOW}📁 Core Directories{RESET}")
    directories = [
        ("core", "Core bot logic"),
        ("services", "API services"),
        ("generators", "Card generators"),
        ("docs", "Documentation"),
        ("tests", "Test suite"),
        (".github", "GitHub config"),
    ]
    for dir, desc in directories:
        checks_total += 1
        if check_directory(dir, desc):
            checks_passed += 1
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    percentage = (checks_passed / checks_total) * 100
    
    if checks_passed == checks_total:
        print(f"{GREEN}✓ ALL CHECKS PASSED!{RESET}")
        print(f"{GREEN}✓ {checks_passed}/{checks_total} checks successful ({percentage:.1f}%){RESET}")
        print(f"\n{GREEN}🎉 GiftsChart is GitHub-ready!{RESET}")
        return 0
    else:
        print(f"{YELLOW}⚠ SOME CHECKS FAILED{RESET}")
        print(f"{YELLOW}✓ {checks_passed}/{checks_total} checks successful ({percentage:.1f}%){RESET}")
        print(f"{RED}✗ {checks_total - checks_passed} checks failed{RESET}")
        print(f"\n{YELLOW}Please fix the missing files before pushing to GitHub.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
