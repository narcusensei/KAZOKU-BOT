# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

import discord
from discord.ext import commands
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import os
import asyncio
import sys
import io
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import (
    CUSTOM_EMOJIS, TEXTS,
    LOG_CHANNELS, SANCTION_COLORS, VOICE_COLORS, STAGE_COLORS,
    MEMBER_COLORS, MESSAGE_COLORS, THREAD_COLORS, INVITE_COLORS,
    EMOJI_COLORS, SOUNDBOARD_COLORS, STICKER_COLORS, EVENT_COLORS,
    SERVER_COLORS, CHANNEL_COLORS, WEBHOOK_COLORS, ROLE_COLORS, DEFAULT_COLOR,
    AUDIT_LOG_LIMIT, CONTENT_MAX_LENGTH, MEMBERS_FILE, DATA_DIR, truncate_text,
    AUDIT_LOG_DELAY_SHORT, AUDIT_LOG_DELAY_DEFAULT, AUDIT_LOG_DELAY_LONG, AUDIT_LOG_DELAY_SLOW,
    LOG_TYPE_IDS, PERMISSION_LABELS_FR, DANGEROUS_PERMISSIONS,
    MAX_ATTACHMENT_CACHE_SIZE, ATTACHMENT_CACHE_TTL, MAX_ATTACHMENT_FILE_SIZE,
    GIVEAWAY_COLOR
)

# --- CONSTANTES LOCALES (non configurables) ---
TZ_PARIS = ZoneInfo("Europe/Paris")

STAGE_EMOJIS = {
    "created": CUSTOM_EMOJIS["stage_created"],
    "edited": CUSTOM_EMOJIS["stage_edited"],
    "deleted": CUSTOM_EMOJIS["stage_deleted"]
}

EVENT_EMOJIS = {
    "created": CUSTOM_EMOJIS["event_created"],
    "edited":  CUSTOM_EMOJIS["event_edited"],
    "deleted": CUSTOM_EMOJIS["event_deleted"]
}

# Mapping des emojis personnalisés pour les sanctions
SANCTION_EMOJIS_MAP = {
    "Ban":           CUSTOM_EMOJIS["sanction_red"],
    "Unban":         CUSTOM_EMOJIS["sanction_green"],
    "Kick":          CUSTOM_EMOJIS["sanction_red"],
    "Mute":          CUSTOM_EMOJIS["sanction_red"],
    "Unmute":        CUSTOM_EMOJIS["sanction_green"],
    "Avertissement": CUSTOM_EMOJIS["sanction_yellow"]
}

# Mapping des emojis personnalisés pour les événements vocaux
VOICE_EMOJIS_MAP = {
    "join":        CUSTOM_EMOJIS["voc_join"],
    "leave":       CUSTOM_EMOJIS["voc_leave"],
    "stream_start": CUSTOM_EMOJIS["stream_on"],
    "stream_end":  CUSTOM_EMOJIS["stream_off"],
    "mute":        CUSTOM_EMOJIS["mic_mute"],
    "unmute":      CUSTOM_EMOJIS["mic_unmute"],
    "deafen":      CUSTOM_EMOJIS["headphone_deactivated"],
    "undeafen":    CUSTOM_EMOJIS["headphone_activated"],
    "video":       CUSTOM_EMOJIS["cam_activated"],
    "no_video":    CUSTOM_EMOJIS["cam_deactivated"],
    "move":        CUSTOM_EMOJIS["stream_on"]
}

# Mapping des niveaux de vérification Discord
VERIFICATION_LEVEL_NAMES = {
    discord.VerificationLevel.none:    "Aucun",
    discord.VerificationLevel.low:     "Faible",
    discord.VerificationLevel.medium:  "Moyen",
    discord.VerificationLevel.high:    "Élevé",
    discord.VerificationLevel.highest: "Très élevé",
}



# --- FONCTIONS UTILITAIRES ---

def create_fake_user(user_id: int, display_name: str = None):
    """Crée un objet utilisateur factice quand l'utilisateur n'est pas disponible."""
    if display_name is None:
        display_name = TEXTS["unknown"]
    return type('User', (), {
        'mention': f"<@{user_id}>",
        'display_name': display_name,
        'global_name': display_name,
        'display_avatar': type('obj', (object,), {'url': None}),
        'id': user_id
    })()


def format_slowmode(seconds: int) -> str:
    """Formate le délai du mode lent en texte."""
    if seconds == 0:
        return TEXTS["slowmode_disabled"]
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    rem_min = minutes % 60
    return f"{hours}h {rem_min}m" if rem_min else f"{hours}h"


def format_archive(minutes: int) -> str:
    """Formate la durée d'archivage en texte."""
    archive_map = {
        60: TEXTS["archive_1h"],
        1440: TEXTS["archive_24h"],
        4320: TEXTS["archive_3d"],
        10080: TEXTS["archive_1w"]
    }
    return archive_map.get(minutes, f"{minutes} minutes")


def get_timestamp() -> str:
    """Retourne le timestamp formaté pour les footers."""
    return datetime.now(TZ_PARIS).strftime('%d/%m/%Y %H:%M')


def format_invite_duration(seconds: int) -> str:
    """Formate une durée en texte lisible."""
    if seconds <= 0:
        return TEXTS["invite_never_expires"]
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    rem_min = minutes % 60
    if hours >= 24:
        days = hours // 24
        rem_hours = hours % 24
        if rem_hours:
            return f"{days}j {rem_hours}h"
        return f"{days}j"
    if rem_min:
        return f"{hours}h {rem_min}m"
    return f"{hours}h"


def truncate_content(content: str, max_len: int = CONTENT_MAX_LENGTH) -> str:
    """Tronque le contenu si nécessaire (alias de truncate_text)."""
    return truncate_text(content, max_len)


def get_voice_state_status(voice_state: discord.VoiceState) -> str:
    """Génère une chaîne de caractères représentant l'état vocal d'un membre."""
    if voice_state is None:
        return ""

    status_emojis = []

    if voice_state.self_mute or voice_state.mute:
        status_emojis.append(CUSTOM_EMOJIS["mic_mute"])
    else:
        status_emojis.append(CUSTOM_EMOJIS["mic_unmute"])

    if voice_state.self_deaf or voice_state.deaf:
        status_emojis.append(CUSTOM_EMOJIS["headphone_deactivated"])
    else:
        status_emojis.append(CUSTOM_EMOJIS["headphone_activated"])

    if voice_state.self_video:
        status_emojis.append(CUSTOM_EMOJIS["cam_activated"])
    else:
        status_emojis.append(CUSTOM_EMOJIS["cam_deactivated"])

    if voice_state.self_stream:
        status_emojis.append(CUSTOM_EMOJIS["stream_on"])

    return " ".join(status_emojis)


def get_channel_type(channel) -> str:
    """Retourne le type de channel vocal."""
    if isinstance(channel, discord.StageChannel):
        return TEXTS["stage_channel_type"]
    return TEXTS["voice_channel_type"]


def get_channel_log_type_str(channel) -> str:
    """Retourne le type de channel pour les logs création/édition (TEXTE/VOCAL/...)."""
    if isinstance(channel, discord.CategoryChannel):
        return TEXTS["channel_type_category"]
    if isinstance(channel, discord.StageChannel):
        return TEXTS["channel_type_stage"]
    if isinstance(channel, discord.VoiceChannel):
        return TEXTS["channel_type_voice"]
    if isinstance(channel, discord.ForumChannel):
        return TEXTS["channel_type_forum"]
    if isinstance(channel, discord.TextChannel):
        if channel.is_news():
            return TEXTS["channel_type_news"]
        return TEXTS["channel_type_text"]
    return TEXTS["channel_type_unknown"]


def get_channel_log_title(channel, action: str) -> str:
    """Retourne le titre du log selon le type de channel et l'action.

    Pour les catégories, on renvoie "CATÉGORIE CRÉÉE/MODIFIÉE/SUPPRIMÉE" (sans préfixe CHANNEL).
    Pour les autres types : "CHANNEL {TYPE} CRÉÉ/MODIFIÉ/SUPPRIMÉ".
    """
    if isinstance(channel, discord.CategoryChannel):
        category_titles = {
            "created": TEXTS["category_created_title"],
            "deleted": TEXTS["category_deleted_title"],
            "edited": TEXTS["category_edited_title"],
        }
        return category_titles.get(action, TEXTS["category_edited_title"])
    type_str = get_channel_log_type_str(channel)
    if action == "created":
        return TEXTS["channel_created_title"].format(type=type_str)
    if action == "deleted":
        return TEXTS["channel_deleted_title"].format(type=type_str)
    return TEXTS["channel_edited_title"].format(type=type_str)


def get_event_location_str(event):
    """Retourne la localisation d'un événement sous forme de string."""
    if event.channel:
        return event.channel.mention
    elif event.location:
        return f"`{event.location}`"
    return TEXTS["none"]


# --- LOGID ---
# Chaque type de log possède un ID fixe défini dans LOG_TYPE_IDS (settings.py).
# L'ID identifie le TYPE de log (tous les "ban" = #L1), pas l'instance.
# Pas de persistance nécessaire : le registre est statique et déterministe.

def _log_id_for(log_type: str) -> str:
    """Retourne le logID formaté pour un type de log donné (ex: 'ban' -> '#L1')."""
    num = LOG_TYPE_IDS.get(log_type, 0)
    return f"#L{num:03d}" if num else "#L000"


def _rgb_to_hsv(r: int, g: int, b: int):
    """Convertit RGB (0-255) vers HSV (H: 0-360, S: 0-1, V: 0-1)."""
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    v = mx
    s = d / mx if mx > 0 else 0
    if d == 0:
        h = 0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60, s, v


def _color_name_fr(color_value: int) -> str:
    """Retourne le nom français d'une couleur à partir de sa valeur hex (0xRRGGBB).

    Utilise la teinte HSV (perception humaine) pour identifier la couleur dominante.
    Retourne 'Aucune' si value == 0 (couleur par défaut de Discord = gris).
    """
    if not color_value:
        return TEXTS["none"]

    r, g, b = (color_value >> 16) & 0xFF, (color_value >> 8) & 0xFF, color_value & 0xFF
    h, s, v = _rgb_to_hsv(r, g, b)

    # Cas spéciaux : couleurs peu saturées (gris/noir/blanc)
    # Quand S est très bas, la teinte H n'a pas de sens → on ignore H
    if s < 0.15:
        if v < 0.15:
            return "Noir"
        if v > 0.9:
            return "Blanc"
        if v > 0.7:
            return "Gris clair"
        return "Gris"

    # Rose pâle : faible saturation mais teinte rouge/rose (H n'est pertinent qu'avec S suffisant)
    if s < 0.4 and (h < 20 or h >= 315) and v > 0.7:
        return "Rose"

    # Classification par teinte (HSV hue)
    # Rouge : 0-15 et 345-360
    if h < 15 or h >= 345:
        return "Rouge"
    # Rose : 315-345
    if h >= 315:
        return "Rose"
    # Orange : 15-45
    if h < 45:
        return "Orange"
    # Or : 45-55 (plus doré, légèrement désaturé)
    if h < 55:
        return "Or"
    # Jaune : 55-70
    if h < 70:
        return "Jaune"
    # Vert : 70-165
    if h < 165:
        return "Vert"
    # Turquoise : 165-200
    if h < 200:
        return "Turquoise"
    # Blurple : 225-245 (bleu Discord désaturé)
    if 225 <= h < 245 and s < 0.75:
        return "Blurple"
    # Bleu : 200-265
    if h < 265:
        return "Bleu"
    # Magenta : 265-315 avec valeur élevée
    if h < 315 and v > 0.8:
        return "Magenta"
    # Violet : 265-315 avec valeur plus faible
    return "Violet"


# Mapping des action_type de sanction -> clé LOG_TYPE_IDS
SANCTION_LOG_TYPES = {
    "Ban":           "sanction_ban",
    "Unban":         "sanction_unban",
    "Kick":          "sanction_kick",
    "Mute":          "sanction_mute",
    "Unmute":        "sanction_unmute",
    "Avertissement": "sanction_avert",
}

# Mapping des action_type vocaux -> clé LOG_TYPE_IDS (variante self/server via action_by)
VOICE_LOG_TYPES = {
    "join":         "voice_join",
    "leave":        "voice_leave",
    "stream_start": "voice_stream_start",
    "stream_end":   "voice_stream_end",
    "move":         "voice_move",
    "video":        "voice_video_on",
    "no_video":     "voice_video_off",
}

# Mapping des action_type stage -> clé LOG_TYPE_IDS
STAGE_LOG_TYPES = {
    "created":          "stage_created",
    "deleted":          "stage_deleted",
    "speaker_added":    "stage_speaker_added",
    "speaker_invited":  "stage_speaker_invited",
    "speaker_self":     "stage_speaker_self",
    "speaker_removed":  "stage_speaker_removed",
}


# --- PERMISSIONS CANONIQUES (dédoublonnées) ---
# discord.Permissions.VALID_FLAGS contient des alias partageant le même bit.
# On garde le nom correspondant à l'interface Discord (un seul par bit réel).
_PERMISSION_CANONICAL = {
    "view_channel",             # alias read_messages exclu
    "use_external_emojis",      # alias external_emojis exclu
    "manage_roles",             # alias manage_permissions exclu
    "manage_expressions",       # alias manage_emojis / manage_emojis_and_stickers exclus
    "use_external_stickers",    # alias external_stickers exclu
    "create_polls",             # alias send_polls exclu
}
# Noms de permissions de rôle à EXCLURE (alias redondants)
_PERMISSION_EXCLUDED = {
    "read_messages",
    "external_emojis",
    "manage_permissions",
    "manage_emojis",
    "manage_emojis_and_stickers",
    "external_stickers",
    "send_polls",
}


# --- CLASSE PRINCIPALE ---

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_cache = {}
        self.pin_cache = {}
        self.voice_move_cache = {}  # Cache pour détecter les déplacements
        self.pending_leave_logs = {}  # Tâches en attente pour les logs de leave
        self.move_lock = asyncio.Lock()  # Verrou pour traiter les moves séquentiellement
        self.move_audit_cache = {}  # Cache temps réel des entries member_move
        self.disconnect_cache = {}  # Cache des member_disconnect (target_id -> {moderator, created_at})
        self.server_mute_cache = {}  # Cache des member_update mute/deafen (entry.id -> {moderator, target_id, created_at})
        self.invite_cache = {}  # Cache des invitations (code -> {inviter_id, inviter_name, inviter_avatar})
        self.vc_status_mod_cache = {}  # Cache modérateur statut vocal (channel_id -> {moderator, time})
        self._banner_cache = {}  # Cache bannière serveur (guild_id -> bytes)
        self._booster_cache = {}  # Cache boost récent (guild_id -> member) pour on_guild_update
        self._attachment_cache = {}  # message_id -> [(filename, bytes, content_type)] sauvegarde proactive des fichiers
        self._attachment_cache_order = []  # FIFO pour limiter la taille du cache

        # Intercepter le gateway event VOICE_CHANNEL_STATUS_UPDATE (non supporté par discord.py)
        self.bot._connection.parsers['VOICE_CHANNEL_STATUS_UPDATE'] = lambda data: asyncio.ensure_future(
            self._parse_voice_channel_status_update(data)
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """Se déclenche quand le bot est prêt."""
        print("📦 Cog 'Logs' chargé.")
        # Pré-charger les bannières actuelles des serveurs
        for guild in self.bot.guilds:
            if guild.banner:
                try:
                    self._banner_cache[guild.id] = await guild.banner.read()
                except Exception:
                    pass

    # NOTE: on_raw_message_edit était utilisé pour les logs pin/unpin, mais le bloc
    # était inaccessible (payload.data est un dict, donc hasattr(payload.data, 'pinned')
    # était toujours False). Le pin/unpin est déjà géré dans on_message_edit.

    # --- MÉTHODES UTILITAIRES ---

    def _get_log_channel(self, channel_type: str):
        """Récupère le channel de logs correspondant."""
        channel_id = LOG_CHANNELS.get(channel_type)
        if not channel_id:
            return None

        channel = self.bot.get_channel(channel_id)
        return channel

    def _cache_attachment_cleanup(self):
        """Nettoie le cache des pièces jointes (FIFO + TTL)."""
        if not self._attachment_cache:
            return
        now = datetime.now(timezone.utc).timestamp()
        # Supprimer les entrées expirées (TTL)
        expired = [mid for mid, data in self._attachment_cache.items() if now - data['time'] > ATTACHMENT_CACHE_TTL]
        for mid in expired:
            self._attachment_cache.pop(mid, None)
            if mid in self._attachment_cache_order:
                self._attachment_cache_order.remove(mid)
        # Si toujours trop grand, supprimer les plus anciens (FIFO)
        while len(self._attachment_cache) > MAX_ATTACHMENT_CACHE_SIZE and self._attachment_cache_order:
            oldest = self._attachment_cache_order.pop(0)
            self._attachment_cache.pop(oldest, None)

    async def _cache_attachments(self, message):
        """Sauvegarde proactivement les pièces jointes d'un message dans le cache.

        Permet de restaurer les fichiers après suppression (individuelle ou bulk).
        Ignore les fichiers trop volumineux (> MAX_ATTACHMENT_FILE_SIZE).
        """
        if not message.attachments:
            return
        files_data = []
        for att in message.attachments:
            if att.size and att.size > MAX_ATTACHMENT_FILE_SIZE:
                continue  # Trop gros, on ignore
            try:
                file_bytes = await att.read()
                files_data.append((att.filename, file_bytes, att.content_type))
            except Exception:
                continue
        if files_data:
            self._attachment_cache[message.id] = {
                'files': files_data,
                'time': datetime.now(timezone.utc).timestamp()
            }
            self._attachment_cache_order.append(message.id)
            self._cache_attachment_cleanup()

    async def _get_moderator_from_audit_log(self, guild, target_id, action_types, time_window: int = 120, limit: int = AUDIT_LOG_LIMIT):
        """Recherche un modérateur dans les audit logs."""
        try:
            async for entry in guild.audit_logs(limit=limit):
                if target_id is not None:
                    if not (entry.target and hasattr(entry.target, 'id') and entry.target.id == target_id):
                        continue
                if action_types and entry.action not in action_types:
                    continue
                log_time = entry.created_at
                if (datetime.now(timezone.utc) - log_time).total_seconds() < time_window:
                    return entry.user
        except (discord.Forbidden, discord.HTTPException, AttributeError):
            pass
        return None

    def _get_mod_info(self, moderator):
        """Retourne (name, avatar_url, mention) d'un modérateur."""
        return (
            moderator.display_name if moderator else TEXTS["unknown"],
            moderator.display_avatar.url if moderator else None,
            moderator.mention if moderator else TEXTS["unknown"]
        )

    def _footer(self, log_type, entity_id):
        """Footer standardisé : "#L001 • ID: {id} • {timestamp}".

        log_type correspond à une clé de LOG_TYPE_IDS (settings.py) : l'ID est fixe
        et identifie le TYPE de log (tous les "ban" = #L1, etc.).
        """
        return f"{_log_id_for(log_type)} • ID: {entity_id} • {get_timestamp()}"

    def _footer_custom(self, log_type, label, entity_id):
        """Footer avec label personnalisé : "#L001 • {label}: {id} • {timestamp}".

        Utilisé pour Emoji/Sound/Sticker/Code/Event (l'ID n'est pas un utilisateur).
        """
        return f"{_log_id_for(log_type)} • {label}: {entity_id} • {get_timestamp()}"

    def _create_sanction_embed(self, action_type, target, moderator, reason, end_time=None, duration_str=None):
        """Crée un embed de sanction."""
        color = SANCTION_COLORS.get(action_type, DEFAULT_COLOR)
        emoji = SANCTION_EMOJIS_MAP.get(action_type, CUSTOM_EMOJIS["sanction_yellow"])

        embed = discord.Embed(color=color)
        embed.set_author(name=f"{target.global_name or target.name} ({action_type})", icon_url=target.display_avatar.url)
        if duration_str:
            embed.description = f"{emoji} **{action_type.upper()}**"
        embed.add_field(name=TEXTS["user_field"], value=f"<@{target.id}>", inline=True)
        embed.add_field(name=TEXTS["moderator_field"], value=f"<@{moderator.id}>" if moderator else TEXTS["unknown_moderator"], inline=True)
        embed.add_field(name=TEXTS["reason_field"], value=truncate_text(reason or TEXTS["no_reason"], 1000), inline=False)

        if action_type == "Mute" and end_time:
            ts_end = int(end_time.timestamp())
            countdown = TEXTS["countdown_prefix"].format(ts=ts_end)
            if duration_str:
                countdown += f" ({duration_str})"
            embed.add_field(name=TEXTS["mute_end_field"], value=countdown, inline=False)

        return embed

    def _create_voice_embed(self, member, action_type, voice_channel=None, voice_state=None, channel_before=None, channel_after=None, moved_by=None, action_by=None):
        """Crée un embed pour les événements vocaux."""
        color = VOICE_COLORS.get(action_type, DEFAULT_COLOR)
        emoji = VOICE_EMOJIS_MAP.get(action_type, CUSTOM_EMOJIS["voc_join"])

        embed = discord.Embed(color=color)

        # Author avec l'avatar
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

        # Utiliser voice_state si fourni, sinon member.voice
        vs = voice_state if voice_state is not None else member.voice
        # État actuel complet calculé une seule fois
        status = get_voice_state_status(vs)

        # Description principale avec état actuel complet
        if action_type == "stream_start":
            embed.description = f"{emoji} **{TEXTS['voice_stream_start_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_stream_start_desc']}", inline=False)
        elif action_type == "stream_end":
            embed.description = f"{emoji} **{TEXTS['voice_stream_end_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_stream_end_desc']}", inline=False)
        elif action_type == "join":
            embed.description = f"{emoji} **{TEXTS['voice_join_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_join_desc']}", inline=False)
        elif action_type == "leave":
            embed.description = f"{emoji} **{TEXTS['voice_leave_title']}** | {status}"
            if action_by:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_kicked_desc']}", inline=False)
            else:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_leave_desc']}", inline=False)
        elif action_type == "mute":
            embed.description = f"{emoji} **{TEXTS['voice_mute_title']}** | {status}"
            if action_by:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_mute_server_desc']}", inline=False)
            else:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_mute_self_desc']}", inline=False)
        elif action_type == "unmute":
            embed.description = f"{emoji} **{TEXTS['voice_unmute_title']}** | {status}"
            if action_by:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_unmute_server_desc']}", inline=False)
            else:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_unmute_self_desc']}", inline=False)
        elif action_type == "deafen":
            embed.description = f"{emoji} **{TEXTS['voice_deafen_title']}** | {status}"
            if action_by:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_deafen_server_desc']}", inline=False)
            else:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_deafen_self_desc']}", inline=False)
        elif action_type == "undeafen":
            embed.description = f"{emoji} **{TEXTS['voice_undeafen_title']}** | {status}"
            if action_by:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_undeafen_server_desc']}", inline=False)
            else:
                embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_undeafen_self_desc']}", inline=False)
        elif action_type == "video":
            embed.description = f"{emoji} **{TEXTS['voice_video_on_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_video_on_desc']}", inline=False)
        elif action_type == "no_video":
            embed.description = f"{emoji} **{TEXTS['voice_video_off_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_video_off_desc']}", inline=False)
        elif action_type == "move":
            channel_before_type = get_channel_type(channel_before) if channel_before else TEXTS["unknown"]
            channel_after_type = get_channel_type(channel_after) if channel_after else TEXTS["unknown"]
            embed.description = f"{emoji} **{TEXTS['voice_move_title']}** | {status}"
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['voice_move_desc']} {channel_before.mention if channel_before else TEXTS['unknown']} ({channel_before_type}) {TEXTS['voice_move_to']} {channel_after.mention if channel_after else TEXTS['unknown']} ({channel_after_type})", inline=False)
            if moved_by:
                embed.add_field(name=TEXTS["voice_moved_by"], value=moved_by.mention, inline=False)

        # Channel info (sauf pour les moves, déjà dans le champ Information)
        if action_type != "move":
            if voice_channel:
                channel_type = get_channel_type(voice_channel)
                embed.add_field(name=TEXTS["voice_channel"], value=f"{voice_channel.mention} ({channel_type})", inline=False)
            elif vs and vs.channel:
                channel_type = get_channel_type(vs.channel)
                embed.add_field(name=TEXTS["voice_channel"], value=f"{vs.channel.mention} ({channel_type})", inline=False)

        # Action par (après Channel) - admin qui a effectué l'action
        if action_by:
            labels = {
                "leave": TEXTS["voice_disconnected_by"],
                "mute": TEXTS["voice_muted_by"],
                "unmute": TEXTS["voice_unmuted_by"],
                "deafen": TEXTS["voice_deafened_by"],
                "undeafen": TEXTS["voice_undeafened_by"],
            }
            label = labels.get(action_type, TEXTS["voice_action_by"])
            embed.add_field(name=label, value=action_by.mention, inline=False)

        # Footer : log_type dépend de l'action et de la variante self/server (action_by)
        if action_type in ("mute", "unmute", "deafen", "undeafen"):
            log_type = f"voice_{action_type}_{'server' if action_by else 'self'}"
        elif action_type == "leave" and action_by:
            log_type = "voice_kick"
        else:
            log_type = VOICE_LOG_TYPES.get(action_type, "voice_join")
        embed.set_footer(text=self._footer(log_type, member.id))

        return embed

    # --- LOGS COMMANDES MODÉRATION ---

    async def log_command_use(self, command_name, user, prefix="/"):
        """Log l'utilisation d'une commande de modération.

        À appeler APRÈS le check de permission (donc pas si accès refusé),
        mais avant/après l'action elle-même (même en cas d'erreur).
        Le prefix affiché est "+" (préfixe) ou "/" (slash) selon le mode utilisé.
        """
        channel = self._get_log_channel("command")
        if not channel:
            return

        embed = discord.Embed(color=discord.Color(int("FFD700", 16)))  # Jaune
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["command_used"]} **{TEXTS["command_used_title"]}**\n{TEXTS["command_used_desc"]}'
        embed.add_field(name=TEXTS["command_name_field"], value=f'`{prefix}{command_name}`', inline=False)
        embed.add_field(name=TEXTS["member_by"], value=user.mention, inline=False)
        embed.set_footer(text=self._footer("command_used", user.id))
        await channel.send(embed=embed)

    # --- LOGS GIVEAWAY ---

    def _build_giveaway_embed(self, giveaway_id, name, description, end_time, creator, participants_count, winners):
        """Construit l'embed vivant d'un giveaway (création, participations, gagnants)."""
        ts = int(end_time.timestamp())
        embed = discord.Embed(color=GIVEAWAY_COLOR)
        embed.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["giveaway"]} **{name}**\n{description or ""}'
        embed.add_field(name=TEXTS["giveaway_id_field"], value=f"`{giveaway_id}`", inline=False)
        embed.add_field(name=TEXTS["giveaway_ends_log_field"], value=f"<t:{ts}:R> - <t:{ts}:F>", inline=False)
        embed.add_field(name=TEXTS["giveaway_created_by"], value=creator.mention, inline=False)
        embed.add_field(name=TEXTS["giveaway_participants"], value=f"`{participants_count}`", inline=False)
        winners_str = " ".join(w.mention for w in winners) if winners else f"`{TEXTS['giveaway_no_winners']}`"
        embed.add_field(name=TEXTS["giveaway_winners"], value=winners_str, inline=False)
        embed.set_footer(text=self._footer("giveaway", creator.id))
        return embed

    async def send_giveaway_log(self, giveaway_id, name, description, end_time, creator):
        """Crée le log d'un giveaway (embed vivant, 0 participation, aucun gagnant).

        Retourne le message du log pour édition future (participations/gagnants).
        """
        log_channel = self._get_log_channel("giveaway")
        if not log_channel:
            return None
        embed = self._build_giveaway_embed(giveaway_id, name, description, end_time, creator, 0, [])
        return await log_channel.send(embed=embed)

    async def update_giveaway_log(self, log_message, giveaway_id, name, description, end_time, creator, participants_count, winners):
        """Met à jour le log vivant d'un giveaway (compteur de participations / gagnants)."""
        if log_message is None:
            return
        embed = self._build_giveaway_embed(giveaway_id, name, description, end_time, creator, participants_count, winners)
        await log_message.edit(embed=embed)

    # --- LOGS SANCTIONS ---

    async def send_log(self, interaction, action_type, target, moderator, reason, duration_str=None, end_time=None):
        """Envoie un log de sanction via une interaction."""
        await self.send_log_sanction_channel(action_type, target, moderator, reason, duration_str, end_time)

    async def send_log_sanction_channel(self, action_type, target, moderator, reason, duration_str=None, end_time=None):
        """Envoie un log de sanction."""
        channel = self._get_log_channel("sanction")
        if not channel:
            return

        embed = self._create_sanction_embed(action_type, target, moderator, reason, end_time, duration_str)
        embed.set_footer(text=self._footer(SANCTION_LOG_TYPES.get(action_type, "sanction_ban"), target.id))
        await channel.send(embed=embed)

    # --- LISTENERS MEMBRES ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self._get_log_channel("member")
        if not channel:
            return

        if member.bot:
            await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
            moderator = await self._get_moderator_from_audit_log(
                member.guild, member.id, [discord.AuditLogAction.bot_add]
            )

            embed = discord.Embed(color=MEMBER_COLORS["bot_join"])
            embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
            embed.description = f'{CUSTOM_EMOJIS["bot_join"]} **{TEXTS["member_bot_join_title"]}**'
            embed.add_field(name=TEXTS["voice_information"], value=f"{member.mention} {TEXTS['member_bot_join_desc']} {moderator.mention if moderator else TEXTS['unknown']}", inline=False)
            embed.set_footer(text=self._footer("member_bot_join", member.id))
            await channel.send(embed=embed)
            return

        # Gestion des membres
        members_file = MEMBERS_FILE
        members_data = {}
        is_rejoin = False

        try:
            if os.path.exists(members_file):
                with open(members_file, 'r', encoding='utf-8') as f:
                    members_data = json.load(f)
            else:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(members_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)

            uid = str(member.id)
            if uid in members_data:
                is_rejoin = True
            members_data[uid] = {
                "name": member.name,
                "last_join": datetime.now(timezone.utc).isoformat()
            }
            with open(members_file, 'w', encoding='utf-8') as f:
                json.dump(members_data, f, indent=4, ensure_ascii=False)
        except (IOError, ValueError):
            # UnicodeEncodeError (pseudos non-cp1252) hérite de ValueError
            pass

        embed = discord.Embed(color=MEMBER_COLORS["join"])
        embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["member_join"]} **{TEXTS["member_join_title"]}**'
        embed.add_field(name=TEXTS["user_field"], value=f"{member.mention} {TEXTS['member_join_desc']}", inline=False)

        if not member.avatar:
            embed.add_field(name=TEXTS["member_no_avatar_warning"], value=f"```diff\n- {TEXTS['member_no_avatar']}\n```", inline=False)

        info = []
        if is_rejoin:
            info.append(f"+ {TEXTS['member_rejoin']}")
        if (datetime.now(timezone.utc) - member.created_at).days < 1:
            info.append(f"+ {TEXTS['member_new_account']}")
        if info:
            embed.add_field(name=TEXTS["info_field"], value="```diff\n" + "\n".join(info) + "\n```", inline=False)

        embed.add_field(name=TEXTS["member_account_created"], value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
        embed.set_footer(text=self._footer("member_join", member.id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self._get_log_channel("member")
        if not channel:
            return

        if member.bot:
            await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
            moderator = await self._get_moderator_from_audit_log(
                member.guild, member.id,
                [discord.AuditLogAction.member_kick, discord.AuditLogAction.member_ban_add],
                time_window=60
            )

            embed = discord.Embed(color=MEMBER_COLORS["bot_leave"])
            embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
            embed.description = f'{CUSTOM_EMOJIS["bot_leave"]} **{TEXTS["member_bot_leave_title"]}**'
            embed.add_field(name=TEXTS["info_field"], value=f"{member.mention} retiré par {moderator.mention if moderator else TEXTS['unknown']}", inline=False)
            embed.set_footer(text=self._footer("member_bot_leave", member.id))
            await channel.send(embed=embed)
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        reason_leave = TEXTS["member_leave_normal_reason"]
        moderator = None

        try:
            async for entry in member.guild.audit_logs(limit=50):
                if entry.target and entry.target.id == member.id:
                    time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                    if time_diff < 60:
                        action = entry.action.name.lower()
                        if 'kick' in action:
                            reason_leave = TEXTS["member_kick_reason"]
                            moderator = entry.user
                            break
                        if 'ban' in action:
                            reason_leave = TEXTS["member_ban_reason"]
                            moderator = entry.user
                            break
        except (discord.Forbidden, discord.HTTPException):
            pass

        if reason_leave in [TEXTS["member_kick_reason"], TEXTS["member_ban_reason"]]:
            # Ignore si le bot est le modérateur (déjà loggé par le cog moderation)
            if not moderator or moderator.id != self.bot.user.id:
                await self.send_log_sanction_channel(reason_leave, member, moderator, TEXTS["manual_action"])

        embed = discord.Embed(color=MEMBER_COLORS["leave"])
        embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["member_leave"]} **{TEXTS["member_leave_title"]}**'

        txt = f"{member.mention} a été **{reason_leave}** par {moderator.mention if moderator else TEXTS['system_fallback']}" if reason_leave != TEXTS["member_leave_normal_reason"] else f"{member.mention} {TEXTS['member_leave_desc']}"
        embed.add_field(name=TEXTS["user_field"], value=txt, inline=False)

        if member.joined_at:
            embed.add_field(name=TEXTS["member_joined_at"], value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=False)

        roles = [r.mention for r in member.roles if not r.is_default()]
        if roles:
            embed.add_field(name=TEXTS["member_roles"], value=" ".join(roles[:10]), inline=False)

        embed.set_footer(text=self._footer("member_leave", member.id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = self._get_log_channel("member")
        if not channel:
            return

        if before.roles != after.roles:
            added = [r for r in after.roles if r not in before.roles and not r.is_default()]
            removed = [r for r in before.roles if r not in after.roles and not r.is_default()]

            # --- Détection boost (rôle premium_subscriber) ---
            premium_role = after.guild.premium_subscriber_role
            booster_added = premium_role and premium_role in added
            booster_removed = premium_role and premium_role in removed

            if booster_added or booster_removed:
                server_channel = self._get_log_channel("server")
                if server_channel:
                    if booster_added:
                        self._booster_cache[after.guild.id] = after
                        color = SERVER_COLORS["booster_add"]
                        field_name = TEXTS["boost_add_field"]
                        field_value = f"{after.mention} {TEXTS['boost_add_desc']}"
                    else:
                        self._booster_cache[after.guild.id] = after
                        color = SERVER_COLORS["booster_remove"]
                        field_name = TEXTS["boost_remove_field"]
                        field_value = f"{after.mention} {TEXTS['boost_remove_desc']}"

                    embed = discord.Embed(color=color)
                    embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
                    embed.description = f'{CUSTOM_EMOJIS["booster"]} **{TEXTS["booster_title"]}**'
                    embed.add_field(name=field_name, value=field_value, inline=False)
                    embed.set_footer(text=self._footer("booster_add" if booster_added else "booster_remove", after.id))
                    await server_channel.send(embed=embed)

                # Exclure le rôle booster du log rôle générique
                if premium_role:
                    added = [r for r in added if r.id != premium_role.id]
                    removed = [r for r in removed if r.id != premium_role.id]

            mod = await self._get_moderator_from_audit_log(
                after.guild, after.id, [discord.AuditLogAction.member_role_update]
            )

            # Si aucun modérateur trouvé via l'audit log, c'est probablement
            # l'utilisateur lui-même via un sélecteur de rôle (self-assign).
            by_member = mod or after

            if added:
                emoji = CUSTOM_EMOJIS["role_added"]
                desc_key = "member_role_add_one_desc" if len(added) == 1 else "member_role_add_many_desc"
                embed = discord.Embed(color=MEMBER_COLORS["role_add"])
                embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
                embed.description = f'{emoji} **{TEXTS["member_role_add_title"]}**\n{TEXTS[desc_key].format(user=after.mention)}'
                embed.add_field(name=TEXTS["member_role_field"], value=truncate_text(", ".join([r.mention for r in added]), 1000), inline=False)
                embed.add_field(name=TEXTS["member_by"], value=by_member.mention, inline=True)
                embed.set_footer(text=self._footer("member_role_add", after.id))
                await channel.send(embed=embed)

            if removed:
                emoji = CUSTOM_EMOJIS["role_removed"]
                desc_key = "member_role_remove_one_desc" if len(removed) == 1 else "member_role_remove_many_desc"
                embed = discord.Embed(color=MEMBER_COLORS["role_remove"])
                embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
                embed.description = f'{emoji} **{TEXTS["member_role_remove_title"]}**\n{TEXTS[desc_key].format(user=after.mention)}'
                embed.add_field(name=TEXTS["member_role_field"], value=truncate_text(", ".join([r.mention for r in removed]), 1000), inline=False)
                embed.add_field(name=TEXTS["member_by"], value=by_member.mention, inline=True)
                embed.set_footer(text=self._footer("member_role_remove", after.id))
                await channel.send(embed=embed)

        if before.nick != after.nick:
            mod = await self._get_moderator_from_audit_log(
                after.guild, after.id, [discord.AuditLogAction.member_update]
            )

            if mod and mod.id == after.id:
                mod = None

            embed = discord.Embed(title=f'{CUSTOM_EMOJIS["member_edited"]} **{TEXTS["member_nick_title"]}**', color=MEMBER_COLORS["nick_change"])
            embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)
            embed.add_field(name=TEXTS["member_nick_old"], value=before.nick or TEXTS["member_no_nick"], inline=True)
            embed.add_field(name=TEXTS["member_nick_new"], value=after.nick or TEXTS["member_no_nick"], inline=True)
            if mod:
                embed.add_field(name=TEXTS["member_by"], value=mod.mention, inline=False)
            embed.set_footer(text=self._footer("member_nick_change", after.id))
            await channel.send(embed=embed)

        if before.timed_out_until != after.timed_out_until:
            mod = await self._get_moderator_from_audit_log(
                after.guild, after.id, [discord.AuditLogAction.member_update]
            )

            # Ignore si le bot est le modérateur (déjà loggé par le cog moderation)
            if mod and mod.id == self.bot.user.id:
                pass
            elif after.timed_out_until:
                dur = after.timed_out_until - datetime.now(timezone.utc)
                s = int(dur.total_seconds())
                d_str = f"{s//3600}h {(s%3600)//60}m"
                await self.send_log_sanction_channel("Mute", after, mod, TEXTS["member_timeout_manual"], d_str, after.timed_out_until)
            elif before.timed_out_until:
                await self.send_log_sanction_channel("Unmute", after, mod, TEXTS["member_timeout_removed"])

    # --- LISTENERS MESSAGES ---

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        if message.poll:
            self.poll_cache[message.id] = message
            # Borner le cache (FIFO : supprimer les plus anciens au-delà de 100)
            while len(self.poll_cache) > 100:
                oldest = next(iter(self.poll_cache))
                del self.poll_cache[oldest]

        # Sauvegarde proactive des pièces jointes (pour restauration après suppression)
        if message.attachments:
            await self._cache_attachments(message)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        """Se déclenche lors d'un /clear (purge) ou d'un ban avec suppression de messages."""
        channel = self._get_log_channel("message")
        file_channel = self._get_log_channel("file")

        for message in messages:
            if not message.content and not message.attachments:
                continue

            discord_file = None  # fichier à attacher (si récupéré du cache)
            # Récupérer les fichiers en cache (les URLs sont mortes après bulk delete)
            cached = self._attachment_cache.pop(message.id, None) if message.attachments else None
            if cached and message.id in self._attachment_cache_order:
                self._attachment_cache_order.remove(message.id)

            embed = discord.Embed(title=f'{CUSTOM_EMOJIS["message_deleted"]} **{TEXTS["message_bulk_delete_title"]}**', color=MESSAGE_COLORS["bulk_delete"])
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

            if message.attachments:
                att = message.attachments[0]
                if att.content_type and att.content_type.startswith('image/'):
                    # Image : essayer l'URL, sinon le cache
                    if cached:
                        for fname, fbytes, _ in cached['files']:
                            if fname == att.filename:
                                discord_file = discord.File(io.BytesIO(fbytes), filename=att.filename)
                                embed.set_image(url=f"attachment://{att.filename}")
                                break
                    else:
                        embed.set_image(url=att.url)
                    embed.add_field(name=TEXTS["message_file"], value=f"{TEXTS['message_image']} {att.filename}", inline=False)
                else:
                    embed.add_field(name=TEXTS["message_file"], value=f"{TEXTS['message_attachment']} {att.filename}", inline=False)
            elif message.content:
                content_show = truncate_content(message.content)
                embed.add_field(name=TEXTS["message_field"], value=f"{content_show}", inline=False)

            embed.add_field(name=TEXTS["message_author_field"], value=message.author.mention, inline=True)
            embed.add_field(name=TEXTS["message_channel_field"], value=message.channel.mention, inline=True)
            embed.add_field(name=TEXTS["method_field"], value=TEXTS["message_clear_command"], inline=False)
            embed.set_footer(text=self._footer("bulk_message_delete", message.author.id))

            # Envoyer le log message (avec le fichier attaché si récupéré du cache)
            if channel:
                if discord_file:
                    await channel.send(file=discord_file, embed=embed)
                else:
                    await channel.send(embed=embed)

            # Log dédié dans le channel fichier (comme on_message_delete)
            if message.attachments and file_channel and cached:
                for att in message.attachments:
                    for fname, fbytes, ftype in cached['files']:
                        if fname != att.filename:
                            continue
                        is_image = ftype and ftype.startswith('image/')
                        dfile = discord.File(io.BytesIO(fbytes), filename=att.filename)

                        fembed = discord.Embed(color=MESSAGE_COLORS["file_deleted"])
                        fembed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                        fembed.description = f'{CUSTOM_EMOJIS["attachment_deleted"]} **{TEXTS["file_deleted_title"]}**'
                        if is_image:
                            fembed.set_image(url=f"attachment://{att.filename}")
                        fembed.add_field(name=TEXTS["file_deleted_name_field"], value=att.filename, inline=False)
                        fembed.add_field(name=TEXTS["file_deleted_from_field"], value=message.author.mention, inline=False)
                        fembed.add_field(name=TEXTS["file_deleted_channel_field"], value=message.channel.mention, inline=False)
                        fembed.set_footer(text=self._footer("file_deleted", message.author.id))
                        await file_channel.send(file=dfile, embed=fembed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Se déclenche lors d'une suppression manuelle."""
        if not message.guild:
            return
        channel = self._get_log_channel("message")
        if not channel:
            return

        # Log sondage supprimé
        poll_message = None
        if message.poll:
            poll_message = message
        elif message.id in self.poll_cache:
            poll_message = self.poll_cache[message.id]

        if poll_message:
            try:
                poll = poll_message.poll

                deleted_by = await self._get_moderator_from_audit_log(
                    message.guild, poll_message.author.id,
                    [discord.AuditLogAction.message_delete]
                )

                if deleted_by and deleted_by.id == poll_message.author.id:
                    deleted_by = None

                embed = discord.Embed(color=MESSAGE_COLORS["poll_deleted"])
                embed.set_author(name=f"{poll_message.author.global_name or poll_message.author.name}", icon_url=poll_message.author.display_avatar.url)
                embed.description = f'{CUSTOM_EMOJIS["message_deleted"]} **{TEXTS["poll_deleted"]}**'

                question_text = poll.question if poll.question else TEXTS["poll_unknown_question"]
                embed.add_field(name=TEXTS["poll_name_field"], value=question_text, inline=False)

                multi = TEXTS["poll_enabled"] if poll.multiple else TEXTS["poll_disabled"]
                embed.add_field(name=TEXTS["poll_multichoice"], value=multi, inline=True)

                if poll.expires_at:
                    ts = int(poll.expires_at.timestamp())
                    embed.add_field(name=TEXTS["poll_end_field"], value=f"{poll.expires_at.strftime('%d/%m/%Y %H:%M')} (<t:{ts}:R>)", inline=True)
                else:
                    embed.add_field(name=TEXTS["poll_end_field"], value=TEXTS["poll_no_expiry"], inline=True)

                embed.add_field(name=TEXTS["poll_author"], value=poll_message.author.mention, inline=False)

                rep_names = []
                rep_votes = []
                if poll.answers:
                    for answer in poll.answers:
                        emoji_str = f"{str(answer.emoji)} " if answer.emoji else ""
                        rep_names.append(f"{emoji_str}{answer.text}")
                        rep_votes.append(f"`{answer.vote_count}` {TEXTS['poll_votes_unit']}")

                if rep_names:
                    embed.add_field(name=TEXTS["poll_answers"], value="\n".join(rep_names), inline=True)
                    embed.add_field(name=TEXTS["poll_votes"], value="\n".join(rep_votes), inline=True)
                    embed.add_field(name="\u200b", value="\u200b", inline=True)

                if deleted_by:
                    embed.add_field(name=TEXTS["poll_deleted_by"], value=deleted_by.mention, inline=False)

                embed.set_footer(text=self._footer("poll_deleted", poll_message.author.id))
                await channel.send(embed=embed)

                if message.id in self.poll_cache:
                    del self.poll_cache[message.id]
                return
            except Exception:
                return

        # Log message classique supprimé
        if not message.content and not message.attachments:
            return

        deleted_by = await self._get_moderator_from_audit_log(
            message.guild, message.author.id,
            [discord.AuditLogAction.message_delete]
        )

        if deleted_by and deleted_by.id == message.author.id:
            deleted_by = None

        embed = discord.Embed(title=f'{CUSTOM_EMOJIS["message_deleted"]} **{TEXTS["message_deleted_title"]}**', color=MESSAGE_COLORS["deleted"])
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)

        if message.attachments:
            att = message.attachments[0]
            if att.content_type and att.content_type.startswith('image/'):
                embed.set_image(url=att.url)
                embed.add_field(name=TEXTS["message_file"], value=f"{TEXTS['message_image']} {att.filename}", inline=False)
            else:
                embed.add_field(name=TEXTS["message_file"], value=f"{TEXTS['message_attachment']} {att.filename}", inline=False)
        elif message.content:
            content_show = truncate_content(message.content)
            embed.add_field(name=TEXTS["message_field"], value=f">>> {content_show}", inline=False)

        embed.add_field(name=TEXTS["message_author_field"], value=message.author.mention, inline=True)
        embed.add_field(name=TEXTS["message_channel_field"], value=message.channel.mention, inline=True)
        if deleted_by:
            embed.add_field(name=TEXTS["message_deleted_by"], value=deleted_by.mention, inline=False)
        embed.set_footer(text=self._footer("message_delete", message.author.id))
        await channel.send(embed=embed)

        # Log pièces jointes supprimées dans le channel fichier
        if message.attachments:
            file_channel = self._get_log_channel("file")
            if file_channel:
                # Récupérer les fichiers en cache (au cas où l'URL serait déjà morte)
                cached = self._attachment_cache.pop(message.id, None)
                if cached and message.id in self._attachment_cache_order:
                    self._attachment_cache_order.remove(message.id)

                for att in message.attachments:
                    is_image = att.content_type and att.content_type.startswith('image/')
                    discord_file = None
                    image_bytes = None  # bytes si on doit uploader l'image via attachment

                    if not is_image:
                        # Pour les autres fichiers : récupérer le contenu (URL ou cache)
                        try:
                            file_bytes = await att.read()
                        except Exception:
                            # URL morte, on cherche dans le cache
                            file_bytes = None
                            if cached:
                                for fname, fbytes, _ in cached['files']:
                                    if fname == att.filename:
                                        file_bytes = fbytes
                                        break
                        if file_bytes:
                            discord_file = discord.File(io.BytesIO(file_bytes), filename=att.filename)
                    else:
                        # Pour les images : récupérer les bytes pour set_image via upload
                        try:
                            image_bytes = await att.read()
                        except Exception:
                            if cached:
                                for fname, fbytes, _ in cached['files']:
                                    if fname == att.filename:
                                        image_bytes = fbytes
                                        break

                    embed = discord.Embed(color=MESSAGE_COLORS["file_deleted"])
                    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                    embed.description = f'{CUSTOM_EMOJIS["attachment_deleted"]} **{TEXTS["file_deleted_title"]}**'

                    # Image : afficher en haut de l'embed (via attachment si URL morte)
                    if is_image:
                        if image_bytes:
                            discord_file = discord.File(io.BytesIO(image_bytes), filename=att.filename)
                            embed.set_image(url=f"attachment://{att.filename}")
                        else:
                            embed.set_image(url=att.url)

                    embed.add_field(name=TEXTS["file_deleted_name_field"], value=att.filename, inline=False)
                    embed.add_field(name=TEXTS["file_deleted_from_field"], value=message.author.mention, inline=False)
                    embed.add_field(name=TEXTS["file_deleted_channel_field"], value=message.channel.mention, inline=False)
                    embed.set_footer(text=self._footer("file_deleted", message.author.id))

                    if discord_file:
                        await file_channel.send(file=discord_file, embed=embed)
                    else:
                        await file_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.guild or after.author.bot:
            return

        channel = self._get_log_channel("message")
        if not channel:
            return

        # Log épinglage / désépinglage
        if before.pinned != after.pinned:
            is_pin = after.pinned
            action_text = TEXTS["pin_action"] if is_pin else TEXTS["unpin_action"]
            emoji = CUSTOM_EMOJIS["message_pin"] if is_pin else CUSTOM_EMOJIS["message_unpin"]
            color = MESSAGE_COLORS["pin"] if is_pin else MESSAGE_COLORS["unpin"]

            moderator = None
            action_type = discord.AuditLogAction.message_pin if is_pin else discord.AuditLogAction.message_unpin
            await asyncio.sleep(AUDIT_LOG_DELAY_SHORT)

            moderator = await self._get_moderator_from_audit_log(
                after.guild, after.author.id, [action_type]
            )

            embed = discord.Embed(color=color)
            embed.set_author(name=after.author.display_name, icon_url=after.author.display_avatar.url)
            embed.description = f"{emoji} **{action_text}**"

            content = after.content or TEXTS["empty_content"]
            content = truncate_content(content)
            embed.add_field(name=TEXTS["message_field"], value=f">>> {content}", inline=False)
            embed.add_field(name=TEXTS["message_author"], value=after.author.mention, inline=True)

            if is_pin and moderator:
                embed.add_field(name=TEXTS["pinned_by"], value=moderator.mention, inline=True)
                self.pin_cache[after.id] = moderator.id
                # Borner le cache (FIFO : supprimer les plus anciens au-delà de 200)
                while len(self.pin_cache) > 200:
                    oldest = next(iter(self.pin_cache))
                    del self.pin_cache[oldest]
            elif not is_pin:
                pinner_id = self.pin_cache.pop(after.id, None)
                if moderator and moderator.id != pinner_id:
                    embed.add_field(name=TEXTS["unpinned_by"], value=moderator.mention, inline=True)

            embed.set_footer(text=self._footer("message_pin" if is_pin else "message_unpin", after.author.id))
            if after.channel:
                embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['jump_to_message']}]({after.jump_url})", inline=False)
            await channel.send(embed=embed)
            return

        # Log édition de texte
        if before.content == after.content:
            return

        embed = discord.Embed(title=f'{CUSTOM_EMOJIS["message_edited"]} **{TEXTS["message_edited_title"]}**', color=MESSAGE_COLORS["edited"])
        embed.set_author(name=after.author.display_name, icon_url=after.author.display_avatar.url)

        old_c = truncate_content(before.content)
        new_c = truncate_content(after.content)

        embed.add_field(name=TEXTS["message_before"], value=f"{old_c}", inline=False)
        embed.add_field(name=TEXTS["message_after"], value=f"{new_c}", inline=False)
        embed.add_field(name=TEXTS["message_channel"], value=after.channel.mention, inline=True)
        embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['message_go']}]({after.jump_url})", inline=True)
        embed.set_footer(text=self._footer("message_edit", after.author.id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Se déclenche quand une réaction est retirée."""
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = self._get_log_channel("message")
        if not channel:
            return

        user_id = payload.user_id
        user = guild.get_member(user_id)

        if not user:
            user_obj = create_fake_user(user_id, f"ID: {user_id}")
        else:
            user_obj = user

        # Gestion emoji
        emoji = payload.emoji
        emoji_display = ""
        emoji_image_url = None

        if emoji.id:
            ext = "gif" if emoji.animated else "png"
            emoji_image_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{ext}?size=64"
            emoji_display = f"[{emoji.name}]({emoji_image_url})"
        else:
            emoji_display = str(emoji)

        embed = discord.Embed(color=MESSAGE_COLORS["reaction"])
        embed.set_author(name=user_obj.display_name, icon_url=user_obj.display_avatar.url)

        embed.description = f'{CUSTOM_EMOJIS["reaction_remove"]} **{TEXTS["reaction_removed"]}**'
        embed.add_field(name=TEXTS["action_field"], value=f"{user_obj.mention} {TEXTS['reaction_removed_desc']}", inline=False)
        embed.add_field(name=TEXTS["reaction_emoji"], value=emoji_display, inline=True)

        jump_url = f"https://discord.com/channels/{guild.id}/{payload.channel_id}/{payload.message_id}"
        embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['jump_to_message']}]({jump_url})", inline=True)
        embed.set_footer(text=self._footer("reaction_remove", user_id))
        await channel.send(embed=embed)

    # --- LOGS SERVEUR ---

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Se déclenche quand les paramètres du serveur sont modifiés."""
        channel = self._get_log_channel("server")
        if not channel:
            return

        # Vérifier qu'au moins une propriété a changé
        changes = []

        if before.name != after.name:
            changes.append(("name", before.name, after.name))

        if before.verification_level != after.verification_level:
            changes.append(("verification", before.verification_level, after.verification_level))

        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append(("content_filter", before.explicit_content_filter, after.explicit_content_filter))

        if before.default_notifications != after.default_notifications:
            changes.append(("notifications", before.default_notifications, after.default_notifications))

        if before.afk_timeout != after.afk_timeout:
            changes.append(("afk_timeout", before.afk_timeout, after.afk_timeout))

        if before.afk_channel != after.afk_channel:
            changes.append(("afk_channel", before.afk_channel, after.afk_channel))

        if before.system_channel != after.system_channel:
            changes.append(("system_channel", before.system_channel, after.system_channel))

        if before.system_channel_flags != after.system_channel_flags:
            changes.append(("system_channel_flags", before.system_channel_flags, after.system_channel_flags))

        if before.banner != after.banner:
            changes.append(("banner", before.banner, after.banner))

        if before.description != after.description:
            changes.append(("description", before.description, after.description))

        # --- Détection boost ---
        if before.premium_subscription_count != after.premium_subscription_count:
            boost_diff = after.premium_subscription_count - before.premium_subscription_count
            booster = self._booster_cache.pop(after.id, None)

            server_channel = self._get_log_channel("server")
            if server_channel:
                if boost_diff > 0:
                    color = SERVER_COLORS["boost_add"]
                    title = TEXTS["boost_add_title"]
                    emoji = CUSTOM_EMOJIS["boost_added"]
                    count_field = TEXTS["boost_count_added_field"]
                    count_val = boost_diff
                else:
                    color = SERVER_COLORS["boost_remove"]
                    title = TEXTS["boost_remove_title"]
                    emoji = CUSTOM_EMOJIS["boost_removed"]
                    count_field = TEXTS["boost_count_removed_field"]
                    count_val = abs(boost_diff)

                embed = discord.Embed(color=color)
                if booster:
                    embed.set_author(name=booster.display_name, icon_url=booster.display_avatar.url)
                embed.description = f'{emoji} **{title}**'
                embed.add_field(name=count_field, value=f"`{count_val}`", inline=False)
                embed.add_field(name=TEXTS["boost_level_field"], value=f"`{after.premium_tier}`", inline=True)
                embed.add_field(name=TEXTS["boost_total_field"], value=f"`{after.premium_subscription_count}`", inline=True)
                embed.set_footer(text=self._footer("boost_add" if boost_diff > 0 else "boost_remove", booster.id if booster else '?'))
                await server_channel.send(embed=embed)

        # Fallback audit log : Discord peut ne pas mettre à jour certains champs
        # (ex: default_notifications deprecated, afk_channel, system_channel)
        # dans le GUILD_UPDATE event, on vérifie via l'audit log
        detected_types = {ct for ct, _, _ in changes}
        fallback_types = {"notifications", "afk_channel", "system_channel"} - detected_types
        if fallback_types:
            await asyncio.sleep(AUDIT_LOG_DELAY_LONG)  # Attendre la création de l'entry audit log
            try:
                async for entry in after.audit_logs(limit=5, action=discord.AuditLogAction.guild_update):
                    log_time = entry.created_at
                    if (datetime.now(timezone.utc) - log_time).total_seconds() < 30:
                        if "notifications" in fallback_types:
                            before_notif = getattr(entry.before, 'default_notifications', None)
                            after_notif = getattr(entry.after, 'default_notifications', None)
                            if before_notif is not None and after_notif is not None and before_notif != after_notif:
                                changes.append(("notifications", before_notif, after_notif))
                        if "system_channel" in fallback_types:
                            before_sys = getattr(entry.before, 'system_channel', None)
                            after_sys = getattr(entry.after, 'system_channel', None)
                            if before_sys != after_sys:
                                changes.append(("system_channel", before_sys, after_sys))
                        if "afk_channel" in fallback_types:
                            before_afk = getattr(entry.before, 'afk_channel', None)
                            after_afk = getattr(entry.after, 'afk_channel', None)
                            if before_afk != after_afk:
                                changes.append(("afk_channel_fallback", before_afk, after_afk))
                        break
            except Exception:
                pass

        if not changes:
            return

        # Préparer l'ancienne bannière depuis le cache (CDN déjà supprimé)
        banner_file = None
        banner_filename = None
        for ct, old_v, new_v in changes:
            if ct == "banner" and old_v:
                cached_bytes = self._banner_cache.get(before.id)
                if cached_bytes:
                    ext = "gif" if old_v.is_animated() else "png"
                    banner_filename = f"old_banner.{ext}"
                    banner_file = discord.File(io.BytesIO(cached_bytes), filename=banner_filename)
                break

        moderator = await self._get_moderator_from_audit_log(
            after, None, [discord.AuditLogAction.guild_update]
        )

        mod_name = moderator.display_name if moderator else TEXTS["unknown"]
        mod_avatar = moderator.display_avatar.url if moderator else None

        embed = discord.Embed(color=SERVER_COLORS["edited"])
        embed.set_author(name=mod_name, icon_url=mod_avatar)
        embed.description = f'{CUSTOM_EMOJIS["server_edited"]} **{TEXTS["server_edited_title"]}**'

        for change_type, old_val, new_val in changes:
            if change_type == "name":
                embed.add_field(
                    name=TEXTS["server_name_field"],
                    value=f"`{old_val}` **-->** `{new_val}`",
                    inline=False
                )

            elif change_type == "description":
                embed.add_field(
                    name=TEXTS["server_description_field"],
                    value=new_val or f"`{TEXTS['none_value_f']}`",
                    inline=False
                )

            elif change_type == "verification":
                embed.add_field(
                    name=TEXTS["server_verification_field"],
                    value=VERIFICATION_LEVEL_NAMES.get(new_val, str(new_val)),
                    inline=False
                )

            elif change_type == "content_filter":
                filter_state = TEXTS["state_enabled"] if new_val != discord.ContentFilter.disabled else TEXTS["state_disabled"]
                embed.add_field(
                    name=TEXTS["server_content_filter_field"],
                    value=filter_state,
                    inline=False
                )

            elif change_type == "notifications":
                notif_state = (
                    f"`{TEXTS['server_notif_all']}`"
                    if new_val == discord.NotificationLevel.all_messages
                    else f"`{TEXTS['server_notif_mentions']}`"
                )
                embed.add_field(
                    name=TEXTS["server_notifications_field"],
                    value=notif_state,
                    inline=False
                )

            elif change_type == "afk_timeout" or change_type == "afk_channel":
                # Éviter les doublons si les deux changent en même temps
                already_afk = any(
                    f.name == TEXTS["server_afk_field"]
                    for f in embed.fields
                )
                if already_afk:
                    continue

                afk_lines = []
                if before.afk_timeout != after.afk_timeout:
                    old_fmt = f"{before.afk_timeout // 60} min" if before.afk_timeout < 3600 else f"{before.afk_timeout // 3600}h"
                    new_fmt = f"{after.afk_timeout // 60} min" if after.afk_timeout < 3600 else f"{after.afk_timeout // 3600}h"
                    afk_lines.append(f'{TEXTS["server_afk_timeout_change"]} | `{old_fmt}` **-->** `{new_fmt}`')

                if before.afk_channel != after.afk_channel:
                    old_ch = before.afk_channel.mention if before.afk_channel else f"`{TEXTS['none_value']}`"
                    new_ch = after.afk_channel.mention if after.afk_channel else f"`{TEXTS['none_value']}`"
                    afk_lines.append(f'{TEXTS["server_afk_channel_change"]} | {old_ch} **-->** {new_ch}')

                embed.add_field(
                    name=TEXTS["server_afk_field"],
                    value="\n".join(afk_lines),
                    inline=False
                )

            elif change_type == "system_channel" or change_type == "system_channel_flags":
                # Éviter les doublons si les deux changent en même temps
                already_sys = any(
                    f.name == TEXTS["server_system_channel_field"]
                    for f in embed.fields
                )
                if already_sys:
                    continue

                lines = []

                # Channel système (si modifié)
                if before.system_channel != after.system_channel:
                    old_ch = before.system_channel.mention if before.system_channel else f"`{TEXTS['none_value']}`"
                    new_ch = after.system_channel.mention if after.system_channel else f"`{TEXTS['none_value']}`"
                    lines.append(f'**{TEXTS["server_system_channel_change"]}** | {old_ch} **-->** {new_ch}')

                # Flags (uniquement ceux qui ont changé)
                if before.system_channel_flags != after.system_channel_flags:
                    flag_checks = [
                        ("join_notifications", TEXTS["server_system_flag_join_notif"]),
                        ("join_notification_replies", TEXTS["server_system_flag_join_reply"]),
                        ("premium_subscriptions", TEXTS["server_system_flag_premium"]),
                        ("guild_reminder_notifications", TEXTS["server_system_flag_reminder"]),
                    ]
                    for flag_attr, flag_label in flag_checks:
                        old_flag = getattr(before.system_channel_flags, flag_attr)
                        new_flag = getattr(after.system_channel_flags, flag_attr)
                        if old_flag != new_flag:
                            state = TEXTS["server_system_enabled"] if new_flag else TEXTS["server_system_disabled"]
                            lines.append(f'{flag_label} - `{state}`')

                embed.add_field(
                    name=TEXTS["server_system_channel_field"],
                    value="\n".join(lines),
                    inline=False
                )

            elif change_type == "afk_channel_fallback":
                old_ch = old_val.mention if old_val and hasattr(old_val, 'mention') else f"`{TEXTS['none_value']}`"
                new_ch = new_val.mention if new_val and hasattr(new_val, 'mention') else f"`{TEXTS['none_value']}`"
                embed.add_field(
                    name=TEXTS["server_afk_field"],
                    value=f'{TEXTS["server_afk_channel_change"]} | {old_ch} **-->** {new_ch}',
                    inline=False
                )

            elif change_type == "banner":
                if old_val and banner_file and banner_filename:
                    embed.set_thumbnail(url=f"attachment://{banner_filename}")
                if new_val:
                    embed.set_image(url=new_val.url)
                    if old_val:
                        embed.add_field(
                            name=TEXTS["server_banner_changed"],
                            value="",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name=TEXTS["server_banner_added"],
                            value="",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name=TEXTS["server_banner_removed"],
                        value="",
                        inline=False
                    )

        embed.set_footer(text=self._footer("server_edited", moderator.id if moderator else '?'))
        if banner_file:
            await channel.send(embed=embed, file=banner_file)
        else:
            await channel.send(embed=embed)

        # Mettre à jour le cache de la bannière
        has_banner_change = any(ct == "banner" for ct, _, _ in changes)
        if has_banner_change:
            after_banner = after.banner
            if after_banner:
                try:
                    self._banner_cache[after.id] = await after_banner.read()
                except Exception:
                    self._banner_cache.pop(after.id, None)
            else:
                self._banner_cache.pop(after.id, None)

    # --- LISTENERS THREADS ---

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        """Se déclenche lors de la création d'un fil."""
        if not thread.guild:
            return

        channel = self._get_log_channel("message")
        if not channel:
            return

        # Vrai nouveau fil
        creator = thread.guild.get_member(thread.owner_id)
        if not creator:
            try:
                creator = await thread.guild.fetch_member(thread.owner_id)
            except discord.NotFound:
                creator = create_fake_user(thread.owner_id, f"ID: {thread.owner_id}")

        embed = discord.Embed(color=THREAD_COLORS["created"])
        embed.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["thread_created"]} **{TEXTS["thread_created_desc"]}**'
        embed.add_field(name=TEXTS["voice_information"], value=f"{creator.mention} {TEXTS['thread_created_text']} **{thread.name}**", inline=False)

        parent_channel = thread.parent
        embed.add_field(name=TEXTS["voice_channel"], value=parent_channel.mention if parent_channel else TEXTS["unknown"], inline=True)
        embed.add_field(name=TEXTS["thread_field"], value=thread.mention, inline=True)
        embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['jump_to_message']}]({thread.jump_url})", inline=False)
        embed.set_footer(text=self._footer("thread_create", creator.id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        """Se déclenche quand le bot rejoint un fil.

        Discord dispatche cet événement (et non on_thread_update) quand un fil archivé
        est rouvert : le fil ayant été retiré du cache à l'archivage, sa réouverture est
        vue comme un "join". On détecte ce cas via l'âge du fil (récent = vrai join, ancien = réouverture).
        """
        if not thread.guild:
            return

        channel = self._get_log_channel("message")
        if not channel:
            return

        # Un fil rouvert existe depuis longtemps (> 30s), contrairement à un fil qu'on rejoint récemment
        age_seconds = (datetime.now(timezone.utc) - thread.created_at).total_seconds()
        if age_seconds <= 30:
            return  # Vrai join récent, pas une réouverture

        # C'est une réouverture de fil archivé
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            thread.guild, thread.id, [discord.AuditLogAction.thread_update]
        )
        member = moderator or thread.guild.get_member(thread.owner_id) or thread.guild.me

        embed = discord.Embed(color=THREAD_COLORS["reopened"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["thread_unlock"]} **{TEXTS["thread_reopened_title"]}**\n\n{member.mention} a `rouvert` un fil'

        parent_channel = thread.parent
        embed.add_field(name=TEXTS["voice_channel"], value=parent_channel.mention if parent_channel else TEXTS["unknown"], inline=True)
        embed.add_field(name=TEXTS["thread_field"], value=thread.mention, inline=True)
        embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['jump_to_message']}]({thread.jump_url})", inline=False)
        embed.set_footer(text=self._footer("thread_reopened", member.id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        """Se déclenche lors de la suppression d'un fil."""
        if not thread.guild:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)

        moderator = await self._get_moderator_from_audit_log(
            thread.guild, thread.id, [discord.AuditLogAction.thread_delete]
        )

        channel = self._get_log_channel("message")
        if not channel:
            return

        embed = discord.Embed(color=THREAD_COLORS["deleted"])
        embed.set_author(name=moderator.display_name if moderator else TEXTS["unknown"], icon_url=moderator.display_avatar.url if moderator else None)

        if moderator:
            embed.description = f'{CUSTOM_EMOJIS["thread_deleted"]} **{TEXTS["thread_deleted_title"]}**\n\n{moderator.mention} {TEXTS["thread_deleted_text"]}'
        else:
            embed.description = f'{CUSTOM_EMOJIS["thread_deleted"]} **{TEXTS["thread_deleted_title"]}**\n\n{TEXTS["thread_deleted_unknown"]}'

        parent_channel = thread.parent
        embed.add_field(name=TEXTS["voice_channel"], value=parent_channel.mention if parent_channel else TEXTS["unknown"], inline=True)
        embed.add_field(name=TEXTS["thread_field"], value=f"**{thread.name}**", inline=True)

        if moderator:
            embed.set_footer(text=self._footer("thread_delete", moderator.id))
        else:
            embed.set_footer(text=self._footer("thread_delete", thread.owner_id))
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        """Se déclenche lors de la modification d'un fil."""
        if not after.guild:
            return

        channel = self._get_log_channel("message")
        if not channel:
            return

        moderator = await self._get_moderator_from_audit_log(
            after.guild, after.id, [discord.AuditLogAction.thread_update]
        )

        if not moderator:
            moderator = after.guild.get_member(after.owner_id) or create_fake_user(after.owner_id)

        # Collecter toutes les modifications
        modifications = []
        primary_action = None  # type d'action dominant si modification unique

        # Changement de nom
        if before.name != after.name:
            modifications.append(f'a changé le nom du fil | **{before.name}** >>> **{after.name}**')

        # Changement mode lent
        if before.slowmode_delay != after.slowmode_delay:
            modifications.append(f'a changé le mode lent | `{format_slowmode(before.slowmode_delay)}` >>> `{format_slowmode(after.slowmode_delay)}`')

        # Changement période d'inactivité
        if before.auto_archive_duration != after.auto_archive_duration:
            modifications.append(f"a changé la période d'inactivité | `{format_archive(before.auto_archive_duration)}` >>> `{format_archive(after.auto_archive_duration)}`")

        # Verrouillage / Déverrouillage
        if before.locked != after.locked:
            if after.locked:
                modifications.append('a `verrouillé` un fil')
                primary_action = "locked"
            else:
                modifications.append('a `déverrouillé` un fil')
                primary_action = "unlocked"

        # Fermeture / Ouverture
        if not before.archived and after.archived:
            modifications.append('a `fermé` un fil')
            primary_action = "closed"
        elif before.archived and not after.archived:
            modifications.append('a `rouvert` un fil')
            primary_action = "reopened"

        if not modifications:
            return

        # Déterminer l'emoji, le titre et le log_type en fonction du type de modification
        emoji = CUSTOM_EMOJIS["thread_edited"]
        title = TEXTS['thread_modified_title']
        log_type = "thread_update"
        color = THREAD_COLORS["updated"]

        # Si une seule modification, spécialiser l'emoji/titre/log_type/couleur selon l'action
        if len(modifications) == 1 and primary_action:
            if primary_action == "locked":
                emoji = CUSTOM_EMOJIS["thread_lock"]
                title = TEXTS['thread_locked_title']
                log_type = "thread_locked"
                color = THREAD_COLORS["locked"]
            elif primary_action == "unlocked":
                emoji = CUSTOM_EMOJIS["thread_unlock"]
                title = TEXTS['thread_unlocked_title']
                log_type = "thread_unlocked"
                color = THREAD_COLORS["unlocked"]
            elif primary_action == "closed":
                emoji = CUSTOM_EMOJIS["thread_close"]
                title = TEXTS['thread_closed_title']
                log_type = "thread_closed"
                color = THREAD_COLORS["closed"]
            elif primary_action == "reopened":
                emoji = CUSTOM_EMOJIS["thread_unlock"]
                title = TEXTS['thread_reopened_title']
                log_type = "thread_reopened"
                color = THREAD_COLORS["reopened"]

        # Créer l'embed avec toutes les modifications
        embed = discord.Embed(color=color)
        embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)

        if len(modifications) == 1:
            # Une seule modification : format simple
            embed.description = f"{emoji} **{title}**\n\n{moderator.mention} {modifications[0]}"
        else:
            # Plusieurs modifications : regrouper
            embed.description = f"{emoji} **{title}**\n\n{moderator.mention} {TEXTS['multiple_modifications_desc']}"
            for i, mod in enumerate(modifications, 1):
                embed.add_field(name=f"{TEXTS['modification_field']} {i}", value=mod, inline=False)

        parent_channel = after.parent
        embed.add_field(name=TEXTS["voice_channel"], value=parent_channel.mention if parent_channel else TEXTS["unknown"], inline=True)
        embed.add_field(name=TEXTS["thread_field"], value=after.mention, inline=True)
        embed.add_field(name=TEXTS["link_field"], value=f"[{TEXTS['jump_to_message']}]({after.jump_url})", inline=False)
        embed.set_footer(text=self._footer(log_type, moderator.id))
        await channel.send(embed=embed)

    # --- LOGS CHANNELS ---

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Se déclenche quand un channel est créé."""
        if not channel.guild:
            return

        log_channel = self._get_log_channel("channel")
        if not log_channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            channel.guild, channel.id, [discord.AuditLogAction.channel_create], limit=50
        )

        member = moderator or channel.guild.me
        is_category = isinstance(channel, discord.CategoryChannel)

        embed = discord.Embed(color=CHANNEL_COLORS["created"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["channel_created"]} **{get_channel_log_title(channel, "created")}**'

        # Description : mention du channel + admin (+ catégorie parente si applicable)
        if is_category:
            channel_display = f"`{channel.name}`"
            desc = TEXTS["category_created_desc"].format(channel=channel_display, moderator=member.mention)
        else:
            channel_display = channel.mention
            desc = TEXTS["channel_created_desc"].format(channel=channel_display, moderator=member.mention)
            if channel.category:
                desc += TEXTS["channel_created_in_category"].format(category=channel.category.mention)
        embed.add_field(name=TEXTS["voice_information"], value=desc, inline=False)

        embed.set_footer(text=self._footer("channel_create", member.id))
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Se déclenche quand un channel est supprimé."""
        if not channel.guild:
            return

        log_channel = self._get_log_channel("channel")
        if not log_channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            channel.guild, channel.id, [discord.AuditLogAction.channel_delete], limit=50
        )

        member = moderator or channel.guild.me
        is_category = isinstance(channel, discord.CategoryChannel)
        # Channel supprimé : la mention afficherait #deleted-channel, on utilise le nom
        channel_display = f"`{channel.name}`"
        category_display = channel.category.name if channel.category else None

        embed = discord.Embed(color=CHANNEL_COLORS["deleted"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["channel_deleted"]} **{get_channel_log_title(channel, "deleted")}**'

        if is_category:
            desc = TEXTS["category_deleted_desc"].format(channel=channel_display, moderator=member.mention)
        else:
            desc = TEXTS["channel_deleted_desc"].format(channel=channel_display, moderator=member.mention)
            if category_display:
                desc += TEXTS["channel_deleted_in_category"].format(category=category_display)
        embed.add_field(name=TEXTS["voice_information"], value=desc, inline=False)

        embed.set_footer(text=self._footer("channel_delete", member.id))
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Se déclenche quand un channel est modifié (propriétés et/ou permissions)."""
        if not after.guild:
            return

        log_channel = self._get_log_channel("channel")
        if not log_channel:
            return

        # --- 1. Changements de propriétés (nom, description, mode lent, etc.) ---
        prop_changes = self._collect_channel_prop_changes(before, after)
        if prop_changes:
            await self._log_channel_props_change(before, after, prop_changes, log_channel)

        # --- 2. Changements d'overwrites (permissions) ---
        if before.overwrites == after.overwrites:
            return

        # Identifier les cibles (roles/members) dont les overwrites ont changé.
        before_ow = {t.id: ow for t, ow in before.overwrites.items()}
        after_ow = {t.id: (t, ow) for t, ow in after.overwrites.items()}

        changes = []  # [(action_key, target, old_ow, new_ow)]
        for target_id, (target, new_overwrite) in after_ow.items():
            if target_id not in before_ow:
                # Nouvel overwrite -> permission créée
                changes.append(("created", target, None, new_overwrite))
            elif before_ow[target_id] != new_overwrite:
                # Overwrite existant modifié -> permission mise à jour
                changes.append(("updated", target, before_ow[target_id], new_overwrite))
        for target_id, old_overwrite in before_ow.items():
            if target_id not in after_ow:
                # Overwrite supprimé -> permission retirée
                # On reconstruit un pseudo-target depuis l'id (déjà supprimé du cache)
                target = after.guild.get_role(target_id) or after.guild.get_member(target_id) or target_id
                changes.append(("deleted", target, old_overwrite, None))

        if not changes:
            return

        # Récupérer les entries audit log overwrite récentes pour identifier modérateur + cible.
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        audit_entries = []  # [{action, user, extra, target_id}]
        try:
            async for entry in after.guild.audit_logs(limit=50):
                if entry.action not in (
                    discord.AuditLogAction.overwrite_create,
                    discord.AuditLogAction.overwrite_update,
                    discord.AuditLogAction.overwrite_delete
                ):
                    continue
                if not (entry.target and getattr(entry.target, 'id', None) == after.id):
                    continue
                log_time = entry.created_at
                if (datetime.now(timezone.utc) - log_time).total_seconds() < 120:
                    extra_id = getattr(entry.extra, 'id', None) if entry.extra else None
                    audit_entries.append({
                        'action': entry.action,
                        'user': entry.user,
                        'extra_id': extra_id,
                        'extra': entry.extra,
                    })
        except (discord.Forbidden, discord.HTTPException, AttributeError):
            pass

        for action_key, target, old_ow, new_ow in changes:
            # Le target peut être un Role, un Member, un Object ou un int (id brute)
            target_id = target if isinstance(target, int) else target.id
            # Cas spécial : le rôle @everyone (rôle par défaut du serveur).
            # role.mention retourne <@&{id}> mais Discord le rend en ajoutant "@" + "@everyone"
            # (car le nom interne du rôle est "@everyone"), ce qui donne "@@everyone".
            # Solution : utiliser role.name qui vaut déjà "@everyone" (avec un seul @).
            if isinstance(target, discord.Role) and target.is_default():
                target_mention = target.name  # "@everyone"
            else:
                target_mention = getattr(target, 'mention', f"<@&{target_id}>")

            # Associer l'entry audit log correspondante (par extra_id == target_id)
            moderator = None
            for ae in audit_entries:
                if ae['extra_id'] == target_id:
                    moderator = ae['user']
                    break
            # Fallback : premier modérateur trouvé si pas de match précis
            if not moderator and audit_entries:
                moderator = audit_entries[0]['user']

            member = moderator or after.guild.me

            # Emoji + couleur + titre selon l'action
            if action_key == "created":
                color = CHANNEL_COLORS["permission_created"]
                emoji = CUSTOM_EMOJIS["channel_permission_created"]
                title = TEXTS["channel_perm_created_title"]
                log_type = "channel_permission_create"
            elif action_key == "deleted":
                color = CHANNEL_COLORS["permission_deleted"]
                emoji = CUSTOM_EMOJIS["channel_permission_deleted"]
                title = TEXTS["channel_perm_deleted_title"]
                log_type = "channel_permission_delete"
            else:
                color = CHANNEL_COLORS["permission_edited"]
                emoji = CUSTOM_EMOJIS["channel_permission_edited"]
                title = TEXTS["channel_perm_updated_title"]
                log_type = "channel_permission_update"

            # Nom du channel : "de la catégorie `name`" ou "du channel #mention"
            if isinstance(after, discord.CategoryChannel):
                channel_text = f"de la catégorie `{after.name}`"
            else:
                channel_text = f"du channel {after.mention}"

            embed = discord.Embed(color=color)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.description = (
                f'{emoji} **{title}**\n'
                f'{member.mention} a modifié les permissions {channel_text} {TEXTS["channel_perm_for_role"]} {target_mention}'
            )

            # Afficher les permissions old / new (uniquement les différences)
            if action_key == "created":
                # Nouvel overwrite : tout est nouveau, afficher la nouvelle version
                perm_lines = self._format_perms(new_ow)
                embed.add_field(name=TEXTS["channel_perm_new_field"], value=perm_lines, inline=False)
            elif action_key == "deleted":
                # Overwrite supprimé : afficher l'ancienne version
                perm_lines = self._format_perms(old_ow)
                embed.add_field(name=TEXTS["channel_perm_old_field"], value=perm_lines, inline=False)
            else:
                # Update : comparer old/new et n'afficher QUE les permissions modifiées
                old_lines, new_lines = self._format_perms_diff(old_ow, new_ow)
                if old_lines:
                    embed.add_field(name=TEXTS["channel_perm_old_field"], value=old_lines, inline=False)
                if new_lines:
                    embed.add_field(name=TEXTS["channel_perm_new_field"], value=new_lines, inline=False)

            embed.set_footer(text=self._footer(log_type, member.id))
            await log_channel.send(embed=embed)

    def _collect_channel_prop_changes(self, before, after) -> list:
        """Détecte les changements de propriétés d'un channel (nom, description, etc.).

        Retourne une liste de tuples (label, valeur_avant --> valeur_après).
        Seuls les champs réellement modifiés sont inclus.
        """
        changes = []

        # Nom (tous types de channel)
        if before.name != after.name:
            changes.append((TEXTS["channel_prop_name"], f"`{before.name}` **-->** `{after.name}`"))

        # Description / topic (texte, forum, stage — pas sur les catégories)
        old_topic, new_topic = before.topic or "", after.topic or ""
        if old_topic != new_topic:
            old_display = truncate_text(old_topic, 200) if old_topic else TEXTS["none"]
            new_display = truncate_text(new_topic, 200) if new_topic else TEXTS["none"]
            changes.append((TEXTS["channel_prop_topic"], f"`{old_display}` **-->** `{new_display}`"))

        # Mode lent (texte, vocal, forum)
        old_slow = getattr(before, 'slowmode_delay', 0)
        new_slow = getattr(after, 'slowmode_delay', 0)
        if old_slow != new_slow:
            changes.append((TEXTS["channel_prop_slowmode"], f"`{format_slowmode(old_slow)}` **-->** `{format_slowmode(new_slow)}`"))

        # Masquer après une période d'inactivité / auto-archive (texte, forum)
        old_archive = getattr(before, 'default_auto_archive_duration', None)
        new_archive = getattr(after, 'default_auto_archive_duration', None)
        if old_archive is not None and new_archive is not None and old_archive != new_archive:
            changes.append((TEXTS["channel_prop_archive"], f"`{format_archive(old_archive)}` **-->** `{format_archive(new_archive)}`"))

        # Catégorie parente (déplacement du channel)
        if before.category_id != after.category_id:
            old_cat = before.category.mention if before.category else f"`{TEXTS['channel_no_category']}`"
            new_cat = after.category.mention if after.category else f"`{TEXTS['channel_no_category']}`"
            changes.append((TEXTS["channel_prop_category"], f"{old_cat} **-->** {new_cat}"))

        # NSFW (texte uniquement)
        if getattr(before, 'nsfw', False) != getattr(after, 'nsfw', False):
            old_nsfw = TEXTS["role_yes"] if before.nsfw else TEXTS["role_no"]
            new_nsfw = TEXTS["role_yes"] if after.nsfw else TEXTS["role_no"]
            changes.append((TEXTS["channel_prop_nsfw"], f"`{old_nsfw}` **-->** `{new_nsfw}`"))

        # Débit audio (vocal uniquement)
        old_bitrate = getattr(before, 'bitrate', None)
        new_bitrate = getattr(after, 'bitrate', None)
        if old_bitrate and new_bitrate and old_bitrate != new_bitrate:
            changes.append((TEXTS["channel_prop_bitrate"], f"`{old_bitrate // 1000} kbps` **-->** `{new_bitrate // 1000} kbps`"))

        # Limite utilisateurs (vocal uniquement, 0 = illimité)
        old_limit = getattr(before, 'user_limit', None)
        new_limit = getattr(after, 'user_limit', None)
        if old_limit is not None and new_limit is not None and old_limit != new_limit:
            old_l = str(old_limit) if old_limit else TEXTS["channel_unlimited"]
            new_l = str(new_limit) if new_limit else TEXTS["channel_unlimited"]
            changes.append((TEXTS["channel_prop_userlimit"], f"`{old_l}` **-->** `{new_l}`"))

        return changes

    async def _log_channel_props_change(self, before, after, changes, log_channel):
        """Génère un log pour les changements de propriétés d'un channel."""
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            after.guild, after.id, [discord.AuditLogAction.channel_update], limit=50
        )
        member = moderator or after.guild.me

        is_category = isinstance(after, discord.CategoryChannel)
        channel_display = f"`{after.name}`" if is_category else after.mention
        desc_template = TEXTS["category_edited_desc"] if is_category else TEXTS["channel_edited_desc"]

        embed = discord.Embed(color=CHANNEL_COLORS["edited"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["channel_edited"]} **{get_channel_log_title(after, "edited")}**\n{desc_template.format(channel=channel_display)}'

        for field_name, field_value in changes:
            embed.add_field(name=field_name, value=field_value, inline=False)

        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer("channel_edit", member.id))
        await log_channel.send(embed=embed)

    def _perm_label_fr(self, perm_name) -> str:
        """Retourne le label français d'une permission."""
        return PERMISSION_LABELS_FR.get(perm_name, perm_name.replace('_', ' ').title())

    def _perm_emoji(self, val) -> str:
        """Retourne l'emoji correspondant à l'état d'une permission."""
        if val is True:
            return CUSTOM_EMOJIS["allow"]
        elif val is False:
            return CUSTOM_EMOJIS["deny"]
        return CUSTOM_EMOJIS["neutral"]

    def _format_perms(self, overwrite) -> str:
        """Formate un PermissionOverwrite en liste lisible avec emojis allow/deny (FR).

        Borné à 1000 caractères (limite Discord : 1024 par field).
        """
        if overwrite is None:
            return TEXTS["none"]
        lines = []
        for perm_name in discord.PermissionOverwrite.VALID_NAMES:
            val = getattr(overwrite, perm_name, None)
            if val is True or val is False:
                lines.append(f'{self._perm_emoji(val)} **{self._perm_label_fr(perm_name)}**')
        return truncate_text("\n".join(lines), 1000) if lines else TEXTS["none"]

    def _format_perms_diff(self, old_ow, new_ow) -> tuple:
        """Compare deux PermissionOverwrite et retourne (lignes_old, lignes_new).

        N'inclut QUE les permissions dont la valeur a changé entre old et new.
        Borné à 1000 caractères par liste (limite Discord).
        """
        old_lines = []
        new_lines = []
        for perm_name in discord.PermissionOverwrite.VALID_NAMES:
            old_val = getattr(old_ow, perm_name, None) if old_ow else None
            new_val = getattr(new_ow, perm_name, None) if new_ow else None
            if old_val != new_val:
                old_lines.append(f'{self._perm_emoji(old_val)} **{self._perm_label_fr(perm_name)}**')
                new_lines.append(f'{self._perm_emoji(new_val)} **{self._perm_label_fr(perm_name)}**')
        return (
            truncate_text("\n".join(old_lines), 1000) if old_lines else TEXTS["none"],
            truncate_text("\n".join(new_lines), 1000) if new_lines else TEXTS["none"],
        )

    # --- LOGS RÔLES SERVEUR ---

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Se déclenche quand un rôle est créé."""
        if not role.guild:
            return

        log_channel = self._get_log_channel("roles")
        if not log_channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            role.guild, role.id, [discord.AuditLogAction.role_create], limit=50
        )
        member = moderator or role.guild.me

        embed = discord.Embed(color=ROLE_COLORS["created"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["role_created"]} **{TEXTS["role_created_title"]}**\n{TEXTS["role_created_desc"].format(name=role.name)}'
        embed.add_field(name=TEXTS["role_field"], value=f"`{role.name}`", inline=False)
        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer("role_create", member.id))
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Se déclenche quand un rôle est supprimé."""
        if not role.guild:
            return

        log_channel = self._get_log_channel("roles")
        if not log_channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            role.guild, role.id, [discord.AuditLogAction.role_delete], limit=50
        )
        member = moderator or role.guild.me

        embed = discord.Embed(color=ROLE_COLORS["deleted"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["role_deleted"]} **{TEXTS["role_deleted_title"]}**\n{TEXTS["role_deleted_desc"].format(name=role.name)}'
        embed.add_field(name=TEXTS["role_field"], value=f"`{role.name}`", inline=False)
        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer("role_delete", member.id))
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Se déclenche quand un rôle est modifié."""
        if not after.guild:
            return

        log_channel = self._get_log_channel("roles")
        if not log_channel:
            return

        # --- Cas spécial : changement d'icône (log dédié) ---
        before_icon = before.icon
        after_icon = after.icon
        icon_changed = str(before_icon) != str(after_icon)
        if icon_changed:
            await self._log_role_icon_change(before, after, before_icon, after_icon, log_channel)

        # --- Cas spécial : changement de permissions (log dédié) ---
        if before.permissions != after.permissions:
            await self._log_role_perms_change(before, after, log_channel)

        # --- Autres changements (nom, couleur, hoist, mentionable) ---
        changes = []

        # Changement de nom
        if before.name != after.name:
            changes.append((TEXTS["role_name_field"], f"`{before.name}` **-->** `{after.name}`"))

        # Changement de couleur
        if before.color != after.color:
            old_color = _color_name_fr(before.color.value)
            new_color = _color_name_fr(after.color.value)
            changes.append((TEXTS["role_color_field"], f"`{old_color}` **-->** `{new_color}`"))

        # Changement hoist (affiché séparément)
        if before.hoist != after.hoist:
            old_hoist = TEXTS["role_yes"] if before.hoist else TEXTS["role_no"]
            new_hoist = TEXTS["role_yes"] if after.hoist else TEXTS["role_no"]
            changes.append((TEXTS["role_hoist_field"], f"`{old_hoist}` **-->** `{new_hoist}`"))

        # Changement mentionable
        if before.mentionable != after.mentionable:
            old_ment = TEXTS["role_yes"] if before.mentionable else TEXTS["role_no"]
            new_ment = TEXTS["role_yes"] if after.mentionable else TEXTS["role_no"]
            changes.append((TEXTS["role_mentionable_field"], f"`{old_ment}` **-->** `{new_ment}`"))

        if not changes:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            after.guild, after.id, [discord.AuditLogAction.role_update], limit=50
        )
        member = moderator or after.guild.me

        embed = discord.Embed(color=ROLE_COLORS["edited"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["role_edited"]} **{TEXTS["role_edited_title"]}**\n{TEXTS["role_edited_desc"].format(name=after.name)}'

        for field_name, field_value in changes:
            embed.add_field(name=field_name, value=field_value, inline=False)

        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer("role_update", member.id))
        await log_channel.send(embed=embed)

    async def _log_role_icon_change(self, before, after, before_icon, after_icon, log_channel):
        """Génère un log dédié pour un changement d'icône de rôle."""
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            after.guild, after.id, [discord.AuditLogAction.role_update], limit=50
        )
        member = moderator or after.guild.me

        # Déterminer le type de changement
        if after_icon is None:
            # Icône supprimée
            desc_template = TEXTS["role_icon_removed_desc"]
            log_type = "role_icon_removed"
            icon_to_show = before_icon  # afficher l'ancienne icône
        elif before_icon is None:
            # Icône ajoutée
            desc_template = TEXTS["role_icon_added_desc"]
            log_type = "role_icon_added"
            icon_to_show = after_icon
        else:
            # Icône modifiée
            desc_template = TEXTS["role_icon_updated_desc"]
            log_type = "role_icon_updated"
            icon_to_show = after_icon

        embed = discord.Embed(color=ROLE_COLORS["edited"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["role_edited"]} **{TEXTS["role_icon_title"]}**\n{desc_template.format(role=after.mention)}'

        # Afficher l'icône concernée en thumbnail
        icon_url = str(icon_to_show) if icon_to_show else None
        if icon_url and icon_url.startswith('http'):
            embed.set_thumbnail(url=icon_url)

        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer(log_type, member.id))
        await log_channel.send(embed=embed)

    async def _log_role_perms_change(self, before, after, log_channel):
        """Génère un log dédié pour un changement de permissions de rôle."""
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            after.guild, after.id, [discord.AuditLogAction.role_update], limit=50
        )
        member = moderator or after.guild.me

        # Comparer les permissions (booléens True/False) au format Ancien/Nouveau
        # En excluant les alias redondants (un seul nom par bit réel)
        old_lines = []
        new_lines = []
        dangerous_added = []  # permissions dangereuses passées à True
        for perm_name in discord.Permissions.VALID_FLAGS:
            if perm_name in _PERMISSION_EXCLUDED:
                continue
            old_val = getattr(before.permissions, perm_name, False)
            new_val = getattr(after.permissions, perm_name, False)
            if old_val == new_val:
                continue
            label = PERMISSION_LABELS_FR.get(perm_name, perm_name.replace('_', ' ').title())
            old_emoji = CUSTOM_EMOJIS["allow"] if old_val else CUSTOM_EMOJIS["deny"]
            new_emoji = CUSTOM_EMOJIS["allow"] if new_val else CUSTOM_EMOJIS["deny"]
            old_lines.append(f"{old_emoji} **{label}**")
            new_lines.append(f"{new_emoji} **{label}**")
            # Détecter les permissions dangereuses nouvellement accordées
            if new_val and not old_val and perm_name in DANGEROUS_PERMISSIONS:
                dangerous_added.append(label)

        embed = discord.Embed(color=ROLE_COLORS["edited"])
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{CUSTOM_EMOJIS["role_permission_edited"]} **{TEXTS["role_perms_title"]}**\n{TEXTS["role_perms_desc"].format(role=after.mention)}'

        if old_lines:
            embed.add_field(name=TEXTS["channel_perm_old_field"], value=truncate_text("\n".join(old_lines), 1000), inline=False)
        if new_lines:
            embed.add_field(name=TEXTS["channel_perm_new_field"], value=truncate_text("\n".join(new_lines), 1000), inline=False)

        # Alerte DANGER si des permissions dangereuses ont été ajoutées
        if dangerous_added:
            danger_content = f"```diff\n- {TEXTS['role_perms_danger_desc']}\n" + "\n".join(f"- {p}" for p in dangerous_added) + "\n```"
            embed.add_field(name=TEXTS["role_perms_danger_title"], value=danger_content, inline=False)

        embed.add_field(name=TEXTS["member_by"], value=member.mention, inline=False)
        embed.set_footer(text=self._footer("role_perms", member.id))
        await log_channel.send(embed=embed)

    # --- LOGS INVITATIONS ---

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Se déclenche quand une invitation est créée."""
        if not invite.guild:
            return

        channel = self._get_log_channel("action")
        if not channel:
            return

        inviter = invite.inviter
        inviter_name = inviter.display_name if inviter else TEXTS["invite_unknown_inviter"]
        inviter_avatar = inviter.display_avatar.url if inviter else None
        inviter_mention = inviter.mention if inviter else TEXTS["invite_unknown_inviter"]

        # Mettre en cache l'inviter pour on_invite_delete
        if inviter:
            self.invite_cache[invite.code] = {
                "id": inviter.id,
                "name": inviter.display_name,
                "mention": inviter.mention
            }

        embed = discord.Embed(color=INVITE_COLORS["created"])
        embed.set_author(name=inviter_name, icon_url=inviter_avatar)
        embed.description = f'{CUSTOM_EMOJIS["invite_created"]} **{TEXTS["invite_created_title"]}**\n\n{inviter_mention} {TEXTS["invite_created_desc"]}'

        embed.add_field(name=TEXTS["invite_link_field"], value=invite.url, inline=False)
        embed.add_field(name=TEXTS["invite_channel_field"], value=invite.channel.mention, inline=False)

        if invite.max_age == 0:
            expiry = TEXTS["invite_never_expires"]
        else:
            expiry = f"`{format_invite_duration(seconds=invite.max_age)}`"
        embed.add_field(name=TEXTS["invite_expiration_field"], value=expiry, inline=False)

        if inviter:
            embed.set_footer(text=self._footer("invite_create", inviter.id))
        else:
            embed.set_footer(text=self._footer_custom("invite_create", "Code", invite.code))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Se déclenche quand une invitation est supprimée."""
        if not invite.guild:
            return

        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)

        # Chercher qui a supprimé l'invitation dans les audit logs
        moderator = None
        try:
            async for entry in invite.guild.audit_logs(limit=50, action=discord.AuditLogAction.invite_delete):
                if entry.target and hasattr(entry.target, 'code') and entry.target.code == invite.code:
                    log_time = entry.created_at
                    if (datetime.now(timezone.utc) - log_time).total_seconds() < 120:
                        moderator = entry.user
                        break
        except (discord.Forbidden, discord.HTTPException):
            pass

        mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)
        if not moderator:
            mod_name = TEXTS["invite_unknown_inviter"]
            mod_mention = TEXTS["invite_unknown_inviter"]

        inviter = invite.inviter
        # Utiliser le cache si inviter n'est pas disponible
        if not inviter and invite.code in self.invite_cache:
            cached = self.invite_cache.pop(invite.code)
            inviter_mention = cached["mention"]
        else:
            inviter_mention = inviter.mention if inviter else TEXTS["invite_unknown_inviter"]
            if invite.code in self.invite_cache:
                del self.invite_cache[invite.code]

        embed = discord.Embed(color=INVITE_COLORS["deleted"])
        embed.set_author(name=mod_name, icon_url=mod_avatar)
        embed.description = f'{CUSTOM_EMOJIS["invite_deleted"]} **{TEXTS["invite_deleted_title"]}**\n\n{mod_mention} {TEXTS["invite_deleted_desc"]}'

        embed.add_field(name=TEXTS["invite_link_field"], value=f"https://discord.gg/{invite.code}", inline=False)
        embed.add_field(name=TEXTS["invite_channel_field"], value=invite.channel.mention, inline=False)
        embed.add_field(name=TEXTS["invite_uses_field"], value=f"`{invite.uses}`", inline=False)
        embed.add_field(name=TEXTS["invite_created_by_field"], value=inviter_mention, inline=False)

        if moderator:
            embed.set_footer(text=self._footer("invite_delete", moderator.id))
        else:
            embed.set_footer(text=self._footer_custom("invite_delete", "Code", invite.code))

        await channel.send(embed=embed)

    # --- LOGS WEBHOOKS ---

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        """Se déclenche quand un webhook est créé/modifié/supprimé dans un channel.

        L'événement gateway WEBHOOKS_UPDATE ne fournit que guild_id + channel_id.
        On croise avec l'audit log pour déterminer l'action et le webhook ciblé.
        """
        if not channel.guild:
            return

        log_channel = self._get_log_channel("channel")
        if not log_channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)

        # Chercher l'entry audit log webhook la plus récente sur ce channel
        webhook_entry = None
        webhook_action = None
        try:
            async for entry in channel.guild.audit_logs(limit=30):
                if entry.action not in (
                    discord.AuditLogAction.webhook_create,
                    discord.AuditLogAction.webhook_update,
                    discord.AuditLogAction.webhook_delete
                ):
                    continue
                # Filtrer par fraîcheur (< 120s)
                if (datetime.now(timezone.utc) - entry.created_at).total_seconds() >= 120:
                    continue
                # Vérifier que l'entry concerne bien ce channel
                target = entry.target
                target_channel_id = getattr(target, 'channel_id', None)
                if target_channel_id is not None and target_channel_id != channel.id:
                    continue
                webhook_entry = entry
                webhook_action = entry.action
                break
        except (discord.Forbidden, discord.HTTPException, AttributeError):
            pass

        if not webhook_entry:
            return

        moderator = webhook_entry.user
        member = moderator or channel.guild.me
        target = webhook_entry.target
        webhook_name = getattr(target, 'name', None) or TEXTS["unknown"]

        # Déterminer le type d'action
        if webhook_action == discord.AuditLogAction.webhook_create:
            color = WEBHOOK_COLORS["created"]
            emoji = CUSTOM_EMOJIS["webhook_created"]
            title = TEXTS["webhook_created_title"]
            desc_template = TEXTS["webhook_created_desc"]
            log_type = "webhook_create"
        elif webhook_action == discord.AuditLogAction.webhook_delete:
            color = WEBHOOK_COLORS["deleted"]
            emoji = CUSTOM_EMOJIS["webhook_deleted"]
            title = TEXTS["webhook_deleted_title"]
            desc_template = TEXTS["webhook_deleted_desc"]
            log_type = "webhook_delete"
        else:  # webhook_update
            before = webhook_entry.before
            after = webhook_entry.after
            # Discord ne peuple before/after qu'avec les attributs modifiés.
            channel_changed = hasattr(after, 'channel')
            name_changed = hasattr(after, 'name')
            avatar_changed = hasattr(after, 'avatar')
            old_avatar = getattr(before, 'avatar', None)
            new_avatar = getattr(after, 'avatar', None)

            # Cas spécial : changement d'avatar uniquement (log dédié)
            if avatar_changed and not name_changed and not channel_changed:
                emoji = CUSTOM_EMOJIS["webhook_updated"]
                if new_avatar is None:
                    # Avatar supprimé/retiré
                    color = WEBHOOK_COLORS["deleted"]
                    title = TEXTS["webhook_avatar_removed_title"]
                    desc_template = TEXTS["webhook_avatar_removed_desc"]
                    log_type = "webhook_avatar_removed"
                elif old_avatar is None:
                    # Avatar ajouté
                    color = WEBHOOK_COLORS["created"]
                    title = TEXTS["webhook_avatar_added_title"]
                    desc_template = TEXTS["webhook_avatar_added_desc"]
                    log_type = "webhook_avatar_added"
                else:
                    # Avatar modifié
                    color = WEBHOOK_COLORS["edited"]
                    title = TEXTS["webhook_avatar_updated_title"]
                    desc_template = TEXTS["webhook_avatar_updated_desc"]
                    log_type = "webhook_avatar_updated"
            elif channel_changed:
                # Déplacement de webhook
                color = WEBHOOK_COLORS["edited"]
                emoji = CUSTOM_EMOJIS["webhook_edited"]
                title = TEXTS["webhook_updated_title"]
                desc_template = TEXTS["webhook_moved_desc"]
                log_type = "webhook_update"
            else:
                # Modification classique (nom, etc.)
                color = WEBHOOK_COLORS["edited"]
                emoji = CUSTOM_EMOJIS["webhook_edited"]
                title = TEXTS["webhook_updated_title"]
                desc_template = TEXTS["webhook_updated_desc"]
                log_type = "webhook_update"

        embed = discord.Embed(color=color)
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.description = f'{emoji} **{title}**\n\n{desc_template.format(name=webhook_name)}'

        # Cas spécial : changement d'avatar uniquement
        if log_type.startswith("webhook_avatar"):
            # Avatar ajouté/modifié : afficher le nouvel avatar en thumbnail
            if new_avatar is not None:
                # new_avatar peut être un hash (string) ou un Asset
                avatar_url = str(new_avatar) if not hasattr(new_avatar, 'url') else new_avatar.url
                # Si c'est un hash, construire l'URL CDN
                if avatar_url and not avatar_url.startswith('http'):
                    ext = 'gif' if avatar_url.startswith('a_') else 'png'
                    avatar_url = f"https://cdn.discordapp.com/icons/{channel.guild.id}/{avatar_url}.{ext}?size=128"
                if avatar_url:
                    embed.set_thumbnail(url=avatar_url)
            else:
                # Avatar supprimé : afficher l'ancien avatar
                if old_avatar is not None:
                    avatar_url = str(old_avatar) if not hasattr(old_avatar, 'url') else old_avatar.url
                    if avatar_url and not avatar_url.startswith('http'):
                        ext = 'gif' if avatar_url.startswith('a_') else 'png'
                        avatar_url = f"https://cdn.discordapp.com/icons/{channel.guild.id}/{avatar_url}.{ext}?size=128"
                    if avatar_url:
                        embed.set_thumbnail(url=avatar_url)
        elif webhook_action == discord.AuditLogAction.webhook_update:
            # Modification classique : afficher nom et channel si modifiés
            if name_changed:
                old_name = getattr(before, 'name', None)
                new_name = getattr(after, 'name', None)
                embed.add_field(
                    name=TEXTS["webhook_name_field"],
                    value=f"`{old_name or TEXTS['none']}` **-->** `{new_name}`",
                    inline=False
                )

            if channel_changed:
                old_ch = getattr(before, 'channel', None)
                new_ch = getattr(after, 'channel', None)
                old_ch_display = old_ch.mention if old_ch else f"`{TEXTS['none']}`"
                new_ch_display = new_ch.mention if new_ch else f"`{TEXTS['none']}`"
                embed.add_field(
                    name=TEXTS["webhook_channel_field"],
                    value=f"{old_ch_display} **-->** {new_ch_display}",
                    inline=False
                )
            else:
                embed.add_field(name=TEXTS["webhook_channel_field"], value=channel.mention, inline=False)
        else:
            # Création / Suppression : afficher le channel où l'action a eu lieu
            embed.add_field(name=TEXTS["webhook_channel_field"], value=channel.mention, inline=False)

        embed.add_field(name=TEXTS["webhook_by_field"], value=member.mention, inline=False)

        # Footer : utiliser l'ID du webhook si dispo, sinon l'ID du modérateur
        webhook_id = getattr(target, 'id', None)
        if webhook_id:
            embed.set_footer(text=self._footer(log_type, member.id))
        else:
            embed.set_footer(text=self._footer(log_type, member.id))

        await log_channel.send(embed=embed)

    # --- LOGS EMOJIS ---

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Se déclenche quand des emojis sont ajoutés ou supprimés."""
        channel = self._get_log_channel("action")
        if not channel:
            return

        before_ids = {e.id: e for e in before}
        after_ids = {e.id: e for e in after}

        # Emoji ajouté
        for emoji in after:
            if emoji.id not in before_ids:
                await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
                moderator = await self._get_moderator_from_audit_log(guild, emoji.id, [discord.AuditLogAction.emoji_create], limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                embed = discord.Embed(color=EMOJI_COLORS["added"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["emoji_added"]} **{TEXTS["emoji_added_title"]}**\n{str(emoji)} a été créé par {mod_mention}'
                embed.set_thumbnail(url=emoji.url)
                embed.add_field(name=TEXTS["emoji_name_field"], value=f"`{emoji.name}`", inline=False)

                if moderator:
                    embed.set_footer(text=self._footer("emoji_added", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("emoji_added", "Emoji ID", emoji.id))

                await channel.send(embed=embed)

        # Emoji supprimé
        for emoji in before:
            if emoji.id not in after_ids:
                await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
                moderator = await self._get_moderator_from_audit_log(guild, emoji.id, [discord.AuditLogAction.emoji_delete], limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                embed = discord.Embed(color=EMOJI_COLORS["removed"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["emoji_removed"]} **{TEXTS["emoji_removed_title"]}**\n`{emoji.name}` a été supprimé par {mod_mention}'

                if moderator:
                    embed.set_footer(text=self._footer("emoji_removed", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("emoji_removed", "Emoji ID", emoji.id))

                await channel.send(embed=embed)

        # Emoji modifié
        for emoji_id, after_emoji in after_ids.items():
            if emoji_id in before_ids:
                before_emoji = before_ids[emoji_id]
                name_changed = before_emoji.name != after_emoji.name

                if not name_changed:
                    continue

                await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
                moderator = await self._get_moderator_from_audit_log(guild, emoji_id, [discord.AuditLogAction.emoji_update], limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                embed = discord.Embed(color=EMOJI_COLORS["edited"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["emoji_edited"]} **{TEXTS["emoji_edited_title"]}**\n{str(after_emoji)} à été modifié par {mod_mention}\n\n**{TEXTS["new_name"]}**\n`{after_emoji.name}`'
                embed.set_thumbnail(url=after_emoji.url)

                if moderator:
                    embed.set_footer(text=self._footer("emoji_edited", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("emoji_edited", "Emoji ID", after_emoji.id))

                await channel.send(embed=embed)

    # --- LOGS STICKERS ---

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        """Se déclenche quand des stickers sont ajoutés, supprimés ou modifiés."""
        channel = self._get_log_channel("action")
        if not channel:
            return

        before_ids = {s.id: s for s in before}
        after_ids = {s.id: s for s in after}

        # Sticker créé
        for sticker in after:
            if sticker.id not in before_ids:
                await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

                moderator = await self._get_moderator_from_audit_log(guild, sticker.id, [discord.AuditLogAction.sticker_create], time_window=30, limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                embed = discord.Embed(color=STICKER_COLORS["created"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["sticker_created"]} **{TEXTS["sticker_created_title"]}**\nLe sticker `{sticker.name}` a été créé par {mod_mention}'
                embed.add_field(name=TEXTS["sticker_emoji_id_field"], value=f"`{sticker.emoji}`", inline=False)
                if sticker.description:
                    embed.add_field(name=TEXTS["sticker_description_field"], value=sticker.description, inline=False)
                embed.set_thumbnail(url=sticker.url)

                if moderator:
                    embed.set_footer(text=self._footer("sticker_created", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("sticker_created", "Sticker ID", sticker.id))

                await channel.send(embed=embed)

        # Sticker supprimé
        for sticker in before:
            if sticker.id not in after_ids:
                await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

                moderator = await self._get_moderator_from_audit_log(guild, sticker.id, [discord.AuditLogAction.sticker_delete], time_window=30, limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                embed = discord.Embed(color=STICKER_COLORS["deleted"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["sticker_deleted"]} **{TEXTS["sticker_deleted_title"]}**\nLe sticker `{sticker.name}` a été supprimé par {mod_mention}'
                embed.add_field(name=TEXTS["sticker_emoji_id_field"], value=f"`{sticker.emoji}`", inline=False)

                if moderator:
                    embed.set_footer(text=self._footer("sticker_deleted", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("sticker_deleted", "Sticker ID", sticker.id))

                await channel.send(embed=embed)

        # Sticker modifié
        for sticker_id, after_sticker in after_ids.items():
            if sticker_id in before_ids:
                before_sticker = before_ids[sticker_id]
                name_changed = before_sticker.name != after_sticker.name
                emoji_changed = before_sticker.emoji != after_sticker.emoji
                desc_changed = before_sticker.description != after_sticker.description

                if not (name_changed or emoji_changed or desc_changed):
                    continue

                await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

                moderator = await self._get_moderator_from_audit_log(guild, after_sticker.id, [discord.AuditLogAction.sticker_update], time_window=30, limit=10)
                mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

                changes = []
                if name_changed:
                    changes.append(f"**{TEXTS['new_name']}**\n`{after_sticker.name}`")
                if emoji_changed:
                    changes.append(f"**{TEXTS['new_emoji_id']}**\n`{after_sticker.emoji}`")
                if desc_changed:
                    changes.append(f"**{TEXTS['new_description']}**\n{after_sticker.description or TEXTS['none']}")

                changes_text = "\n".join(changes)

                embed = discord.Embed(color=STICKER_COLORS["modified"])
                embed.set_author(name=mod_name, icon_url=mod_avatar)
                embed.description = f'{CUSTOM_EMOJIS["sticker_edited"]} **{TEXTS["sticker_modified_title"]}**\n{changes_text}\n\n**{TEXTS["sticker_modified_by"]}**\n{mod_mention}'

                if moderator:
                    embed.set_footer(text=self._footer("sticker_modified", moderator.id))
                else:
                    embed.set_footer(text=self._footer_custom("sticker_modified", "Sticker ID", after_sticker.id))

                await channel.send(embed=embed)

    # --- LOGS SOUNDBOARD ---

    @commands.Cog.listener()
    async def on_soundboard_sound_create(self, sound):
        """Se déclenche quand un son soundboard est ajouté."""
        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

        moderator = await self._get_moderator_from_audit_log(sound.guild, None, [discord.AuditLogAction.soundboard_sound_create], time_window=30, limit=10)
        mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

        embed = discord.Embed(color=SOUNDBOARD_COLORS["added"])
        embed.set_author(name=mod_name, icon_url=mod_avatar)
        embed.description = f'{CUSTOM_EMOJIS["soundboard_added"]} **{TEXTS["soundboard_added_title"]}**\nLa soundboard `{sound.name}` a été ajouté par {mod_mention}'

        if moderator:
            embed.set_footer(text=self._footer("soundboard_added", moderator.id))
        else:
            embed.set_footer(text=self._footer_custom("soundboard_added", "Sound ID", sound.id))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_soundboard_sound_delete(self, sound):
        """Se déclenche quand un son soundboard est supprimé."""
        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

        moderator = await self._get_moderator_from_audit_log(sound.guild, None, [discord.AuditLogAction.soundboard_sound_delete], time_window=30, limit=10)
        mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

        embed = discord.Embed(color=SOUNDBOARD_COLORS["removed"])
        embed.set_author(name=mod_name, icon_url=mod_avatar)
        embed.description = f'{CUSTOM_EMOJIS["soundboard_removed"]} **{TEXTS["soundboard_removed_title"]}**\nLa soundboard `{sound.name}` a été retiré par {mod_mention}'

        if moderator:
            embed.set_footer(text=self._footer("soundboard_removed", moderator.id))
        else:
            embed.set_footer(text=self._footer_custom("soundboard_removed", "Sound ID", sound.id))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_soundboard_sound_update(self, before, after):
        """Se déclenche quand un son soundboard est modifié."""
        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_SLOW)

        moderator = await self._get_moderator_from_audit_log(after.guild, None, [discord.AuditLogAction.soundboard_sound_update], time_window=30, limit=10)
        mod_name, mod_avatar, mod_mention = self._get_mod_info(moderator)

        changes = []
        if before.name != after.name:
            changes.append(f"**{TEXTS['new_name']}**\n`{after.name}`")
        if str(before.emoji) != str(after.emoji):
            changes.append(f"**{TEXTS['new_emoji']}**\n{str(after.emoji)}")

        if not changes:
            return

        changes_text = "\n".join(changes)

        embed = discord.Embed(color=SOUNDBOARD_COLORS["modified"])
        embed.set_author(name=mod_name, icon_url=mod_avatar)
        embed.description = f'{CUSTOM_EMOJIS["soundboard_edited"]} **{TEXTS["soundboard_modified_title"]}**\n{changes_text}\n\n**{TEXTS["soundboard_modified_by"]}**\n{mod_mention}'

        if moderator:
            embed.set_footer(text=self._footer("soundboard_modified", moderator.id))
        else:
            embed.set_footer(text=self._footer_custom("soundboard_modified", "Sound ID", after.id))

        await channel.send(embed=embed)

    # --- LOGS CONFÉRENCE (STAGE) ---

    def _create_stage_embed(self, member, action_type, stage_channel, topic=None, invited_member=None):
        """Crée un embed pour les événements de conférence."""
        color = STAGE_COLORS.get(action_type, DEFAULT_COLOR)
        emoji = STAGE_EMOJIS.get(action_type, CUSTOM_EMOJIS["stage_created"])

        embed = discord.Embed(color=color)

        # Déterminer l'auteur à afficher
        if action_type in ["speaker_added", "speaker_invited", "speaker_self"] and invited_member:
            embed.set_author(name=invited_member.display_name, icon_url=invited_member.display_avatar.url)
        else:
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

        if action_type == "created":
            status = get_voice_state_status(member.voice)
            embed.description = f"{emoji} **{TEXTS['stage_created_title']}** | {status}\n\n{member.mention} {TEXTS['stage_created_desc']} dans {stage_channel.mention}"
            if topic:
                embed.add_field(name=TEXTS["topic_field"], value=topic, inline=False)
            embed.add_field(name=TEXTS["voice_channel"], value=stage_channel.mention, inline=False)
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], member.id))

        elif action_type == "speaker_added":
            embed.description = f"{emoji} **{TEXTS['stage_speaker_added_title']}**\n\n{invited_member.mention} à accepté de devenir intervenant dans {stage_channel.mention}"
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], invited_member.id))

        elif action_type == "speaker_invited":
            embed.description = f"{emoji} **{TEXTS['stage_speaker_invited_title']}**\n\n{invited_member.mention} à été invité à devenir intervenant dans {stage_channel.mention}"
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], invited_member.id))

        elif action_type == "speaker_self":
            embed.description = f"{emoji} **{TEXTS['stage_speaker_self_title']}**\n\n{member.mention} {TEXTS['stage_speaker_self_desc']} {stage_channel.mention}"
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], member.id))

        elif action_type == "deleted":
            embed.description = f"{emoji} **{TEXTS['stage_deleted_title']}**\n\nLa conférence {stage_channel.mention} {TEXTS['stage_deleted_desc']} {member.mention}"
            embed.add_field(name=TEXTS["voice_channel"], value=stage_channel.mention, inline=False)
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], member.id))

        elif action_type == "speaker_removed":
            embed.description = f"{emoji} **{TEXTS['stage_speaker_removed_title']}**\n\n{member.mention} {TEXTS['stage_speaker_removed_desc']} dans {stage_channel.mention}"
            embed.add_field(name=TEXTS["voice_channel"], value=stage_channel.mention, inline=False)
            embed.set_footer(text=self._footer(STAGE_LOG_TYPES[action_type], member.id))

        return embed

    @commands.Cog.listener()
    async def on_stage_instance_create(self, stage_instance):
        """Se déclenche lors de la création d'une instance de scène (conférence lancée)."""
        channel = self._get_log_channel("stage")
        if not channel:
            return

        # Récupérer le créateur depuis les logs d'audit
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            stage_instance.guild, None, [discord.AuditLogAction.stage_instance_create], time_window=10, limit=10
        )

        member = moderator or stage_instance.guild.me

        stage_channel = self.bot.get_channel(stage_instance.channel_id)
        if not stage_channel:
            return

        embed = self._create_stage_embed(member, "created", stage_channel, stage_instance.topic)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_stage_instance_delete(self, stage_instance):
        """Se déclenche lors de la suppression d'une instance de scène (conférence finie)."""
        log_channel = self._get_log_channel("stage")
        if not log_channel:
            return

        # Récupérer celui qui a arrêté la conférence depuis les logs d'audit
        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(
            stage_instance.guild, None, [discord.AuditLogAction.stage_instance_delete], time_window=10, limit=10
        )

        member = moderator or stage_instance.guild.me

        stage_channel = self.bot.get_channel(stage_instance.channel_id)
        if not stage_channel:
            return

        # Logger les intervenants qui quittent (speaker_removed)
        if isinstance(stage_channel, discord.StageChannel):
            for m in stage_channel.members:
                if not m.bot and m.voice and not m.voice.suppress:
                    embed = self._create_stage_embed(m, "speaker_removed", stage_channel)
                    await log_channel.send(embed=embed)

        embed = self._create_stage_embed(member, "deleted", stage_channel)
        await log_channel.send(embed=embed)

    # --- LISTENERS VOCAUX ---

    async def _process_move(self, member, channel_before, channel_after, voice_state, guild, log_channel):
        """Traite un déplacement vocal.

        Discord cumule les moves en une seule audit log entry (ex: "X moved 3 users to Channel").
        Le created_at de l'entry reste celui du PREMIER move de la cumulation.
        Strategy:
        1. Cache temps réel: match par proximité de timestamp (pour différencier les admins)
        2. API fallback: entry member_move la plus récente avec age < 120s
           (gère le cumul car l'entry reste valide pendant toute la session de cumulation)
        """
        moderator = None
        move_time = datetime.now(timezone.utc)

        for delay in [0.1, 0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0]:
            await asyncio.sleep(delay)

            async with self.move_lock:
                # 1. Cache temps réel (pour différencier les admins)
                best_diff = float('inf')
                best_mod = None
                for data in self.move_audit_cache.values():
                    diff = abs((data['created_at'] - move_time).total_seconds())
                    if diff < best_diff:
                        best_diff = diff
                        best_mod = data['moderator']

                if best_mod and best_diff < 10:
                    moderator = best_mod
                    break

                # 2. API: entry member_move la plus récente (< 120s)
                # Discord cumule les moves: l'entry reste valide tant que le cumul continue
                try:
                    now = datetime.now(timezone.utc)
                    async for entry in guild.audit_logs(limit=10, action=discord.AuditLogAction.member_move):
                        entry_time = entry.created_at
                        age = (now - entry_time).total_seconds()
                        if age < 120:
                            moderator = entry.user
                            break
                except Exception:
                    pass

            if moderator:
                break

        embed = self._create_voice_embed(
            member, "move",
            voice_channel=channel_after, voice_state=voice_state,
            channel_before=channel_before, channel_after=channel_after,
            moved_by=moderator
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Se déclenche lors d'un changement d'état vocal."""
        log_channel = self._get_log_channel("voice")
        if not log_channel:
            return

        # Ignorer les bots
        if member.bot:
            return

        current_time = datetime.now(timezone.utc)
        MOVE_TIMEOUT = 2

        # Connexion à un channel vocal
        if before.channel is None and after.channel is not None:
            # Annuler la tâche de leave en attente si elle existe
            if member.id in self.pending_leave_logs:
                self.pending_leave_logs[member.id].cancel()
                del self.pending_leave_logs[member.id]

            # Vérifier si c'est un déplacement (leave + join rapide)
            if member.id in self.voice_move_cache:
                move_data = self.voice_move_cache[member.id]
                del self.voice_move_cache[member.id]

                if (current_time - move_data["time"]).total_seconds() < MOVE_TIMEOUT:
                    asyncio.create_task(self._process_move(
                        member, move_data["channel"], after.channel, after,
                        member.guild, log_channel
                    ))
                    return

            # Connexion normale
            embed = self._create_voice_embed(member, "join", after.channel)
            await log_channel.send(embed=embed)
            return

        # Déconnexion d'un channel vocal
        if before.channel is not None and after.channel is None:
            # Si le membre était intervenant dans un stage, log "speaker_removed"
            if isinstance(before.channel, discord.StageChannel) and not before.suppress:
                stage_channel = self._get_log_channel("stage")
                if stage_channel:
                    embed = self._create_stage_embed(member, "speaker_removed", before.channel)
                    await stage_channel.send(embed=embed)

            self.voice_move_cache[member.id] = {
                "channel": before.channel,
                "time": current_time
            }

            async def log_leave_after_delay(m=member, b=before, lc=log_channel):
                try:
                    await asyncio.sleep(MOVE_TIMEOUT)
                    if m.id in self.voice_move_cache:
                        del self.voice_move_cache[m.id]
                        if m.id in self.pending_leave_logs:
                            del self.pending_leave_logs[m.id]

                        # Vérifier si c'est une déconnexion forcée (admin)
                        disconnected_by = None
                        leave_time = datetime.now(timezone.utc)

                        for delay in [0, 0.5, 1.0, 1.5, 2.0]:
                            await asyncio.sleep(delay)
                            # Chercher l'entry member_disconnect la plus proche du leave
                            best_diff = float('inf')
                            best_mod = None
                            best_key = None
                            for key, data in self.disconnect_cache.items():
                                diff = abs((data['created_at'] - leave_time).total_seconds())
                                if diff < best_diff:
                                    best_diff = diff
                                    best_mod = data['moderator']
                                    best_key = key

                            if best_mod and best_diff < 10:
                                disconnected_by = best_mod
                                del self.disconnect_cache[best_key]
                                break

                        # Fallback API si pas trouvé via le cache
                        if not disconnected_by:
                            try:
                                async for entry in m.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                                    entry_time = entry.created_at
                                    age = (datetime.now(timezone.utc) - entry_time).total_seconds()
                                    if age < 15:
                                        disconnected_by = entry.user
                                        break
                            except Exception:
                                pass

                        embed = self._create_voice_embed(m, "leave", voice_state=b, action_by=disconnected_by)
                        await lc.send(embed=embed)
                except asyncio.CancelledError:
                    pass

            task = asyncio.create_task(log_leave_after_delay())
            self.pending_leave_logs[member.id] = task
            return

        # Déplacement direct (quand le channel change dans le même événement)
        if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            asyncio.create_task(self._process_move(
                member, before.channel, after.channel, after,
                member.guild, log_channel
            ))
            return

        # Stream lancé
        if not before.self_stream and after.self_stream:
            voice_channel = after.channel or before.channel
            embed = self._create_voice_embed(member, "stream_start", voice_channel)
            await log_channel.send(embed=embed)
            return

        # Stream terminé
        if before.self_stream and not after.self_stream:
            embed = self._create_voice_embed(member, "stream_end")
            await log_channel.send(embed=embed)
            return

        # --- GESTION DES CONFÉRENCIERS (STAGE CHANNEL) ---
        current_channel = after.channel or before.channel
        if current_channel and isinstance(current_channel, discord.StageChannel):
            suppress_changed = before.suppress != after.suppress
            hand_cleared = (
                before.requested_to_speak_at is not None
                and after.requested_to_speak_at is None
            )

            # Étape 1 : Admin invite (main levée effacée, suppress inchangé)
            if hand_cleared and not suppress_changed:
                stage_channel = self._get_log_channel("stage")
                if stage_channel:
                    embed = self._create_stage_embed(member, "speaker_added", current_channel, invited_member=member)
                    await stage_channel.send(embed=embed)
                    return

            # Étape 2 : Suppress change
            if suppress_changed:
                stage_channel = self._get_log_channel("stage")
                if stage_channel:
                    if before.suppress and not after.suppress:
                        if hand_cleared:
                            # Admin a invité/déplacé le user (même event)
                            embed = self._create_stage_embed(member, "speaker_invited", current_channel, invited_member=member)
                        elif member.guild_permissions.administrator or member.guild_permissions.move_members:
                            # Admin/mod s'est mis intervenant lui-même
                            embed = self._create_stage_embed(member, "speaker_self", current_channel)
                        else:
                            # User normal a accepté l'invitation
                            embed = self._create_stage_embed(member, "speaker_invited", current_channel, invited_member=member)
                        await stage_channel.send(embed=embed)
                        return
                    elif not before.suppress and after.suppress:
                        embed = self._create_stage_embed(member, "speaker_removed", current_channel)
                        await stage_channel.send(embed=embed)
                        return

        # Server mute/deafen (par un admin)
        server_mute_changed = before.mute != after.mute
        server_deaf_changed = before.deaf != after.deaf

        if server_mute_changed or server_deaf_changed:
            # Trouver l'admin via le cache puis l'API
            moderator = None
            for delay in [0.5, 1.0, 1.5]:
                await asyncio.sleep(delay)
                best_diff = float('inf')
                best_mod = None
                best_key = None
                for key, data in self.server_mute_cache.items():
                    if data['target_id'] == member.id:
                        diff = abs((data['created_at'] - datetime.now(timezone.utc)).total_seconds())
                        if diff < best_diff:
                            best_diff = diff
                            best_mod = data['moderator']
                            best_key = key
                if best_mod and best_diff < 10:
                    moderator = best_mod
                    del self.server_mute_cache[best_key]
                    break

            # Fallback API
            if not moderator:
                try:
                    async for entry in member.guild.audit_logs(limit=10, action=discord.AuditLogAction.member_update):
                        entry_time = entry.created_at
                        age = (datetime.now(timezone.utc) - entry_time).total_seconds()
                        if age > 15:
                            break
                        if entry.target and entry.target.id == member.id:
                            moderator = entry.user
                            break
                except Exception:
                    pass

            voice_channel = after.channel or before.channel
            if server_deaf_changed:
                action = "deafen" if after.deaf else "undeafen"
                embed = self._create_voice_embed(member, action, voice_channel=voice_channel, action_by=moderator)
                await log_channel.send(embed=embed)
            if server_mute_changed:
                action = "mute" if after.mute else "unmute"
                embed = self._create_voice_embed(member, action, voice_channel=voice_channel, action_by=moderator)
                await log_channel.send(embed=embed)
            return

        # Changements d'état (mute, deaf, video) - self actions
        mute_changed = before.self_mute != after.self_mute
        deaf_changed = before.self_deaf != after.self_deaf
        video_changed = before.self_video != after.self_video

        if deaf_changed and mute_changed:
            mute_action = "mute" if after.self_mute else "unmute"
            deaf_action = "deafen" if after.self_deaf else "undeafen"
            embed = self._create_voice_embed(member, deaf_action)
            await log_channel.send(embed=embed)
            embed = self._create_voice_embed(member, mute_action)
            await log_channel.send(embed=embed)
            return

        if mute_changed:
            action = "mute" if after.self_mute else "unmute"
            embed = self._create_voice_embed(member, action)
            await log_channel.send(embed=embed)
            return

        if deaf_changed:
            action = "deafen" if after.self_deaf else "undeafen"
            embed = self._create_voice_embed(member, action)
            await log_channel.send(embed=embed)
            return

        if video_changed:
            action = "video" if after.self_video else "no_video"
            embed = self._create_voice_embed(member, action)
            await log_channel.send(embed=embed)
            return

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        """Cache en temps réel les entries member_move et member_disconnect."""
        if not entry.user:
            return

        if entry.action == discord.AuditLogAction.member_move:
            self.move_audit_cache[entry.id] = {
                'moderator': entry.user,
                'created_at': entry.created_at
            }
            # Nettoyer le cache (garder les 50 derniers)
            if len(self.move_audit_cache) > 50:
                keys = sorted(self.move_audit_cache.keys())
                for k in keys[:25]:
                    del self.move_audit_cache[k]

        elif entry.action == discord.AuditLogAction.member_disconnect:
            # member_disconnect n'a pas toujours entry.target, on stocke par entry.id
            self.disconnect_cache[entry.id] = {
                'moderator': entry.user,
                'created_at': entry.created_at
            }
            # Nettoyer le cache (supprimer les entrées de plus de 5 minutes)
            now = datetime.now(timezone.utc)
            to_remove = [k for k, v in self.disconnect_cache.items()
                         if (now - v['created_at']).total_seconds() > 300]
            for k in to_remove:
                del self.disconnect_cache[k]

        elif entry.action == discord.AuditLogAction.member_update:
            # Cache les member_update pour server mute/deafen
            if entry.target:
                self.server_mute_cache[entry.id] = {
                    'moderator': entry.user,
                    'target_id': entry.target.id,
                    'created_at': entry.created_at
                }
                # Nettoyer le cache (supprimer les entrées de plus de 5 minutes)
                now = datetime.now(timezone.utc)
                to_remove = [k for k, v in self.server_mute_cache.items()
                             if (now - v['created_at']).total_seconds() > 300]
                for k in to_remove:
                    del self.server_mute_cache[k]

        # Voice channel status — cacher l'auteur de l'action.
        # Action 192 = set/update du statut, action 193 = suppression/effacement du statut.
        # NOTE: en streaming temps réel, entry.user est fréquemment None (Discord ne
        # peuple pas les users comme en REST). On stocke donc user_id (toujours présent)
        # et on résout l'utilisateur plus tard via bot.get_user()/fetch_user().
        elif entry.action.value in (192, 193):
            target_id = getattr(entry, '_target_id', None)
            if target_id and entry.user_id:
                self.vc_status_mod_cache[target_id] = {
                    'user_id': entry.user_id,
                    'created_at': entry.created_at
                }
                # Nettoyer le cache (supprimer les entrées de plus de 5 minutes)
                now = datetime.now(timezone.utc)
                to_remove = [k for k, v in self.vc_status_mod_cache.items()
                             if (now - v['created_at']).total_seconds() > 300]
                for k in to_remove:
                    del self.vc_status_mod_cache[k]

    # --- LOGS STATUT CHANNEL VOCAL ---

    async def _parse_voice_channel_status_update(self, data):
        """Intercepte VOICE_CHANNEL_STATUS_UPDATE — déclencheur principal."""
        channel_id = int(data['id'])
        guild_id = int(data['guild_id'])
        status = data.get('status') or None

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(channel_id)
        if not channel or not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
            return

        # Auto-suppression Discord (channel vide), ignorer
        if not status and not channel.members:
            return

        # Modérateur : cache temps réel (rempli par on_audit_log_entry_create) puis
        # fallback API. On détecte l'action 192 (set/update) ET 193 (remove).
        # Le filtre created_at >= event_time exclut l'entry PRÉCÉDENTE (qui serait
        # sinon réutilisée à tort), car elle est antérieure à l'instant de détection.
        event_time = datetime.now(timezone.utc)
        mod_user_id = None
        for delay in [AUDIT_LOG_DELAY_SHORT, 0.3, 0.5, 1.0, 1.5, 2.0]:
            await asyncio.sleep(delay)

            # 1. Cache temps réel (rempli par on_audit_log_entry_create, stocke user_id)
            mod_info = self.vc_status_mod_cache.pop(channel_id, None)
            if mod_info:
                mod_user_id = mod_info['user_id']
                break

            # 2. Fallback API : entry créée APRÈS event_time, du bon channel.
            # On attend un peu plus avant de requêter l'API car Discord met du temps
            # à créer l'entry ; les premiers tours reposent sur le cache temps réel.
            try:
                async for entry in guild.audit_logs(limit=10):
                    if entry.action.value not in (192, 193):
                        continue
                    if getattr(entry, '_target_id', None) != channel_id:
                        continue
                    # N'accepter que l'entry de CETTE action (postérieure à event_time)
                    if entry.created_at >= event_time and entry.user_id:
                        mod_user_id = entry.user_id
                        break
            except Exception:
                pass

            if mod_user_id:
                break

        if not mod_user_id:
            return
            return

        # Résoudre l'utilisateur depuis user_id (cache bot puis API en fallback)
        moderator = self.bot.get_user(mod_user_id)
        if not moderator:
            try:
                moderator = await self.bot.fetch_user(mod_user_id)
            except discord.HTTPException:
                return

        if not moderator:
            return

        is_set = bool(status)
        action_key = "status_set" if is_set else "status_remove"
        log_channel = self._get_log_channel("voice")
        if not log_channel:
            return

        embed = discord.Embed(color=VOICE_COLORS[action_key])
        embed.set_author(name=moderator.display_name, icon_url=moderator.display_avatar.url)
        embed.description = (
            f'{CUSTOM_EMOJIS["vocstatutchannel"]} **{TEXTS[f"voice_{action_key}_title"]}**\n'
            f'{moderator.mention} {TEXTS[f"voice_{action_key}_desc"]} {channel.mention}'
        )

        if is_set:
            embed.add_field(name=TEXTS["voice_status_label"], value=str(status), inline=False)

        embed.set_footer(text=self._footer(f"voice_{action_key}", moderator.id))

        await log_channel.send(embed=embed)

    # --- LOGS ÉVÉNEMENTS ---

    def _build_event_embed(self, color, description, event=None, user=None, log_type="event_edited"):
        """Construit un embed standard pour les logs d'événements."""
        embed = discord.Embed(color=color)
        embed.set_author(
            name=user.display_name if user else TEXTS["unknown"],
            icon_url=user.display_avatar.url if user else None
        )
        embed.description = description
        if event and event.cover_image:
            embed.set_thumbnail(url=event.cover_image.url)
        if user:
            embed.set_footer(text=self._footer(log_type, user.id))
        elif event:
            embed.set_footer(text=self._footer_custom(log_type, "Event ID", event.id))
        return embed

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        """Se déclenche quand un événement est créé."""
        if not event.guild:
            return

        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(event.guild, event.id, [discord.AuditLogAction.scheduled_event_create], limit=50)
        user = moderator or event.creator

        embed = self._build_event_embed(
            EVENT_COLORS["created"],
            f'{EVENT_EMOJIS["created"]} **{TEXTS["event_created_title"]}**\n\n'
            f"L'évènement [{event.name}]({event.url}) a été créé par {user.mention if user else TEXTS['unknown']}",
            event=event, user=user, log_type="event_created"
        )

        description = event.description or TEXTS["event_no_description"]
        embed.add_field(name=TEXTS["event_description_field"], value=truncate_content(description), inline=False)
        embed.add_field(name=TEXTS["event_location_field"], value=get_event_location_str(event), inline=False)
        start_ts = int(event.start_time.timestamp())
        embed.add_field(name=TEXTS["event_start_field"], value=f"<t:{start_ts}:F> | **<t:{start_ts}:R>**", inline=False)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        """Se déclenche quand un événement est supprimé."""
        if not event.guild:
            return

        channel = self._get_log_channel("action")
        if not channel:
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(event.guild, event.id, [discord.AuditLogAction.scheduled_event_delete], limit=50)

        embed = self._build_event_embed(
            EVENT_COLORS["deleted"],
            f'{EVENT_EMOJIS["deleted"]} **{TEXTS["event_deleted_title"]}**\n\n'
            f"L'évènement `{event.name}` a été supprimé par {moderator.mention if moderator else TEXTS['unknown']}",
            user=moderator, log_type="event_deleted"
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before, after):
        """Se déclenche quand un événement est modifié."""
        if not after.guild:
            return

        channel = self._get_log_channel("action")
        if not channel:
            return

        has_name = before.name != after.name
        has_desc = (before.description or "") != (after.description or "")
        has_start = before.start_time != after.start_time
        has_end = before.end_time != after.end_time
        has_loc = get_event_location_str(before) != get_event_location_str(after)
        has_type = before.entity_type != after.entity_type
        has_cover = before._cover_image != after._cover_image
        has_status_start = before.status != after.status and after.status == discord.EventStatus.active
        has_status_stop = before.status != after.status and after.status in (discord.EventStatus.completed, discord.EventStatus.canceled)

        if not (has_name or has_desc or has_start or has_end or has_loc or has_type or has_cover or has_status_start or has_status_stop):
            return

        await asyncio.sleep(AUDIT_LOG_DELAY_DEFAULT)
        moderator = await self._get_moderator_from_audit_log(after.guild, after.id, [discord.AuditLogAction.scheduled_event_update], limit=50)
        mod_mention = moderator.mention if moderator else TEXTS["unknown"]

        if has_status_start:
            await channel.send(embed=self._build_event_embed(
                EVENT_COLORS["created"],
                f'{EVENT_EMOJIS["created"]} L\'évènement **[{after.name}]({after.url})** a été lancé par {mod_mention}',
                event=after, user=moderator, log_type="event_started"
            ))

        if has_status_stop:
            await channel.send(embed=self._build_event_embed(
                EVENT_COLORS["deleted"],
                f'{EVENT_EMOJIS["deleted"]} L\'évènement **[{after.name}]({after.url})** a été arrêté par {mod_mention}',
                event=after, user=moderator, log_type="event_stopped"
            ))

        if has_cover:
            action = TEXTS["event_cover_removed"] if after._cover_image is None else TEXTS["event_cover_added"]
            await channel.send(embed=self._build_event_embed(
                EVENT_COLORS["edited"],
                f'{EVENT_EMOJIS["edited"]} L\'image de l\'évènement **[{after.name}]({after.url})** a été {action} par {mod_mention}',
                event=after, user=moderator,
                log_type="event_cover_removed" if after._cover_image is None else "event_cover_added"
            ))

        has_content = has_name or has_desc or has_start or has_end or has_loc or has_type
        if not has_content:
            return

        desc = (
            f'{EVENT_EMOJIS["edited"]} **{TEXTS["event_edited_title"]}**\n\n'
            f"L'évènement [{after.name}]({after.url}) a été modifié par {mod_mention}"
        )

        embed = self._build_event_embed(EVENT_COLORS["edited"], desc, event=after, user=moderator)

        if has_name:
            embed.add_field(name=TEXTS["event_new_name_field"], value=f"`{after.name}`", inline=False)
        if has_desc:
            description = after.description or TEXTS["event_no_description"]
            embed.add_field(name=TEXTS["event_new_description_field"], value=truncate_content(description), inline=False)
        if has_loc:
            embed.add_field(name=TEXTS["event_new_location_field"], value=get_event_location_str(after), inline=False)
        if has_start:
            start_ts = int(after.start_time.timestamp())
            embed.add_field(name=TEXTS["event_new_start_field"], value=f"<t:{start_ts}:F> | **<t:{start_ts}:R>**", inline=False)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))
