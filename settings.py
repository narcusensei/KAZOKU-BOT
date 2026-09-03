import discord

# ==============================================================
#                        K4ZK-BOT SETTINGS
#           Modifiez les valeurs ici pour personnaliser le bot
# ==============================================================


# ======================== BOT ================================

BOT_PREFIX = "+"

BOT_ACTIVITY_TYPE = discord.ActivityType.listening
BOT_ACTIVITY_NAME = "narcus 👑"

BOT_FOOTER = "𝘒4𝘡𝘖𝘒𝘜 © 2026"

TOKEN_ENV_VAR = "DISCORD_TOKEN"


# ===================== CHANNEL IDS ===========================

LOG_CHANNELS = {
    "sanction": 1245708015861108807,
    "member":   1353501264557903892,
    "message":  1353501353548189707,
    "voice":    1353501399673213008,
    "stage":    1353501399673213008,  # Même channel que voice
    "action":   1493690708417052723,
    "file":     1353501728330354799,
    "server":   1353501830205931622,
    "channel":  1353502124096491635,
    "roles":    1518186113578045490,
    "command":  1532487860199096450,
    "giveaway": 1544354898160652289
}


# ===================== COULEURS ==============================
# Palette : Vert (positif) • Rouge (négatif) • Jaune/Or (neutre) • Violet (spécial)
#   discord.Color(int("00FF00", 16))  → Vert
#   discord.Color(int("FF0000", 16))  → Rouge
#   discord.Color(int("FFD700", 16))  → Jaune / Or
#   discord.Color(int("800080", 16))  → Violet

# --- Couleurs des sanctions ---
SANCTION_COLORS = {
    "Ban":           discord.Color(int("FF0000", 16)),  # Rouge
    "Unban":         discord.Color(int("00FF00", 16)),  # Vert
    "Kick":          discord.Color(int("FF0000", 16)),  # Rouge
    "Mute":          discord.Color(int("FF0000", 16)),  # Rouge
    "Unmute":        discord.Color(int("00FF00", 16)),  # Vert
    "Avertissement": discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleurs vocales ---
VOICE_COLORS = {
    "join":         discord.Color(int("00FF00", 16)),  # Vert
    "leave":        discord.Color(int("FF0000", 16)),  # Rouge
    "stream_start": discord.Color(int("800080", 16)),  # Violet
    "stream_end":   discord.Color(int("800080", 16)),  # Violet
    "mute":         discord.Color(int("FF0000", 16)),  # Rouge
    "unmute":       discord.Color(int("00FF00", 16)),  # Vert
    "deafen":       discord.Color(int("FF0000", 16)),  # Rouge
    "undeafen":     discord.Color(int("00FF00", 16)),  # Vert
    "video":        discord.Color(int("00FF00", 16)),  # Vert
    "no_video":     discord.Color(int("FF0000", 16)),  # Rouge
    "move":          discord.Color(int("800080", 16)),  # Violet
    "status_set":    discord.Color(int("00FF00", 16)),  # Vert
    "status_remove": discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs stage / conférence ---
STAGE_COLORS = {
    "created": discord.Color(int("00FF00", 16)),  # Vert
    "edited":  discord.Color(int("FFD700", 16)),  # Jaune
    "deleted": discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs membres ---
MEMBER_COLORS = {
    "bot_join":    discord.Color(int("00FF00", 16)),  # Vert
    "bot_leave":   discord.Color(int("FF0000", 16)),  # Rouge
    "join":        discord.Color(int("00FF00", 16)),  # Vert
    "leave":       discord.Color(int("FF0000", 16)),  # Rouge
    "role_add":    discord.Color(int("00FF00", 16)),  # Vert
    "role_remove": discord.Color(int("FF0000", 16)),  # Rouge
    "nick_change": discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleurs des logs messages ---
MESSAGE_COLORS = {
    "deleted":      discord.Color(int("FF0000", 16)),  # Rouge
    "edited":       discord.Color(int("FFD700", 16)),  # Jaune
    "bulk_delete":  discord.Color(int("FF0000", 16)),  # Rouge
    "poll_deleted": discord.Color(int("FF0000", 16)),  # Rouge
    "pin":          discord.Color(int("00FF00", 16)),  # Vert
    "unpin":        discord.Color(int("FF0000", 16)),  # Rouge
    "reaction":     discord.Color(int("FF0000", 16)),  # Rouge
    "file_deleted": discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs threads ---
THREAD_COLORS = {
    "created":   discord.Color(int("00FF00", 16)),  # Vert
    "deleted":   discord.Color(int("FF0000", 16)),  # Rouge
    "updated":   discord.Color(int("FFD700", 16)),  # Jaune
    "locked":    discord.Color(int("FF0000", 16)),  # Rouge
    "unlocked":  discord.Color(int("00FF00", 16)),  # Vert
    "closed":    discord.Color(int("FF0000", 16)),  # Rouge
    "reopened":  discord.Color(int("00FF00", 16))   # Vert
}

# --- Couleurs des logs channels ---
CHANNEL_COLORS = {
    "created":   discord.Color(int("00FF00", 16)),  # Vert
    "deleted":   discord.Color(int("FF0000", 16)),  # Rouge
    "edited":    discord.Color(int("FFD700", 16)),  # Jaune
    "permission_created": discord.Color(int("00FF00", 16)),  # Vert
    "permission_deleted": discord.Color(int("FF0000", 16)),  # Rouge
    "permission_edited":  discord.Color(int("FFD700", 16)),  # Jaune
    "followed":           discord.Color(int("800080", 16)),  # Violet
    "followed_updated":   discord.Color(int("800080", 16)),  # Violet
    "unfollowed":         discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs rôles ---
ROLE_COLORS = {
    "created":  discord.Color(int("00FF00", 16)),  # Vert
    "deleted":  discord.Color(int("FF0000", 16)),  # Rouge
    "edited":   discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleurs des logs webhooks ---
WEBHOOK_COLORS = {
    "created":  discord.Color(int("00FF00", 16)),  # Vert
    "deleted":  discord.Color(int("FF0000", 16)),  # Rouge
    "edited":   discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleurs des logs invitations ---
INVITE_COLORS = {
    "created":  discord.Color(int("00FF00", 16)),  # Vert
    "modified": discord.Color(int("FFD700", 16)),  # Jaune
    "deleted":  discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs emojis ---
EMOJI_COLORS = {
    "added":   discord.Color(int("00FF00", 16)),  # Vert
    "removed": discord.Color(int("FF0000", 16)),  # Rouge
    "edited":  discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleurs des logs soundboard ---
SOUNDBOARD_COLORS = {
    "added":     discord.Color(int("00FF00", 16)),  # Vert
    "modified":  discord.Color(int("FFD700", 16)),  # Jaune
    "removed":   discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs stickers ---
STICKER_COLORS = {
    "created":  discord.Color(int("00FF00", 16)),  # Vert
    "modified": discord.Color(int("FFD700", 16)),  # Jaune
    "deleted":  discord.Color(int("FF0000", 16))   # Rouge
}

# --- Couleurs des logs événements ---
EVENT_COLORS = {
    "created":  discord.Color(int("00FF00", 16)),  # Vert
    "deleted":  discord.Color(int("FF0000", 16)),  # Rouge
    "edited":   discord.Color(int("FFD700", 16))   # Jaune
}

# --- Couleur liste sanctions ---
SANCTIONLIST_COLOR = discord.Color(int("800080", 16))  # Violet

# --- Couleur des logs giveaway ---
GIVEAWAY_COLOR = discord.Color(int("B821FF", 16))  # Violet

# --- Couleurs serveur ---
SERVER_COLORS = {
    "edited":       discord.Color(int("FFD700", 16)),  # Jaune
    "boost_add":    discord.Color(int("00FF00", 16)),  # Vert
    "boost_remove": discord.Color(int("FF0000", 16)),  # Rouge
    "booster_add":  discord.Color(int("00FF00", 16)),  # Vert
    "booster_remove": discord.Color(int("FF0000", 16))  # Rouge
}

# --- Couleur par défaut (fallback) ---
DEFAULT_COLOR = discord.Color(int("FFD700", 16))  # Jaune


# ================== EMOJIS CUSTOM ===========================
# Format : "<:nom:ID>"
# Remplacez les IDs par les vôtres si vous changez de serveur.

CUSTOM_EMOJIS = {
    # Sanctions
    "sanction_red":    "<:sanctionred:1488276069298606110>",
    "sanction_green":  "<:sanctiongreen:1488276067352318023>",
    "sanction_yellow": "<:sanctionyellow:1488276077179834488>",

    # Vocal
    "mic_mute":              "<:micmute:1488276063258808381>",
    "mic_unmute":            "<:micunmute:1488276064361906206>",
    "headphone_deactivated": "<:headphonedesactivated:1488276051003048067>",
    "headphone_activated":   "<:headphoneactivated:1488276049539240076>",
    "cam_activated":         "<:camactivated:1488276046628524092>",
    "cam_deactivated":       "<:camdesactivated:1488276047849066729>",
    "stream_on":             "<:streamon:1488276084846755880>",
    "stream_off":            "<:streamoff:1488276083366428822>",
    "voc_join":              "<:vocjoin:1488276095919849583>",
    "voc_leave":             "<:vocleave:1488276097601638501>",
    "vocstatutchannel":      "<:vocstatutchannel:1500902263411970100>",

    # Stage / Conférence
    "stage_created": "<:stagecreated:1488276079771914252>",
    "stage_edited":  "<:stageedited:1488276082011406377>",
    "stage_deleted": "<:stagedeleted:1488276081025880286>",

    # Invitations
    "invite_created":  "<:invitecreated:1493694938028970076>",
    "invite_deleted":  "<:invitedeleted:1493694940188770344>",

    # Emojis
    "emoji_added":        "<:emojiadded:1494018343139803286>",
    "emoji_removed":      "<:emojiremoved:1494018344674660422>",
    "emoji_edited":       "<:emojiedited:1500077061434511400>",

    # Soundboard
    "soundboard_added":   "<:soundboardadded:1494075887220424866>",
    "soundboard_removed": "<:soundboardremoved:1494075888814395564>",
    "soundboard_edited":  "<:soundboardedited:1494082062737604889>",

    # Stickers
    "sticker_created": "<:stickerscreated:1495387030178234525>",
    "sticker_edited":  "<:stickeredited:1495387032284041437>",
    "sticker_deleted": "<:stickerdeleted:1495387031206105189>",

    # Événements
    "event_created":  "<:eventcreated:1498798030701334679>",
    "event_deleted":  "<:eventdeleted:1498798031657631956>",
    "event_edited":   "<:eventedited:1498798033054335137>",

    # Messages
    "message_pin":     "<:messagepin:1488276060654145536>",
    "message_unpin":   "<:messageunpin:1488276061887402117>",
    "message_deleted":        "<:messagedeleted:1488276058355535962>",
    "message_edited":         "<:messageedited:1488276059634798784>",
    "attachment_deleted":     "<:attachementdeleted:1502367605007057126>",
    "server_edited":          "<:serveredited:1502613232072921201>",
    "reaction_remove": "<:reactionremove:1488276065355956285>",

    # Boost
    "boost_added":    "<:boostadded:1508147530662281357>",
    "boost_removed":  "<:boostremoved:1508147532591661196>",
    "booster":        "<:boost:1508147529219440801>",

    # Membres
    "bot_join":       "<:botjoin:1488276044225183896>",
    "bot_leave":      "<:botleave:1488276045042946109>",
    "member_join":    "<:membersjoin:1488276054710816838>",
    "member_leave":   "<:membersleave:1488276056292200548>",
    "member_edited":  "<:membersedited:1488276053280423956>",

    # Threads
    "thread_created":       "<:threadcreated:1488276087380119582>",
    "thread_deleted":       "<:threaddeleted:1488276089049583757>",
    "thread_edited":        "<:threadedited:1488276090429636669>",
    "thread_lock":          "<:threadlock:1488276093013065928>",
    "thread_unlock":        "<:threadunlock:1488276094745575565>",
    "thread_close":         "<:threadclose:1488276086113571047>",
    "slowmode":             "<:slowmode:1488276078630797352>",
    "inactive_period":      "<:inactivedperiod:1488276052299088115>",

    # Channels
    "channel_created":            "<:channelcreated:1518282522411274362>",
    "channel_deleted":            "<:channeldeleted:1518282524038795324>",
    "channel_edited":             "<:channeledited:1518282525191962696>",
    "channel_permission_created": "<:channelpermissioncreated:1518283209585197169>",
    "channel_permission_deleted": "<:channelpermissiondeleted:1518283210935767161>",
    "channel_permission_edited":  "<:channelpermissionedited:1518283212038602762>",
    "channel_followed":           "<:channelfollowed:1518283313117135098>",
    "channel_followed_updated":   "<:channelfollowedupdated:1518283314337939527>",
    "channel_unfollowed":         "<:channelunfollowed:1518283315331989515>",

    # Webhooks
    "webhook_created": "<:webhookcreated:1518283426690629723>",
    "webhook_deleted": "<:webhookdeleted:1518283427831611394>",
    "webhook_edited":  "<:webhookedited:1518283429291233463>",
    "webhook_updated": "<:webhookupdated:1518283430675218602>",

    # Rôles
    "role_created":            "<:rolescreated:1528414817927299226>",
    "role_deleted":            "<:rolesdeleted:1528414819164754012>",
    "role_edited":             "<:rolesedited:1528414820859379732>",
    "role_permission_edited":  "<:rolespermissionedited:1528414821710827560>",
    "role_added":              "<:rolesadded:1528414816811749396>",
    "role_removed":            "<:rolesremoved:1528414822696489120>",

    # Permissions / Statut
    "neutral": "<:neutral:1521250990307934449>",
    "deny":    "<:deny:1521250989070356490>",
    "allow":   "<:allow:1521250987669721298>",

    # Commandes
    "command_used": "<:command:1532490948766859264>",
    "info":         "<:info:1543917767521206322>",

    # Giveaway
    "giveaway":     "<:giveaway:1536503849823637594>",
    "winner":       "<:winner:1543961179968245862>",
    "participant":  "<:participant:1543961178726866964>",
}


# ================ EMOJIS UNICODE ============================
# Emojis standards utilisés dans les embeds et réponses.

SANCTION_EMOJIS = {
    "Ban":           "⛔",
    "Unban":         "🔓",
    "Kick":          "👞",
    "Mute":          "🔇",
    "Unmute":        "🔊",
    "Avertissement": "⚠️"
}

UNICODE_EMOJIS = {
    "ping":    "🏓",
    "check":   "✅",
    "cross":   "❌",
    "warning": "⚠️",
    "pin":     "📌",
    "package": "📦",
    "refresh": "🔄",
    "trash":   "🗑️",
    "party":   "🎉"
}


# ================== TEXTES ===================================
# Tous les textes affichés dans les embeds et messages.

TEXTS = {
    # --- Commandes base ---
    "ping_response":           "Pong ! Latence :",
    "profile_error":           "Une erreur est survenue lors de l'affichage du profil.",
    "profile_no_roles":        "Aucun rôle",
    "profile_not_on_server":   "Inconnu (Pas sur le serveur)",
    "profile_off_server":      "Membre hors serveur",
    "sync_success":            "✅ Sync effectué !",
    "sync_error":              "❌ Erreur lors de la synchronisation.",

    # --- Profil fields ---
    "profile_identity":        "Identité",
    "profile_info":            "Information",
    "profile_dates":           "Dates",
    "profile_username":        "Pseudo :",
    "profile_id":              "ID :",
    "profile_roles":           "Rôles :",
    "profile_discord_since":   "Membre Discord depuis :",
    "profile_server_since":    "Membre Serveur depuis :",

    # --- Modération : erreurs ---
    "permission_denied":                "Permission refusée.",
    "missing_permission":               "Permission manquante.",
    "internal_error":                   "Erreur interne.",
    "no_role_for_command":              "Tu n'as pas le rôle nécessaire pour utiliser /{command_name}.",
    "cannot_sanction_owner":            "Tu ne peux pas sanctionner le propriétaire du serveur !",
    "cannot_sanction_higher":           "Tu ne peux pas sanctionner {target} (rôle supérieur ou égal).",
    "bot_cannot_sanction":              "Je ne peux pas sanctionner {target} (mon rôle est trop bas).",
    "clear_amount_error":               "Le nombre doit être entre {min} et {max}.",
    "clear_error":                      "Erreur lors de la suppression.",
    "mute_error":                       "Erreur lors du mute.",
    "unmute_error":                     "Erreur lors de l'unmute.",
    "kick_error":                       "Erreur lors du kick.",
    "ban_error":                        "Erreur lors du ban.",
    "unban_error":                      "Erreur lors de l'unban.",
    "user_not_found":                   "Utilisateur introuvable.",
    "user_not_on_server":               "Cet utilisateur n'est pas sur le serveur.",
    "user_not_banned":                  "Cet utilisateur n'est pas banni.",
    "ban_check_error":                  "Erreur lors de la vérification du ban.",
    "invalid_id":                       "L'ID doit être un nombre.",
    "no_duration":                      "Tu dois définir une durée.",
    "self_mute":                        "Tu ne peux pas te mute toi-même.",
    "cannot_warn_bot":                  "Impossible d'avertir un bot.",

    # --- Modération : sanctions ---
    "mute_title":                       "[MUTE]",
    "mute_description":                 "a été mute pour {dur}.",
    "mute_reason":                      "Raison",
    "sanction_by":                      "Par {name}",
    "unmute_title":                     "[UNMUTE]",
    "unmute_description":               "a été unmute.",
    "unmute_reason":                    "Fin du timeout",
    "kick_title":                       "[KICK]",
    "kick_description":                 "a été kické.",
    "ban_title":                        "[BAN]",
    "ban_description":                  "a été banni.",
    "unban_title":                      "[UNBAN]",
    "unban_description":                "a été débanni.",
    "avert_title":                      "[AVERTISSEMENT]",
    "avert_description":                "a été averti. (Total: {count})",
    "avert_dm_title":                   "⚠️ AVERTISSEMENT",
    "avert_dm_description":             "Tu as reçu un avertissement sur **{guild}**.",
    "clear_success":                    "✅ Suppression de {n} message(s).",

    # --- Modération : sanctionliste ---
    "sanctionlist_title":               "Sanctions de {name}",
    "sanctionlist_empty":               "Aucune sanction. 🎉",
    "sanctionlist_reason":              "Raison :",
    "sanctionlist_by":                  "Par :",
    "select_placeholder":               "Sélectionne une sanction à supprimer...",
    "select_delete_specific":           "🗑️ Supprimer une sanction spécifique",
    "select_delete_all":                "⚠️ Supprimer TOUTES les sanctions",
    "sanction_deleted":                 "✅ La sanction **{type}** a été effacée.",
    "sanction_not_found":               "❌ Erreur : Sanction introuvable.",
    "no_sanctions_to_delete":           "Aucune sanction (Ban/Kick/Mute/Avert) à supprimer.",
    "choose_sanction":                  "Choisis la sanction à effacer ci-dessous :",
    "all_sanctions_deleted":            "✅ Toutes les sanctions ont été supprimées.",
    "nothing_to_delete":                "Il n'y a rien à supprimer.",
    "data_read_error":                  "Erreur de lecture du fichier.",
    "data_save_error":                  "Erreur lors de la sauvegarde.",

    # --- Logs : divers ---
    "command_used_title":               "COMMANDE UTILISÉE",
    "info_title":                       "INFO COMMANDE",
    "command_used_desc":                "Une commande modération à été utilisé",
    "command_name_field":               "Commande",
    "unknown":                          "Inconnu",
    "none":                             "Aucune",
    "slowmode_disabled":                "Désactivé",
    "empty_content":                    "*(Contenu vide ou image)*",
    "jump_to_message":                  "Aller au message",

    # --- Logs : pins ---
    "pin_action":                       "MESSAGE ÉPINGLÉ",
    "unpin_action":                     "MESSAGE DÉSÉPINGLÉ",
    "pinned_by":                        "Épinglé par",
    "unpinned_by":                      "Désépinglé par",
    "message_field":                    "Message",
    "message_author":                   "Auteur du message",

    # --- Logs : sanctions ---
    "user_field":                       "Utilisateur",
    "moderator_field":                  "Modérateur",
    "reason_field":                     "Raison",
    "mute_end_field":                   "Fin du Mute",
    "unknown_moderator":                "Inconnu",
    "no_reason":                        "Aucune",

    # --- Logs : vocal ---
    "voice_join_title":                 "CONNEXION VOCAL",
    "voice_join_desc":                  "a rejoint un vocal",
    "voice_leave_title":                "DÉCONNEXION VOCAL",
    "voice_leave_desc":                 "a quitté un vocal",
    "voice_kicked_desc":                "a été déconnecté du vocal",
    "voice_mute_title":                 "MICRO DÉSACTIVÉ",
    "voice_mute_self_desc":             "a désactivé son micro",
    "voice_mute_server_desc":           "a été rendu muet",
    "voice_unmute_title":               "MICRO ACTIVÉ",
    "voice_unmute_self_desc":           "a activé son micro",
    "voice_unmute_server_desc":         "a été démuté",
    "voice_deafen_title":               "CASQUE DÉSACTIVÉ",
    "voice_deafen_self_desc":           "a désactivé son casque",
    "voice_deafen_server_desc":         "a été mis en sourdine",
    "voice_undeafen_title":             "CASQUE ACTIVÉ",
    "voice_undeafen_self_desc":         "a activé son casque",
    "voice_undeafen_server_desc":       "a été sorti de la sourdine",
    "voice_video_on_title":             "CAMÉRA ACTIVÉE",
    "voice_video_on_desc":              "a activé sa caméra",
    "voice_video_off_title":            "CAMÉRA DÉSACTIVÉE",
    "voice_video_off_desc":             "a désactivé sa caméra",
    "voice_stream_start_title":         "STREAM LANCÉ",
    "voice_stream_start_desc":          "a lancé un stream",
    "voice_stream_end_title":           "STREAM TERMINÉ",
    "voice_stream_end_desc":            "a terminé son stream",
    "voice_move_title":                 "DÉPLACÉ",
    "voice_move_desc":                  "a été déplacé de",
    "voice_move_to":                    "vers",
    "voice_moved_by":                   "Déplacé par",
    "voice_channel":                    "Channel",
    "voice_information":                "Information",
    "voice_disconnected_by":            "Déconnecté par",
    "voice_muted_by":                   "Muet par",
    "voice_unmuted_by":                 "Démuté par",
    "voice_deafened_by":                "Casque désactivé par",
    "voice_undeafened_by":              "Casque activé par",
    "voice_action_by":                  "Action par",
    "voice_status_set_title":           "STATUT CHANNEL VOCAL AJOUTÉ",
    "voice_status_set_desc":            "à défini le statut du channel",
    "voice_status_remove_title":        "STATUT CHANNEL VOCAL RETIRÉ",
    "voice_status_remove_desc":         "à retiré le statut du channel",
    "voice_status_label":               "Statut",

    # --- Logs : serveur ---
    "server_edited_title":              "SERVEUR MODIFIÉ",
    "server_name_field":                "Nom",
    "server_description_field":         "Description",
    "server_verification_field":        "Niveau De Vérification",
    "server_content_filter_field":      "Filtre de contenu explicite",
    "server_notifications_field":       "Notification par défaut",
    "server_afk_field":                 "AFK",
    "server_afk_timeout_change":        "Le délai a été modifié",
    "server_afk_channel_change":        "Le channel a été modifié",
    "server_system_channel_field":      "Salon système",
    "server_system_channel_change":     "Channel système",
    "server_system_flag_join_notif":    "Message d'accueil aléatoire lorsque quelqu'un rejoint ce serveur",
    "server_system_flag_join_reply":    "Répondre aux messages de bienvenue avec un autocollant",
    "server_system_flag_premium":       "Message lorsque quelqu'un booste ce serveur",
    "server_system_flag_reminder":      "Infos utiles pour la configuration du serveur",
    "server_system_enabled":            "Activé",
    "server_system_disabled":           "Désactivé",

    # --- Logs : boost ---
    "boost_add_title":                  "AJOUT BOOST SERVEUR",
    "boost_remove_title":               "RETRAIT BOOST SERVEUR",
    "booster_title":                    "BOOSTER",
    "boost_count_added_field":          "Nombre de boost ajouté",
    "boost_count_removed_field":        "Nombre de boost retiré",
    "boost_level_field":                "Niveau de boost",
    "boost_total_field":                "Nombre de boost",
    "boost_add_desc":                   "boost le serveur",
    "boost_remove_desc":                "ne boost plus le serveur",
    "boost_add_field":                  "Ajout Boost",
    "boost_remove_field":               "Retrait Boost",

    # --- Logs : membres ---
    "member_bot_join_title":            "BOT AJOUTÉ",
    "member_bot_join_desc":             "a été ajouté par",
    "member_join_title":                "ARRIVÉE",
    "member_join_desc":                 "a rejoint",
    "member_no_avatar_warning":         "ATTENTION!",
    "member_no_avatar":                 "Pas d'avatar",
    "member_rejoin":                    "Rejoint le serveur",
    "member_new_account":               "Nouveau compte",
    "member_account_created":           "Compte Créé",
    "member_bot_leave_title":           "BOT RETIRÉ",
    "member_leave_title":               "DÉPART",
    "member_leave_desc":                "a quitté",
    "member_joined_at":                 "A rejoint",
    "member_roles":                     "Rôles",
    "member_role_add_title":            "RÔLES AJOUTÉS",
    "member_role_remove_title":         "RÔLES RETIRÉS",
    "member_role_add_one_desc":         "Un rôle à été ajouté pour {user}",
    "member_role_add_many_desc":        "Des rôles ont été ajoutés pour {user}",
    "member_role_remove_one_desc":      "Un rôle à été retiré pour {user}",
    "member_role_remove_many_desc":     "Des rôles ont été retirés pour {user}",
    "member_role_field":                "Rôle(s)",
    "member_by":                        "Par",
    "member_nick_title":                "NOM MODIFIÉ",
    "member_nick_old":                  "Ancien",
    "member_nick_new":                  "Nouveau",
    "member_no_nick":                   "Aucun",
    "member_timeout_manual":            "Timeout manuel",
    "member_timeout_removed":           "Timeout retiré",

    # --- Logs : messages ---
    "message_deleted_title":            "MESSAGE SUPPRIMÉ",
    "message_bulk_delete_title":        "MESSAGE SUPPRIMÉ (Clear)",
    "message_edited_title":             "MESSAGE ÉDITÉ",
    "message_before":                   "Avant",
    "message_after":                    "Après",
    "message_channel":                  "Channel",
    "message_go":                       "Aller",
    "message_deleted_by":               "Supprimé par",
    "message_author_field":             "Auteur",
    "message_channel_field":            "Channel",
    "message_file":                     "Fichier",
    "message_image":                    "Image :",
    "message_attachment":               "Fichier :",
    "file_deleted_title":               "PIECE JOINTE SUPPRIMÉE",
    "file_deleted_name_field":          "Nom",
    "file_deleted_from_field":          "Fichier de",
    "file_deleted_channel_field":       "Channel",
    "message_clear_command":            "Commande /clear",

    # --- Logs : sondages ---
    "poll_deleted":                     "Sondage Supprimé",
    "poll_unknown_question":            "Question inconnue",
    "poll_name_field":                  "NomDuSondage",
    "poll_multichoice":                 "Choix multiple",
    "poll_enabled":                     "Activé",
    "poll_disabled":                    "Désactivé",
    "poll_end_field":                   "Fin",
    "poll_no_expiry":                   "Aucune",
    "poll_author":                      "Auteur du sondage",
    "poll_answers":                     "Réponses",
    "poll_votes":                       "Votes",
    "poll_votes_unit":                  "votes",
    "poll_deleted_by":                  "Supprimé par",

    # --- Logs : réactions ---
    "reaction_removed":                 "Réaction retirée",
    "reaction_removed_desc":            "a retiré une réaction d'un message",
    "reaction_emoji":                   "Emoji",

    # --- Logs : threads ---
    "thread_created_desc":              "Création d'un fil",
    "thread_created_text":              "a créé un nouveau fil",
    "thread_deleted_title":             "FIL SUPPRIMÉ",
    "thread_deleted_text":              "a supprimé un fil",
    "thread_deleted_unknown":           "Fil supprimé",
    "thread_modified_title":            "FIL MODIFIÉ",
    "thread_locked_title":              "FIL VÉRROUILLÉ",
    "thread_unlocked_title":            "FIL DÉVERROUILLÉ",
    "thread_closed_title":              "FIL FERMÉ",
    "thread_reopened_title":            "FIL ROUVERT",

    # --- Logs : stage / conférence ---
    "stage_created_title":              "CONFÉRENCE LANCÉ",
    "stage_created_desc":               "a lancé une conférence",
    "stage_speaker_added_title":        "NOUVEL INTERVENANT",
    "stage_speaker_invited_title":      "INVITATION CONFÉRENCIÈR",
    "stage_deleted_title":              "CONFÉRENCE FINI",
    "stage_deleted_desc":               "a été arrêtée par",
    "stage_speaker_removed_title":      "DISCUSSION QUITTÉE",
    "stage_speaker_removed_desc":       "n'est plus conférencier",
    "stage_channel_type":               "Channel Conférence",
    "voice_channel_type":               "Channel Vocal",

    # --- Logs : champs génériques ---
    "link_field":                       "Lien",
    "method_field":                     "Méthode",
    "info_field":                       "Info",
    "action_field":                     "Action",
    "thread_field":                     "Fil",
    "none_value":                       "Aucun",
    "none_value_f":                     "Aucune",
    "system_fallback":                  "Système",
    "manual_action":                    "Action manuelle",
    "countdown_prefix":                 "Dans **<t:{ts}:R>**",
    "state_enabled":                    "Activé",
    "state_disabled":                   "Désactivé",
    "new_name":                         "Nouveau nom",
    "new_emoji":                        "Nouvel emoji",
    "new_emoji_id":                     "Nouvel emoji ID",
    "new_description":                  "Nouvelle description",

    # --- Logs : bannière serveur ---
    "server_banner_changed":            "Bannière changée",
    "server_banner_added":              "Bannière ajoutée",
    "server_banner_removed":            "Bannière retirée",

    # --- Logs : événement cover ---
    "event_cover_removed":              "retiré",
    "event_cover_added":                "ajouté",

    # --- Logs : notifications serveur ---
    "server_notif_all":                 "Tous les messages",
    "server_notif_mentions":            "Uniquement les mentions",

    # --- Logs : soundboard ---
    "soundboard_removed_title":         "SOUNDBOARD RETIRÉ",

    # --- Logs : raisons internes ---
    "member_leave_normal_reason":       "Normal",
    "member_kick_reason":               "Kick",
    "member_ban_reason":                "Ban",

    # --- Logs : stage speaker_self ---
    "stage_speaker_self_title":         "NOUVEL INTERVENANT",
    "stage_speaker_self_desc":          "est devenu intervenant dans",
    "topic_field":                      "**Sujet**",

    # --- Logs : threads avancé ---
    "modification_field":               "Modification",
    "multiple_modifications_desc":      "a effectué plusieurs modifications :",

    # --- Logs : archive ---
    "archive_1h":                       "1 heure",
    "archive_24h":                      "24 heures",
    "archive_3d":                       "3 jours",
    "archive_1w":                       "1 semaine",

    # --- Logs : invitations ---
    "invite_created_title":             "INVITATION CRÉÉE",
    "invite_created_desc":              "à créé une invitation",
    "invite_deleted_title":             "INVITATION SUPPRIMÉ",
    "invite_deleted_desc":              "à supprimé une invitation",
    "invite_link_field":                "Lien",
    "invite_channel_field":             "Channel",
    "invite_expiration_field":          "Expiration",
    "invite_never_expires":             "Jamais",
    "invite_unknown_inviter":           "Inconnu",
    "invite_uses_field":                "Utilisation",
    "invite_created_by_field":          "Créé par",

    # --- Logs : webhooks ---
    "webhook_created_title":            "WEBHOOK CRÉÉ",
    "webhook_deleted_title":            "WEBHOOK SUPPRIMÉ",
    "webhook_updated_title":            "WEBHOOK MODIFIÉ",
    "webhook_created_desc":             "Le webhook **{name}** à été créé",
    "webhook_deleted_desc":             "Le webhook **{name}** à été supprimé",
    "webhook_updated_desc":             "Le webhook **{name}** à été modifié",
    "webhook_moved_desc":               "Le webhook **{name}** à été déplacé",
    "webhook_name_field":               "Nom",
    "webhook_channel_field":            "Channel",
    "webhook_by_field":                 "Par",

    # --- Logs : webhooks avatar ---
    "webhook_avatar_added_title":       "WEBHOOK AVATAR AJOUTÉ",
    "webhook_avatar_updated_title":     "WEBHOOK AVATAR MODIFIÉ",
    "webhook_avatar_removed_title":     "WEBHOOK AVATAR RETIRÉ",
    "webhook_avatar_added_desc":        "L'avatar du webhook **{name}** à été ajouté",
    "webhook_avatar_updated_desc":      "L'avatar du webhook **{name}** à été modifié",
    "webhook_avatar_removed_desc":      "L'avatar du webhook **{name}** à été retiré",

    # --- Logs : giveaway ---
    "giveaway_id_field":                "ID Giveaway",
    "giveaway_ends_field":              "Fin dans",
    "giveaway_ends_log_field":          "Fin",
    "giveaway_created_by":              "Créé par",
    "giveaway_participants":            "Participation(s)",
    "giveaway_winners":                 "Gagnant(s)",
    "giveaway_no_winners":              "Aucun",

    # --- Giveaway : commandes ---
    "giveaway_button_join":             "Participer",
    "giveaway_open_form_button":        "Ouvrir le formulaire",
    "giveaway_form_title":              "Créer un Giveaway",
    "giveaway_form_time_label":         "Temps (ex: 30s, 10min, 1h, 2jours)",
    "giveaway_form_winners_label":      "Nombre de gagnants",
    "giveaway_form_prize_label":        "Récompense",
    "giveaway_form_desc_label":         "Description (1000 caractères max)",
    "giveaway_time_invalid":            "Temps invalide. Formats acceptés : 30s, 10min, 1h, 2jours",
    "giveaway_winners_invalid":         "Le nombre de gagnants doit être un nombre ≥ 1",
    "giveaway_desc_too_long":           "La description ne peut pas dépasser 1000 caractères",
    "giveaway_created_ok":              "✅ Giveaway #{gid} créé !",
    "giveaway_create_error":            "❌ Erreur lors de la création du giveaway.",
    "giveaway_not_found":               "❌ Giveaway #{gid} introuvable",
    "giveaway_not_ended":               "❌ Ce giveaway n'est pas encore terminé.",
    "giveaway_already_ended":           "❌ Ce giveaway est déjà terminé",
    "giveaway_ended_ok":                "✅ Giveaway #{gid} terminé !",
    "giveaway_deleted_ok":              "✅ Giveaway #{gid} supprimé !",
    "giveaway_rerolled_ok":             "✅ Nouveau tirage effectué pour le giveaway #{gid} !",
    "giveaway_join_ok":                 "✅ Tu participes au giveaway **{prize}** !",
    "giveaway_leave_ok":                "❌ Ta participation au giveaway **{prize}** à été retirée.",
    "giveaway_msg_title":               "GIVEAWAY — {prize}",
    "giveaway_msg_ended_title":         "GIVEAWAY TERMINÉ — {prize}",
    "giveaway_msg_deleted_title":       "GIVEAWAY SUPPRIMÉ — {prize}",
    "giveaway_winners_announce":        "🎉 Félicitation {winners} !! Tu as gagné **{prize}** !!",
    "giveaway_winners_announce_many":   "🎉 Félicitation {winners} !! Vous avez gagné **{prize}** !!",
    "giveaway_stopped_announce":        "Le Giveaway à été arrêté par conséquent aucun gagnant n'a été désigné.",
    "giveaway_deleted_announce":        "🗑️ Le Giveaway **{prize}** à été supprimé avec succès",
    "giveaway_reroll_announce":         "🔄 {admin} à relancé le Giveaway | 🎉 Félicitation {winners}",
    "giveaway_no_participants":         "Aucun participant",

    # --- Logs : rôles serveur ---
    "role_created_title":               "RÔLE CRÉÉ",
    "role_deleted_title":               "RÔLE SUPPRIMÉ",
    "role_edited_title":                "RÔLE MODIFIÉ",
    "role_created_desc":                "Le rôle `{name}` à été créé",
    "role_deleted_desc":                "Le rôle `{name}` à été supprimé",
    "role_edited_desc":                 "Le rôle `{name}` à été modifié",
    "role_name_field":                  "Nom",
    "role_color_field":                 "Couleur",
    "role_hoist_field":                 "Affiché séparément",
    "role_mentionable_field":           "Mentionnable",
    "role_yes":                         "Oui",
    "role_no":                          "Non",
    "role_field":                       "Rôle",
    "role_icon_title":                  "ICÔNE RÔLE MODIFIÉ",
    "role_icon_added_desc":             "L'icône du rôle {role} à été ajouté",
    "role_icon_updated_desc":           "L'icône du rôle {role} à été modifié",
    "role_icon_removed_desc":           "L'icône du rôle {role} à été supprimé",
    "role_perms_title":                 "PERMISSIONS RÔLE MODIFIÉ",
    "role_perms_desc":                  "Les permissions du rôle {role} ont été modifiées",
    "role_perms_danger_title":          "⚠️ DANGER !!!",
    "role_perms_danger_desc":           "Permissions dangereuse(s) ajoutée(s)",

    # --- Logs : channels ---
    "channel_created_title":            "CHANNEL {type} CRÉÉ",
    "channel_created_desc":             "Le channel {channel} à été créé par {moderator}",
    "channel_created_in_category":      " dans la catégorie {category}",
    "channel_deleted_title":            "CHANNEL {type} SUPPRIMÉ",
    "channel_edited_title":             "CHANNEL {type} MODIFIÉ",
    "category_edited_title":            "CATÉGORIE MODIFIÉE",
    "channel_edited_desc":              "Le channel {channel} à été modifié",
    "category_edited_desc":             "La catégorie {channel} à été modifiée",
    "channel_no_category":              "Aucune",
    "channel_unlimited":                "Illimité",
    "channel_prop_name":                "Nom",
    "channel_prop_topic":               "Description",
    "channel_prop_slowmode":            "Mode lent",
    "channel_prop_archive":             "Masquer après inactivité",
    "channel_prop_category":            "Catégorie",
    "channel_prop_nsfw":                "NSFW",
    "channel_prop_bitrate":             "Débit",
    "channel_prop_userlimit":           "Limite utilisateurs",
    "channel_deleted_desc":             "Le channel {channel} à été supprimé par {moderator}",
    "category_created_title":           "CATÉGORIE CRÉÉE",
    "category_deleted_title":           "CATÉGORIE SUPPRIMÉE",
    "category_created_desc":            "La catégorie {channel} à été créée par {moderator}",
    "category_deleted_desc":            "La catégorie {channel} à été supprimée par {moderator}",
    "channel_deleted_in_category":      " dans la catégorie {category}",
    "channel_type_text":                "TEXTE",
    "channel_type_voice":               "VOCAL",
    "channel_type_forum":               "FORUM",
    "channel_type_news":                "ANNONCE",
    "channel_type_stage":               "CONFÉRENCE",
    "channel_type_category":            "CATÉGORIE",
    "channel_type_unknown":             "INCONNU",
    "channel_field":                    "Channel",

    # --- Logs : permissions de channel ---
    "channel_perm_created_title":       "PERMISSIONS AJOUTÉES",
    "channel_perm_deleted_title":       "PERMISSIONS RETIRÉES",
    "channel_perm_updated_title":       "PERMISSIONS MODIFIÉES",
    "channel_perm_old_field":           "Ancienne(s) permission(s)",
    "channel_perm_new_field":           "Nouvelle(s) permission(s)",
    "channel_perm_for_role":            "pour le rôle",

    # --- Logs : emojis ---
    "emoji_added_title":                "EMOJI CRÉÉ",
    "emoji_removed_title":              "EMOJI SUPPRIMÉ",
    "emoji_edited_title":               "EMOJI MODIFIÉ",
    "emoji_name_field":                 "Nom",
    "emoji_id_field":                   "ID",

    # --- Logs : soundboard ---
    "soundboard_added_title":           "SOUNDBOARD AJOUTÉ",
    "soundboard_modified_title":        "SOUNDBOARD MODIFIÉ",
    "soundboard_modified_by":           "Modifié par",

    # --- Logs : stickers ---
    "sticker_created_title":            "STICKERS CRÉÉ",
    "sticker_modified_title":           "STICKERS MODIFIÉ",
    "sticker_deleted_title":            "STICKERS SUPPRIMÉ",
    "sticker_emoji_id_field":           "Emoji ID",
    "sticker_description_field":        "Description",
    "sticker_modified_by":              "Modifié par",

    # --- Logs : événements ---
    "event_created_title":              "ÉVÉNEMENT CRÉÉ",
    "event_deleted_title":              "ÉVÉNEMENT SUPPRIMÉ",
    "event_edited_title":               "ÉVÉNEMENT MODIFIÉ",
    "event_description_field":          "Description",
    "event_start_field":                "Date/Heure",
    "event_location_field":             "Emplacement",
    "event_no_description":             "Aucune description",
    "event_new_name_field":             "Nouveau nom",
    "event_new_description_field":      "Nouvelle description",
    "event_new_location_field":         "Nouvel emplacement",
    "event_new_start_field":            "Nouvelle date/heure",
}


# ============ TRADUCTION DES PERMISSIONS =====================
# Mapping nom technique discord.py -> nom français lisible.
# Utilisé pour les logs de permissions de channel.

PERMISSION_LABELS_FR = {
    "administrator":                "Administrateur",
    "view_audit_log":               "Voir les logs d'audit",
    "view_guild_insights":          "Voir les analyses du serveur",
    "manage_guild":                 "Gérer le serveur",
    "change_nickname":              "Changer de pseudo",
    "manage_nicknames":             "Gérer les pseudos",
    "kick_members":                 "Expulser des membres",
    "ban_members":                  "Bannir des membres",
    "moderate_members":             "Exclure temporairement (timeout)",
    "create_expressions":           "Créer des expressions",
    "manage_expressions":           "Gérer les expressions",
    "manage_emojis":                "Gérer les emojis",
    "manage_emojis_and_stickers":   "Gérer les emojis et stickers",
    "manage_events":                "Gérer les événements",
    "create_events":                "Créer des événements",
    "view_creator_monetization_analytics": "Voir les analyses de monétisation",
    "manage_webhooks":              "Gérer les webhooks",
    "view_channel":                 "Voir le salon",
    "read_messages":                "Lire les messages",
    "read_message_history":         "Voir l'historique des messages",
    "send_messages":                "Envoyer des messages",
    "send_tts_messages":            "Envoyer des messages TTS",
    "send_polls":                   "Envoyer des sondages",
    "create_polls":                 "Créer des sondages",
    "embed_links":                  "Intégrer des liens",
    "attach_files":                 "Joindre des fichiers",
    "mention_everyone":             "Mentionner @\u200beveryone/@\u200bhere",
    "external_emojis":              "Utiliser des emojis externes",
    "use_external_emojis":          "Utiliser des emojis externes",
    "external_stickers":            "Utiliser des stickers externes",
    "use_external_stickers":        "Utiliser des stickers externes",
    "add_reactions":                "Ajouter des réactions",
    "use_external_apps":            "Utiliser des apps externes",
    "use_application_commands":     "Utiliser les commandes d'application",
    "manage_messages":              "Gérer les messages",
    "manage_threads":               "Gérer les fils",
    "create_public_threads":        "Créer des fils publics",
    "create_private_threads":       "Créer des fils privés",
    "send_messages_in_threads":     "Envoyer des messages dans les fils",
    "pin_messages":                 "Épingler des messages",
    "manage_channels":              "Gérer le salon",
    "manage_permissions":           "Gérer les permissions",
    "manage_roles":                 "Gérer les rôles",
    "create_instant_invite":        "Créer une invitation",
    "send_voice_messages":          "Envoyer des messages vocaux",
    "use_soundboard":               "Utiliser le soundboard",
    "use_external_sounds":          "Utiliser des sons externes",
    "priority_speaker":             "Haut-parleur prioritaire",
    "stream":                       "Partager son écran",
    "connect":                      "Se connecter",
    "speak":                        "Parler",
    "use_voice_activation":         "Utiliser la détection de voix",
    "mute_members":                 "Rendre muet (voix)",
    "deafen_members":               "Mettre en sourdine (voix)",
    "move_members":                 "Déplacer des membres",
    "request_to_speak":             "Demander à parler",
    "use_embedded_activities":      "Utiliser les activités",
    "set_voice_channel_status":     "Définir le statut du salon vocal",
    "bypass_slowmode":              "Contourner le mode lent",
}


# ============ PERMISSIONS DANGEREUSES =======================
# Permissions considérées comme critiques/sensibles : si l'une d'elles est
# ajoutée à un rôle, une alerte "DANGER" est affichée dans le log.
DANGEROUS_PERMISSIONS = {
    "administrator",
    "manage_guild",
    "manage_channels",
    "manage_roles",
    "manage_webhooks",
    "manage_messages",
    "manage_threads",
    "manage_expressions",
    "manage_events",
    "ban_members",
    "kick_members",
    "moderate_members",
    "view_audit_log",
    "view_guild_insights",
    "mention_everyone",
    "view_creator_monetization_analytics",
}


# =============== PERMISSIONS =================================
# Rôles autorisés par commande.
# "+" = Owner/Admin, "~" = Modérateur, "-" = Helper

PERMISSIONS = {
    "kick":          ["+", "~", "-"],
    "ban":           ["+", "~"],
    "mute":          ["+", "~", "-"],
    "avert":         ["+", "~", "-"],
    "clear":         ["+", "~", "-"],
    "sanctionliste": ["+", "~", "-"],
    "unban":         ["+"],
    "unmute":        ["+", "~"],

    # Giveaway
    "createg":       ["+", "~"],
    "startg":        ["+", "~"],
    "endg":          ["+", "~"],
    "deletedg":      ["+", "~"],
    "rerollg":       ["+", "~"],

    # Dev
    "sync":          ["+"]
}

SANCTION_TYPES = ["Ban", "Kick", "Mute", "Avertissement"]


# ================ DATA PATHS ================================

DATA_DIR = "data"
WARNINGS_FILE = "data/warnings.json"
MEMBERS_FILE = "data/members.json"
GIVEAWAYS_FILE = "data/giveaways.json"


# ============= LOG TYPE IDS ==================================
# Chaque type de log possède un ID FIXE et DÉFINITIF (#L1, #L2, ...).
# L'ID identifie le TYPE de log : tous les logs "ban" portent #L1, tous les
# logs "voice_join" portent #L2, etc. L'ID est attitré une fois pour toutes
# et ne change jamais (ne pas réordonner ni réutiliser les numéros).
#
# Pour ajouter un nouveau type : ajouter une entrée avec un nouveau numéro.

LOG_TYPE_IDS = {
    # --- Sanctions (#L1 - #L6) ---
    "sanction_ban":           1,
    "sanction_unban":         2,
    "sanction_kick":          3,
    "sanction_mute":          4,
    "sanction_unmute":        5,
    "sanction_avert":         6,

    # --- Vocal (#L7 - #L19) ---
    "voice_join":             7,
    "voice_leave":            8,
    "voice_kick":             9,
    "voice_stream_start":    10,
    "voice_stream_end":      11,
    "voice_mute_self":       12,
    "voice_mute_server":     13,
    "voice_unmute_self":     14,
    "voice_unmute_server":   15,
    "voice_deafen_self":     16,
    "voice_deafen_server":   17,
    "voice_undeafen_self":   18,
    "voice_undeafen_server": 19,

    # --- Vocal : video / move (#L20 - #L22) ---
    "voice_video_on":        20,
    "voice_video_off":       21,
    "voice_move":            22,

    # --- Stage / Conférence (#L23 - #L28) ---
    "stage_created":          23,
    "stage_deleted":          24,
    "stage_speaker_added":    25,
    "stage_speaker_invited":  26,
    "stage_speaker_self":     27,
    "stage_speaker_removed":  28,

    # --- Statut channel vocal (#L29 - #L30) ---
    "voice_status_set":       29,
    "voice_status_remove":    30,

    # --- Membres (#L31 - #L37) ---
    "member_bot_join":        31,
    "member_join":            32,
    "member_bot_leave":       33,
    "member_leave":           34,
    "member_role_add":        35,
    "member_role_remove":     36,
    "member_nick_change":     37,

    # --- Boost (#L38 - #L41) ---
    "booster_add":            38,
    "booster_remove":         39,
    "boost_add":              40,
    "boost_remove":           41,

    # --- Messages (#L42 - #L49) ---
    "message_delete":         42,
    "poll_deleted":           43,
    "file_deleted":           44,
    "message_edit":           45,
    "message_pin":            46,
    "message_unpin":          47,
    "bulk_message_delete":    48,
    "reaction_remove":        49,

    # --- Serveur (#L50) ---
    "server_edited":          50,

    # --- Threads (#L51 - #L53) ---
    "thread_create":          51,
    "thread_delete":          52,
    "thread_update":          53,
    "thread_locked":          83,
    "thread_unlocked":        84,
    "thread_closed":          85,
    "thread_reopened":        86,

    # --- Channels (#L54 - #L55) ---
    "channel_create":         54,
    "channel_delete":         55,

    # --- Channels permissions (#L74 - #L76) ---
    "channel_permission_create":  74,
    "channel_permission_delete":  75,
    "channel_permission_update":  76,

    # --- Webhooks (#L77 - #L79) ---
    "webhook_create":         77,
    "webhook_delete":         78,
    "webhook_update":         79,

    # --- Webhooks avatar (#L80 - #L82) ---
    "webhook_avatar_added":   80,
    "webhook_avatar_updated": 81,
    "webhook_avatar_removed": 82,

    # --- Rôles serveur (#L87 - #L89) ---
    "role_create":            87,
    "role_delete":            88,
    "role_update":            89,
    "role_icon_added":        90,
    "role_icon_updated":      91,
    "role_icon_removed":      92,
    "role_perms":             93,

    # --- Commandes modération (#L94) ---
    "command_used":           94,

    # --- Channel edité (#L95) ---
    "channel_edit":           95,

    # --- Info commande (#L96) ---
    "info":                   96,

    # --- Giveaway (#L97) ---
    "giveaway":               97,

    # --- Invitations (#L56 - #L57) ---
    "invite_create":          56,
    "invite_delete":          57,

    # --- Emojis (#L58 - #L60) ---
    "emoji_added":            58,
    "emoji_removed":          59,
    "emoji_edited":           60,

    # --- Stickers (#L61 - #L63) ---
    "sticker_created":        61,
    "sticker_deleted":        62,
    "sticker_modified":       63,

    # --- Soundboard (#L64 - #L66) ---
    "soundboard_added":       64,
    "soundboard_removed":     65,
    "soundboard_modified":    66,

    # --- Événements (#L67 - #L73) ---
    "event_created":          67,
    "event_deleted":          68,
    "event_started":          69,
    "event_stopped":          70,
    "event_cover_added":      71,
    "event_cover_removed":    72,
    "event_edited":           73,
}


# ============= LIMITES NUMÉRIQUES ===========================

# Profil
MAX_ROLES_DISPLAY = 10
MAX_ROLES_LENGTH = 1000
ROLES_TRUNCATE_SUFFIX = "..."

# Modération
MAX_CLEAR_AMOUNT = 100
MIN_CLEAR_AMOUNT = 1
MAX_SANCTIONS_DISPLAY = 10
MAX_SANCTIONS_SELECT = 24

# Logs
AUDIT_LOG_TIMEOUT = 5
AUDIT_LOG_LIMIT = 100
THREAD_REOPEN_THRESHOLD = 120  # secondes
CONTENT_MAX_LENGTH = 1000  # < 1024 : laisse la marge pour les préfixes de formatage (">>> " etc.)

# Sauvegarde proactive des pièces jointes (pour les logs de suppression)
# Le bot met en cache les fichiers des messages pour pouvoir les restaurer
# après suppression (individuelle ou en masse type ban).
# ATTENTION : consomme de la mémoire. MAX_ATTACHMENT_CACHE_SIZE borne le cache.
MAX_ATTACHMENT_CACHE_SIZE = 500   # nombre maximum de messages mis en cache
ATTACHMENT_CACHE_TTL = 3600       # durée de vie en secondes (1h)
MAX_ATTACHMENT_FILE_SIZE = 8_000_000  # taille max par fichier (8 Mo) - on ignore les gros fichiers

# Délais d'attente (en secondes) pour la disponibilité des audit logs Discord.
# Discord crée les entries audit log avec un léger décalage ; ces sleeps permettent
# de les retrouver de façon fiable. Ajuster si les logs "modérateur" sont souvent vides.
AUDIT_LOG_DELAY_SHORT = 0.5   # Actions quasi-immédiates (pin, vc status)
AUDIT_LOG_DELAY_DEFAULT = 1.0 # Délai standard (la plupart des listeners)
AUDIT_LOG_DELAY_LONG = 1.5    # Cas sensibles (guild_update fallback)
AUDIT_LOG_DELAY_SLOW = 2.0    # Actions lentes à apparaître (stickers, soundboard)


# ============= FONCTIONS UTILITAIRES =========================

def truncate_text(text: str, max_len: int, suffix: str = "...") -> str:
    """Tronque un texte si nécessaire."""
    return text[:max_len - len(suffix)] + suffix if len(text) > max_len else text
