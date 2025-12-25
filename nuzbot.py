import discord
from disc_token import TOKEN
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import SlashCommandOptionType
from database import *
from scraper import fetch_pokemon_data

# Create an instance of the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize slash commands
slash = SlashCommand(bot, sync_commands=True)  # Initialize SlashCommand

# Thresholds for calculating points (mutable and defined in-memory)
THRESHOLDS = [(350, 1), (465, 2), (515, 3), (579, 4), (9999, 5)]

@bot.event
async def on_ready():
    await initialize_database()
    print(f'We have logged in as {bot.user}')

@slash.slash(
    name="run",
    description="Manage your runs in Pokémon game",
    options=[
        {
            "name": "action",
            "description": "Action to perform on the run",
            "type": SlashCommandOptionType.STRING,
            "required": True,
            "choices": [
                {"name": "add", "value": "add"},
                {"name": "delete", "value": "delete"},
                {"name": "select", "value": "select"},
                {"name": "list", "value": "list"},
                {"name": "view", "value": "view"}
            ]
        },
        {
            "name": "name",
            "description": "Name of the run or Pokémon",
            "type": SlashCommandOptionType.STRING,
            "required": False
        },
        {
            "name": "generation",
            "description": "Generation of the Pokémon game",
            "type": SlashCommandOptionType.INTEGER,
            "required": False
        }
    ]
)
async def _run(ctx, action, name=None, generation=None):
    """Slash command to manage runs."""
    if action.lower() == "add":
        if not name or not generation:
            await ctx.send("Usage: `/run add <name> <generation>`")
            return
        await add_run(name, generation)
        await ctx.send(f"Run '{name}' for generation '{generation}' added.")

    elif action.lower() == "delete":
        if not name:
            await ctx.send("Usage: `/run delete <name>`")
            return
        await delete_run(name)
        await ctx.send(f"Run '{name}' deleted.")

    elif action.lower() == "select":
        if not name:
            await ctx.send("Usage: `/run select <name>`")
            return
        await select_run(name)
        await ctx.send(f"Run '{name}' selected.")

    elif action.lower() == "list":
        runs = await list_runs()
        if not runs:
            await ctx.send("No runs found.")
            return
        response = "\n".join([f"Name: {run[0]}, Generation: {run[1]}" for run in runs])
        await ctx.send(f"Available runs:\n{response}")

    elif action.lower() == "view":
        if not name:
            await ctx.send("Usage: `/run view <name>`")
            return
        run_name = name
        pokemon = await get_pokemon_by_run(run_name)
        if not pokemon:
            await ctx.send(f"No Pokémon found for run '{run_name}'.")
            return
        response = "\n".join(
            [
                f"Name: {p['name']}, Route: {p['route']}, BST: {p['bst']}, "
                f"Points: {p['points']}, Status: {p['status']}"
                # Recognized issue: TypeError: tuple indices must be integers or slices, not str
                for p in pokemon
            ]
        )
        await ctx.send(f"Pokémon for run '{run_name}':\n{response}")

    else:
        await ctx.send("Invalid action. Use `/run add`, `/run delete`, `/run select`, `/run list`, or `/run view`.")


@slash.slash(
    name="add", 
    description="Add a Pokémon to your active run",
    options=[
        {
            "name": "name",
            "description": "Name of the Pokémon to add",
            "type": SlashCommandOptionType.STRING,
            "required": True
        },
        {
            "name": "route",
            "description": "Route where the Pokémon is located",
            "type": SlashCommandOptionType.STRING,
            "required": True
        }
    ]
)
async def _add(ctx, name: str, route: str):
    """Slash command to add a Pokémon to the active run."""
    active_run = await get_active_run()
    if not active_run:
        await ctx.send("No active run. Use `/run select <name>` to select one.")
        return

    pokemon_data = fetch_pokemon_data(name)
    if not pokemon_data:
        await ctx.send(f"Could not find data for Pokémon '{name}'.")
        return

    bst = pokemon_data['bst']
    points = calculate_point_value(bst, THRESHOLDS)
    await add_pokemon(name, route, bst, points, active_run)
    await ctx.send(f"Added {name} (Route: {route}, BST: {bst}, Points: {points}) to run '{active_run}'.")


@slash.slash(name="status", description="Update the status of a Pokémon (alive or dead)")
async def _status(ctx, name: str, new_status: str):
    """Slash command to update the status of a Pokémon."""
    if new_status.lower() not in ["alive", "dead"]:
        await ctx.send("Invalid status. Use 'alive' or 'dead'.")
        return

    active_run = await get_active_run()
    if not active_run:
        await ctx.send("No active run. Use `/run select <name>` to select one.")
        return

    await update_pokemon_status(name, active_run, new_status.lower())
    await ctx.send(f"Updated status of {name} to {new_status}.")

@slash.slash(name="threshold", description="View or set the threshold for Pokémon point values")
async def _threshold(ctx, action: str, *args):
    """Slash command to view or set point thresholds based on BST."""
    global THRESHOLDS
    if action.lower() == "view":
        response = "\n".join([f"{max_bst} BST = {points} points" for max_bst, points in THRESHOLDS])
        await ctx.send(f"Current thresholds:\n{response}")

    elif action.lower() == "set":
        if len(args) != 2:
            await ctx.send("Usage: `/threshold set <max_bst> <points>`")
            return
        try:
            max_bst = int(args[0])
            points = int(args[1])
        except ValueError:
            await ctx.send("Both <max_bst> and <points> must be integers.")
            return
        THRESHOLDS = sorted(THRESHOLDS + [(max_bst, points)], key=lambda x: x[0])
        await ctx.send(f"Threshold updated: {max_bst} BST = {points} points.")
    else:
        await ctx.send("Invalid action. Use `/threshold view` or `/threshold set`.")

# Run the bot with your token
bot.run(TOKEN)