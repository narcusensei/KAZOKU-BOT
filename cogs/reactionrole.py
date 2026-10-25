# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

import discord
import asyncio
import json
import os
import re
import sys
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    TEXTS, CUSTOM_EMOJIS, REACTION_ROLES_FILE
)
from cogs.base import send_auto_delete

from cogs.logs import get_timestamp, _log_id_for

RR_COLOR = "B821FF"  # Violet (identité du bot)

# --- STOCKAGE (lock + écriture atomique, cf. conventions) ---

_rr_lock = asyncio.Lock()


def load_rr() -> dict:
    """Charge la config des rôles à réaction : {message_id: {guild_id, channel_id, pairs}}."""
    if os.path.exists(REACTION_ROLES_FILE):
        try:
            with open(REACTION_ROLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_rr(data: dict) -> None:
    """Sauvegarde atomique de la config des rôles à réaction."""
    tmp = REACTION_ROLES_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, REACTION_ROLES_FILE)


def parse_emoji_arg(raw: str):
    """Normalise un émoji passé en argument.

    Retourne (clé_canonique, format_réaction) ou (None, None) si invalide.
    Accepte : <:nom:ID>, <a:nom:ID>, nom:ID, ou un émoji Unicode.
    """
    raw = raw.strip()
    m = re.fullmatch(r'<(a?):([A-Za-z0-9_~]+):(\d{15,25})>', raw)
    if m:
        animated, name, eid = m.groups()
        return f'{name}:{eid}', f'<{animated}:{name}:{eid}>'
    m = re.fullmatch(r'(a?):?([A-Za-z0-9_~]+):(\d{15,25})', raw)
    if m:
        animated, name, eid = m.groups()
        return f'{name}:{eid}', f'<{animated}:{name}:{eid}>'
    # émoji Unicode (jamais un ID de rôle ou un nombre)
    if raw and not raw.isdigit() and len(raw) <= 12 and not re.search(r'[ <>@]', raw):
        return raw, raw
    return None, None


def reaction_key_from_partial(emoji: discord.PartialEmoji) -> str:
    """Clé canonique d'un émoji reçu dans un payload de réaction."""
    if emoji.id:
        return f'{emoji.name}:{emoji.id}'
    return emoji.name


class ReactionRole(commands.Cog):
    """Rôles à réaction : réagir à un émoji donne/retire un rôle."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("📦 Cog 'ReactionRole' chargé.")

    # --- RECHERCHE DU MESSAGE ---

    async def _find_message(self, guild, channel, message_id: int):
        """Retrouve un message : d'abord le salon courant, puis tout le serveur."""
        try:
            return await channel.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden):
            pass
        for ch in guild.text_channels:
            if ch.id == channel.id:
                continue
            try:
                return await ch.fetch_message(message_id)
            except (discord.NotFound, discord.Forbidden):
                continue
        return None

    # --- PARCOURS DES PAIRES ---

    def _parse_pairs(self, guild, pairs_str: str):
        """Valide la chaîne "emoji1 rôle1 emoji2 rôle2…".

        Retourne (liaisons, erreur) : liaisons = [(clé, format_réaction, rôle)],
        erreur = None ou message d'erreur complet.
        """
        parts = pairs_str.split()
        if not parts or len(parts) % 2 != 0:
            return None, TEXTS["rr_err_odd_pairs"]
        bindings = []
        for i in range(0, len(parts), 2):
            emoji_raw, role_raw = parts[i], parts[i + 1]
            key, react_fmt = parse_emoji_arg(emoji_raw)
            if key is None:
                return None, TEXTS["rr_err_bad_emoji"].format(emoji=emoji_raw)
            if not role_raw.isdigit():
                return None, TEXTS["rr_err_role_not_found"].format(role=role_raw)
            role = guild.get_role(int(role_raw))
            if role is None:
                return None, TEXTS["rr_err_role_not_found"].format(role=role_raw)
            if role >= guild.me.top_role:
                return None, TEXTS["rr_err_role_too_high"].format(role=role.mention)
            bindings.append((key, react_fmt, role))
        return bindings, None

    # --- LOGS ---

    async def _log_config(self, log_type: str, user, message, pairs_desc: str, count: int):
        """Log de configuration (#L106-#L108) dans le channel action."""
        logs_cog = self.bot.get_cog('Logs')
        if not logs_cog:
            return
        log_channel = logs_cog._get_log_channel("action")
        if not log_channel:
            return
        try:
            embed = discord.Embed(color=discord.Color(int(RR_COLOR, 16)))
            embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
            titles = {
                "reaction_role_add": TEXTS["rr_log_add_title"],
                "reaction_role_remove": TEXTS["rr_log_remove_title"],
                "reaction_role_removeall": TEXTS["rr_log_removeall_title"],
            }
            descs = {
                "reaction_role_add": TEXTS["rr_log_add_desc"],
                "reaction_role_remove": TEXTS["rr_log_remove_desc"],
                "reaction_role_removeall": TEXTS["rr_log_removeall_desc"],
            }
            embed.title = f'{CUSTOM_EMOJIS["role_added"]} **{titles[log_type]}**'
            embed.description = descs[log_type].format(count=count)
            jump = message.jump_url if message else "`?`"
            embed.add_field(name=TEXTS["rr_log_message_field"], value=jump, inline=False)
            embed.add_field(name=TEXTS["rr_log_pairs_field"], value=pairs_desc, inline=False)
            embed.add_field(name=TEXTS["member_by"], value=user.mention, inline=False)
            embed.set_footer(text=logs_cog._footer(log_type, user.id))
            await log_channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

    def log_command_use(self, ctx: commands.Context, command_name: str) -> None:
        """Log l'utilisation de la commande (+ ou / selon le mode)."""
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use(command_name, ctx.author, prefix))

    # --- ÉCOUTEURS DE RÉACTIONS ---

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Donne le rôle quand un membre ajoute la réaction configurée."""
        if payload.user_id == self.bot.user.id:
            return
        entry = load_rr().get(str(payload.message_id))
        if not entry:
            return
        role_id = entry.get("pairs", {}).get(reaction_key_from_partial(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(entry.get("guild_id") or payload.guild_id)
        if not guild:
            return
        member = payload.member or guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        role = guild.get_role(int(role_id))
        if role is None or role in member.roles:
            return
        try:
            await member.add_roles(role, reason="Rôle à réaction")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Rôle à réaction : impossible de donner {role.name} à {member} : {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Retire le rôle quand un membre enlève la réaction configurée."""
        if payload.user_id == self.bot.user.id:
            return
        entry = load_rr().get(str(payload.message_id))
        if not entry:
            return
        role_id = entry.get("pairs", {}).get(reaction_key_from_partial(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(entry.get("guild_id") or payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if member is None or member.bot:
            return
        role = guild.get_role(int(role_id))
        if role is None or role not in member.roles:
            return
        try:
            await member.remove_roles(role, reason="Rôle à réaction (retrait)")
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Rôle à réaction : impossible de retirer {role.name} à {member} : {e}")

    # --- COMMANDES ---

    @commands.hybrid_group(name="reactionrole", invoke_without_command=True)
    async def reactionrole(self, ctx: commands.Context):
        """Gestion des rôles à réaction."""
        await send_auto_delete(ctx, TEXTS["rr_usage"], ephemeral=True)

    @reactionrole.command(name="add", description="Ajouter des rôles à réaction sur un message (Add reaction roles)")
    @app_commands.describe(
        message_id="ID du message",
        pairs="Paires emoji rôleID séparées par des espaces (ex: 🎮 123456789 🔧 987654321)"
    )
    async def add(self, ctx: commands.Context, message_id: str, *, pairs: str):
        """Lie des émojis à des rôles sur un message et réagit avec ces émojis."""
        if ctx.guild is None:
            await send_auto_delete(ctx, TEXTS["rr_err_guild_only"], ephemeral=True)
            return
        mod_cog = self.bot.get_cog('Moderation')
        if not mod_cog or not await mod_cog.check_permission(ctx, "reactionrole"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "reactionrole add")

        if not message_id.isdigit():
            await send_auto_delete(ctx, TEXTS["rr_err_message_not_found"], ephemeral=True)
            return
        message = await self._find_message(ctx.guild, ctx.channel, int(message_id))
        if message is None:
            await send_auto_delete(ctx, TEXTS["rr_err_message_not_found"], ephemeral=True)
            return

        bindings, err = self._parse_pairs(ctx.guild, pairs)
        if err:
            await send_auto_delete(ctx, err, ephemeral=True)
            return

        # Sauvegarde de la config
        async with _rr_lock:
            data = load_rr()
            entry = data.setdefault(str(message.id), {
                "guild_id": ctx.guild.id,
                "channel_id": message.channel.id,
                "pairs": {}
            })
            for key, _fmt, role in bindings:
                entry["pairs"][key] = str(role.id)
            save_rr(data)

        # Le bot ajoute les réactions sur le message
        for _key, react_fmt, _role in bindings:
            try:
                await message.add_reaction(react_fmt)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass

        pairs_desc = "\n".join(f'{fmt} → {role.mention}' for _k, fmt, role in bindings)
        await send_auto_delete(ctx, TEXTS["rr_added_ok"], ephemeral=True)
        await self._log_config("reaction_role_add", ctx.author, message, pairs_desc, len(bindings))

    @reactionrole.command(name="remove", description="Retirer des rôles à réaction d'un message (Remove reaction roles)")
    @app_commands.describe(
        message_id="ID du message",
        pairs="Paires emoji rôleID à retirer (ex: 🎮 123456789)"
    )
    async def remove(self, ctx: commands.Context, message_id: str, *, pairs: str):
        """Retire des liaisons émoji → rôle d'un message."""
        if ctx.guild is None:
            await send_auto_delete(ctx, TEXTS["rr_err_guild_only"], ephemeral=True)
            return
        mod_cog = self.bot.get_cog('Moderation')
        if not mod_cog or not await mod_cog.check_permission(ctx, "reactionrole"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "reactionrole remove")

        async with _rr_lock:
            data = load_rr()
            entry = data.get(str(message_id))
            if not entry or not entry.get("pairs"):
                await send_auto_delete(ctx, TEXTS["rr_err_no_config"], ephemeral=True)
                return

            parts = pairs.split()
            if not parts or len(parts) % 2 != 0:
                await send_auto_delete(ctx, TEXTS["rr_err_odd_pairs"], ephemeral=True)
                return

            removed = []  # (clé, format réaction, rôle)
            for i in range(0, len(parts), 2):
                emoji_raw, role_raw = parts[i], parts[i + 1]
                key, react_fmt = parse_emoji_arg(emoji_raw)
                if key is None or not role_raw.isdigit():
                    continue
                if entry["pairs"].get(key) == role_raw:
                    role = ctx.guild.get_role(int(role_raw))
                    removed.append((key, react_fmt, role or role_raw))
                    del entry["pairs"][key]

            if not removed:
                await send_auto_delete(ctx, TEXTS["rr_err_nothing_removed"], ephemeral=True)
                return

            if not entry["pairs"]:
                data.pop(str(message_id), None)
            save_rr(data)

        # Retirer les réactions du bot sur le message (best-effort)
        message = await self._find_message(ctx.guild, ctx.channel, int(message_id))
        if message:
            for _key, react_fmt, _role in removed:
                try:
                    await message.remove_reaction(react_fmt, self.bot.user)
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    pass

        pairs_desc = "\n".join(
            f'{fmt} → {r.mention if hasattr(r, "mention") else f"<@&{r}>"}'
            for _k, fmt, r in removed
        )
        await send_auto_delete(ctx, TEXTS["rr_removed_ok"], ephemeral=True)
        await self._log_config("reaction_role_remove", ctx.author, message, pairs_desc, len(removed))

    @reactionrole.command(name="removeall", description="Retirer tous les rôles à réaction d'un message (Remove all)")
    @app_commands.describe(message_id="ID du message")
    async def removeall(self, ctx: commands.Context, message_id: str):
        """Retire toutes les liaisons émoji → rôle d'un message."""
        if ctx.guild is None:
            await send_auto_delete(ctx, TEXTS["rr_err_guild_only"], ephemeral=True)
            return
        mod_cog = self.bot.get_cog('Moderation')
        if not mod_cog or not await mod_cog.check_permission(ctx, "reactionrole"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "reactionrole removeall")

        async with _rr_lock:
            data = load_rr()
            entry = data.pop(str(message_id), None)
            if not entry:
                await send_auto_delete(ctx, TEXTS["rr_err_no_config"], ephemeral=True)
                return
            count = len(entry.get("pairs", {}))
            save_rr(data)

        # Retirer toutes les réactions du bot (best-effort, émojis animés inclus)
        message = await self._find_message(ctx.guild, ctx.channel, int(message_id))
        if message:
            for key in entry.get("pairs", {}):
                for react_fmt in (key, f'<:{key}>', f'<a:{key}>'):
                    try:
                        await message.remove_reaction(react_fmt, self.bot.user)
                        break
                    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                        continue

        await send_auto_delete(ctx, TEXTS["rr_removedall_ok"], ephemeral=True)
        await self._log_config("reaction_role_removeall", ctx.author, message, f'`{count}`', count)


async def setup(bot):
    """Setup du cog ReactionRole."""
    await bot.add_cog(ReactionRole(bot))
