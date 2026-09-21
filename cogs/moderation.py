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
from zoneinfo import ZoneInfo
from typing import Optional, Tuple, List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    PERMISSIONS, SANCTION_COLORS, SANCTION_TYPES,
    MAX_CLEAR_AMOUNT, MIN_CLEAR_AMOUNT, MAX_SANCTIONS_DISPLAY, MAX_SANCTIONS_SELECT,
    WARNINGS_FILE, DATA_DIR, UNICODE_EMOJIS, TEXTS, SANCTIONLIST_COLOR, truncate_text,
    CUSTOM_EMOJIS, SANCTION_CUSTOM_EMOJIS
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

# Verrou protégeant role_restore.json (read-modify-write avec awaits réseau)
_role_restore_lock = asyncio.Lock()

# Plafond Discord pour le timeout (28 jours)
MAX_MUTE_DURATION = timedelta(days=28)


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

        # Log de la suppression dans le channel sanction
        mod_cog = interaction.client.get_cog('Moderation')
        if mod_cog:
            asyncio.create_task(mod_cog._log_sanction_deleted(interaction, uid, sanction=removed))


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

            deleted_count = len(data[uid])  # Compter AVANT de supprimer
            del data[uid]
            try:
                save_warnings_data(data)
            except (IOError, json.JSONDecodeError):
                await interaction.response.send_message(TEXTS["data_save_error"], ephemeral=True)
                return

        self.stop()
        await interaction.response.edit_message(content=f'{UNICODE_EMOJIS["check"]} {TEXTS["all_sanctions_deleted"]}', embed=None, view=None)

        # Log de la suppression totale dans le channel sanction
        mod_cog = interaction.client.get_cog('Moderation')
        if mod_cog:
            asyncio.create_task(mod_cog._log_sanction_deleted(interaction, uid, count=deleted_count))


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
        self._restore_tasks = {}  # user_id -> tâche de restauration (anti-GC + annulation)
        self._restore_initialized = False  # Garde anti-duplication au on_ready

    def cog_unload(self):
        """Annule toutes les tâches de restauration en attente."""
        for task in self._restore_tasks.values():
            task.cancel()
        self._restore_tasks.clear()

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
        is_owner = ctx.author.id == ctx.guild.owner_id

        if not is_owner and not await self.check_permission(ctx, command_name):
            return False, TEXTS["no_role_for_command"].format(command_name=command_name)

        author_member = await self.get_member(ctx.guild, ctx.author.id)
        if not author_member:
            return False, TEXTS["internal_error"]

        target_member = await self.get_member(ctx.guild, target.id)

        if target_member:
            if target.id == ctx.guild.owner_id:
                return False, TEXTS["cannot_sanction_owner"]
            # Check hiérarchie auteur : bypassé pour l'owner du serveur
            if not is_owner and author_member.top_role <= target_member.top_role:
                return False, TEXTS["cannot_sanction_higher"].format(target=target.display_name)
            # Check hiérarchie du BOT : TOUJOURS appliqué (même l'owner ne peut pas
            # dépasser les limites Discord — le rôle du bot doit être assez haut)
            if ctx.guild.me.top_role <= target_member.top_role:
                return False, TEXTS["bot_cannot_sanction"].format(target=target.display_name)

        return True, None

    def send_logs(self, ctx: commands.Context, action_type: str, target: discord.abc.User, moderator: discord.abc.User, reason: str, duration_str: str = None, end_time: datetime = None) -> None:
        """Envoie les logs au cog Logs si disponible."""
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            asyncio.create_task(logs_cog.send_log(ctx, action_type, target, moderator, reason, duration_str, end_time))

    # --- Contournement 2FA (utilisateurs autorisés après checks hiérarchie) ---

    # Fichier de restauration différée des rôles (survit aux redémarrages)
    ROLE_RESTORE_FILE = os.path.join(DATA_DIR, "role_restore.json")

    def _load_role_restore(self) -> dict:
        """Charge les rôles en attente de restauration."""
        try:
            with open(self.ROLE_RESTORE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return {}

    def _save_role_restore(self, data: dict) -> None:
        """Sauvegarde atomique des rôles en attente de restauration."""
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = self.ROLE_RESTORE_FILE + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, self.ROLE_RESTORE_FILE)

    def _get_mod_roles(self, member: discord.Member) -> list:
        """Retourne les rôles du membre qui ont des permissions de modération.

        Ces rôles déclenchent l'exigence 2FA de Discord qui bloque les bots.
        """
        return [
            role for role in member.roles
            if role != member.guild.default_role
            and not role.is_bot_managed()
            and (
                role.permissions.administrator
                or role.permissions.kick_members
                or role.permissions.ban_members
                or role.permissions.moderate_members
            )
        ]

    def _create_restore_task(self, user_id: int, restore_at: datetime):
        """Crée une tâche asyncio qui restaurera les rôles à l'heure donnée.

        La tâche est stockée dans _restore_tasks (anti-GC + annulation propre
        via cog_unload ou unmute). Remplace toute tâche existante pour cet user.
        """
        # Annuler toute tâche précédente pour ce user
        old = self._restore_tasks.pop(user_id, None)
        if old and not old.done():
            old.cancel()

        delay = (restore_at - datetime.now(timezone.utc)).total_seconds() + 2  # +2s marge
        if delay <= 0:
            delay = 0.5

        async def _restore():
            try:
                await asyncio.sleep(delay)
                await self._restore_roles_now(user_id)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"❌ Erreur tâche restauration rôles #{user_id}: {e}")
            finally:
                self._restore_tasks.pop(user_id, None)

        task = asyncio.create_task(_restore())
        self._restore_tasks[user_id] = task
        return task

    async def _schedule_role_restore(self, member: discord.Member, mod_roles: list, mute_end: datetime):
        """Programme la restauration des rôles à la fin du mute.

        Persiste dans un JSON (lock protégé) pour survivre aux redémarrages du bot.
        """
        async with _role_restore_lock:
            data = self._load_role_restore()
            data[str(member.id)] = {
                "guild_id": member.guild.id,
                "role_ids": [r.id for r in mod_roles],
                "restore_at": mute_end.isoformat()
            }
            self._save_role_restore(data)

        self._create_restore_task(member.id, mute_end)

    async def _restore_roles_now(self, user_id: int):
        """Restaure les rôles d'un utilisateur si le mute est terminé.

        Si le timeout est encore actif (re-mute pendant l'attente),
        re-programme automatiquement une nouvelle tâche au nouvel horaire.
        """
        async with _role_restore_lock:
            data = self._load_role_restore()
            uid = str(user_id)
            if uid not in data:
                return

            info = data[uid]
            try:
                restore_at = datetime.fromisoformat(info["restore_at"])
            except (ValueError, KeyError):
                data.pop(uid, None)
                self._save_role_restore(data)
                return

            if datetime.now(timezone.utc) < restore_at:
                return  # Pas encore l'heure (appelé prématurément)

            guild = self.bot.get_guild(info["guild_id"])
            if not guild:
                data.pop(uid, None)
                self._save_role_restore(data)
                return

            # Utiliser get_member + fetch_member (fallback) pour gérer les miss cache
            member = await self.get_member(guild, user_id)
            if not member:
                # Membre parti : re-programmer avec plafond (évite les retries infinis
                # pour les membres bannis/kickés qui ne reviendront jamais)
                misses = info.get("miss_count", 0) + 1
                if misses >= 24:  # ~24h de tentatives, purger
                    data.pop(uid, None)
                    self._save_role_restore(data)
                    print(f"🗑️ Restauration #{uid} purgée (24h sans retrouver le membre)")
                    return
                data[uid]["miss_count"] = misses
                future = datetime.now(timezone.utc) + timedelta(hours=1)
                data[uid]["restore_at"] = future.isoformat()
                self._save_role_restore(data)
                self._create_restore_task(user_id, future)
                return

            # Vérifier que le timeout est bien terminé
            if member.timed_out_until and member.timed_out_until > datetime.now(timezone.utc):
                # Encore mute (re-mute pendant l'attente) : re-programmer au nouveau horaire
                new_restore = member.timed_out_until + timedelta(seconds=2)
                data[uid]["restore_at"] = new_restore.isoformat()
                self._save_role_restore(data)
                self._create_restore_task(user_id, new_restore)
                return

            roles = [guild.get_role(rid) for rid in info["role_ids"]]
            roles = [r for r in roles if r]  # Filtrer les rôles supprimés

            if roles:
                try:
                    await member.add_roles(*roles, reason="Fin de mute — restauration des rôles de modération")
                    print(f"✅ Rôles de modération restaurés pour {member}")
                except (discord.Forbidden, discord.HTTPException) as e:
                    # Échec : garder l'entrée et re-programmer un retry (pas de perte silencieuse)
                    retries = info.get("retry_count", 0) + 1
                    if retries >= 5:
                        print(f"🚨 CRITIQUE : Impossible de restaurer les rôles de {member} après "
                              f"{retries} tentatives : {e} — intervention manuelle requise")
                        data.pop(uid, None)
                        self._save_role_restore(data)
                        return
                    data[uid]["retry_count"] = retries
                    retry_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                    data[uid]["restore_at"] = retry_at.isoformat()
                    self._save_role_restore(data)
                    self._create_restore_task(user_id, retry_at)
                    print(f"⚠️ Échec add_roles pour {member} (tentative {retries}/5), retry dans 5min: {e}")
                    return

            data.pop(uid, None)
            self._save_role_restore(data)

    async def _apply_sanction_with_role_strip(self, ctx: commands.Context, target_member: discord.Member, action: str, **kwargs):
        """Applique une sanction en contournant l'exigence 2FA.

        Accessible à tout utilisateur ayant passé les checks de permission et
        de hiérarchie dans check_sanction_possible.
        Si Discord refuse l'action (Forbidden) parce que la cible a des rôles de
        modération protégés par la 2FA, on retire ces rôles et on applique la sanction.

        Pour un mute : les rôles sont restaurés à la FIN du mute (via JSON persistant).
        Pour un kick/ban : les rôles ne sont pas restaurés (le membre quitte le serveur).

        `action` : 'mute', 'kick', ou 'ban'
        Retourne True si la sanction a été appliquée, False sinon.
        """
        try:
            if action == 'mute':
                await target_member.edit(timed_out_until=kwargs['mute_end'])
            elif action == 'kick':
                await target_member.kick(reason=kwargs.get('reason'))
            elif action == 'ban':
                await ctx.guild.ban(discord.Object(id=target_member.id), reason=kwargs.get('reason'))
            return True
        except discord.Forbidden:
            pass  # Tomber dans le contournement ci-dessous
        except discord.HTTPException:
            return False

        # Contournement 2FA : accessible à tout utilisateur qui a passé les checks
        # de permission et de hiérarchie dans check_sanction_possible.
        # (Un admin + peut sanctionner un autre + si son rôle est plus haut.)

        mod_roles = self._get_mod_roles(target_member)
        if not mod_roles:
            return False  # Pas de rôles à retirer, le problème est ailleurs

        print(f"🔓 Bypass 2FA : {ctx.author} retire temporairement {len(mod_roles)} rôle(s) de modération à {target_member}")
        try:
            # Retirer les rôles de modération
            await target_member.remove_roles(*mod_roles, reason="Bypass 2FA (sanction)")
            await asyncio.sleep(0.5)  # Laisser Discord propager

            # Appliquer la sanction
            if action == 'mute':
                await target_member.edit(timed_out_until=kwargs['mute_end'])
                # Programmer la restauration à la fin du mute (pas immédiate !)
                await self._schedule_role_restore(target_member, mod_roles, kwargs['mute_end'])
            elif action == 'kick':
                await target_member.kick(reason=kwargs.get('reason'))
            elif action == 'ban':
                await ctx.guild.ban(discord.Object(id=target_member.id), reason=kwargs.get('reason'))

            return True

        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Bypass 2FA échoué : {e}")
            # Restaurer les rôles si la sanction a échoué
            try:
                await target_member.add_roles(*mod_roles, reason="Bypass 2FA échoué — restauration")
            except (discord.Forbidden, discord.HTTPException) as restore_err:
                # Double échec : les rôles sont perdus — tracer pour intervention manuelle
                print(f"🚨 CRITIQUE : {target_member} a perdu {len(mod_roles)} rôle(s) de modération "
                      f"(sanction ET restauration en échec) : {restore_err}")
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        """Au démarrage : restaurer les mutes expirés ET re-programmer les mutes en cours."""
        print("📦 Cog 'Moderation' chargé.")

        # Garde : ne s'exécuter qu'au premier on_ready (pas à chaque reconnexion)
        if self._restore_initialized:
            return
        self._restore_initialized = True

        data = self._load_role_restore()
        for uid in list(data.keys()):
            try:
                restore_at = datetime.fromisoformat(data[uid]["restore_at"])
                if restore_at <= datetime.now(timezone.utc):
                    # Mute expiré pendant l'arrêt → restaurer maintenant
                    asyncio.create_task(self._restore_roles_now(int(uid)))
                else:
                    # Mute encore en cours → re-programmer la tâche (sinon perdue au redémarrage)
                    self._create_restore_task(int(uid), restore_at)
            except (ValueError, KeyError):
                data.pop(uid, None)
                self._save_role_restore(data)

    async def _log_sanction_deleted(self, interaction: discord.Interaction, user_id: str, sanction: dict = None, count: int = 0):
        """Log la suppression d'une ou plusieurs sanctions dans le channel sanction."""
        logs_cog = self.bot.get_cog('Logs')
        if not logs_cog:
            return
        channel = logs_cog._get_log_channel("sanction")
        if not channel:
            return

        moderator = interaction.user

        try:
            if sanction:
                # Suppression d'une sanction spécifique
                embed = discord.Embed(color=discord.Color(int("FF0000", 16)))  # Rouge
                embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
                embed.description = f'{CUSTOM_EMOJIS["deleted"]} **{TEXTS["sanction_deleted_log_title"]}**\n{TEXTS["sanction_deleted_log_desc"]}'
                embed.add_field(name=TEXTS["sanction_deleted_target_field"], value=f"<@{user_id}>", inline=True)
                embed.add_field(name="Type", value=f"`{sanction.get('type', '?')}`", inline=True)
                embed.add_field(name=TEXTS["sanctionlist_reason"], value=truncate_text(sanction.get('reason', '?'), 500), inline=False)
                embed.add_field(name=TEXTS["sanction_deleted_by_field"], value=moderator.mention, inline=False)
                embed.set_footer(text=f'#L102 • ID: {moderator.id} • {datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M")}')
                await channel.send(embed=embed)
            else:
                # Suppression de toutes les sanctions
                embed = discord.Embed(color=discord.Color(int("8B0000", 16)))  # Rouge foncé
                embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
                embed.description = f'{CUSTOM_EMOJIS["deleted"]} **{TEXTS["sanction_all_deleted_log_title"]}**\n{TEXTS["sanction_all_deleted_log_desc"].format(count=count)}'
                embed.add_field(name=TEXTS["sanction_deleted_target_field"], value=f"<@{user_id}>", inline=True)
                embed.add_field(name=TEXTS["sanction_deleted_by_field"], value=moderator.mention, inline=False)
                embed.set_footer(text=f'#L103 • ID: {moderator.id} • {datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M")}')
                await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass

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
                # En préfixe (+clear), le message de commande fait partie de la
                # purge : on le compense pour supprimer `amount` vrais messages.
                extra = 0 if ctx.interaction else 1
                deleted = await ctx.channel.purge(limit=amount + extra)
                deleted = len(deleted) - extra

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
        if duration.total_seconds() <= 0 or duration > MAX_MUTE_DURATION:
            await send_auto_delete(ctx,TEXTS["no_duration"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)

        mute_end = datetime.now(timezone.utc) + duration
        success = await self._apply_sanction_with_role_strip(ctx, target_member, 'mute', mute_end=mute_end)
        if not success:
            await send_auto_delete(ctx, TEXTS["missing_permission"], ephemeral=True)
            return

        dur_str = format_duration(hours, minutes, seconds)
        await add_sanction_data_async(user.id, "Mute", reason or TEXTS["none"], ctx.author.name, dur_str)

        self.send_logs(ctx, "Mute", user, ctx.author, reason or TEXTS["none"], dur_str, mute_end)

        embed = discord.Embed(color=SANCTION_COLORS.get("Mute"))
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Mute"]]} **{TEXTS["mute_title"]}**\n\n**{user.name}** {TEXTS["mute_description"].format(dur=dur_str)}'
        if reason:
            embed.add_field(name=TEXTS["mute_reason"], value=truncate_text(reason, 1000))
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

        # Restaurer immédiatement les rôles de modération si le mute avait été
        # fait avec le bypass 2FA (retrait temporaire de rôles)
        async with _role_restore_lock:
            data = self._load_role_restore()
            if str(user.id) in data:
                # Annuler la tâche programmée (elle ne servira plus à rien)
                task = self._restore_tasks.pop(user.id, None)
                if task and not task.done():
                    task.cancel()
                # Forcer la restauration (le délai n'est plus pertinent — unmute manuel)
                data[str(user.id)]["restore_at"] = datetime.now(timezone.utc).isoformat()
                self._save_role_restore(data)

        if str(user.id) in data:
            await self._restore_roles_now(user.id)

        await add_sanction_data_async(user.id, "Unmute", TEXTS["unmute_reason"], ctx.author.name)
        self.send_logs(ctx, "Unmute", user, ctx.author, TEXTS["unmute_reason"])

        embed = discord.Embed(color=SANCTION_COLORS.get("Unmute"))
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Unmute"]]} **{TEXTS["unmute_title"]}**\n\n**{user.name}** {TEXTS["unmute_description"]}'
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

        success = await self._apply_sanction_with_role_strip(ctx, user, 'kick', reason=reason)
        if not success:
            await send_auto_delete(ctx,TEXTS["kick_error"], ephemeral=True)
            return

        # Enregistrer et logger seulement si l'action a réussi
        await add_sanction_data_async(user.id, "Kick", reason or TEXTS["none"], ctx.author.name)
        self.send_logs(ctx, "Kick", user, ctx.author, reason or TEXTS["none"])

        embed = discord.Embed(color=SANCTION_COLORS.get("Kick"))
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Kick"]]} **{TEXTS["kick_title"]}**\n\n**{user.name}** {TEXTS["kick_description"]}'
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

        # La cible peut être hors serveur (ban par ID), on tente avec le membre si présent
        ban_member = await self.get_member(ctx.guild, user.id)
        if ban_member:
            success = await self._apply_sanction_with_role_strip(ctx, ban_member, 'ban', reason=reason)
        else:
            try:
                await ctx.guild.ban(discord.Object(id=user.id), reason=reason)
                success = True
            except (discord.Forbidden, discord.HTTPException):
                success = False

        if not success:
            await send_auto_delete(ctx,TEXTS["ban_error"], ephemeral=True)
            return

        # Enregistrer et logger seulement si l'action a réussi
        await add_sanction_data_async(user.id, "Ban", reason or TEXTS["none"], ctx.author.name)
        self.send_logs(ctx, "Ban", user, ctx.author, reason or TEXTS["none"])

        embed = discord.Embed(color=SANCTION_COLORS.get("Ban"))
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Ban"]]} **{TEXTS["ban_title"]}**\n\n**{user.name}** {TEXTS["ban_description"]}'
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

        embed = discord.Embed(color=SANCTION_COLORS.get("Unban"))
        embed.set_author(name=user_to_unban.display_name, icon_url=user_to_unban.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Unban"]]} **{TEXTS["unban_title"]}**\n\n**{user_to_unban.name}** {TEXTS["unban_description"]}'
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

        embed = discord.Embed(color=SANCTION_COLORS.get("Avertissement"))
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS[SANCTION_CUSTOM_EMOJIS["Avertissement"]]} **{TEXTS["avert_title"]}**\n\n**{user.name}** {TEXTS["avert_description"].format(count=count)}'
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
                emoji_key = SANCTION_CUSTOM_EMOJIS.get(s_type)
                emoji = CUSTOM_EMOJIS[emoji_key] if emoji_key else UNICODE_EMOJIS['package']
                value = f"**{TEXTS['sanctionlist_reason']}** {sanction['reason']}\n**{TEXTS['sanctionlist_by']}** {sanction['moderator']}"
                embed.add_field(name=f"{emoji} {s_type}", value=value, inline=False)
        else:
            embed.description = f"{TEXTS['sanctionlist_empty']} {UNICODE_EMOJIS['party']}"

        view = MainSanctionView(str(user.id))
        await send_auto_delete(ctx,embed=embed, view=view)


async def setup(bot):
    """Setup du cog."""
    await bot.add_cog(Moderation(bot))
