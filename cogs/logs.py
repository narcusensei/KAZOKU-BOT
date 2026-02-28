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

    # --- FONCTION LOGS SANCTIONS (POUR LES COMMANDES) ---
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
        embed.set_author(name=f"{target.global_name or target.name} ({action_type})", icon_url=target.display_avatar.url)
        embed.description = f"{emoji} **{action_type.upper()}**"

        embed.add_field(name="Utilisateur", value=f"<@{target.id}>", inline=True)
        embed.add_field(name="Modérateur", value=f"<@{moderator.id}>", inline=True)
        embed.add_field(name="Raison", value=reason or "Aucune", inline=False)

        if action_type == "Mute" and end_time:
            ts_end = int(end_time.timestamp())
            relative_time = f"<t:{ts_end}:R>"
            absolute_time = end_time.strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="Fin du Mute", value=f"Dans **{relative_time}**\n🔔 {absolute_time} UTC", inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {target.id} • {current_time}")

        await channel.send(embed=embed)

    # --- FONCTION POUR LOGS SANCTIONS MANUELLES (MENU CLIC DROIT) ---
    async def send_log_sanction_channel(self, action_type, target, moderator, reason, duration_str=None, end_time=None):
        channel_id = LOG_CHANNELS.get("sanction")
        if not channel_id:
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        colors = {
            "Ban": discord.Color.red(),
            "Kick": discord.Color.orange(),
            "Mute": discord.Color.gold(),
            "Unmute": discord.Color.blue()
        }

        emojis = {
            "Ban": "⛔",
            "Kick": "👞",
            "Mute": "🔇",
            "Unmute": "🔊"
        }

        color = colors.get(action_type, discord.Color.blue())
        emoji = emojis.get(action_type, "📝")

        embed = discord.Embed(color=color)
        embed.set_author(name=f"{target.global_name or target.name} ({action_type})", icon_url=target.display_avatar.url)
        embed.description = f"{emoji} **{action_type.upper()}**"

        embed.add_field(name="Utilisateur", value=f"<@{target.id}>", inline=True)
        embed.add_field(name="Modérateur", value=f"<@{moderator.id}>", inline=True)
        embed.add_field(name="Raison", value=reason or "Manuel", inline=False)

        if action_type == "Mute" and end_time:
            ts_end = int(end_time.timestamp())
            relative_time = f"<t:{ts_end}:R>"
            absolute_time = end_time.strftime('%d/%m/%Y %H:%M')
            embed.add_field(name="Fin du Mute", value=f"Dans **{relative_time}**\n🔔 {absolute_time} UTC", inline=False)
        elif duration_str:
            # Si on a la durée en texte mais pas la date de fin (pour un unmute par ex)
            embed.add_field(name="Durée", value=duration_str, inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {target.id} • {current_time}")

        await channel.send(embed=embed)

    # --- LISTENER : ARRIVÉE (Gestion BOTS + HUMAINS + REJOIN) ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        # --- CAS 1 : C'EST UN BOT ---
        if member.bot:
            await asyncio.sleep(1.0) # Pause pour audit log
            moderator = None
            try:
                async for entry in member.guild.audit_logs(limit=10):
                    if entry.target.id == member.id:
                        if 'add' in entry.action.name.lower():
                            moderator = entry.user
                            break
            except Exception as e:
                print(f"Erreur audit logs (Ajout Bot) : {e}")

            embed = discord.Embed(color=discord.Color.green())
            embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
            embed.description = f"🤖 **BOT AJOUTÉ**"

            mod_mention = f"<@{moderator.id}>" if moderator else "Inconnu"
            embed.add_field(name="Information", value=f"{member.mention} a été ajouté dans le serveur par {mod_mention}", inline=False)

            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {member.id} • {current_time}")

            await channel.send(embed=embed)
            return

        # --- CAS 2 : C'EST UN HUMAIN ---
        # Gestion mémoire (Rejoin)
        members_file = "data/members.json"
        members_data = {}
        is_rejoin = False
        try:
            if os.path.exists(members_file):
                with open(members_file, 'r', encoding='utf-8') as f:
                    try: members_data = json.load(f)
                    except: members_data = {}
            else:
                if not os.path.exists("data"): os.makedirs("data")
                with open(members_file, 'w') as f: json.dump({}, f)
            uid = str(member.id)
            if uid in members_data: is_rejoin = True
            members_data[uid] = {"name": member.name, "last_join": datetime.now(timezone.utc).isoformat()}
            with open(members_file, 'w', encoding='utf-8') as f: json.dump(members_data, f, indent=4)
        except Exception as e: print(f"Erreur fichier membres : {e}")

        # Embed Humain
        embed = discord.Embed(color=discord.Color.green())
        embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
        embed.description = f"🟢 **ARRIVÉE**"
        embed.add_field(name="Utilisateur", value=f"{member.mention} a rejoint", inline=False)

        if not member.avatar:
            embed.add_field(name="ATTENTION!", value="```diff\n- Pas d'avatar\n```", inline=False)

        info_messages = []
        if is_rejoin: info_messages.append("+ Rejoint le serveur")
        if (datetime.now(timezone.utc) - member.created_at).days < 1:
            info_messages.append(f"+ Nouveau compte")

        if info_messages:
            embed.add_field(name="Info", value="```diff\n" + "\n".join(info_messages) + "\n```", inline=False)

        created_ts = int(member.created_at.timestamp())
        embed.add_field(name="Compte Créé", value=f"<t:{created_ts}:F> (<t:{created_ts}:R>)", inline=False)

        invite_found = False
        invite_text = ""
        if hasattr(member, 'inviter') and member.inviter:
            invite_text = f"Créée par <@{member.inviter.id}>"
            invite_found = True
        if invite_found: embed.add_field(name="Invite", value=invite_text, inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {member.id} • {current_time}")

        await channel.send(embed=embed)

    # --- LISTENER : DÉPART (Gestion BOTS + HUMAINS + SANCTIONS MANUELLES - FIXÉE) ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        # --- CAS 1 : C'EST UN BOT ---
        if member.bot:
            await asyncio.sleep(1.0)
            moderator = None
            reason_leave = "Normal"
            try:
                async for entry in member.guild.audit_logs(limit=10):
                    # CORRECTION ICI : On vérifie que target existe
                    if entry.target and entry.target.id == member.id:
                        time_diff = (datetime.now(timezone.utc) - entry.created_at).seconds
                        if time_diff > 60: continue

                        action_name = entry.action.name.lower()
                        if 'kick' in action_name:
                            moderator = entry.user
                            reason_leave = "Kick"
                            break
                        elif 'ban' in action_name:
                            moderator = entry.user
                            reason_leave = "Ban"
                            break
            except Exception as e:
                print(f"Erreur audit logs (Retrait Bot) : {e}")

            embed = discord.Embed(color=discord.Color.orange())
            embed.set_author(name=f"{member.global_name or member.name}", icon_url=member.display_avatar.url)
            embed.description = f"🤖 **BOT RETIRÉ**"

            mod_mention = f"<@{moderator.id}>" if moderator else "Inconnu"
            embed.add_field(name="Information", value=f"{member.mention} a été retiré du serveur par {mod_mention}", inline=False)

            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {member.id} • {current_time}")

            await channel.send(embed=embed)
            return

        # --- CAS 2 : C'EST UN HUMAIN ---
        await asyncio.sleep(1.0)
        reason_leave = "Normal"
        moderator = None
        sanction_type = None

        try:
            async for entry in member.guild.audit_logs(limit=50):
                # CORRECTION ICI : On vérifie que target existe
                if entry.target and entry.target.id == member.id:
                    action_name = entry.action.name
                    time_diff = (datetime.now(timezone.utc) - entry.created_at).seconds
                    if time_diff > 60: continue

                    if 'kick' in action_name.lower():
                        reason_leave = "Kick"; moderator = entry.user; sanction_type = "Kick"; break
                    elif 'ban' in action_name.lower():
                        reason_leave = "Ban"; moderator = entry.user; sanction_type = "Ban"; break
        except Exception as e:
            print(f"!!! ERREUR DANS AUDIT LOGS : {e}")

        # Envoi du log Sanction si c'était un kick/ban manuel
        if reason_leave in ["Kick", "Ban"]:
            await self.send_log_sanction_channel(reason_leave, member, moderator, "Action manuelle (Clic droit)")

        # Envoi du log Membre
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
            if len(roles) > 10: roles_str += f" ... (+{len(roles) - 10} autres)"
            embed.add_field(name="Rôles", value=roles_str, inline=False)

        if sanction_type:
            info_text = f"```diff\n- Membre {sanction_type}\n```"
            embed.add_field(name="Info", value=info_text, inline=False)

        current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
        embed.set_footer(text=f"ID: {member.id} • {current_time}")

        await channel.send(embed=embed)

    # --- LISTENER : MODIFICATION MEMBRE (RÔLES + AVATAR + NOM DE SERVEUR + MUTE) ---
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        # 1. AJOUT/RETRAIT DE RÔLE
        if before.roles != after.roles:
            added = [role for role in after.roles if role not in before.roles and not role.is_default()]
            removed = [role for role in before.roles if role not in after.roles and not role.is_default()]

            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target and entry.target.id == after.id:
                        if 'update' in entry.action.name.lower() and 'role' in entry.action.name.lower():
                            moderator = entry.user
                            break
            except: pass

            if added:
                roles_names = ", ".join([r.mention for r in added])
                embed = discord.Embed(title="🔹 **RÔLES DONNÉS**", color=discord.Color.green())
                embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)
                count = len(added)
                txt_roles = "role" if count == 1 else "rôles"
                txt_verbe = "a été donné" if count == 1 else "ont été donnés"
                embed.add_field(name="Information", value=f"**Un/Plusieurs {txt_roles}** {txt_verbe} à {after.mention}", inline=False)
                mod_text = f"<@{moderator.id}>" if moderator else "Inconnu"
                embed.add_field(name="Donné par", value=mod_text, inline=False)
                embed.add_field(name="Rôles", value=roles_names, inline=False)
                current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
                embed.set_footer(text=f"ID: {after.id} • {current_time}")
                await channel.send(embed=embed)

            if removed:
                roles_names = ", ".join([r.mention for r in removed])
                embed = discord.Embed(title="🔻 **RÔLES SUPPRIMÉS**", color=discord.Color.orange())
                embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)
                count = len(removed)
                txt_roles = "role" if count == 1 else "rôles"
                txt_verbe = "a été retiré" if count == 1 else "ont été retirés"
                embed.add_field(name="Information", value=f"**Un/Plusieurs {txt_roles}** {txt_verbe} à {after.mention}", inline=False)
                mod_text = f"<@{moderator.id}>" if moderator else "Inconnu"
                embed.add_field(name="Retiré par", value=mod_text, inline=False)
                embed.add_field(name="Rôles", value=roles_names, inline=False)
                current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
                embed.set_footer(text=f"ID: {after.id} • {current_time}")
                await channel.send(embed=embed)

        # 2. CHANGEMENT D'AVATAR SERVEUR
        if before.display_avatar.url != after.display_avatar.url:
            embed = discord.Embed(title="🖼️ **AVATAR SERVEUR MODIFIÉ**", color=discord.Color.blue())
            embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)
            embed.add_field(name="Information", value=f"{after.mention} a ajouté un avatar serveur", inline=False)
            embed.set_thumbnail(url=after.display_avatar.url)
            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {after.id} • {current_time}")
            await channel.send(embed=embed)

        # 3. CHANGEMENT DE NOM DE SERVEUR (NICKNAME)
        if before.nick != after.nick:
            # On cherche qui a changé le nom (Audit Logs)
            moderator = None
            is_self_change = True # Par défaut, on suppose que c'est l'utilisateur

            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target and entry.target.id == after.id:
                        # L'action est member_update
                        if 'update' in entry.action.name.lower() and 'member' in entry.action.name.lower():
                            # Si l'ID de l'auteur est différent de l'ID du membre, c'est un Modo
                            if entry.user.id != after.id:
                                moderator = entry.user
                                is_self_change = False
                                break
            except: pass

            embed = discord.Embed(title="🏷️ **NOM DE SERVEUR MODIFIÉ**", color=discord.Color.blue())
            embed.set_author(name=f"{after.global_name or after.name}", icon_url=after.display_avatar.url)

            # Si c'est un modérateur qui a changé le nom
            if moderator:
                text = f"{moderator.mention} à changé le nom sur le serveur de {after.mention}"
            else:
                text = f"{after.mention} a changé son nom sur le serveur"

            # Affichage de l'ancien et du nouveau
            old_name = before.nick if before.nick else "Aucun"
            new_name = after.nick if after.nick else "Aucun"

            embed.add_field(name="Information", value=f"{text}\n**{old_name}** ---> **{new_name}**", inline=False)

            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"ID: {after.id} • {current_time}")

            await channel.send(embed=embed)

        # 4. DÉTECTION MUTE/UNMUTE MANUEL (Timeout)
        timeout_before = before.timed_out_until
        timeout_after = after.timed_out_until

        # Cas : Mute manuel
        if timeout_after and not timeout_before:
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target and entry.target.id == after.id:
                        if 'update' in entry.action.name.lower() and 'member' in entry.action.name.lower():
                            moderator = entry.user
                            break
            except: pass

            duration = timeout_after - datetime.now(timezone.utc)
            seconds = int(duration.total_seconds())
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            dur_str = f"{h}h {m}m {s}s"

            await self.send_log_sanction_channel("Mute", after, moderator, "Mute manuel (Timeout)", dur_str, timeout_after)

        # Cas : Unmute manuel
        elif not timeout_after and timeout_before:
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target and entry.target.id == after.id:
                        if 'update' in entry.action.name.lower() and 'member' in entry.action.name.lower():
                            moderator = entry.user
                            break
            except: pass

            await self.send_log_sanction_channel("Unmute", after, moderator, "Unmute manuel (Timeout retiré)")


    # --- LISTENER : MODIFICATION SERVEUR ---
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        channel_id = LOG_CHANNELS.get("member")
        if not channel_id: return
        channel = self.bot.get_channel(channel_id)
        if not channel: return

        # 1. MODIFICATION NOM SERVEUR
        if before.name != after.name:
            embed = discord.Embed(title="🏛️ **Modification Nom Serveur**", color=discord.Color.purple())
            embed.add_field(name="Ancien nom", value=before.name, inline=True)
            embed.add_field(name="Nouveau nom", value=after.name, inline=True)
            await channel.send(embed=embed)

        # 2. MODIFICATION AVATAR SERVEUR
        if before.icon != after.icon:
            # On cherche qui a modifié l'avatar
            moderator = None
            try:
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.action == discord.AuditLogAction.guild_update:
                        # On vérifie que c'est une action récente (moins de 5 secondes) pour être sûr que c'est la bonne
                        time_diff = (datetime.now(timezone.utc) - entry.created_at).seconds
                        if time_diff < 5:
                            moderator = entry.user
                            break
            except Exception as e:
                print(f"Erreur audit logs (Modif Avatar) : {e}")

            embed = discord.Embed(color=discord.Color.purple())

            # Logo + Username de la personne qui a modifié
            if moderator:
                embed.set_author(name=f"**{moderator.global_name or moderator.name}**", icon_url=moderator.display_avatar.url)

            embed.description = "🖼️ **Avatar serveur modifié**"

            # Texte + Mention
            mod_mention = f"<@{moderator.id}>" if moderator else "Inconnu"
            embed.add_field(name="Action", value=f"{mod_mention} a ajouté un avatar serveur", inline=False)

            # Image à droite en petit (Thumbnail)
            if after.icon:
                embed.set_thumbnail(url=after.icon.url)

            # Footer avec ID de l'utilisateur et Date
            current_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
            footer_id = moderator.id if moderator else "Inconnu"
            embed.set_footer(text=f"ID: {footer_id} • {current_time}")

            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))