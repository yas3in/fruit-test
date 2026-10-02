#!/usr/bin/env python3
"""
FruitCraft Web Admin Dashboard Launcher.

Simply run:
    python dashboard.py

Open in your browser:
    http://localhost:8000
"""

import os
import sys

# Ensure src is on python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from fruitcraft_bot.bot_actions import action_start_dashboard

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FruitCraft Web Admin Dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind dashboard server (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    args = parser.parse_args()

    action_start_dashboard(host=args.host, port=args.port)
