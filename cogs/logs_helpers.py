# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

"""Helpers purs du cog Logs : fonctions et mappings sans état runtime.

Extraits de cogs/logs.py pour alléger le monolithe. cogs/logs.py les réimporte
(et donc les ré-exporte) : `from cogs.logs import get_timestamp, _log_id_for`
continue de fonctionner pour les autres cogs.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from settings import (
    CUSTOM_EMOJIS, TEXTS, LOG_TYPE_IDS, CONTENT_MAX_LENGTH, truncate_text,
)

# --- CONSTANTES LOCALES (non configurables) ---
TZ_PARIS = ZoneInfo("Europe/Paris")

STAGE_EMOJIS = {
    "created": CUSTOM_EMOJIS["stage_created"],
    "edited":  CUSTOM_EMOJIS["stage_edited"],
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


def get_voice_state_status(voice_state) -> str:
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


def get_event_location_str(event) -> str:
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
# Noms de permissions de rôle à EXCLURE (alias redondants) — on garde le nom
# correspondant à l'interface Discord (un seul par bit réel).
_PERMISSION_EXCLUDED = {
    "read_messages",
    "external_emojis",
    "manage_permissions",
    "manage_emojis",
    "manage_emojis_and_stickers",
    "external_stickers",
    "send_polls",
}
