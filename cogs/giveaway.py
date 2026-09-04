# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

import discord
import asyncio
import json
import os
import re
import random
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks
from discord import app_commands

from settings import (
    TEXTS, CUSTOM_EMOJIS,
    GIVEAWAYS_FILE, DATA_DIR, GIVEAWAY_COLOR
)
from cogs.base import send_auto_delete

# --- CONSTANTES LOCALES ---
MAX_PRIZE_LENGTH = 100        # limite du titre (embed title max 256, on borne large)
MAX_WINNERS = 25              # limite raisonnable de gagnants
ENDED_RETENTION_DAYS = 7      # purge des giveaways terminés après 7 jours
NO_MENTIONS = discord.AllowedMentions.none()  # annonces : jamais de ping @everyone via prize/desc

# --- PARSING DU TEMPS ---

_TIME_RE = re.compile(r'^(\d+)\s*(s|sec|secs|seconde|secondes|m|min|mins|minute|minutes|h|heures?|j|jours?|d|days?)$', re.IGNORECASE)
_TIME_UNITS = {
    's': 1, 'sec': 1, 'secs': 1, 'seconde': 1, 'secondes': 1,
    'm': 60, 'min': 60, 'mins': 60, 'minute': 60, 'minutes': 60,
    'h': 3600, 'heure': 3600, 'heures': 3600,
    'j': 86400, 'jour': 86400, 'jours': 86400, 'd': 86400, 'day': 86400, 'days': 86400,
}


def parse_duration(text: str):
    """Parse une durée texte ('30s', '10min', '1h', '2jours') en timedelta, sinon None."""
    match = _TIME_RE.match(text.strip())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2).lower()
    seconds = amount * _TIME_UNITS[unit]
    if seconds <= 0 or seconds > 86400 * 31:  # max 31 jours
        return None
    return timedelta(seconds=seconds)


# --- STOCKAGE ---

_giveaways_lock = asyncio.Lock()


def load_giveaways() -> dict:
    """Charge l'état des giveaways depuis le JSON (retourne un état vide si corrompu)."""
    if os.path.exists(GIVEAWAYS_FILE):
        try:
            with open(GIVEAWAYS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("giveaways"), dict):
                return data
        except (IOError, json.JSONDecodeError):
            pass
    return {"next_id": 1, "giveaways": {}}


def save_giveaways(data: dict) -> None:
    """Sauvegarde atomique : écrit dans un fichier temporaire puis remplace."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp_file = GIVEAWAYS_FILE + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp_file, GIVEAWAYS_FILE)


# --- VUE PERSISTANTE (bouton Participer) ---

class GiveawayView(discord.ui.View):
    """Vue persistante du bouton Participer (custom_id fixe, giveaway identifié via message.id)."""

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label=TEXTS["giveaway_button_join"], style=discord.ButtonStyle.success, custom_id="giveaway:join")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.handle_join(interaction)


# --- MODAL DE CRÉATION ---

class GiveawayModal(discord.ui.Modal, title=TEXTS["giveaway_form_title"]):
    """Formulaire interactif de création d'un giveaway.

    Sécurité : seul l'utilisateur autorisé (créateur de la commande) peut soumettre
    le formulaire — la permission est re-vérifiée à la soumission.
    """

    time_input = discord.ui.TextInput(
        label=TEXTS["giveaway_form_time_label"],
        placeholder="10min",
        min_length=2,
        max_length=20,
        required=True
    )
    winners_input = discord.ui.TextInput(
        label=TEXTS["giveaway_form_winners_label"],
        placeholder="1",
        min_length=1,
        max_length=3,
        required=True
    )
    prize_input = discord.ui.TextInput(
        label=TEXTS["giveaway_form_prize_label"],
        placeholder="Nitro",
        min_length=1,
        max_length=MAX_PRIZE_LENGTH,
        required=True
    )
    desc_input = discord.ui.TextInput(
        label=TEXTS["giveaway_form_desc_label"],
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )

    def __init__(self, cog, authorized_user_id: int):
        super().__init__()
        self.cog = cog
        self.authorized_user_id = authorized_user_id

    async def on_submit(self, interaction: discord.Interaction):
        # Re-vérification de la permission : seul l'auteur de la commande peut soumettre
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return

        duration = parse_duration(str(self.time_input))
        if duration is None:
            await interaction.response.send_message(TEXTS["giveaway_time_invalid"], ephemeral=True)
            return

        try:
            winners_count = int(str(self.winners_input))
            if winners_count < 1 or winners_count > MAX_WINNERS:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(TEXTS["giveaway_winners_invalid"], ephemeral=True)
            return

        prize = str(self.prize_input).strip()[:MAX_PRIZE_LENGTH]
        description = str(self.desc_input).strip()[:1000] if self.desc_input.value else ""

        await interaction.response.defer(ephemeral=True)
        gid = None
        try:
            gid = await self.cog.create_giveaway(interaction, prize, description, winners_count, duration)
        except Exception:
            pass
        if gid:
            await interaction.followup.send(TEXTS["giveaway_created_ok"].format(gid=gid), ephemeral=True)
        else:
            await interaction.followup.send(TEXTS["giveaway_create_error"], ephemeral=True)


# --- BOUTON OUVRIR LE FORMULAIRE (pour le préfixe) ---

class OpenFormView(discord.ui.View):
    """Vue temporaire avec un bouton ouvrant le modal de création (usage préfixe).

    Le modal ne sera soumissible que par l'auteur de la commande.
    """

    def __init__(self, cog, authorized_user_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.authorized_user_id = authorized_user_id

    @discord.ui.button(label=TEXTS["giveaway_open_form_button"], style=discord.ButtonStyle.primary, emoji="📝")
    async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return
        await interaction.response.send_modal(GiveawayModal(self.cog, self.authorized_user_id))
        try:
            await interaction.message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


# --- COG GIVEAWAY ---

class Giveaway(commands.Cog):
    """Système de giveaway : création, participation, tirage, fin, suppression, reroll."""

    def __init__(self, bot):
        self.bot = bot
        self._view_registered = False
        self._end_tasks = {}  # gid -> tâche de fin programmée (précise à la seconde)
        self.check_expired_giveaways.start()

    def cog_unload(self):
        self.check_expired_giveaways.cancel()
        for task in self._end_tasks.values():
            task.cancel()
        self._end_tasks.clear()

    @commands.Cog.listener()
    async def on_ready(self):
        """Enregistre la vue persistante (une seule fois)."""
        if not self._view_registered:
            self.bot.add_view(GiveawayView(self))
            self._view_registered = True
            print("📦 Cog 'Giveaway' chargé.")

    # --- PERMISSIONS (délègue au cog Moderation) ---

    async def check_permission(self, ctx: commands.Context, command_name: str) -> bool:
        mod_cog = self.bot.get_cog('Moderation')
        if mod_cog:
            return await mod_cog.check_permission(ctx, command_name)
        return False

    def log_command_use(self, ctx: commands.Context, command_name: str) -> None:
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use(command_name, ctx.author, prefix))

    # --- TÂCHES DE FIN PROGRAMMÉES ---

    def _schedule_end(self, gid: str, end_time: datetime):
        """Programme la fin exacte d'un giveaway (à la seconde près).

        La boucle check_expired_giveaways reste en filet de sécurité (redémarrages).
        """
        old = self._end_tasks.pop(gid, None)
        if old:
            old.cancel()

        async def _delayed_end():
            try:
                delay = (end_time - datetime.now(timezone.utc)).total_seconds()
                if delay > 0:
                    await asyncio.sleep(delay + 0.3)  # +0.3s de marge (quasi instantané)
                # IMPORTANT : se retirer du dict AVANT end_giveaway, sinon
                # end_giveaway annulerait cette tâche elle-même (CancelledError).
                self._end_tasks.pop(gid, None)
                data = load_giveaways()
                g = data["giveaways"].get(str(gid))
                if g and g.get("status") == "active":
                    await self.end_giveaway(gid)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"❌ Erreur fin giveaway #{gid}: {e}")
                self._end_tasks.pop(gid, None)

        self._end_tasks[gid] = asyncio.create_task(_delayed_end())

    def _cancel_scheduled_end(self, gid: str):
        task = self._end_tasks.pop(str(gid), None)
        if task:
            task.cancel()

    # --- HELPERS DONNÉES ---

    def _get_giveaway_by_message(self, message_id: int):
        """Retourne (gid, data) du giveaway actif correspondant à un message."""
        data = load_giveaways()
        for gid, g in data["giveaways"].items():
            if g.get("message_id") == message_id and g.get("status") == "active":
                return gid, g
        return None, None

    def _get_giveaway(self, gid_str: str):
        """Retourne (gid, data) d'un giveaway par son ID."""
        data = load_giveaways()
        g = data["giveaways"].get(str(gid_str))
        return (str(gid_str), g) if g else (None, None)

    @staticmethod
    def _mentions_from_ids(user_ids):
        return [f"<@{uid}>" for uid in user_ids]

    # --- CONSTRUCTION EMBED ---

    def _build_giveaway_message_embed(self, g, status="active", winners_mentions=None, deleted_by=None):
        """Construit l'embed du message de giveaway (public, avec bouton)."""
        if status == "ended":
            title = TEXTS["giveaway_msg_ended_title"].format(prize=g["prize"])
            color = discord.Color(int("FF0000", 16))  # Rouge
        elif status == "deleted":
            title = TEXTS["giveaway_msg_deleted_title"].format(prize=g["prize"])
            color = discord.Color(int("FF0000", 16))  # Rouge
        else:
            title = TEXTS["giveaway_msg_title"].format(prize=g["prize"])
            color = GIVEAWAY_COLOR

        embed = discord.Embed(title=title[:256], color=color)

        desc_lines = []
        if g.get("description"):
            desc_lines.append(g["description"][:1000])
        desc_lines.append("")
        end_dt = datetime.fromisoformat(g["end_time"])
        ts = int(end_dt.timestamp())
        if status == "active":
            desc_lines.append(f'{CUSTOM_EMOJIS["giveaway"]} **{TEXTS["giveaway_ends_field"]} :** <t:{ts}:R> - <t:{ts}:F>')
        desc_lines.append(f'{CUSTOM_EMOJIS["winner"]} **{TEXTS["giveaway_winners"]} :** `{g["winners_count"]}`')
        desc_lines.append(f'{CUSTOM_EMOJIS["participant"]} **{TEXTS["giveaway_participants"]} :** `{len(g.get("participants", []))}`')
        desc_lines.append(f'{TEXTS["giveaway_created_by"]} : <@{g["creator_id"]}>')
        if status == "ended":
            winners = " ".join(winners_mentions) if winners_mentions else f'`{TEXTS["giveaway_no_participants"]}`'
            desc_lines.append(f'**{TEXTS["giveaway_winners"]} :** {winners}')
        if status == "deleted" and deleted_by:
            desc_lines.append(f'\n🗑️ Supprimé par {deleted_by}')
        embed.description = "\n".join(desc_lines)[:4096]
        return embed

    # --- LOGIQUE MÉTIER ---

    async def create_giveaway(self, source, prize: str, description: str, winners_count: int, duration: timedelta):
        """Crée un giveaway actif : message public + log #L097 + sauvegarde JSON.

        `source` : interaction (modal) ou Context (startg).
        Retourne l'ID du giveaway créé, ou None en cas d'échec.
        Les appels réseau sont faits HORS lock ; le lock ne protège que le JSON.
        """
        creator = source.user if isinstance(source, discord.Interaction) else source.author
        channel = source.channel
        if not getattr(channel, "guild", None):
            return None  # Commande en DM : refus

        end_time = datetime.now(timezone.utc) + duration
        prize = prize[:MAX_PRIZE_LENGTH]
        description = (description or "")[:1000]

        # 1. Message public avec bouton (hors lock)
        g_preview = {
            "prize": prize, "description": description,
            "winners_count": winners_count, "end_time": end_time.isoformat(),
            "creator_id": creator.id, "participants": []
        }
        try:
            msg = await channel.send(embed=self._build_giveaway_message_embed(g_preview), view=GiveawayView(self))
        except (discord.Forbidden, discord.HTTPException):
            return None

        # 2. Log giveaway #L097 (hors lock ; échec non bloquant)
        log_message_id = None
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            try:
                log_msg = await logs_cog.send_giveaway_log("?", prize, description, end_time, creator)
                if log_msg:
                    log_message_id = log_msg.id
            except Exception:
                log_message_id = None

        # 3. Attribuer l'ID et sauvegarder (lock : uniquement le JSON)
        async with _giveaways_lock:
            data = load_giveaways()
            gid = str(data["next_id"])
            data["next_id"] += 1
            data["giveaways"][gid] = {
                "prize": prize,
                "description": description,
                "winners_count": winners_count,
                "end_time": end_time.isoformat(),
                "creator_id": creator.id,
                "guild_id": channel.guild.id,
                "channel_id": channel.id,
                "message_id": msg.id,
                "log_message_id": log_message_id,
                "participants": [],
                "status": "active",
                "winners": []
            }
            save_giveaways(data)

        self._schedule_end(gid, end_time)
        return gid

    async def _update_giveaway_display(self, g, status="active", winners_mentions=None, deleted_by=None):
        """Met à jour le message public ET le log #L097 d'un giveaway. Silencieux en cas d'échec."""
        guild = self.bot.get_guild(g["guild_id"])
        if not guild:
            return

        # Message public
        channel = guild.get_channel(g["channel_id"])
        if channel and g.get("message_id"):
            try:
                msg = channel.get_partial_message(g["message_id"])
                view = GiveawayView(self) if status == "active" else None
                embed = self._build_giveaway_message_embed(g, status, winners_mentions, deleted_by)
                await msg.edit(embed=embed, view=view)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        # Log #L097
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog and g.get("log_message_id"):
            log_channel = logs_cog._get_log_channel("giveaway")
            if log_channel:
                try:
                    log_msg = await log_channel.fetch_message(g["log_message_id"])
                    creator = self.bot.get_user(g["creator_id"]) or guild.get_member(g["creator_id"])
                    if creator:
                        winners_objs = [guild.get_member(uid) for uid in g.get("winners", [])]
                        winners_objs = [w for w in winners_objs if w]
                        await logs_cog.update_giveaway_log(
                            log_msg, g.get("gid", "?"), g["prize"], g.get("description", ""),
                            datetime.fromisoformat(g["end_time"]), creator,
                            len(g.get("participants", [])), winners_objs
                        )
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

    async def end_giveaway(self, gid: str):
        """Termine un giveaway : tirage, éditions message + log, annonce. Retourne g ou None."""
        self._cancel_scheduled_end(gid)
        async with _giveaways_lock:
            data = load_giveaways()
            g = data["giveaways"].get(str(gid))
            if not g or g["status"] != "active":
                return None
            g["status"] = "ended"
            participants = g.get("participants", [])
            n = min(g["winners_count"], len(participants))
            g["winners"] = random.sample(participants, n) if n > 0 else []
            save_giveaways(data)
            g["gid"] = str(gid)

        winners_mentions = self._mentions_from_ids(g["winners"])
        await self._update_giveaway_display(g, status="ended", winners_mentions=winners_mentions)

        # Annonce des gagnants dans le channel (mentions autorisées uniquement pour les gagnants)
        guild = self.bot.get_guild(g["guild_id"])
        channel = guild.get_channel(g["channel_id"]) if guild else None
        if channel:
            try:
                if winners_mentions:
                    template = TEXTS["giveaway_winners_announce"] if len(winners_mentions) == 1 else TEXTS["giveaway_winners_announce_many"]
                    await channel.send(
                        template.format(prize=g["prize"], winners=" ".join(winners_mentions)),
                        allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
                    )
                else:
                    await channel.send(TEXTS["giveaway_stopped_announce"], allowed_mentions=NO_MENTIONS)
            except (discord.Forbidden, discord.HTTPException):
                pass
        return g

    async def delete_giveaway(self, gid: str, deleted_by_mention: str):
        """Annule un giveaway : éditions + suppression du JSON. Retourne g ou None."""
        self._cancel_scheduled_end(gid)
        async with _giveaways_lock:
            data = load_giveaways()
            g = data["giveaways"].pop(str(gid), None)
            if not g:
                return None
            save_giveaways(data)
            g["gid"] = str(gid)

        await self._update_giveaway_display(g, status="deleted", deleted_by=deleted_by_mention)

        guild = self.bot.get_guild(g["guild_id"])
        channel = guild.get_channel(g["channel_id"]) if guild else None
        if channel:
            try:
                await channel.send(TEXTS["giveaway_deleted_announce"].format(prize=g["prize"]), allowed_mentions=NO_MENTIONS)
            except (discord.Forbidden, discord.HTTPException):
                pass
        return g

    async def reroll_giveaway(self, gid: str, rerolled_by_mention: str):
        """Re-tire les gagnants d'un giveaway terminé. Retourne g ou None."""
        async with _giveaways_lock:
            data = load_giveaways()
            g = data["giveaways"].get(str(gid))
            if not g or g["status"] != "ended":
                return None
            participants = g.get("participants", [])
            n = min(g["winners_count"], len(participants))
            g["winners"] = random.sample(participants, n) if n > 0 else []
            save_giveaways(data)
            g["gid"] = str(gid)

        winners_mentions = self._mentions_from_ids(g["winners"])
        await self._update_giveaway_display(g, status="ended", winners_mentions=winners_mentions)

        guild = self.bot.get_guild(g["guild_id"])
        channel = guild.get_channel(g["channel_id"]) if guild else None
        if channel:
            try:
                if winners_mentions:
                    await channel.send(
                        TEXTS["giveaway_reroll_announce"].format(admin=rerolled_by_mention, winners=" ".join(winners_mentions)),
                        allowed_mentions=discord.AllowedMentions(users=True, everyone=False, roles=False)
                    )
                else:
                    await channel.send(TEXTS["giveaway_stopped_announce"], allowed_mentions=NO_MENTIONS)
            except (discord.Forbidden, discord.HTTPException):
                pass
        return g

    # --- PARTICIPATION (bouton) ---

    async def handle_join(self, interaction: discord.Interaction):
        """Toggle la participation de l'utilisateur au giveaway du message cliqué."""
        gid, _ = self._get_giveaway_by_message(interaction.message.id)
        if not gid:
            await interaction.response.send_message(TEXTS["giveaway_not_found"].format(gid="?"), ephemeral=True)
            return

        async with _giveaways_lock:
            data = load_giveaways()
            g = data["giveaways"].get(gid)
            if not g or g["status"] != "active":
                await interaction.response.send_message(TEXTS["giveaway_already_ended"], ephemeral=True)
                return

            participants = g.setdefault("participants", [])
            if interaction.user.id in participants:
                participants.remove(interaction.user.id)
                joined = False
            else:
                participants.append(interaction.user.id)
                joined = True
            save_giveaways(data)

        # Répondre AVANT l'édition (l'édition peut prendre du temps — évite "Unknown interaction")
        if joined:
            reply = TEXTS["giveaway_join_ok"].format(prize=g["prize"])
        else:
            reply = TEXTS["giveaway_leave_ok"].format(prize=g["prize"])
        await interaction.response.send_message(reply, ephemeral=True)

        # Mise à jour des affichages (non bloquante pour l'utilisateur)
        await self._update_giveaway_display(g)

    # --- TÂCHE DE FOND : FIN AUTOMATIQUE + PURGE ---

    @tasks.loop(minutes=1)
    async def check_expired_giveaways(self):
        """Filet de sécurité : termine les expirés (redémarrage), re programme les tâches perdues,
        purge les giveaways terminés de plus de 7 jours."""
        try:
            data = load_giveaways()
            now = datetime.now(timezone.utc)
            changed = False
            for gid, g in list(data["giveaways"].items()):
                try:
                    end_dt = datetime.fromisoformat(g["end_time"])
                except (KeyError, ValueError):
                    continue
                if g.get("status") == "active":
                    if end_dt <= now:
                        # Expiré (ex: pendant un redémarrage) → terminer maintenant
                        try:
                            await self.end_giveaway(gid)
                        except Exception as e:
                            print(f"❌ Erreur fin auto giveaway #{gid}: {e}")
                    elif gid not in self._end_tasks:
                        # Tâche de fin perdue (ex: redémarrage) → re programmer
                        self._schedule_end(gid, end_dt)
                elif g.get("status") == "ended" and end_dt < now - timedelta(days=ENDED_RETENTION_DAYS):
                    # Purge : giveaway terminé de plus de 7 jours
                    data["giveaways"].pop(gid, None)
                    changed = True
            if changed:
                async with _giveaways_lock:
                    current = load_giveaways()
                    now_cutoff = now - timedelta(days=ENDED_RETENTION_DAYS)
                    for gid in list(current["giveaways"].keys()):
                        g = current["giveaways"][gid]
                        if g.get("status") == "ended":
                            try:
                                if datetime.fromisoformat(g["end_time"]) < now_cutoff:
                                    current["giveaways"].pop(gid, None)
                            except (KeyError, ValueError):
                                current["giveaways"].pop(gid, None)
                    save_giveaways(current)
        except Exception as e:
            print(f"❌ Erreur loop giveaway: {e}")

    @check_expired_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # --- COMMANDES ---

    @commands.hybrid_command(name="createg", description="Créer un giveaway via formulaire (Create a giveaway)")
    async def createg_slash(self, ctx: commands.Context):
        """Ouvre le formulaire interactif de création de giveaway."""
        if not await self.check_permission(ctx, "createg"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "createg")

        if ctx.interaction is not None:
            # Slash : ouvrir le modal directement
            await ctx.interaction.response.send_modal(GiveawayModal(self, ctx.author.id))
        else:
            # Préfixe : envoyer un bouton qui ouvrira le modal (réservé à l'auteur)
            await ctx.send(
                f'{CUSTOM_EMOJIS["giveaway"]} Clique sur le bouton pour ouvrir le formulaire de création :',
                view=OpenFormView(self, ctx.author.id)
            )

    @commands.hybrid_command(name="startg", description="Créer un giveaway directement (Start a giveaway)")
    @app_commands.describe(
        time="Temps (ex: 30s, 10min, 1h, 2jours)",
        winner="Nombre de gagnants (1-25)",
        prize="Récompense",
        desc="Description (Optionnel/Optional)"
    )
    async def startg_slash(self, ctx: commands.Context, time: str, winner: int, prize: str, desc: str = ""):
        """Crée et démarre un giveaway avec les paramètres donnés."""
        if not await self.check_permission(ctx, "startg"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "startg")

        duration = parse_duration(time)
        if duration is None:
            await send_auto_delete(ctx, TEXTS["giveaway_time_invalid"], ephemeral=True)
            return

        if winner < 1 or winner > MAX_WINNERS:
            await send_auto_delete(ctx, TEXTS["giveaway_winners_invalid"], ephemeral=True)
            return

        if len(desc) > 1000:
            await send_auto_delete(ctx, TEXTS["giveaway_desc_too_long"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        gid = None
        try:
            gid = await self.create_giveaway(ctx, prize.strip(), desc.strip(), winner, duration)
        except Exception:
            gid = None
        if gid:
            await send_auto_delete(ctx, TEXTS["giveaway_created_ok"].format(gid=gid), ephemeral=True)
        else:
            await send_auto_delete(ctx, TEXTS["giveaway_create_error"], ephemeral=True)

    @commands.hybrid_command(name="endg", description="Terminer un giveaway (End a giveaway)")
    @app_commands.describe(giveaway_id="ID du giveaway")
    async def endg_slash(self, ctx: commands.Context, giveaway_id: str):
        """Termine immédiatement un giveaway et tire les gagnants."""
        if not await self.check_permission(ctx, "endg"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "endg")

        gid, g = self._get_giveaway(giveaway_id)
        if not g:
            await send_auto_delete(ctx, TEXTS["giveaway_not_found"].format(gid=giveaway_id), ephemeral=True)
            return
        if g["status"] != "active":
            await send_auto_delete(ctx, TEXTS["giveaway_already_ended"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        result = await self.end_giveaway(gid)
        if result:
            await send_auto_delete(ctx, TEXTS["giveaway_ended_ok"].format(gid=gid), ephemeral=True)
        else:
            await send_auto_delete(ctx, TEXTS["giveaway_already_ended"], ephemeral=True)

    @commands.hybrid_command(name="deletedg", description="Supprimer un giveaway (Delete a giveaway)")
    @app_commands.describe(giveaway_id="ID du giveaway")
    async def deletedg_slash(self, ctx: commands.Context, giveaway_id: str):
        """Annule et supprime un giveaway."""
        if not await self.check_permission(ctx, "deletedg"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "deletedg")

        gid, g = self._get_giveaway(giveaway_id)
        if not g:
            await send_auto_delete(ctx, TEXTS["giveaway_not_found"].format(gid=giveaway_id), ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        result = await self.delete_giveaway(gid, ctx.author.mention)
        if result:
            await send_auto_delete(ctx, TEXTS["giveaway_deleted_ok"].format(gid=gid), ephemeral=True)
        else:
            await send_auto_delete(ctx, TEXTS["giveaway_not_found"].format(gid=giveaway_id), ephemeral=True)

    @commands.hybrid_command(name="rerollg", description="Retirer les gagnants (Reroll a giveaway)")
    @app_commands.describe(giveaway_id="ID du giveaway")
    async def rerollg_slash(self, ctx: commands.Context, giveaway_id: str):
        """Effectue un nouveau tirage parmi les participants d'un giveaway terminé."""
        if not await self.check_permission(ctx, "rerollg"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "rerollg")

        gid, g = self._get_giveaway(giveaway_id)
        if not g:
            await send_auto_delete(ctx, TEXTS["giveaway_not_found"].format(gid=giveaway_id), ephemeral=True)
            return
        if g["status"] == "active":
            await send_auto_delete(ctx, TEXTS["giveaway_not_ended"], ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        result = await self.reroll_giveaway(gid, ctx.author.mention)
        if result:
            await send_auto_delete(ctx, TEXTS["giveaway_rerolled_ok"].format(gid=gid), ephemeral=True)
        else:
            await send_auto_delete(ctx, TEXTS["giveaway_not_found"].format(gid=gid), ephemeral=True)


async def setup(bot):
    """Setup du cog Giveaway."""
    await bot.add_cog(Giveaway(bot))
