# Copyright (c) 2026 narcus
# SPDX-License-Identifier: AGPL-3.0-only

"""Tests des parseurs et helpers purs — aucun réseau, aucun bot requis.

Lancement (depuis la racine du repo, venv avec requirements-dev) : `pytest`
"""

from datetime import timedelta

import discord

from settings import (
    truncate_text, PERMISSIONS, ROLE_ADMIN, ROLE_MODO, ROLE_HELPER,
)
from cogs.giveaway import parse_duration
from cogs.moderation import format_duration
from cogs.reactionrole import parse_emoji_arg, reaction_key_from_partial
from cogs.reminder import format_interval
from cogs.logs_helpers import (
    format_slowmode, format_archive, format_invite_duration,
    _log_id_for, _color_name_fr, create_fake_user,
)


# --- parse_duration (giveaways / rappels) ---

def test_parse_duration_valid():
    assert parse_duration("30s") == timedelta(seconds=30)
    assert parse_duration("10min") == timedelta(minutes=10)
    assert parse_duration("1h") == timedelta(hours=1)
    assert parse_duration("2jours") == timedelta(days=2)
    assert parse_duration("5j") == timedelta(days=5)
    assert parse_duration("1seconde") == timedelta(seconds=1)
    assert parse_duration("2 Days") == timedelta(days=2)  # insensible à la casse
    assert parse_duration("31jours") == timedelta(days=31)  # borne max incluse


def test_parse_duration_invalid():
    assert parse_duration("0s") is None          # zéro interdit
    assert parse_duration("32j") is None         # > 31 jours
    assert parse_duration("1h30") is None        # format composé non supporté
    assert parse_duration("abc") is None
    assert parse_duration("") is None
    assert parse_duration("-5min") is None       # négatif
    assert parse_duration(" forever") is None


# --- format_duration (modération) ---

def test_format_duration():
    assert format_duration(1, 2, 3) == "1h 2m 3s"
    assert format_duration(2, 0, 0) == "2h"
    assert format_duration(0, 30, 0) == "30m"
    assert format_duration(0, 0, 5) == "5s"
    assert format_duration(0, 0, 0) == "0s"


# --- parse_emoji_arg / reaction_key_from_partial (rôles à réaction) ---

WELove_ID = "827923754283075584"

def test_parse_emoji_arg_custom_full():
    key, fmt = parse_emoji_arg(f"<:welove:{WELove_ID}>")
    assert key == f"welove:{WELove_ID}"
    assert fmt == f"<:welove:{WELove_ID}>"


def test_parse_emoji_arg_animated():
    key, fmt = parse_emoji_arg(f"<a:welove:{WELove_ID}>")
    assert key == f"welove:{WELove_ID}"
    assert fmt == f"<a:welove:{WELove_ID}>"


def test_parse_emoji_arg_compact():
    # Format compact "nom:ID" (sans chevrons) accepté
    key, fmt = parse_emoji_arg(f"welove:{WELove_ID}")
    assert key == f"welove:{WELove_ID}"
    assert fmt == f"<:welove:{WELove_ID}>"


def test_parse_emoji_arg_unicode():
    assert parse_emoji_arg("🎮") == ("🎮", "🎮")


def test_parse_emoji_arg_invalid():
    assert parse_emoji_arg(WELove_ID) == (None, None)   # un ID seul n'est pas un émoji
    assert parse_emoji_arg("<:welove:123>") == (None, None)  # ID trop court + chevrons
    assert parse_emoji_arg("émoji trop long") == (None, None)  # > 12 chars


def test_reaction_key_roundtrip():
    """La clé produite par la commande add doit matcher celle du listener raw."""
    key_cmd, _ = parse_emoji_arg(f"<a:welove:{WELove_ID}>")
    payload_emoji = discord.PartialEmoji(name="welove", id=int(WELove_ID), animated=True)
    key_listener = reaction_key_from_partial(payload_emoji)
    assert key_cmd == key_listener == f"welove:{WELove_ID}"


def test_reaction_key_unicode():
    assert reaction_key_from_partial(discord.PartialEmoji(name="🎮")) == "🎮"


# --- format_interval (rappels) ---

def test_format_interval():
    assert format_interval(timedelta(minutes=30)) == "30min"
    assert format_interval(timedelta(hours=2)) == "2h"
    assert format_interval(timedelta(hours=1, minutes=30)) == "1h 30min"
    assert format_interval(timedelta(days=2, hours=3)) == "2j 3h"
    assert format_interval(timedelta(days=1)) == "1j"


# --- truncate_text (settings) ---

def test_truncate_text():
    assert truncate_text("abc", 8) == "abc"
    assert truncate_text("abcdefgh", 8) == "abcdefgh"   # borne exacte inchangée
    assert truncate_text("hello world", 8) == "hello..."
    assert truncate_text("", 5) == ""


# --- helpers logs (cogs/logs_helpers.py) ---

def test_format_slowmode():
    assert format_slowmode(0) == "Désactivé"
    assert format_slowmode(45) == "45s"
    assert format_slowmode(120) == "2m"
    assert format_slowmode(3600) == "1h"
    assert format_slowmode(5400) == "1h 30m"


def test_format_archive():
    assert format_archive(60) == "1 heure"
    assert format_archive(1440) == "24 heures"
    assert format_archive(4320) == "3 jours"
    assert format_archive(10080) == "1 semaine"
    assert format_archive(100) == "100 minutes"   # valeur hors presets


def test_format_invite_duration():
    assert format_invite_duration(0) == "Jamais"
    assert format_invite_duration(45) == "45s"
    assert format_invite_duration(90) == "1m"
    assert format_invite_duration(3600) == "1h"
    assert format_invite_duration(5400) == "1h 30m"
    assert format_invite_duration(90000) == "1j 1h"
    assert format_invite_duration(172800) == "2j"


def test_log_id_for():
    assert _log_id_for("sanction_ban") == "#L001"
    assert _log_id_for("reaction_role_removeall") == "#L108"
    assert _log_id_for("type_inconnu") == "#L000"


def test_color_name_fr():
    assert _color_name_fr(0) == "Aucune"
    assert _color_name_fr(0xFF0000) == "Rouge"
    assert _color_name_fr(0x00FF00) == "Vert"
    assert _color_name_fr(0xFFD700) == "Or"
    assert _color_name_fr(0xFFFFFF) == "Blanc"
    # Ambiguïté assumée : 0 = couleur par défaut Discord ET noir pur → "Aucune"
    assert _color_name_fr(0x000000) == "Aucune"
    assert _color_name_fr(0xFF00FF) == "Magenta"
    assert _color_name_fr(0x800080) == "Violet"
    assert _color_name_fr(0x5865F2) == "Blurple"   # bleu Discord


def test_create_fake_user():
    u = create_fake_user(123, "Quelqu'un")
    assert u.id == 123
    assert u.mention == "<@123>"
    assert u.display_name == "Quelqu'un"
    assert u.display_avatar.url is None


# --- intégrité de la matrice de permissions (settings) ---

def test_permissions_matrix():
    assert len(PERMISSIONS) == 18
    # Uniquement des IDs de rôles (int) — plus aucun nom
    for cmd, roles in PERMISSIONS.items():
        assert roles, f"{cmd} : liste vide"
        for r in roles:
            assert isinstance(r, int), f"{cmd} : {r!r} n'est pas un ID de rôle"
    # Commandes critiques réservées Admin
    assert PERMISSIONS["unban"] == [ROLE_ADMIN]
    assert PERMISSIONS["sync"] == [ROLE_ADMIN]
    # Le Helper ne mute/avertit/efface que via ces trois commandes
    helper_cmds = {c for c, roles in PERMISSIONS.items() if ROLE_HELPER in roles}
    assert helper_cmds == {"mute", "avert", "clear"}
    # Toutes les commandes modérées incluent au moins Admin ou Modo
    for cmd in ("kick", "ban", "sanctionliste", "unmute", "gcreate", "gstart",
                "gend", "gdelete", "greroll", "reminder", "reminderlist",
                "embed", "reactionrole"):
        assert ROLE_ADMIN in PERMISSIONS[cmd] and ROLE_MODO in PERMISSIONS[cmd], cmd
