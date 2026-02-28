import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()

# INTENTS OBLIGATOIRES POUR LES LOGS
intents.members = True          # OBLIGATOIRE pour Arrivée/Départ + Rôles
intents.voice_states = True     # OBLIGATOIRE pour Vocal (Déplacement/Stream)
intents.message_content = True  # OBLIGATOIRE pour Messages (déjà là)
intents.presences = True      # <--- Souvent utile
intents.invites = True        # <--- Pour la source de l'invite
intents.moderation = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user.name}')
    print(f'Prefixe : +')
    print('------')

    # Ton statut
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="narcus 👑"
        )
    )

async def main():
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("Token manquant")

        try:
            # On charge la Base
            await bot.load_extension("cogs.base")
            print("Extension 'cogs.base' chargée.")

            # On charge la Modération (NOUVEAU)
            await bot.load_extension("cogs.moderation")
            print("Extension 'cogs.moderation' chargée.")

            # On charge les Logs
            await bot.load_extension("cogs.logs")
            print("Extension 'cogs.logs' chargée.")

        except Exception as e:
            print(f"Erreur lors du chargement des cogs : {e}")

        async with bot:
            await bot.start(token)

if __name__ == "__main__":
    # On lance la boucle événementielle avec asyncio
    import asyncio
    asyncio.run(main())