#!/usr/bin/env python3
"""
FruitCraft Automation Bot CLI & Web Dashboard.

Usage:
  python bot.py dashboard         # Launch Web Admin Dashboard at http://localhost:8000
  python bot.py info              # Display player profile & stats & top 10 weakest cards
  python bot.py quest             # Run auto quest loop (1 weakest card, 10-card fallback, 8s sleep)
  python bot.py quest --count 20  # Run 20 auto quests
  python bot.py quest --delay 8   # Run auto quests with custom delay (default: 8s)
  python bot.py battle            # Run auto battles (default 10, 8s delay)
  python bot.py battle --count 5  # Run 5 battles
  python bot.py mine              # Collect mined gold
  python bot.py menu              # Interactive Persian menu (includes dashboard launch option)
"""

import os
import sys
import argparse

# Ensure src is on python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from fruitcraft_bot.bot_actions import (
    get_configured_client,
    action_account_info,
    action_auto_quest,
    action_auto_battle,
    action_collect_mine,
    action_start_dashboard,
    interactive_menu,
    get_weakest_available_card,
    get_sorted_weakest_cards,
    get_top_attack_cards
)


def main():
    parser = argparse.ArgumentParser(description="FruitCraft Automation Bot & Web Dashboard")
    parser.add_argument("command", nargs="?", choices=["info", "quest", "battle", "mine", "dashboard", "menu"], default="menu",
                        help="Action to perform: info, quest, battle, mine, dashboard, menu")
    parser.add_argument("--count", type=int, default=0, help="Number of quests or battles (0 = infinite loop for quests)")
    parser.add_argument("--delay", type=float, default=8.0, help="Delay in seconds between quests/attacks (default: 8.0)")
    parser.add_argument("--port", type=int, default=8000, help="Web dashboard port (default: 8000)")
    parser.add_argument("--session", type=str, default="fruit", help="Session file name (default: fruit -> fruit.fb)")
    parser.add_argument("--key", type=str, default=None, help="FruitCraft Restore Key")
    parser.add_argument("--base-url", type=str, default=None, help="Game API base URL")

    args = parser.parse_args()

    if args.command == "dashboard":
        action_start_dashboard(port=args.port)
        return

    bot = get_configured_client(
        session_name=args.session,
        restore_key=args.key,
        base_url=args.base_url
    )

    if args.command == "info":
        action_account_info(bot)
    elif args.command == "quest":
        action_auto_quest(bot, count=args.count, delay=args.delay)
    elif args.command == "battle":
        count = args.count if args.count > 0 else 10
        action_auto_battle(bot, count=count, delay=args.delay)
    elif args.command == "mine":
        action_collect_mine(bot)
    else:
        interactive_menu(bot)


if __name__ == "__main__":
    main()
