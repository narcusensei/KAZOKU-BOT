import discord
import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from discord.ext import commands, tasks

from settings import (
    TEXTS, CUSTOM_EMOJIS,
    REMINDERS_FILE, DATA_DIR,
    DISBOARD_BOT_ID, BUMP_REMINDER_ENABLED, BUMP_REMINDER_DELAY_SECONDS,
    BUMP_REMINDER_ROLE_ID, BUMP_SUCCESS_PHRASES, BUMP_REMINDERS_FILE
)
from cogs.base import send_auto_delete
from cogs.giveaway import parse_duration
from cogs.logs import _log_id_for, get_timestamp

# --- CONSTANTES ---
MIN_INTERVAL = timedelta(minutes=5)   # intervalle minimum entre 2 rappels
MAX_INTERVAL = timedelta(days=31)     # maximum accepté par parse_duration (giveaway.py)

# --- STOCKAGE ---

_reminders_lock = asyncio.Lock()


def load_reminders() -> dict:
    """Charge les rappels depuis le JSON (état vide si corrompu)."""
    if os.path.exists(REMINDERS_FILE):
        try:
            with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("reminders"), dict):
                return data
        except (IOError, json.JSONDecodeError):
            pass
    return {"next_id": 1, "reminders": {}}


def save_reminders(data: dict) -> None:
    """Sauvegarde atomique des rappels."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = REMINDERS_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, REMINDERS_FILE)


# --- STOCKAGE RAPPELS BUMP DISBOARD (one-shot) ---

_bump_lock = asyncio.Lock()


def load_bump_reminders() -> dict:
    """Charge les rappels de bump : {guild_id: trigger_iso} (état vide si corrompu)."""
    if os.path.exists(BUMP_REMINDERS_FILE):
        try:
            with open(BUMP_REMINDERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (IOError, json.JSONDecodeError):
            pass
    return {}


def save_bump_reminders(data: dict) -> None:
    """Sauvegarde atomique des rappels de bump."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = BUMP_REMINDERS_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, BUMP_REMINDERS_FILE)


def format_interval(td: timedelta) -> str:
    """Formate un intervalle en texte lisible."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 3600:
        return f"{total_seconds // 60}min"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h" + (f" {minutes}min" if minutes else "")
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    return f"{days}j" + (f" {hours}h" if hours else "")


# --- MODAL DE CRÉATION ---

class ReminderModal(discord.ui.Modal, title=TEXTS["reminder_form_title"]):
    """Formulaire interactif de création d'un rappel."""

    interval_input = discord.ui.TextInput(
        label=TEXTS["reminder_form_interval_label"],
        placeholder="1h, 30min, 2jours",
        min_length=2,
        max_length=20,
        required=True
    )
    role_input = discord.ui.TextInput(
        label=TEXTS["reminder_form_role_label"],
        placeholder="123456789",
        min_length=1,
        max_length=25,
        required=True
    )
    name_input = discord.ui.TextInput(
        label=TEXTS["reminder_form_name_label"],
        placeholder="Réunion hebdo",
        min_length=1,
        max_length=100,
        required=True
    )
    desc_input = discord.ui.TextInput(
        label=TEXTS["reminder_form_desc_label"],
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )

    def __init__(self, cog, authorized_user_id: int):
        super().__init__()
        self.cog = cog
        self.authorized_user_id = authorized_user_id

    async def on_submit(self, interaction: discord.Interaction):
        # Re-vérification de la permission
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return

        # Validation de l'intervalle
        duration = parse_duration(str(self.interval_input))
        if duration is None or duration < MIN_INTERVAL or duration > MAX_INTERVAL:
            await interaction.response.send_message(
                TEXTS["reminder_interval_invalid"], ephemeral=True
            )
            return

        # Validation du rôle (ID ou mention <@&ID>)
        role_text = str(self.role_input).strip()
        role_match = re.search(r'(\d{15,25})', role_text)
        if not role_match:
            await interaction.response.send_message(TEXTS["reminder_role_invalid"], ephemeral=True)
            return
        role_id = int(role_match.group(1))
        guild = interaction.guild
        role = guild.get_role(role_id) if guild else None
        if not role:
            await interaction.response.send_message(TEXTS["reminder_role_invalid"], ephemeral=True)
            return

        name = str(self.name_input).strip()[:100].upper()
        description = str(self.desc_input).strip()[:1000] if self.desc_input.value else ""

        await interaction.response.defer(ephemeral=True)
        rid = None
        try:
            rid = await self.cog.create_reminder(
                interaction, name, description, role_id, duration
            )
        except Exception:
            rid = None

        if rid:
            await interaction.followup.send(TEXTS["reminder_created_ok"], ephemeral=True)
        else:
            await interaction.followup.send(TEXTS["reminder_create_error"], ephemeral=True)


# --- BOUTON OUVRIR LE FORMULAIRE (préfixe) ---

class ReminderOpenFormView(discord.ui.View):
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
            ReminderModal(self.cog, self.authorized_user_id)
        )
        try:
            await interaction.message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass


# --- VUE LISTE INTERACTIVE ---

class ReminderListView(discord.ui.View):
    """Vue interactive : sélecteur + boutons pour supprimer un ou tous les rappels."""

    def __init__(self, cog, user_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.select(
        placeholder=TEXTS["reminder_list_placeholder"],
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_reminder(self, interaction: discord.Interaction, select: discord.ui.Select):
        # La sélection ne fait rien d'elle-même, juste informative
        await interaction.response.defer()

    @discord.ui.button(label=TEXTS["reminder_delete_button"], style=discord.ButtonStyle.danger)
    async def delete_one(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return

        select = self.children[0]
        if not select.values:
            await interaction.response.send_message(
                "❌ Sélectionne d'abord un rappel dans la liste.", ephemeral=True
            )
            return

        rid = select.values[0]
        deleted = await self.cog.delete_reminder(rid, interaction.user)
        if deleted:
            # Rafraîchir la liste
            await interaction.response.edit_message(
                embed=self.cog._build_reminder_list_embed(interaction.user),
                view=self.cog._build_reminder_list_view(interaction.user)
            )
        else:
            await interaction.response.send_message(
                "❌ Rappel introuvable ou déjà supprimé.", ephemeral=True
            )

    @discord.ui.button(label=TEXTS["reminder_delete_all_button"], style=discord.ButtonStyle.danger)
    async def delete_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(TEXTS["permission_denied"], ephemeral=True)
            return

        await interaction.response.defer()
        await self.cog.delete_all_reminders(interaction.user)
        await interaction.followup.send(TEXTS["reminder_all_deleted_ok"])


# --- COG RAPPEL ---

class Reminder(commands.Cog):
    """Système de rappels automatiques avec rôle ciblé."""

    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()
        if BUMP_REMINDER_ENABLED:
            self.check_bump_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()
        if BUMP_REMINDER_ENABLED:
            self.check_bump_reminders.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("📦 Cog 'Reminder' chargé.")

    # --- PERMISSIONS ---

    async def check_permission(self, ctx: commands.Context, command_name: str) -> bool:
        mod_cog = self.bot.get_cog('Moderation')
        if mod_cog:
            return await mod_cog.check_permission(ctx, command_name)
        return False

    # --- HELPERS ---

    def _build_reminder_list_embed(self, user) -> discord.Embed:
        """Construit l'embed de la liste des rappels."""
        data = load_reminders()
        embed = discord.Embed(color=discord.Color(int("FFD700", 16)))  # Jaune
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.title = f'{CUSTOM_EMOJIS["info"]} **{TEXTS["reminder_list_title"]}**'

        if data["reminders"]:
            lines = []
            for rid, r in data["reminders"].items():
                interval = format_interval(timedelta(seconds=r["interval_seconds"]))
                lines.append(f'`#{rid}` **{r["name"]}** → <@&{r["role_id"]}> toutes les `{interval}`')
            embed.description = "\n".join(lines)[:4000]
        else:
            embed.description = TEXTS["reminder_list_empty"]

        embed.set_footer(text=f'{_log_id_for("reminder_list")} • {get_timestamp()}')
        return embed

    def _build_reminder_list_view(self, user) -> ReminderListView:
        """Construit la vue de la liste avec options à jour."""
        view = ReminderListView(self, user.id)
        data = load_reminders()
        options = []
        for rid, r in data["reminders"].items():
            interval = format_interval(timedelta(seconds=r["interval_seconds"]))
            options.append(discord.SelectOption(
                label=f"#{rid} — {r['name'][:80]}",
                value=str(rid),
                description=f"Toutes les {interval} → <@&{r['role_id']}>"
            ))
        view.select_reminder.options = options[:25]
        return view

    # --- LOGIQUE MÉTIER ---

    async def create_reminder(self, source, name: str, description: str, role_id: int, interval: timedelta) -> str:
        """Crée un rappel : log #L098 + sauvegarde. Retourne l'ID ou None."""
        creator = source.user if isinstance(source, discord.Interaction) else source.author
        channel = source.channel
        if not getattr(channel, "guild", None):
            return None

        interval_seconds = int(interval.total_seconds())
        next_trigger = datetime.now(timezone.utc) + interval

        # Log de création #L098
        logs_cog = self.bot.get_cog('Logs')
        log_channel = logs_cog._get_log_channel("action") if logs_cog else None
        if log_channel:
            try:
                embed = discord.Embed(color=discord.Color(int("00FF00", 16)))  # Vert
                embed.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
                embed.description = (
                    f'{CUSTOM_EMOJIS["allow"]} **{TEXTS["reminder_created_title"]}**\n'
                    f'{TEXTS["reminder_created_desc"]}'
                )
                embed.add_field(name=TEXTS["reminder_role_field"], value=f"<@&{role_id}>", inline=True)
                embed.add_field(
                    name=TEXTS["reminder_trigger_field"],
                    value=f"`{format_interval(interval)}`",
                    inline=True
                )
                embed.add_field(
                    name=TEXTS["reminder_reason_field"],
                    value=description or TEXTS["reminder_auto_default"],
                    inline=False
                )
                embed.add_field(name=TEXTS["member_by"], value=creator.mention, inline=False)
                embed.set_footer(
                    text=f'{_log_id_for("reminder_create")} • ID: {creator.id} • {get_timestamp()}'
                )
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

        # Sauvegarde
        async with _reminders_lock:
            data = load_reminders()
            rid = str(data["next_id"])
            data["next_id"] += 1
            data["reminders"][rid] = {
                "name": name,
                "description": description,
                "role_id": role_id,
                "interval_seconds": interval_seconds,
                "channel_id": channel.id,
                "guild_id": channel.guild.id,
                "creator_id": creator.id,
                "next_trigger": next_trigger.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            save_reminders(data)

        return rid

    async def delete_reminder(self, rid: str, deleted_by) -> bool:
        """Supprime un rappel + log #L099. Retourne True si supprimé."""
        async with _reminders_lock:
            data = load_reminders()
            r = data["reminders"].pop(str(rid), None)
            if not r:
                return False
            save_reminders(data)

        # Log de suppression #L099
        logs_cog = self.bot.get_cog('Logs')
        log_channel = logs_cog._get_log_channel("action") if logs_cog else None
        if log_channel:
            try:
                embed = discord.Embed(color=discord.Color(int("FF0000", 16)))  # Rouge
                embed.set_author(name=deleted_by.display_name, icon_url=deleted_by.display_avatar.url)
                embed.description = (
                    f'{CUSTOM_EMOJIS["deny"]} **{TEXTS["reminder_deleted_title"]}**\n'
                    f'{TEXTS["reminder_deleted_desc"]}'
                )
                embed.add_field(name="Rappel", value=f"**{r['name']}**", inline=False)
                embed.add_field(name=TEXTS["member_by"], value=deleted_by.mention, inline=False)
                embed.set_footer(
                    text=f'{_log_id_for("reminder_delete")} • ID: {deleted_by.id} • {get_timestamp()}'
                )
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

        return True

    async def delete_all_reminders(self, deleted_by) -> int:
        """Supprime tous les rappels en une seule opération + un seul log récapitulatif."""
        async with _reminders_lock:
            data = load_reminders()
            count = len(data["reminders"])
            data["reminders"] = {}
            save_reminders(data)

        if count == 0:
            return 0

        # Un seul log récapitulatif #L099 (pas N logs individuels)
        logs_cog = self.bot.get_cog('Logs')
        log_channel = logs_cog._get_log_channel("action") if logs_cog else None
        if log_channel:
            try:
                embed = discord.Embed(color=discord.Color(int("FF0000", 16)))  # Rouge
                embed.set_author(name=deleted_by.display_name, icon_url=deleted_by.display_avatar.url)
                embed.description = (
                    f'{CUSTOM_EMOJIS["deny"]} **{TEXTS["reminder_deleted_title"]}**\n'
                    f'{count} rappel(s) supprimé(s)'
                )
                embed.add_field(name=TEXTS["member_by"], value=deleted_by.mention, inline=False)
                embed.set_footer(
                    text=f'{_log_id_for("reminder_delete")} • ID: {deleted_by.id} • {get_timestamp()}'
                )
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

        return count

    async def send_reminder(self, rid: str, r: dict) -> bool:
        """Envoie le message de rappel automatique dans le channel configuré.

        Retourne True si envoyé avec succès, False sinon (guild/channel introuvables, erreur).
        """
        guild = self.bot.get_guild(r["guild_id"])
        if not guild:
            return False
        channel = guild.get_channel(r["channel_id"])
        if not channel:
            return False

        description = r.get("description") or TEXTS["reminder_auto_default"]
        content = f'<@&{r["role_id"]}>'
        embed = discord.Embed(color=discord.Color(int("B821FF", 16)))  # Violet
        embed.description = (
            f'{CUSTOM_EMOJIS["info"]} **RAPPEL {r["name"]}**\n'
            f'{description}'
        )
        embed.set_footer(text=f'{_log_id_for("reminder_auto")} • {get_timestamp()}')

        try:
            await channel.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True, everyone=False)
            )
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    # --- BOUCLE D'ENVOI ---

    @tasks.loop(seconds=10)
    async def check_reminders(self):
        """Vérifie toutes les 10 secondes si un rappel doit être envoyé."""
        try:
            data = load_reminders()
            now = datetime.now(timezone.utc)
            for rid, r in list(data["reminders"].items()):
                try:
                    trigger = datetime.fromisoformat(r["next_trigger"])
                    interval = timedelta(seconds=r["interval_seconds"])
                except (KeyError, ValueError, TypeError):
                    # Donnée corrompue : purger ce rappel pour ne pas spammer la console
                    async with _reminders_lock:
                        current = load_reminders()
                        current["reminders"].pop(rid, None)
                        save_reminders(current)
                    continue

                if trigger > now:
                    continue

                # Rattrapage post-arrêt : avancer le next_trigger jusqu'à dépasser now
                # (évite l'envoi en rafale de tous les rappels manqués)
                next_trigger = trigger
                while next_trigger <= now:
                    next_trigger += interval

                # Reprogrammer AVANT l'envoi (si l'envoi échoue, le rappel
                # n'est pas renvoyé toutes les 10s à l'infini)
                async with _reminders_lock:
                    current = load_reminders()
                    if rid in current["reminders"]:
                        current["reminders"][rid]["next_trigger"] = next_trigger.isoformat()
                        save_reminders(current)

                # Envoyer le rappel (une seule fois, même si plusieurs cycles manqués)
                sent_ok = await self.send_reminder(rid, r)

                # Auto-purge : trop d'échecs consécutifs (channel/guilde supprimés)
                if not sent_ok:
                    async with _reminders_lock:
                        current = load_reminders()
                        if rid in current["reminders"]:
                            fails = current["reminders"][rid].get("send_fails", 0) + 1
                            if fails >= 5:
                                current["reminders"].pop(rid, None)
                                print(f"🗑️ Rappel #{rid} purgé (5 échecs d'envoi consécutifs)")
                            else:
                                current["reminders"][rid]["send_fails"] = fails
                            save_reminders(current)
                else:
                    # Réussite : reset le compteur
                    async with _reminders_lock:
                        current = load_reminders()
                        if rid in current["reminders"] and "send_fails" in current["reminders"][rid]:
                            del current["reminders"][rid]["send_fails"]
                            save_reminders(current)
        except Exception as e:
            print(f"❌ Erreur loop reminder: {e}")

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # --- DISBOARD : RAPPEL AUTOMATIQUE APRÈS UN BUMP RÉUSSI ---

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Détecte un bump Disboard RÉUSSI et programme un rappel 2h plus tard.

        Un bump réussi = message du bot Disboard contenant une phrase de succès
        ("Bump effectué" / "Bump done"). Un bump refusé (cooldown) a un contenu
        différent ("attendez X minutes") et ne déclenche donc rien.
        """
        if not BUMP_REMINDER_ENABLED or not message.guild:
            return
        if message.author.id != DISBOARD_BOT_ID:
            return

        content = (message.content or "").lower()
        if not any(phrase in content for phrase in BUMP_SUCCESS_PHRASES):
            return  # bump refusé ou message autre → pas de rappel

        await self.schedule_bump_reminder(message.channel)

    async def schedule_bump_reminder(self, channel) -> None:
        """Programme le rappel de bump pour ce serveur (1 seul en attente par guilde)."""
        trigger = (datetime.now(timezone.utc)
                   + timedelta(seconds=BUMP_REMINDER_DELAY_SECONDS)).isoformat()
        async with _bump_lock:
            data = load_bump_reminders()
            gid = str(channel.guild.id)
            if gid in data:
                return  # un rappel de bump est déjà en attente pour ce serveur
            data[gid] = {"trigger": trigger, "channel_id": channel.id}
            save_bump_reminders(data)

        # Log de programmation #L104
        logs_cog = self.bot.get_cog('Logs')
        log_channel = logs_cog._get_log_channel("action") if logs_cog else None
        if log_channel:
            try:
                embed = discord.Embed(color=discord.Color(int("00B0F0", 16)))  # Bleu
                embed.description = (
                    f'{CUSTOM_EMOJIS["info"]} **{TEXTS["bump_reminder_log_title"]}**\n'
                    f'{TEXTS["bump_reminder_log_desc"]}'
                )
                embed.add_field(
                    name=TEXTS["reminder_trigger_field"],
                    value=f"<t:{int(datetime.now(timezone.utc).timestamp()) + BUMP_REMINDER_DELAY_SECONDS}:R>",
                    inline=False
                )
                embed.set_footer(
                    text=f'{_log_id_for("bump_reminder")} • {get_timestamp()}'
                )
                await log_channel.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

    @tasks.loop(seconds=10)
    async def check_bump_reminders(self):
        """Vérifie les rappels de bump arrivés à échéance (one-shot : supprimés après envoi)."""
        try:
            data = load_bump_reminders()
            now = datetime.now(timezone.utc)
            for gid, info in list(data.items()):
                try:
                    trigger = datetime.fromisoformat(info["trigger"])
                except (KeyError, ValueError, TypeError):
                    async with _bump_lock:
                        current = load_bump_reminders()
                        current.pop(gid, None)
                        save_bump_reminders(current)
                    continue

                if trigger > now:
                    continue

                # Retirer AVANT l'envoi (évite les envois en boucle si échec)
                async with _bump_lock:
                    current = load_bump_reminders()
                    current.pop(gid, None)
                    save_bump_reminders(current)

                await self.send_bump_reminder(int(gid), info.get("channel_id"))
        except Exception as e:
            print(f"❌ Erreur loop bump reminder: {e}")

    @check_bump_reminders.before_loop
    async def before_check_bump(self):
        await self.bot.wait_until_ready()

    async def send_bump_reminder(self, guild_id: int, channel_id: int) -> None:
        """Envoie le rappel de rebump dans le salon du bump."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return

        content = f"<@&{BUMP_REMINDER_ROLE_ID}>" if BUMP_REMINDER_ROLE_ID else None
        embed = discord.Embed(color=discord.Color(int("00B0F0", 16)))  # Bleu
        embed.description = (
            f'{CUSTOM_EMOJIS["info"]} **{TEXTS["bump_reminder_title"]}**\n'
            f'{TEXTS["bump_reminder_desc"]}'
        )
        embed.set_footer(text=f'{_log_id_for("bump_reminder")} • {get_timestamp()}')

        try:
            await channel.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(roles=True, everyone=False)
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            print(f"❌ Envoi rappel bump impossible (guilde {guild_id}) : {e}")

    # --- COMMANDES ---

    def log_command_use(self, ctx: commands.Context, command_name: str) -> None:
        """Log l'utilisation d'une commande de rappel (+ ou / selon le mode)."""
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            prefix = "+" if ctx.interaction is None else "/"
            asyncio.create_task(logs_cog.log_command_use(command_name, ctx.author, prefix))

    @commands.hybrid_command(name="reminder", description="Créer un rappel automatique (Create a reminder)")
    async def reminder_slash(self, ctx: commands.Context):
        """Ouvre le formulaire de création d'un rappel."""
        if not await self.check_permission(ctx, "reminder"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "reminder")

        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(
                ReminderModal(self, ctx.author.id)
            )
        else:
            await ctx.send(
                f'{CUSTOM_EMOJIS["info"]} Clique sur le bouton pour ouvrir le formulaire de création :',
                view=ReminderOpenFormView(self, ctx.author.id)
            )

    @commands.hybrid_command(name="reminderlist", description="Liste des rappels (Reminder list)")
    async def reminderlist_slash(self, ctx: commands.Context):
        """Affiche la liste interactive des rappels."""
        if not await self.check_permission(ctx, "reminderlist"):
            await send_auto_delete(ctx, TEXTS["permission_denied"], ephemeral=True)
            return

        self.log_command_use(ctx, "reminderlist")

        data = load_reminders()
        embed = self._build_reminder_list_embed(ctx.author)

        if data["reminders"]:
            view = self._build_reminder_list_view(ctx.author)
            await send_auto_delete(ctx, embed=embed, view=view)
        else:
            await send_auto_delete(ctx, embed=embed)


async def setup(bot):
    """Setup du cog Reminder."""
    await bot.add_cog(Reminder(bot))
