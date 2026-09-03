import os
import asyncio
from typing import List
from dotenv import load_dotenv
import discord
from discord.ext import commands
from settings import BOT_PREFIX, BOT_ACTIVITY_TYPE, BOT_ACTIVITY_NAME, TOKEN_ENV_VAR

# --- CONSTANTES LOCALES ---
DEFAULT_TOKEN_ERROR = "❌ Token manquant dans le fichier .env"

# Liste des cogs à charger
COGS_EXTENSIONS: List[str] = [
    "cogs.base",
    "cogs.moderation",
    "cogs.logs",
    "cogs.giveaway"
]

# --- CONFIGURATION ---

load_dotenv()


def configure_intents() -> discord.Intents:
    """Configure les intents nécessaires pour le bot."""
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    intents.messages = True
    intents.reactions = True
    intents.moderation = True
    return intents


def create_bot() -> commands.Bot:
    """Crée et configure l'instance du bot."""
    intents = configure_intents()
    bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

    # Attacher l'événement on_ready
    @bot.event
    async def on_ready():
        print(f'✅ Connecté en tant que {bot.user.name}')
        print(f'📌 Préfixe : {BOT_PREFIX}')
        print('----------------------')
        await setup_bot_activity(bot)

    # Handler d'erreurs global (commandes préfixe) : informe l'utilisateur au lieu d'un silence total
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignorer les commandes inconnues (évite le spam)
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Argument manquant : `{error.param.name}`", ephemeral=True)
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argument invalide. Vérifie le format (mention, nombre...).", ephemeral=True)
            return
        if isinstance(error, commands.CommandInvokeError):
            print(f"❌ Erreur commande '{ctx.command.name}' : {error.original}")
            await ctx.send("❌ Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True)
            return
        print(f"❌ Erreur commande : {error}")

    return bot


async def setup_bot_activity(bot: commands.Bot) -> None:
    """Configure l'activité du bot."""
    await bot.change_presence(
        activity=discord.Activity(
            type=BOT_ACTIVITY_TYPE,
            name=BOT_ACTIVITY_NAME
        )
    )


async def load_cogs(bot: commands.Bot) -> None:
    """Charge tous les cogs listés."""
    for cog in COGS_EXTENSIONS:
        try:
            await bot.load_extension(cog)
            print(f"📦 Extension '{cog}' chargée.")
        except commands.ExtensionNotFound:
            print(f"❌ Extension '{cog}' introuvable.")
        except commands.ExtensionAlreadyLoaded:
            print(f"⚠️ Extension '{cog}' déjà chargée.")
        except commands.NoEntryPointError:
            print(f"❌ Extension '{cog}' : pas de fonction setup.")
        except Exception as e:
            print(f"❌ Erreur lors du chargement de '{cog}' : {e}")


async def main() -> None:
    """Fonction principale de démarrage du bot."""
    token = os.getenv(TOKEN_ENV_VAR)
    if not token:
        raise ValueError(DEFAULT_TOKEN_ERROR)

    bot = create_bot()
    await load_cogs(bot)

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
