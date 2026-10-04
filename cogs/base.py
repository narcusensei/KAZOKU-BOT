# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

import discord
import asyncio
import re
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


# --- MODAL DE CRÉATION D'EMBED ---

EMBED_DEFAULT_COLOR = "B821FF"  # Violet (identité du bot)

class EmbedModal(discord.ui.Modal, title=TEXTS["embed_form_title"]):
    """Formulaire interactif de création d'embed personnalisé."""

    title_input = discord.ui.TextInput(
        label=TEXTS["embed_form_title_label"],
        max_length=256,
        required=False
    )
    desc_input = discord.ui.TextInput(
        label=TEXTS["embed_form_desc_label"],
        style=discord.TextStyle.paragraph,
        max_length=4000,
        required=True
    )
    color_input = discord.ui.TextInput(
        label=TEXTS["embed_form_color_label"],
        placeholder="#FF0000",
        max_length=7,
        required=False
    )
    image_input = discord.ui.TextInput(
        label=TEXTS["embed_form_image_label"],
        placeholder=TEXTS["embed_form_image_placeholder"],
        max_length=500,
        required=False
    )
    footer_input = discord.ui.TextInput(
        label=TEXTS["embed_form_footer_label"],
        max_length=256,
        required=False
    )

    def __init__(self, cog, authorized_user_id: int):
        super().__init__()
        self.cog = cog
        self.authorized_user_id = authorized_user_id

    async def on_submit(self, interaction: discord.Interaction):
        # Re-vérification de la permission (seul l'auteur de la commande peut soumettre)
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return

        # Validation de la couleur (hex 6 chiffres, # optionnel, violet par défaut)
        color_raw = str(self.color_input).strip() if self.color_input.value else ""
        if color_raw:
            match = re.fullmatch(r'#?([0-9a-fA-F]{6})', color_raw)
            if not match:
                await interaction.response.send_message(TEXTS["embed_color_invalid"], ephemeral=True)
                return
            color = discord.Color(int(match.group(1), 16))
        else:
            color = discord.Color(int(EMBED_DEFAULT_COLOR, 16))

        # Validation de l'URL d'image : n'importe quelle URL http(s) directe
        # (avec ou sans extension — c'est Discord qui fait le rendu).
        # Préfixe "mini:" pour afficher en miniature au lieu de grande image.
        image_raw = str(self.image_input).strip() if self.image_input.value else ""
        is_thumbnail = image_raw.lower().startswith("mini:")
        image_url = image_raw[5:].strip() if is_thumbnail else image_raw
        if image_url and not re.fullmatch(r'https?://\S+', image_url):
            await interaction.response.send_message(TEXTS["embed_image_invalid"], ephemeral=True)
            return

        # Construction de l'embed
        embed = discord.Embed(color=color, description=str(self.desc_input).strip())
        if self.title_input.value:
            embed.title = str(self.title_input).strip()
        if self.footer_input.value:
            embed.set_footer(text=str(self.footer_input).strip())
        if image_url:
            if is_thumbnail:
                embed.set_thumbnail(url=image_url)
            else:
                embed.set_image(url=image_url)

        # Publication dans le channel de la commande
        await interaction.response.defer(ephemeral=True)
        try:
            await interaction.channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            await interaction.followup.send(TEXTS["embed_send_error"], ephemeral=True)
            return
        await interaction.followup.send(TEXTS["embed_sent_ok"], ephemeral=True)

        # Log #L105 dans le channel action
        logs_cog = self.cog.bot.get_cog('Logs')
        if not logs_cog:
            return
        log_channel = logs_cog._get_log_channel("action")
        if not log_channel:
            return
        try:
            log_embed = discord.Embed(color=discord.Color(int(EMBED_DEFAULT_COLOR, 16)))  # Violet
            log_embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            log_embed.description = (
                f'{CUSTOM_EMOJIS["info"]} **{TEXTS["embed_log_title"]}**\n'
                f'{TEXTS["embed_log_desc"]}'
            )
            title_display = embed.title or TEXTS["embed_log_no_title"]
            log_embed.add_field(name=TEXTS["embed_log_title_field"], value=truncate_text(title_display, 1000), inline=False)
            log_embed.add_field(name=TEXTS["member_by"], value=interaction.user.mention, inline=False)
            log_embed.add_field(name=TEXTS["channel_field"], value=interaction.channel.mention, inline=False)
            log_embed.set_footer(text=logs_cog._footer("embed_create", interaction.user.id))
            await log_channel.send(embed=log_embed)
        except (discord.Forbidden, discord.HTTPException):
            pass


# --- BOUTON OUVRIR LE FORMULAIRE (préfixe) ---

class EmbedOpenFormView(discord.ui.View):
    """Vue avec un bouton ouvrant le modal (usage préfixe)."""

    def __init__(self, cog, authorized_user_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.authorized_user_id = authorized_user_id

    @discord.ui.button(label="📝 Ouvrir le formulaire", style=discord.ButtonStyle.primary)
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return
        await interaction.response.send_modal(
            EmbedModal(self.cog, self.authorized_user_id)
        )
        try:
            await interaction.message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


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
        """Affiche la liste de toutes les commandes du bot, réparties par catégorie."""
        commands_list = (
            "━━━━━━━ 🤖 **GÉNÉRAL** ━━━━━━━\n"
            "**Ping** - `/ping ou +ping`\n"
            "**Profile User** - `/profil ou +profil [user]`\n"
            "**Info** - `/info ou +info`\n"
            "**Sync** - `/sync ou +sync`\n"
            "**Embed** - `/embed ou +embed`\n"
            "━━━━━━━ 🔨 **MODÉRATION** ━━━━━━━\n"
            "**Supprimer Message** - `/clear ou +clear 50 [user]`\n"
            "**Mute** - `/mute ou +mute [user] [raison] [h] [m] [s]`\n"
            "**Unmute** - `/unmute ou +unmute [user]`\n"
            "**Kick** - `/kick ou +kick [user] [raison]`\n"
            "**Ban** - `/ban ou +ban [user] [raison]`\n"
            "**Unban** - `/unban ou +unban [ID User] [raison]`\n"
            "**Avertissement** - `/avert ou +avert [user] [raison]`\n"
            "**Liste Sanction** - `/sanctionliste ou +sanctionliste [user]`\n"
            "━━━━━━━ 🎉 **GIVEAWAY** ━━━━━━━\n"
            "**Créer** - `/gcreate ou +gcreate`\n"
            "**Démarrer** - `/gstart ou +gstart [temps] [gagnants] [récompense] [desc]`\n"
            "**Terminer** - `/gend ou +gend [ID]`\n"
            "**Supprimer** - `/gdelete ou +gdelete [ID]`\n"
            "**Reroll** - `/greroll ou +greroll [ID]`\n"
            "━━━━━━━ ⏰ **RAPPEL** ━━━━━━━\n"
            "**Créer** - `/reminder ou +reminder`\n"
            "**Liste** - `/reminderlist ou +reminderlist`"
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
        # Check guild EN PREMIER (check_permission accède à guild.owner_id)
        if ctx.guild is None:
            await send_auto_delete(ctx, "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True)
            return

        # Vérification de permission (fail-closed : refuser si le cog Moderation est absent)
        mod_cog = self.bot.get_cog('Moderation')
        if not mod_cog or not await mod_cog.check_permission(ctx, "sync"):
            await send_auto_delete(ctx, "❌ Commande réservée à l'Owner et aux Admins.", ephemeral=True)
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

    @commands.hybrid_command(name="embed", description="Créer un embed personnalisé (Create a custom embed)")
    async def embed_slash(self, ctx: commands.Context):
        """Ouvre le formulaire de création d'embed personnalisé."""
        # Check guild EN PREMIER (check_permission accède à guild.owner_id)
        if ctx.guild is None:
            await send_auto_delete(ctx, "❌ Cette commande doit être utilisée dans un serveur.", ephemeral=True)
            return

        # Vérification de permission (fail-closed : refuser si le cog Moderation est absent)
        mod_cog = self.bot.get_cog('Moderation')
        if not mod_cog or not await mod_cog.check_permission(ctx, "embed"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        # Log de l'utilisation de la commande (+embed ou /embed selon le mode)
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use("embed", ctx.author, prefix))

        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(
                EmbedModal(self, ctx.author.id)
            )
        else:
            await ctx.send(
                f'{CUSTOM_EMOJIS["info"]} {TEXTS["embed_open_form"]}',
                view=EmbedOpenFormView(self, ctx.author.id)
            )


async def setup(bot):
    """Setup du cog Base."""
    await bot.add_cog(Base(bot))
