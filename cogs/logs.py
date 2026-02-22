import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

# --- CONFIGURATION DES CHANNELS DE LOGS ---
# Mets l'ID du salon où les logs doivent s'envoyer
LOG_CHANNELS = {
    "sanction": 1245708015861108807  # <--- REMPLACE PAR L'ID DE TON SALON SANCTION
}
# -------------------------------------

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, interaction, action_type, target, moderator, reason, duration_str=None, end_time=None):
        """Fonction centrale pour envoyer un log structuré"""
        channel_id = LOG_CHANNELS.get("sanction")

        # On ne log que si l'ID est configuré
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"Erreur : Channel de log non trouvé pour l'ID {channel_id}")
            return

        # --- CONFIGURATION DU STYLE ---
        # Définition des emojis et couleurs selon l'action
        colors = {
            "Ban": discord.Color.red(),
            "Unban": discord.Color.green(),
            "Kick": discord.Color.orange(),
            "Mute": discord.Color.gold(),
            "Unmute": discord.Color.blue(),
            "Avertissement": discord.Color.light_gray()
        }

        emojis = {
            "Ban": "⛔",
            "Unban": "🔓",
            "Kick": "👞",
            "Mute": "🔇",
            "Unmute": "🔊",
            "Avertissement": "⚠️"
        }

        color = colors.get(action_type, discord.Color.blue())
        emoji = emojis.get(action_type, "📝")

        # --- CRÉATION DE L'EMBED ---
        embed = discord.Embed(color=color)

        # Titre : logo + Username (Author du embed)
        embed.set_author(name=f"{target.global_name or target.name} ({action_type})", icon_url=target.display_avatar.url)

        # Description : Emojis + Nom de l'action
        embed.description = f"{emoji} **{action_type.upper()}**"

        # --- CHAMPS : USER & MODÉRATEUR (Inline pour mettre côte à côte) ---
        # Cela crée le tableau demandé : User | Modérateur
        embed.add_field(name="Utilisateur", value=f"<@{target.id}>", inline=True)
        embed.add_field(name="Modérateur", value=f"<@{moderator.id}>", inline=True)

        # --- RAISON ---
        embed.add_field(name="Raison", value=reason or "Aucune", inline=False)

        # --- INFOS SPÉCIFIQUES (Mute) ---
        if action_type == "Mute" and end_time:
            # Calcul du temps restant si possible, ou affichage brut
            embed.add_field(name="Fin du Mute", value=f"🔔 {end_time.strftime('%d/%m/%Y %H:%M')} UTC", inline=False)

        if duration_str:
            # On ajoute la durée (ex: 30s) dans la raison ou un champ à part si on veut suivre exactement la demande
            # Mais l'utilisateur a demandé "Fin du Mute dans...", donc on peut ajouter "Dans X temps" dans le champ précédent
            # Je vais modifier le champ ci-dessus pour inclure la durée
            if action_type == "Mute" and duration_str:
                 embed.set_field_at(index=2, name="Fin du Mute", value=f"Dans **{duration_str}**")

        # --- FOOTER : ID & DATE ---
        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {target.id} • {current_time}")

        # Envoi
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))