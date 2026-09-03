import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import BOT_FOOTER, MAX_ROLES_DISPLAY, MAX_ROLES_LENGTH, ROLES_TRUNCATE_SUFFIX, UNICODE_EMOJIS, TEXTS, truncate_text, CUSTOM_EMOJIS

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


# --- FONCTIONS UTILITAIRES ---

async def send_auto_delete(ctx, content=None, **kwargs):
    """Envoie une réponse via ctx.send avec nettoyage automatique.

    En mode préfixe (+), les réponses destinées à être éphémères ne le sont pas
    (Discord ne supporte l'éphéméral que pour les slash). Elles sont donc
    automatiquement supprimées après 15 secondes pour ne pas polluer le channel.
    En mode slash, comportement inchangé (éphéméral Discord).
    """
    message = await ctx.send(content, **kwargs)
    if kwargs.get('ephemeral') and ctx.interaction is None:
        await message.delete(delay=15)
    return message


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

    @commands.hybrid_command(name="ping", description="Vérifie la latence du bot (Check bot latency)")
    async def ping_slash(self, ctx: commands.Context):
        """Affiche la latence du bot."""
        latency = round(self.bot.latency * 1000)
        await send_auto_delete(ctx,f'{UNICODE_EMOJIS["ping"]} {TEXTS["ping_response"]} **{latency}ms**')

    @commands.hybrid_command(name="profil", description="Affiche un profil détaillé (Display a detailed profile - Compatible ID)")
    @app_commands.describe(user="Utilisateur (Optionnel/Optional)", user_id="ID de l'utilisateur (si pas sur le serveur)")
    async def profil_slash(self, ctx: commands.Context, user: discord.User = None, user_id: str = None):
        """Affiche le profil détaillé d'un utilisateur."""
        await ctx.defer()

        try:
            guild = ctx.guild

            # Support ID brut : le sélecteur slash ne résout pas toujours un
            # utilisateur hors serveur, on fetch directement par ID.
            if not user and user_id:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except (ValueError, discord.NotFound, discord.HTTPException):
                    await send_auto_delete(ctx,TEXTS["invalid_id"], ephemeral=True)
                    return

            target_user = user or ctx.author
            member = await get_member(guild, target_user.id)

            color = get_user_color(target_user, member)
            roles_str = format_roles(member) if member else TEXTS["profile_off_server"]

            embed = self._create_profile_embed(guild, target_user, member, color, roles_str)
            await send_auto_delete(ctx,embed=embed)

        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Erreur /profil : {e}")
            await send_auto_delete(ctx,TEXTS["profile_error"], ephemeral=True)
        except Exception as e:
            import traceback
            print(f"❌ Erreur inattendue /profil : {type(e).__name__}: {e}")
            traceback.print_exc()
            await send_auto_delete(ctx,TEXTS["profile_error"], ephemeral=True)

    @commands.hybrid_command(name="info", description="Affiche la liste des commandes (Show command list)")
    async def info_slash(self, ctx: commands.Context):
        """Affiche la liste de toutes les commandes du bot."""
        commands_list = (
            "**Liste des commande :**\n\n"
            "**Ping** - `/ping ou +ping`\n"
            "**Profile User** - `/profil ou +profil [user]`\n"
            "**Sync Commande** - `/sync ou +sync`\n"
            "**Supprimer Message** - `/clear ou +clear 50 [user]`\n"
            "**Mute** - `/mute ou +mute [user] [raison] [h] [m] [s]`\n"
            "**Unmute** - `/unmute ou +unmute [user]`\n"
            "**Kick** - `/kick ou +kick [user] [raison]`\n"
            "**Ban** - `/ban ou +ban [user] [raison]`\n"
            "**Unban** - `/unban ou +unban [ID User] [raison]`\n"
            "**Avertissement** - `/avert ou +avert [user] [raison]`\n"
            "**Liste Sanction** - `/sanctionliste ou +sanctionliste [user]`\n"
            "**Créer Giveaway** - `/createg ou +createg`\n"
            "**Démarrer Giveaway** - `/startg ou +startg [temps] [gagnants] [récompense]`\n"
            "**Terminer Giveaway** - `/endg ou +endg [ID]`\n"
            "**Supprimer Giveaway** - `/deletedg ou +deletedg [ID]`\n"
            "**Reroll Giveaway** - `/rerollg ou +rerollg [ID]`"
        )

        embed = discord.Embed(color=discord.Color(int("B821FF", 16)))  # Violet
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["info"]} **{TEXTS["info_title"]}**\n{commands_list}'
        embed.set_footer(text=self._footer("info", ctx.author.id))
        await send_auto_delete(ctx,embed=embed)

    def _footer(self, log_type: str, entity_id) -> str:
        """Génère le footer standardisé avec logID (même format que le cog Logs)."""
        from cogs.logs import get_timestamp, _log_id_for
        return f"{_log_id_for(log_type)} • ID: {entity_id} • {get_timestamp()}"

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

    @commands.hybrid_command(name='sync', description="Synchronise les commandes slash sur le serveur (Dev)")
    async def sync(self, ctx: commands.Context):
        """Synchronise les commandes slash sur le serveur (Dev, réservé Owner/Admin)."""
        # Vérification de permission (délègue au cog Moderation)
        mod_cog = self.bot.get_cog('Moderation')
        if mod_cog and not await mod_cog.check_permission(ctx, "sync"):
            await ctx.send("❌ Commande réservée au propriétaire du serveur.", ephemeral=True)
            return
        if ctx.guild is None:
            await ctx.send("❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True)
            return

        print("🔄 Synchronisation des commandes slash...")

        # Log de l'utilisation de la commande (+sync ou /sync selon le mode)
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use("sync", ctx.author, prefix))

        self.bot.tree.copy_global_to(guild=ctx.guild)

        try:
            synced = await self.bot.tree.sync(guild=ctx.guild)
            print(f"{UNICODE_EMOJIS['check']} Sync terminé. {len(synced)} commandes chargées.")
            await send_auto_delete(ctx,f"{UNICODE_EMOJIS['check']} {TEXTS['sync_success']} {len(synced)} commandes chargées.")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"{UNICODE_EMOJIS['cross']} Erreur Sync : {e}")
            await send_auto_delete(ctx,f"{UNICODE_EMOJIS['cross']} {TEXTS['sync_error']}")


async def setup(bot):
    """Setup du cog Base."""
    await bot.add_cog(Base(bot))
