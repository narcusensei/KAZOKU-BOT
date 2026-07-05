import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import BOT_FOOTER, MAX_ROLES_DISPLAY, MAX_ROLES_LENGTH, ROLES_TRUNCATE_SUFFIX, UNICODE_EMOJIS, TEXTS, truncate_text

# --- FONCTIONS UTILITAIRES ---

async def get_member(guild: discord.Guild, user_id: int) -> Optional[discord.Member]:
    """Récupère un membre depuis le cache ou l'API."""
    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except (discord.NotFound, discord.HTTPException):
            return None
    return member


def format_roles(member: discord.Member) -> str:
    """Formate la liste des rôles d'un membre."""
    roles_list = [
        role.mention for role in reversed(member.roles)
        if role != member.guild.default_role
    ][:MAX_ROLES_DISPLAY]

    roles_str = " ".join(roles_list) if roles_list else TEXTS["profile_no_roles"]
    return truncate_text(roles_str, MAX_ROLES_LENGTH, ROLES_TRUNCATE_SUFFIX)


def format_discord_timestamp(dt: Optional[datetime]) -> str:
    """Formate un datetime Discord en texte lisible."""
    if not dt:
        return TEXTS["unknown"]
    ts = int(dt.timestamp())
    return f"<t:{ts}:F> (<t:{ts}:R>)"


def get_user_color(user: discord.User, member: Optional[discord.Member] = None) -> discord.Color:
    """Retourne la couleur appropriée pour un utilisateur."""
    if member and member.color.value != 0:
        return member.color
    if user.accent_color:
        return user.accent_color
    return discord.Color.gold()


# --- COG BASE ---

class Base(commands.Cog):
    """Cog de base avec les commandes principales."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Appelé quand le bot est prêt."""
        print("📦 Cog 'Base' chargé.")

    # --- COMMANDES SLASH ---

    @app_commands.command(name="ping", description="Vérifie la latence du bot")
    async def ping_slash(self, interaction: discord.Interaction):
        """Affiche la latence du bot."""
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'{UNICODE_EMOJIS["ping"]} {TEXTS["ping_response"]} **{latency}ms**')

    @app_commands.command(name="bonjour", description="Dit bonjour")
    async def bonjour_slash(self, interaction: discord.Interaction):
        """Dit bonjour à l'utilisateur."""
        await interaction.response.send_message(f'{TEXTS["hello_response"]} {interaction.user.mention} ! {UNICODE_EMOJIS["wave"]}')

    @app_commands.command(name="profil", description="Affiche un profil détaillé (Compatible ID)")
    @app_commands.describe(utilisateur="L'utilisateur (Laisse vide pour toi)")
    async def profil_slash(self, interaction: discord.Interaction, utilisateur: discord.User = None):
        """Affiche le profil détaillé d'un utilisateur."""
        await interaction.response.defer(thinking=True)

        try:
            guild = interaction.guild
            target_user = utilisateur or interaction.user
            member = await get_member(guild, target_user.id)

            color = get_user_color(target_user, member)
            roles_str = format_roles(member) if member else TEXTS["profile_off_server"]

            embed = self._create_profile_embed(guild, target_user, member, color, roles_str)
            await interaction.followup.send(embed=embed)

        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Erreur /profil : {e}")
            await interaction.followup.send(TEXTS["profile_error"], ephemeral=True)

    def _create_profile_embed(self, guild: discord.Guild, user: discord.User, member: Optional[discord.Member], color: discord.Color, roles_str: str) -> discord.Embed:
        """Crée l'embed de profil."""
        embed = discord.Embed(title=user.display_name, color=color)

        # Bannière (si existante)
        if user.banner:
            embed.set_image(url=user.banner.url)

        # Avatar
        embed.set_thumbnail(url=user.display_avatar.url)

        # Identité
        embed.add_field(name=TEXTS["profile_identity"], value=f"***{user.display_name}***", inline=False)

        # Informations
        info_text = (
            f"**{TEXTS['profile_username']}** {user.display_name} - {user.name}\n"
            f"**{TEXTS['profile_id']}** `{user.id}`\n"
            f"**{TEXTS['profile_roles']}**\n{roles_str}"
        )
        embed.add_field(name=TEXTS["profile_info"], value=info_text, inline=False)

        # Dates
        if member and member.joined_at:
            joined_str = format_discord_timestamp(member.joined_at)
        else:
            joined_str = TEXTS["profile_not_on_server"]

        dates_text = (
            f"**{TEXTS['profile_discord_since']}**\n{format_discord_timestamp(user.created_at)}\n\n"
            f"**{TEXTS['profile_server_since']}**\n{joined_str}"
        )
        embed.add_field(name=TEXTS["profile_dates"], value=dates_text, inline=False)

        embed.set_footer(text=BOT_FOOTER, icon_url=self.bot.user.avatar.url)

        return embed

    # --- COMMANDES PRÉFIXE (+) ---

    @commands.command(name='sync')
    async def sync(self, ctx: commands.Context):
        """Synchronise les commandes slash sur le serveur (Dev)."""
        print("🔄 Synchronisation des commandes slash...")

        self.bot.tree.copy_global_to(guild=ctx.guild)

        try:
            synced = await self.bot.tree.sync(guild=ctx.guild)
            print(f"{UNICODE_EMOJIS['check']} Sync terminé. {len(synced)} commandes chargées.")
            await ctx.send(f"{UNICODE_EMOJIS['check']} {TEXTS['sync_success']} {len(synced)} commandes chargées.")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"{UNICODE_EMOJIS['cross']} Erreur Sync : {e}")
            await ctx.send(f"{UNICODE_EMOJIS['cross']} {TEXTS['sync_error']}")


async def setup(bot):
    """Setup du cog Base."""
    await bot.add_cog(Base(bot))
