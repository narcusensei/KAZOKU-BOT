import discord
from discord import app_commands  ## Import important pour les slash commands ##
from discord.ext import commands

class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog 'Base' chargé.")

    # --- COMMANDES SLASH (Correction) ---
    @app_commands.command(name="ping", description="Vérifie la latence du bot")
    async def ping_slash(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'Pong ! 🏓 Latence : {latency}ms')

    @app_commands.command(name="bonjour", description="Dit bonjour")
    async def bonjour_slash(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Salut {interaction.user.mention} !')

    # --- COMMANDES PRÉFIXE (+) ---
    @commands.command(name='sync')
    async def sync(self, ctx):
        """Synchronise les commandes slash sur le serveur."""

        print("Début de la synchronisation...")

        # On force les commandes globales à s'afficher sur ce serveur pour les tests
        self.bot.tree.copy_global_to(guild=ctx.guild)

        try:
            synced = await self.bot.tree.sync(guild=ctx.guild)
            print(f"Sync terminé. {len(synced)} commandes chargées.")
            await ctx.send(f"Sync effectué ! {len(synced)} commandes chargées.")
        except Exception as e:
            print(f"Erreur Sync : {e}")
            await ctx.send("Erreur lors de la sync.")

    @app_commands.command(name="profil", description="Affiche un profil détaillé (Compatible ID)")
    @app_commands.describe(utilisateur="L'utilisateur (ID ou Mention) dont tu veux voir le profil (Laisse vide pour toi)")
    async def profil_slash(self, interaction: discord.Interaction, utilisateur: discord.User = None): # <--- Ajout de = None

        await interaction.response.defer(thinking=True)

        try:
            guild = interaction.guild
            # Si l'utilisateur n'est pas précisé, on prend celui qui tape la commande
            target_user = utilisateur or interaction.user

            # --- FIX CACHE (CRITIQUE) ---
            # On essaie d'abord le cache local
            member = guild.get_member(target_user.id)

            # Si le cache est vide (ce qui arrive chez toi), on force le téléchargement depuis Discord
            if not member:
                try:
                    member = await guild.fetch_member(target_user.id)
                except Exception as e:
                    print(f"Impossible de fetch le membre {target_user.id} : {e}")
                    # member reste None, ce qui affichera "Membre hors serveur"
            # ---------------------------

            # --- CONSTRUCTION DES DONNÉES ---

            # Couleur
            color = discord.Color.gold()
            if member and member.color.value != 0:
                color = member.color
            elif target_user.accent_color:
                color = target_user.accent_color

            # Liste des Rôles
            roles_str = "Membre hors serveur"
            if member:
                roles_list = [role.mention for role in reversed(member.roles) if role != member.guild.default_role][:10]
                roles_str = " ".join(roles_list) if roles_list else "Aucun rôle"

            if len(roles_str) > 1000: roles_str = roles_str[:1000] + "..."

            # --- CRÉATION DE L'EMBED ---

            embed = discord.Embed(
                title=target_user.display_name, # Le titre est le Display Name
                color=color
            )

            # BANNIÈRE (si existante)
            if target_user.banner:
                embed.set_image(url=target_user.banner.url)

            # AVATAR (Display Avatar)
            embed.set_thumbnail(url=target_user.display_avatar.url)

            # 1. Display Name
            embed.add_field(
                name="Identité",
                value=f"***{target_user.display_name}***",
                inline=False
            )

            # 2. Information de l'utilisateur
            info_text = (
                f"**Pseudo :** {target_user.display_name} - {target_user.name}\n"
                f"**ID :** `{target_user.id}`\n"
                f"**Rôles :**\n{roles_str}"
            )
            embed.add_field(
                name="Information",
                value=info_text,
                inline=False
            )

            # 3. Dates
            created_ts = int(target_user.created_at.timestamp())

            # Date arrivée serveur
            joined_str = "Inconnu (Pas sur le serveur)"
            if member and member.joined_at:
                joined_ts = int(member.joined_at.timestamp())
                joined_str = f"<t:{joined_ts}:F> (<t:{joined_ts}:R>)"

            dates_text = (
                f"**Membre Discord depuis :**\n<t:{created_ts}:F> (<t:{created_ts}:R>)\n\n"
                f"**Membre Serveur depuis :**\n{joined_str}"
            )
            embed.add_field(
                name="",
                value=dates_text,
                inline=False
            )

            embed.set_footer(text="𝘒4𝘡𝘖𝘒𝘜 © 2026", icon_url=self.bot.user.avatar.url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Erreur /profil : {e}")
            await interaction.followup.send("Impossible de charger le profil.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Base(bot))