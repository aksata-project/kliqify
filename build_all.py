#!/usr/bin/env python3
"""
KLIQIFY - Master Build Script
Compiles all HTML pages into Blogger-compatible XML templates using centralized config.
"""

import os
import sys
import json
import time

def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'config.json')
    example_file = os.path.join(base_dir, 'config.example.json')

    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f), config_file
    elif os.path.exists(example_file):
        with open(example_file, 'r', encoding='utf-8') as f:
            return json.load(f), example_file
    return {}, None

def format_size(bytes_num):
    for unit in ['B', 'KB', 'MB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} GB"

def main():
    print("=" * 60)
    print("           KLIQIFY - MASTER TEMPLATE COMPILER")
    print("=" * 60)

    cfg, cfg_source = load_config()
    if cfg_source:
        print(f"[*] Loaded Config : {os.path.basename(cfg_source)}")
        print(f"    - APP_URL     : {cfg.get('app_url', 'N/A')}")
        gas_url = cfg.get('gas_app_url', 'N/A')
        print(f"    - GAS_APP_URL : {gas_url[:55]}..." if len(gas_url) > 55 else f"    - GAS_APP_URL : {gas_url}")
    else:
        print("[!] No config.json found. Using built-in defaults.")

    print("-" * 60)
    start_time = time.time()
    errors = []

    # 1. Build Landing Page
    print("\n[1/3] Compiling Landing Page (landingpage.html -> landingpage.xml)...")
    try:
        import build_landing
        build_landing.convert_to_blogger('landingpage.html')
        size = os.path.getsize('landingpage.xml')
        print(f"      [OK] landingpage.xml generated ({format_size(size)})")
    except Exception as e:
        print(f"      [ERROR] Failed to compile landing page: {e}")
        errors.append(("landingpage.xml", str(e)))

    # 2. Build Dashboard SPA
    print("\n[2/3] Compiling Dashboard SPA (dashboard.html + login-register.html -> dashboard.xml)...")
    try:
        import build_dashboard_spa
        build_dashboard_spa.build_dashboard_xml()
        size = os.path.getsize('dashboard.xml')
        print(f"      [OK] dashboard.xml generated ({format_size(size)})")
    except Exception as e:
        print(f"      [ERROR] Failed to compile dashboard SPA: {e}")
        errors.append(("dashboard.xml", str(e)))

    # 3. Build Continue Page
    print("\n[3/3] Compiling Continue Page (continue.html -> continue.xml)...")
    try:
        import build_continue
        build_continue.build_continue_xml()
        size = os.path.getsize('continue.xml')
        print(f"      [OK] continue.xml generated ({format_size(size)})")
    except Exception as e:
        print(f"      [ERROR] Failed to compile continue page: {e}")
        errors.append(("continue.xml", str(e)))

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    if not errors:
        print(f"[SUCCESS] All templates built successfully in {elapsed:.2f}s!")
        print("Ready to deploy to Blogger themes or test locally.")
    else:
        print(f"[WARNING] Build finished with {len(errors)} error(s):")
        for target, err in errors:
            print(f"  - {target}: {err}")
    print("=" * 60)

if __name__ == '__main__':
    main()

