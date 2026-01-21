#!/usr/bin/env python3
"""Master script to generate all sankey diagrams for Peru and Ecuador"""
import subprocess
import sys
from pathlib import Path

def run_script(script_path):
    """Run a Python script and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {script_path.name}")
    print('='*60)
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {script_path.name} failed with exit code {e.returncode}")
        return False

def main():
    """Generate all sankey diagrams"""
    base_dir = Path(__file__).parent

    scripts = [
        base_dir / "generate_peru_europe.py",
        base_dir / "generate_peru_germany.py",
        base_dir / "generate_ecuador_europe.py",
        base_dir / "generate_ecuador_germany.py",
    ]

    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "Sankey 2026 Generation Suite" + " "*20 + "║")
    print("║" + " "*15 + "Peru & Ecuador" + " "*28 + "║")
    print("╚" + "="*58 + "╝")

    results = {}
    for script in scripts:
        if not script.exists():
            print(f"\nERROR: {script} not found!")
            results[script.name] = False
            continue

        success = run_script(script)
        results[script.name] = success

    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)

    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    total = len(results)
    successful = sum(1 for s in results.values() if s)

    print(f"\n{successful}/{total} scripts completed successfully")

    if successful == total:
        print("\n✓ All sankey diagrams generated successfully!")
        print(f"\nOutputs located in:")
        print(f"  • sankey2026/peru/europe/")
        print(f"  • sankey2026/peru/germany/")
        print(f"  • sankey2026/ecuador/europe/")
        print(f"  • sankey2026/ecuador/germany/")
    else:
        print(f"\n⚠ {total - successful} script(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
