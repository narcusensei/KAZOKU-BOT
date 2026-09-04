# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

import discord
import asyncio
from discord.ext import commands
from discord import app_commands
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    PERMISSIONS, SANCTION_EMOJIS, SANCTION_COLORS, SANCTION_TYPES,
    MAX_CLEAR_AMOUNT, MIN_CLEAR_AMOUNT, MAX_SANCTIONS_DISPLAY, MAX_SANCTIONS_SELECT,
    WARNINGS_FILE, DATA_DIR, UNICODE_EMOJIS, TEXTS, SANCTIONLIST_COLOR, truncate_text
)
from cogs.base import send_auto_delete

# --- FONCTIONS UTILITAIRES ---

def ensure_data_directory():
    """S'assure que le répertoire data existe."""
    os.makedirs(DATA_DIR, exist_ok=True)


def format_duration(hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    """Formate une durée en texte lisible."""
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def get_current_timestamp() -> str:
    """Retourne le timestamp UTC actuel formaté."""
    return datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")


# Verrou global protégeant warnings.json contre les accès concurrents (read-modify-write).
# Partagé entre le cog Moderation et les vues UI (SpecificSanctionView / MainSanctionView).
_warnings_lock = asyncio.Lock()


async def add_sanction_data_async(user_id: int, sanction_type: str, reason: str, moderator: str, duration: str = "") -> int:
    """Version asynchrone et thread-safe d'add_sanction_data (utilise le verrou global)."""
    async with _warnings_lock:
        return add_sanction_data(user_id, sanction_type, reason, moderator, duration)


# --- VUES ---

class SpecificSanctionView(discord.ui.View):
    """Vue pour sélectionner et supprimer une sanction spécifique."""

    def __init__(self, user_id: str):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.select(
        placeholder=TEXTS["select_placeholder"],
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_idx = int(select.values[0])
        uid = self.user_id

        async with _warnings_lock:
            try:
                data = load_warnings_data()
            except (IOError, json.JSONDecodeError):
                await interaction.response.send_message(TEXTS["data_read_error"], ephemeral=True)
                return

            if uid in data and len(data[uid]) > selected_idx:
                removed = data[uid].pop(selected_idx)
                try:
                    save_warnings_data(data)
                except (IOError, json.JSONDecodeError):
                    await interaction.response.send_message(TEXTS["data_save_error"], ephemeral=True)
                    return
            else:
                await interaction.response.send_message(f'{UNICODE_EMOJIS["cross"]} {TEXTS["sanction_not_found"]}', ephemeral=True)
                return

        await interaction.response.send_message(f'{UNICODE_EMOJIS["check"]} {TEXTS["sanction_deleted"].format(type=removed["type"])}', ephemeral=True)
        self.stop()


class MainSanctionView(discord.ui.View):
    """Vue principale de gestion des sanctions."""

    def __init__(self, user_id: str):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label=TEXTS["select_delete_specific"], style=discord.ButtonStyle.primary)
    async def specific_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            data = load_warnings_data()
        except (IOError, json.JSONDecodeError):
            await interaction.response.send_message(TEXTS["data_read_error"], ephemeral=True)
            return

        uid = self.user_id
        allowed_types = SANCTION_TYPES

        valid_sanctions = []
        if uid in data:
            for idx, sanction in enumerate(data[uid]):
                if sanction.get("type") in allowed_types:
                    valid_sanctions.append((idx, sanction))

        if not valid_sanctions:
            await interaction.response.send_message(TEXTS["no_sanctions_to_delete"], ephemeral=True)
            return

        options = []
        for real_idx, sanction in valid_sanctions[-MAX_SANCTIONS_SELECT:]:
            s_type = sanction.get("type")
            date_short = sanction['date'].split(' ')[0]
            reason_short = truncate_text(sanction['reason'], 30)

            options.append(discord.SelectOption(
                label=f"{s_type} ({date_short})",
                value=str(real_idx),
                description=reason_short
            ))

        view = SpecificSanctionView(self.user_id)
        view.select_callback.options = options

        await interaction.response.send_message(TEXTS["choose_sanction"], view=view, ephemeral=True)

    @discord.ui.button(label=TEXTS["select_delete_all"], style=discord.ButtonStyle.danger)
    async def delete_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = self.user_id

        async with _warnings_lock:
            try:
                data = load_warnings_data()
            except (IOError, json.JSONDecodeError):
                await interaction.response.send_message(TEXTS["data_read_error"], ephemeral=True)
                return

            if uid not in data:
                await interaction.response.send_message(TEXTS["nothing_to_delete"], ephemeral=True)
                return

            del data[uid]
            try:
                save_warnings_data(data)
            except (IOError, json.JSONDecodeError):
                await interaction.response.send_message(TEXTS["data_save_error"], ephemeral=True)
                return

        self.stop()
        await interaction.response.edit_message(content=f'{UNICODE_EMOJIS["check"]} {TEXTS["all_sanctions_deleted"]}', embed=None, view=None)


# --- FONCTIONS DE GESTION DES DONNÉES ---

def load_warnings_data() -> Dict[str, Any]:
    """Charge les données des avertissements depuis le fichier JSON."""
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur chargement warnings: {e}")
            return {}
    return {}


def save_warnings_data(data: Dict[str, Any]) -> None:
    """Sauvegarde les données des avertissements dans le fichier JSON."""
    ensure_data_directory()
    with open(WARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def add_sanction_data(user_id: int, sanction_type: str, reason: str, moderator: str, duration: str = "") -> int:
    """Ajoute une sanction aux données et retourne le nouveau total."""
    data = load_warnings_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = []

    data[uid].append({
        "type": sanction_type,
        "reason": reason,
        "duration": duration,
        "date": get_current_timestamp(),
        "moderator": moderator
    })

    save_warnings_data(data)
    return len(data[uid])


def get_sanctions_by_type(user_id: int) -> List[Dict[str, Any]]:
    """Retourne les sanctions d'un utilisateur filtrées par type."""
    data = load_warnings_data()
    uid = str(user_id)
    allowed_types = SANCTION_TYPES

    sanctions = []
    if uid in data:
        sanctions = [s for s in data[uid] if s.get("type") in allowed_types]

    return sanctions


# --- COG MODÉRATION ---

class Moderation(commands.Cog):
    """Cog de gestion de la modération."""

    def __init__(self, bot):
        self.bot = bot

    # --- VÉRIFICATION DES PERMISSIONS ---

    async def get_member(self, guild: discord.Guild, user_id: int) -> Optional[discord.Member]:
        """Récupère un membre depuis le cache ou via l'API."""
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except (discord.NotFound, discord.HTTPException):
                pass
        return member

    async def check_permission(self, ctx: commands.Context, command_name: str) -> bool:
        """Vérifie si l'utilisateur a la permission d'exécuter une commande."""
        user = ctx.author
        if user.id == ctx.guild.owner_id:
            return True

        author_member = await self.get_member(ctx.guild, user.id)
        if not author_member:
            return False

        allowed_roles = PERMISSIONS.get(command_name, [])
        user_roles_names = [role.name for role in author_member.roles]
        return any(role in allowed_roles for role in user_roles_names)

    async def check_sanction_possible(self, ctx: commands.Context, target: discord.abc.User, command_name: str) -> Tuple[bool, Optional[str]]:
        """Vérifie si une sanction est possible (permissions + hiérarchie)."""
        if ctx.author.id == ctx.guild.owner_id:
            return True, None

        if not await self.check_permission(ctx, command_name):
            return False, TEXTS["no_role_for_command"].format(command_name=command_name)

        author_member = await self.get_member(ctx.guild, ctx.author.id)
        if not author_member:
            return False, TEXTS["internal_error"]

        target_member = await self.get_member(ctx.guild, target.id)

        if target_member:
            if target.id == ctx.guild.owner_id:
                return False, TEXTS["cannot_sanction_owner"]
            if author_member.top_role <= target_member.top_role:
                return False, TEXTS["cannot_sanction_higher"].format(target=target.display_name)
            if ctx.guild.me.top_role <= target_member.top_role:
                return False, TEXTS["bot_cannot_sanction"].format(target=target.display_name)

        return True, None

    def send_logs(self, ctx: commands.Context, action_type: str, target: discord.abc.User, moderator: discord.abc.User, reason: str, duration_str: str = None, end_time: datetime = None) -> None:
        """Envoie les logs au cog Logs si disponible."""
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            asyncio.create_task(logs_cog.send_log(ctx, action_type, target, moderator, reason, duration_str, end_time))

    def log_command_use(self, ctx: commands.Context, command_name: str) -> None:
        """Log l'utilisation d'une commande de modération (après check de permission).

        Affiche +commande (préfixe) ou /commande (slash) selon le mode utilisé.
        """
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use(command_name, ctx.author, prefix))

    # --- COMMANDES ---

    @commands.hybrid_command(name="clear", description="Supprime des messages (Delete messages)")
    @app_commands.describe(amount="Nombre de messages 1-100", user="Utilisateur ou ID (Optionnel/Optional)")
    async def clear_slash(self, ctx: commands.Context, amount: int, user: discord.User = None):
        """Supprime des messages dans le channel."""
        if not await self.check_permission(ctx, "clear"):
            await send_auto_delete(ctx,TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "clear")

        if not MIN_CLEAR_AMOUNT <= amount <= MAX_CLEAR_AMOUNT:
            await send_auto_delete(ctx,TEXTS["clear_amount_error"].format(min=MIN_CLEAR_AMOUNT, max=MAX_CLEAR_AMOUNT), ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            if user:
                deleted = await self._clear_user_messages(ctx, user, amount)
            else:
                deleted = await ctx.channel.purge(limit=amount)
                deleted = len(deleted)

            await send_auto_delete(ctx,TEXTS["clear_success"].format(n=deleted), ephemeral=True)
        except (discord.Forbidden, discord.HTTPException):
            await send_auto_delete(ctx,TEXTS["clear_error"], ephemeral=True)

    async def _clear_user_messages(self, ctx: commands.Context, user: discord.User, amount: int) -> int:
        """Supprime les messages d'un utilisateur spécifique."""
        to_delete = []
        async for message in ctx.channel.history(limit=100):
            if message.author == user:
                to_delete.append(message)
                if len(to_delete) >= amount:
                    break

        if not to_delete:
            return 0

        try:
            await ctx.channel.delete_messages(to_delete)
            return len(to_delete)
        except discord.HTTPException:
            # Fallback : suppression individuelle
            for msg in to_delete:
                try:
                    await msg.delete()
                except discord.HTTPException:
                    pass
            return len(to_delete)

    @commands.hybrid_command(name="mute", description="Mute un membre (Mute a member)")
    @app_commands.describe(user="Membre", reason="Raison (Optionnel/Optional)", hours="Heures", minutes="Minutes", seconds="Secondes")
    async def mute_slash(self, ctx: commands.Context, user: discord.User, reason: str = None, hours: int = 0, minutes: int = 0, seconds: int = 0):
        """Applique un timeout à un membre."""
        can_proceed, error_msg = await self.check_sanction_possible(ctx, user, "mute")
        if not can_proceed:
            await send_auto_delete(ctx,error_msg, ephemeral=True)
            return

        self.log_command_use(ctx, "mute")

        if user == ctx.author:
            await send_auto_delete(ctx,TEXTS["self_mute"], ephemeral=True)
            return

        target_member = await self.get_member(ctx.guild, user.id)
        if not target_member:
            await send_auto_delete(ctx,TEXTS["user_not_on_server"], ephemeral=True)
            return

        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        if duration.total_seconds() <= 0:
            await send_auto_delete(ctx,TEXTS["no_duration"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            mute_end = datetime.now(timezone.utc) + duration
            await target_member.edit(timed_out_until=mute_end)
        except discord.Forbidden:
            await send_auto_delete(ctx,TEXTS["missing_permission"], ephemeral=True)
            return
        except discord.HTTPException:
            await send_auto_delete(ctx,TEXTS["mute_error"], ephemeral=True)
            return

        dur_str = format_duration(hours, minutes, seconds)
        await add_sanction_data_async(user.id, "Mute", reason or TEXTS["none"], ctx.author.name, dur_str)

        self.send_logs(ctx, "Mute", user, ctx.author, reason or TEXTS["none"], dur_str, mute_end)

        embed = discord.Embed(
            title=TEXTS["mute_title"],
            description=f"**{user.name}** {TEXTS['mute_description'].format(dur=dur_str)}",
            color=SANCTION_COLORS.get("Mute")
        )
        if reason:
            embed.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
        embed.set_footer(text=TEXTS["sanction_by"].format(name=ctx.author.name))
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="unmute", description="Unmute un membre (Unmute a member)")
    @app_commands.describe(user="Membre")
    async def unmute_slash(self, ctx: commands.Context, user: discord.User):
        """Retire le timeout d'un membre."""
        if not await self.check_permission(ctx, "unmute"):
            await send_auto_delete(ctx,TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "unmute")

        member = await self.get_member(ctx.guild, user.id)
        if not member:
            await send_auto_delete(ctx,TEXTS["user_not_found"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            await member.edit(timed_out_until=None)
        except discord.Forbidden:
            await send_auto_delete(ctx,TEXTS["missing_permission"], ephemeral=True)
            return
        except discord.HTTPException:
            await send_auto_delete(ctx,TEXTS["unmute_error"], ephemeral=True)
            return

        await add_sanction_data_async(user.id, "Unmute", TEXTS["unmute_reason"], ctx.author.name)
        self.send_logs(ctx, "Unmute", user, ctx.author, TEXTS["unmute_reason"])

        embed = discord.Embed(
            title=TEXTS["unmute_title"],
            description=f"**{user.name}** {TEXTS['unmute_description']}",
            color=SANCTION_COLORS.get("Unmute")
        )
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="kick", description="Kick un membre (Kick a member)")
    @app_commands.describe(user="Membre", reason="Raison (Optionnel/Optional)")
    async def kick_slash(self, ctx: commands.Context, user: discord.Member, reason: str = None):
        """Expulse un membre du serveur."""
        can_proceed, error_msg = await self.check_sanction_possible(ctx, user, "kick")
        if not can_proceed:
            await send_auto_delete(ctx,error_msg, ephemeral=True)
            return

        self.log_command_use(ctx, "kick")

        await ctx.defer(ephemeral=True)

        try:
            await user.kick(reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await send_auto_delete(ctx,TEXTS["kick_error"], ephemeral=True)
            return

        # Enregistrer et logger seulement si l'action a réussi
        await add_sanction_data_async(user.id, "Kick", reason or TEXTS["none"], ctx.author.name)
        self.send_logs(ctx, "Kick", user, ctx.author, reason or TEXTS["none"])

        embed = discord.Embed(
            title=TEXTS["kick_title"],
            description=f"**{user.name}** {TEXTS['kick_description']}",
            color=SANCTION_COLORS.get("Kick")
        )
        if reason:
            embed.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="ban", description="Ban un utilisateur (Ban a user)")
    @app_commands.describe(user="Utilisateur", reason="Raison (Optionnel/Optional)")
    async def ban_slash(self, ctx: commands.Context, user: discord.User, reason: str = None):
        """Bannit un utilisateur du serveur."""
        can_proceed, error_msg = await self.check_sanction_possible(ctx, user, "ban")
        if not can_proceed:
            await send_auto_delete(ctx,error_msg, ephemeral=True)
            return

        self.log_command_use(ctx, "ban")

        await ctx.defer(ephemeral=True)

        try:
            await ctx.guild.ban(discord.Object(id=user.id), reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await send_auto_delete(ctx,TEXTS["ban_error"], ephemeral=True)
            return

        # Enregistrer et logger seulement si l'action a réussi
        await add_sanction_data_async(user.id, "Ban", reason or TEXTS["none"], ctx.author.name)
        self.send_logs(ctx, "Ban", user, ctx.author, reason or TEXTS["none"])

        embed = discord.Embed(
            title=TEXTS["ban_title"],
            description=f"**{user.name}** {TEXTS['ban_description']}",
            color=SANCTION_COLORS.get("Ban")
        )
        if reason:
            embed.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="unban", description="Débannir un utilisateur par ID (Unban a user by ID)")
    @app_commands.describe(target_id="ID de l'utilisateur", reason="Raison (Optionnel/Optional)")
    async def unban_slash(self, ctx: commands.Context, target_id: str, reason: str = None):
        """Débannit un utilisateur."""
        if not await self.check_permission(ctx, "unban"):
            await send_auto_delete(ctx,TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "unban")

        try:
            user_id = int(target_id)
        except ValueError:
            await send_auto_delete(ctx,TEXTS["invalid_id"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        try:
            ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
            user_to_unban = ban_entry.user
        except discord.NotFound:
            await send_auto_delete(ctx,TEXTS["user_not_banned"], ephemeral=True)
            return
        except discord.HTTPException:
            await send_auto_delete(ctx,TEXTS["ban_check_error"], ephemeral=True)
            return

        try:
            await ctx.guild.unban(user_to_unban, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            await send_auto_delete(ctx,TEXTS["unban_error"], ephemeral=True)
            return

        # Enregistrer et logger seulement si l'action a réussi
        await add_sanction_data_async(user_to_unban.id, "Unban", reason or TEXTS["none"], ctx.author.name)
        self.send_logs(ctx, "Unban", user_to_unban, ctx.author, reason or TEXTS["none"])

        embed = discord.Embed(
            title=TEXTS["unban_title"],
            description=f"**{user_to_unban.name}** {TEXTS['unban_description']}",
            color=SANCTION_COLORS.get("Unban")
        )
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="avert", description="Avertir un utilisateur (Warn a user)")
    @app_commands.describe(user="Utilisateur", reason="Raison")
    async def avert_slash(self, ctx: commands.Context, user: discord.User, reason: str):
        """Envoie un avertissement à un utilisateur."""
        can_proceed, error_msg = await self.check_sanction_possible(ctx, user, "avert")
        if not can_proceed:
            await send_auto_delete(ctx,error_msg, ephemeral=True)
            return

        self.log_command_use(ctx, "avert")

        if user.bot:
            await send_auto_delete(ctx,TEXTS["cannot_warn_bot"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        count = await add_sanction_data_async(user.id, "Avertissement", reason, ctx.author.name)
        self.send_logs(ctx, "Avertissement", user, ctx.author, reason)

        # Envoi DM
        try:
            embed_dm = discord.Embed(
                title=TEXTS["avert_dm_title"],
                description=TEXTS["avert_dm_description"].format(guild=ctx.guild.name),
                color=SANCTION_COLORS.get("Avertissement")
            )
            embed_dm.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
            await user.send(embed=embed_dm)
        except (discord.Forbidden, discord.HTTPException):
            pass  # L'utilisateur a désactivé les DMs

        embed = discord.Embed(
            title=TEXTS["avert_title"],
            description=f"**{user.name}** {TEXTS['avert_description'].format(count=count)}",
            color=SANCTION_COLORS.get("Avertissement")
        )
        embed.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
        await send_auto_delete(ctx,embed=embed)

    @commands.hybrid_command(name="sanctionliste", description="Voir les sanctions (View sanctions)")
    @app_commands.describe(user="Utilisateur")
    async def sanctionliste_slash(self, ctx: commands.Context, user: discord.User):
        """Affiche la liste des sanctions d'un utilisateur."""
        if not await self.check_permission(ctx, "sanctionliste"):
            await send_auto_delete(ctx,TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "sanctionliste")

        sanctions = get_sanctions_by_type(user.id)

        embed = discord.Embed(
            title=TEXTS["sanctionlist_title"].format(name=user.name),
            color=SANCTIONLIST_COLOR
        )

        if sanctions:
            sanctions.reverse()
            for sanction in sanctions[:MAX_SANCTIONS_DISPLAY]:
                s_type = sanction.get("type")
                emoji = SANCTION_EMOJIS.get(s_type, f"{UNICODE_EMOJIS['package']}")
                value = f"**{TEXTS['sanctionlist_reason']}** {sanction['reason']}\n**{TEXTS['sanctionlist_by']}** {sanction['moderator']}"
                embed.add_field(name=f"{emoji} {s_type}", value=value, inline=False)
        else:
            embed.description = f"{TEXTS['sanctionlist_empty']} {UNICODE_EMOJIS['party']}"

        view = MainSanctionView(str(user.id))
        await send_auto_delete(ctx,embed=embed, view=view)


async def setup(bot):
    """Setup du cog."""
    await bot.add_cog(Moderation(bot))
