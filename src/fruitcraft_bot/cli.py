"""FruitCraft Command-Line Interface."""

import os
import sys
import click

from fruitcraft_bot.bot_actions import (
    get_configured_client,
    action_account_info,
    action_auto_quest,
    action_auto_battle,
    action_collect_mine,
    interactive_menu
)


@click.group()
@click.option("--key", help="FruitCraft Restore Key")
@click.pass_context
def cli(ctx, key):
    """FruitCraft Unofficial Automation CLI (powered by fruitbot)."""
    ctx.ensure_object(dict)
    ctx.obj["bot"] = get_configured_client(restore_key=key)


@cli.command()
@click.pass_context
def info(ctx):
    """Display account information."""
    action_account_info(ctx.obj["bot"])


@cli.command()
@click.option("--count", default=0, help="Number of quests (0 = infinite)")
@click.option("--delay", default=8.0, help="Delay in seconds between quests (default: 8.0)")
@click.pass_context
def quest(ctx, count, delay):
    """Run auto quest (picks single weakest card, 8s sleep between quests)."""
    action_auto_quest(ctx.obj["bot"], count=count, delay=delay)


@cli.command()
@click.option("--count", default=10, help="Number of battles")
@click.option("--delay", default=8.0, help="Delay in seconds between battles (default: 8.0)")
@click.pass_context
def battle(ctx, count, delay):
    """Run auto battle against opponents."""
    action_auto_battle(ctx.obj["bot"], count=count, delay=delay)


@cli.command()
@click.pass_context
def mine(ctx):
    """Collect gold from gold mine."""
    action_collect_mine(ctx.obj["bot"])


@cli.command()
@click.pass_context
def menu(ctx):
    """Open interactive menu."""
    interactive_menu(ctx.obj["bot"])


if __name__ == "__main__":
    cli()
