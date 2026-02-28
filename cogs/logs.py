import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import json
import os
import asyncio

# --- CONFIGURATION DES CHANNELS DE LOGS ---
# IMPORTANT : Remplace les 000000... par les vrais IDs de tes salons
LOG_CHANNELS = {
    "sanction": 1245708015861108807,  # ID du channel Sanction
    "member": 1353501264557903892    # ID du channel Membre
}
# -------------------------------------

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- FONCTION LOGS SANCTIONS ---
    # --- FONCTION LOGS SANCTIONS (FOOTER NETTOYÉ) ---
    async def send_log(self, interaction, action_type, target, moderator, reason, duration_str=None, end_time=None):
        channel_id = LOG_CHANNELS.get("sanction")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

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

        embed = discord.Embed(color=color)

        # Titre : Le nom de la personne sanctionnée
        embed.set_author(name=f"{target.global_name or target.name} ({action_type})", icon_url=target.display_avatar.url)
        embed.description = f"{emoji} **{action_type.upper()}**"

        embed.add_field(name="Utilisateur", value=f"<@{target.id}>", inline=True)
        # Le modérateur apparaît ici (comme demandé, et pas en bas à droite)
        embed.add_field(name="Modérateur", value=f"<@{moderator.id}>", inline=True)
        embed.add_field(name="Raison", value=reason or "Aucune", inline=False)

        if action_type == "Mute" and end_time:
            ts_end = int(end_time.timestamp())
            relative_time = f"<t:{ts_end}:R>"
            absolute_time = end_time.strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="Fin du Mute", value=f"Dans **{relative_time}**\n🔔 {absolute_time} UTC", inline=False)

        # --- FOOTER : Seulement ID et Date (Pas de nom du modérateur) ---
        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {target.id} • {current_time}")
        # -------------------------------------------------------------

        await channel.send(embed=embed)


    # --- LISTENER : ARRIVÉE ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"--- DEBUG ARRIVÉE : {member.name} vient de rejoindre !")

        channel_id = LOG_CHANNELS.get("member")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        # --- GESTION DE LA MÉMOIRE (REJOIN) ---
        members_file = "data/members.json"
        members_data = {}
        is_rejoin = False

        try:
            if os.path.exists(members_file):
                with open(members_file, 'r', encoding='utf-8') as f:
                    try:
                        members_data = json.load(f)
                        if not isinstance(members_data, dict):
                            members_data = {}
                    except:
                        members_data = {}
            else:
                if not os.path.exists("data"):
                    os.makedirs("data")
                with open(members_file, 'w') as f:
                    json.dump({}, f)

            uid = str(member.id)
            if uid in members_data:
                is_rejoin = True
                print(f">>> DÉTECTION REJOIN : {member.name}")

            members_data[uid] = {
                "name": member.name,
                "last_join": datetime.now(timezone.utc).isoformat()
            }

            with open(members_file, 'w', encoding='utf-8') as f:
                json.dump(members_data, f, indent=4)

        except Exception as e:
            print(f"Erreur fichier membres : {e}")
            is_rejoin = False
        # -------------------------------------------------------------------

        # Création de l'Embed
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
        embed.description = f"🟢 **ARRIVÉE**"
        embed.add_field(name="Utilisateur", value=f"{member.mention} a rejoint", inline=False)

        # ATTENTION (Pas d'avatar)
        if not member.avatar:
            warning_text = "```diff\n- Pas d'avatar\n```"
            embed.add_field(name="ATTENTION!", value=warning_text, inline=False)

        # INFO (Rejoin ou Nouveau compte)
        info_messages = []
        if is_rejoin:
            info_messages.append("+ Rejoint le serveur")

        if (datetime.now(timezone.utc) - member.created_at).days < 1:
            info_messages.append(f"+ Nouveau compte")

        if info_messages:
            info_text = "```diff\n" + "\n".join(info_messages) + "\n```"
            embed.add_field(name="Info", value=info_text, inline=False)

        # Compte Créé
        created_ts = int(member.created_at.timestamp())
        embed.add_field(name="Compte Créé", value=f"<t:{created_ts}:F> (<t:{created_ts}:R>)", inline=False)

        # Invite
        invite_found = False
        invite_text = ""
        if hasattr(member, 'inviter') and member.inviter:
            invite_text = f"Créée par <@{member.inviter.id}>"
            invite_found = True

        if invite_found:
            embed.add_field(name="Invite", value=invite_text, inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {member.id} • {current_time}")

        await channel.send(embed=embed)


    # --- LISTENER : DÉPART (VERSION SOUPLE) ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        # On attend 2 secondes pour laisser le temps à Discord d'écrire le kick
        await asyncio.sleep(2.0)

        # --- ANALYSE AUDIT LOGS ---
        reason_leave = "Normal"
        moderator = None
        sanction_type = None

        try:
            # On regarde les 50 dernières actions
            async for entry in member.guild.audit_logs(limit=50):
                if entry.target.id == member.id:

                    # --- DEBUG : Affiche l'action trouvée ---
                    action_name = entry.action.name
                    print(f">>> Action trouvée pour {member.name} : {action_name}")
                    # --------------------------------------

                    # On vérifie si l'action est ancienne (plus de 60 secondes)
                    time_diff = (datetime.now(timezone.utc) - entry.created_at).seconds
                    if time_diff > 60:
                        print(f">>> Trop vieux, on ignore.")
                        continue

                    # --- RECHERCHE SOUPLE DU KICK ---
                    # On regarde si le mot "kick" est présent dans le nom de l'action (insensible à la casse)
                    if 'kick' in action_name.lower():
                        reason_leave = "Kick"
                        moderator = entry.user
                        sanction_type = "Kick"
                        print(f">>> DÉTECTION KICK CONFIRMÉE !")
                        break

                    # --- RECHERCHE DU BAN ---
                    elif 'ban' in action_name.lower():
                        reason_leave = "Ban"
                        moderator = entry.user
                        sanction_type = "Ban"
                        break

        except Exception as e:
            print(f"!!! ERREUR AUDIT LOGS : {e}")
            import traceback
            traceback.print_exc()

        # --- CONSTRUCTION DE L'EMBED ---
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
        embed.description = f"👋 **DÉPART**"

        if reason_leave in ["Kick", "Ban"]:
            mod_mention = f"<@{moderator.id}>" if moderator else "Système"
            embed.add_field(name="Utilisateur", value=f"{member.mention} a été **{reason_leave}** par {mod_mention}", inline=False)
        else:
            embed.add_field(name="Utilisateur", value=f"{member.mention} a quitté le serveur", inline=False)

        joined_date_str = "Inconnu"
        if member.joined_at:
            joined_ts = int(member.joined_at.timestamp())
            joined_relative = f"<t:{joined_ts}:R>"
            joined_full = member.joined_at.strftime('%d/%m/%Y %H:%M')
            joined_date_str = f"{joined_full} ({joined_relative})"

        embed.add_field(name="A rejoint", value=joined_date_str, inline=False)

        roles = [r.mention for r in member.roles if not r.is_default()]
        if roles:
            roles_str = ", ".join(roles[:10])
            if len(roles) > 10:
                roles_str += f" ... (+{len(roles) - 10} autres)"
            embed.add_field(name="Rôles", value=roles_str, inline=False)

        if sanction_type:
            info_text = f"```diff\n- Membre {sanction_type}\n```"
            embed.add_field(name="Info", value=info_text, inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {member.id} • {current_time}")

        await channel.send(embed=embed)

    # --- LISTENER : MODIFICATION RÔLES (VERSION AMÉLIORÉE) ---
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        # Détection des rôles ajoutés/retirés
        added = [role for role in after.roles if role not in before.roles and not role.is_default()]
        removed = [role for role in before.roles if role not in after.roles and not role.is_default()]

        # --- SI ROLES AJOUTÉS ---
        if added:
            # On cherche qui a donné les rôles (Audit Logs)
            moderator = None
            try:
                # On regarde les 5 dernières actions
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target.id == after.id:
                        # On cherche l'action de mise à jour de rôle
                        if 'update' in entry.action.name.lower() and 'role' in entry.action.name.lower():
                            # Pour éviter de confondre un ajout et un retrait, on vérifie (si possible)
                            # Mais dans les logs, l'action est unique "member_role_update"
                            moderator = entry.user
                            break
            except Exception as e:
                print(f"Erreur audit logs pour rôles : {e}")

            # Création de l'Embed (Ajout)
            embed = discord.Embed(title="🔹 **RÔLES DONNÉS**", color=discord.Color.green())

            # Avatar + Username
            embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)

            # Phrase : Un/Plusieurs...
            count = len(added)
            txt_roles = "role" if count == 1 else "rôles"
            txt_verbe = "a été donné" if count == 1 else "ont été donnés"
            embed.add_field(name="Information", value=f"**Un/Plusieurs {txt_roles}** {txt_verbe} à {after.mention}", inline=False)

            # Donné par
            mod_text = "Inconnu (Système/Bot)"
            if moderator:
                mod_text = f"<@{moderator.id}>"
            embed.add_field(name="Donné par", value=mod_text, inline=False)

            # Liste des rôles
            roles_names = ", ".join([r.mention for r in added])
            embed.add_field(name="Rôles", value=roles_names, inline=False)

            # Footer
            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {after.id} • {current_time}")

            await channel.send(embed=embed)

        # --- SI ROLES RETIRÉS ---
        if removed:
            # Même logique pour trouver le modérateur
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target.id == after.id:
                        if 'update' in entry.action.name.lower() and 'role' in entry.action.name.lower():
                            moderator = entry.user
                            break
            except Exception as e:
                print(f"Erreur audit logs pour rôles : {e}")

            # Création de l'Embed (Retrait)
            embed = discord.Embed(title="🔻 **RÔLES SUPPRIMÉS**", color=discord.Color.orange())

            # Avatar + Username
            embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)

            # Phrase
            count = len(removed)
            txt_roles = "role" if count == 1 else "rôles"
            txt_verbe = "a été retiré" if count == 1 else "ont été retirés"
            embed.add_field(name="Information", value=f"**Un/Plusieurs {txt_roles}** {txt_verbe} à {after.mention}", inline=False)

            # Retiré par
            mod_text = "Inconnu (Système/Bot)"
            if moderator:
                mod_text = f"<@{moderator.id}>"
            embed.add_field(name="Retiré par", value=mod_text, inline=False)

            # Liste des rôles
            roles_names = ", ".join([r.mention for r in removed])
            embed.add_field(name="Rôles", value=roles_names, inline=False)

            # Footer
            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {after.id} • {current_time}")

            await channel.send(embed=embed)


    # --- LISTENER : MODIFICATION SERVEUR ---
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        # 1. MODIFICATION NOM SERVEUR
        if before.name != after.name:
            embed = discord.Embed(title="🏛️ Modification Nom Serveur", color=discord.Color.purple())
            embed.add_field(name="Ancien nom", value=before.name, inline=True)
            embed.add_field(name="Nouveau nom", value=after.name, inline=True)
            await channel.send(embed=embed)

        # 2. MODIFICATION AVATAR SERVEUR
        if before.icon != after.icon:
            embed = discord.Embed(title="🖼️ Modification Avatar Serveur", color=discord.Color.purple())
            embed.set_image(url=after.icon.url if after.icon else "Aucun")
            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))