import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION DES PERMISSIONS SPÉCIFIQUES ---
# À gauche : le nom interne de la commande
# À droite : la liste des rôles autorisés
PERMISSIONS = {
    "kick": ["+", "~", "-"],
    "ban": ["+", "~"],
    "mute": ["+", "~", "-"],
    "avert": ["+", "~", "-"],
    "clear": ["+", "~", "-"],
    "sanctionliste": ["+", "~", "-"],
    "unban": ["+"],
    "unmute": ["+", "~"]
}
# -------------------------------------------------

# --- VUES POUR LE SYSTÈME DE MENU ---

# 1. Vue pour le choix spécifique (Le menu déroulant)
class SpecificSanctionView(discord.ui.View):
    def __init__(self, bot, user_id, member_name, interaction_origin):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = str(user_id)
        self.member_name = member_name
        self.interaction_origin = interaction_origin # Pour mettre à jour le message principal si besoin

    @discord.ui.select(
        placeholder="Sélectionne une sanction à supprimer...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_idx = int(select.values[0])

        # Chargement des données
        warnings_file = "data/warnings.json"
        if os.path.exists(warnings_file):
            with open(warnings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        uid = str(self.user_id)
        if uid in data:
            # On récupère la sanction à supprimer
            # Note: select.values[0] contient l'index réel
            removed = data[uid].pop(selected_idx)

            # Sauvegarde
            with open(warnings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            await interaction.response.send_message(f"✅ La sanction **{removed['type']}** a été effacée.", ephemeral=True)

            # Si on voulait rafraîchir le message d'origine, c'est possible mais complexe.
            # Pour l'instant, on se contente de la confirmation éphémère.

# 2. Vue Principale (Les 2 gros boutons)
class MainSanctionView(discord.ui.View):
    def __init__(self, bot, user_id, member_name):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = str(user_id)
        self.member_name = member_name

    @discord.ui.button(label="🗑️ Supprimer une sanction spécifique", style=discord.ButtonStyle.primary)
    async def specific_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Charger les données
        warnings_file = "data/warnings.json"
        data = {}
        if os.path.exists(warnings_file):
            with open(warnings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        uid = str(self.user_id)

        # Filtrer : Uniquement Ban, Kick, Mute, Avertissement
        allowed_types = ["Ban", "Kick", "Mute", "Avertissement"]

        valid_sanctions = []
        if uid in data:
            for idx, sanction in enumerate(data[uid]):
                if sanction.get("type") in allowed_types:
                    valid_sanctions.append((idx, sanction))

        if not valid_sanctions:
            await interaction.response.send_message("Aucune sanction (Ban/Kick/Mute/Avert) à supprimer.", ephemeral=True)
            return

        # Créer les options pour le menu
        options = []
        for real_idx, sanction in valid_sanctions[-24:]: # Limite 24 options
            s_type = sanction.get("type")
            date_short = sanction['date'].split(' ')[0]
            reason_short = (sanction['reason'][:30] + '...') if len(sanction['reason']) > 30 else sanction['reason']

            options.append(discord.SelectOption(
                label=f"{s_type} ({date_short})",
                value=str(real_idx),
                description=reason_short
            ))

        # Envoyer le nouveau menu
        view = SpecificSanctionView(self.bot, self.user_id, self.member_name, interaction)
        view.select_callback.options = options

        await interaction.response.send_message("Choisis la sanction à effacer ci-dessous :", view=view, ephemeral=True)

    @discord.ui.button(label="⚠️ Supprimer TOUTES les sanctions", style=discord.ButtonStyle.danger)
    async def delete_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Charger et supprimer
        warnings_file = "data/warnings.json"
        if os.path.exists(warnings_file):
            with open(warnings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        uid = str(self.user_id)
        if uid in data:
            del data[uid]
            with open(warnings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # On désactive les boutons après action
            self.stop()
            await interaction.response.edit_message(content="✅ Toutes les sanctions ont été supprimées.", embed=None, view=None)
        else:
            await interaction.response.send_message("Il n'y a rien à supprimer.", ephemeral=True)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "data/warnings.json"

    # --- GESTION FICHIERS ---
    def load_data(self):
        if os.path.exists(self.warnings_file):
            try:
                with open(self.warnings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_data(self, data):
        with open(self.warnings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def add_sanction(self, user_id, s_type, reason, moderator, duration=""):
        data = self.load_data()
        uid = str(user_id)
        if uid not in data:
            data[uid] = []

        data[uid].append({
            "type": s_type,
            "reason": reason,
            "duration": duration,
            "date": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M"),
            "moderator": moderator
        })
        self.save_data(data)
        return len(data[uid])

    # --- VÉRIFICATION DES PERMISSIONS SÉPARÉES ---
    async def check_perm(self, interaction, command_name):
        """Vérifie si l'utilisateur a le droit d'utiliser la commande"""
        user = interaction.user

        # Le propriétaire a tout le temps les droits
        if user.id == interaction.guild.owner_id:
            return True

        # On essaie de récupérer le membre depuis le cache
        author_member = interaction.guild.get_member(user.id)

        # --- FIX CRITIQUE : Si pas dans le cache, on force le téléchargement depuis Discord ---
        if not author_member:
            try:
                author_member = await interaction.guild.fetch_member(user.id)
            except Exception as e:
                print(f"Impossible de récupérer le membre pour check_perm : {e}")
                return False
        # ------------------------------------------------------------------------------------

        allowed_roles = PERMISSIONS.get(command_name, [])
        user_roles_names = [role.name for role in author_member.roles]

        if any(role in allowed_roles for role in user_roles_names):
            return True

        return False

    # --- VÉRIFICATION HIÉRARCHIQUE (COMPATIBLE ID) ---
    async def check_sanction_possible(self, interaction, target, command_name):
        """
        target peut être un discord.Member OU un discord.User.
        Si c'est un User (hors ligne), on vérifie juste les permissions de base.
        """

        # --- PRIORITÉ ABSOLUE : LE PROPRIÉTAIRE ---
        if interaction.user.id == interaction.guild.owner_id:
            return True, None
        # ----------------------------------------

        # 1. Vérifier les permissions de l'auteur (Roles)
        if not await self.check_perm(interaction, command_name):
            return False, f"Tu n'as pas le rôle nécessaire pour utiliser la commande /{command_name} !"

        # 2. Récupération du membre auteur
        author_member = interaction.guild.get_member(interaction.user.id)
        if not author_member:
            try:
                author_member = await interaction.guild.fetch_member(interaction.user.id)
            except Exception as e:
                print(f"Erreur fetch membre hiérarchie : {e}")
                return False, "Erreur interne : Impossible de récupérer tes rôles."

        # 3. Récupération du membre cible (si dispo sur le serveur)
        # On tente d'abord le cache, puis fetch si échec (comme pour /profil)
        target_member = interaction.guild.get_member(target.id)
        if not target_member:
            try:
                target_member = await interaction.guild.fetch_member(target.id)
            except:
                pass # target_member reste None = utilisateur hors serveur

        # 4. Vérification HIÉRARCHIQUE (Seulement si la cible est dans le serveur)
        if target_member:
            # Propriétaire ?
            if target.id == interaction.guild.owner_id:
                return False, "Tu ne peux pas sanctionner le propriétaire du serveur !"

            # Auteur < Cible ?
            if author_member.top_role <= target_member.top_role:
                return False, f"Tu ne peux pas sanctionner {target.display_name} car son rôle est supérieur ou égal au tien."

            # Bot < Cible ?
            if interaction.guild.me.top_role <= target_member.top_role:
                return False, f"Je ne peux pas sanctionner {target.display_name} car mon rôle n'est pas assez élevé."

        return True, None

    async def send_dm(self, member, content, embed):
        try:
            await member.send(content=content, embed=embed)
        except discord.Forbidden:
            pass

    # --- COMMANDE CLEAR (VERSION PRIVÉE) ---
    @app_commands.command(name="clear", description="Clear des messages")
    @app_commands.describe(amount="Nombre de messages (1-100)", utilisateur="Optionnel : Clear seulement les messages de cet utilisateur")
    async def clear_slash(self, interaction: discord.Interaction, amount: int, utilisateur: discord.Member = None):

        if not await self.check_perm(interaction, "clear"):
            await interaction.response.send_message("Bruh t'as pas les perms bouffon", ephemeral=True)
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("Le nombre doit être entre 1 et 100.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        deleted = 0

        if utilisateur:
            # Cas 1 : Chercher X messages spécifiques d'une personne
            to_delete = []
            async for message in interaction.channel.history(limit=100):
                if message.author == utilisateur:
                    to_delete.append(message)
                    if len(to_delete) >= amount:
                        break

            if to_delete:
                if len(to_delete) == 1:
                    await to_delete[0].delete()
                else:
                    await interaction.channel.delete_messages(to_delete)
                deleted = len(to_delete)
                await interaction.followup.send(f"Suppression de {deleted} messages de {utilisateur.name}.", ephemeral=True)
            else:
                await interaction.followup.send(f"Aucun message trouvé pour {utilisateur.name} dans les derniers 100 messages.", ephemeral=True)

        else:
            # Cas 2 : Clear classique (CORRECTION ICI)
            deleted_list = await interaction.channel.purge(limit=amount)
            deleted = len(deleted_list) # <--- On compte le nombre d'éléments de la liste
            await interaction.followup.send(f"Suppression de {deleted} messages terminée.", ephemeral=True)

    # --- COMMANDE MUTE (Compatible ID) ---
    @app_commands.command(name="mute", description="Mute un membre (ID ou Mention)")
    @app_commands.describe(utilisateur="Membre (ID ou Mention)", reason="Raison du mute", hours="Heures", minutes="Minutes", seconds="Secondes")
    async def mute_slash(self, interaction: discord.Interaction, utilisateur: discord.User, reason: str = None, hours: int = 0, minutes: int = 0, seconds: int = 0):

        can_proceed, error_msg = await self.check_sanction_possible(interaction, utilisateur, "mute")
        if not can_proceed:
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        if utilisateur == interaction.user:
            await interaction.response.send_message("Pourquoi tu te mutes toi-même ?", ephemeral=True)
            return

        # Pour mute, il est IMPÉRATIF d'avoir un objet Member (présent sur le serveur)
        target_member = interaction.guild.get_member(utilisateur.id)
        if not target_member:
            try:
                target_member = await interaction.guild.fetch_member(utilisateur.id)
            except:
                await interaction.response.send_message("Cet utilisateur n'est pas sur le serveur, impossible de le mute.", ephemeral=True)
                return

        duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        if duration.total_seconds() == 0:
            await interaction.response.send_message("Tu dois définir une durée !", ephemeral=True)
            return

        mute_end = datetime.now(timezone.utc) + duration
        await interaction.response.defer(ephemeral=True)

        try:
            await target_member.edit(timed_out_until=mute_end)
        except discord.Forbidden:
            await interaction.followup.send("Je n'ai pas la permission 'Modérer les membres'.", ephemeral=True)
            return

        dur_str = f"{hours}h {minutes}m {seconds}s"
        self.add_sanction(utilisateur.id, "Mute", reason or "Aucune", interaction.user.name, dur_str)

        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Mute", utilisateur, interaction.user, reason or "Aucune", dur_str, mute_end)
        # -----------------------

        embed = discord.Embed(
            title="[MUTE]",
            description=f"L'utilisateur **{utilisateur.name}** ({utilisateur.id}) a été mute pour {dur_str}.",
            color=discord.Color.orange()
        )
        if reason: embed.add_field(name="Raison", value=reason)
        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE UNMUTE (Compatible ID) ---
    @app_commands.command(name="unmute", description="Unmute un membre (ID ou Mention)")
    @app_commands.describe(utilisateur="Membre (ID ou Mention)")
    async def unmute_slash(self, interaction: discord.Interaction, utilisateur: discord.User):

        # Vérification permission
        if not await self.check_perm(interaction, "unmute"):
            await interaction.response.send_message("Tu n'as pas la permission de unmute.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # --- Récupération du Membre (Obligatoire pour muter/démuter) ---
        # On essaie de récupérer le membre depuis le cache
        member = interaction.guild.get_member(utilisateur.id)

        # Si pas dans le cache, on télécharge depuis Discord
        if not member:
            try:
                member = await interaction.guild.fetch_member(utilisateur.id)
            except discord.NotFound:
                await interaction.followup.send("Cet utilisateur n'est pas sur le serveur. Impossible de unmuter quelqu'un qui a quitté le serveur.", ephemeral=True)
                return
        # -------------------------------------------------------------

        # Vérification Hiérarchique (Réutilisation de la logique existante)
        # On vérifie juste si l'utilisateur a le droit de sanctionner ce membre
        can_proceed, error_msg = await self.check_sanction_possible(interaction, utilisateur, "unmute")
        if not can_proceed:
            await interaction.followup.send(error_msg, ephemeral=True)
            return

        try:
            # On retire le mute en mettant None
            await member.edit(timed_out_until=None)
        except discord.Forbidden:
            await interaction.followup.send("Je n'ai pas la permission 'Modérer les membres'.", ephemeral=True)
            return

        # Enregistrement
        self.add_sanction(utilisateur.id, "Unmute", "Fin du timeout", interaction.user.name)

        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Unmute", utilisateur, interaction.user, "Fin du timeout")
        # -----------------------

        # Embed Unifié
        embed = discord.Embed(
            title="[UNMUTE]",
            description=f"L'utilisateur **{utilisateur.name}** ({utilisateur.id}) a été unmute.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE KICK (Design Unifié + Privé) ---
    @app_commands.command(name="kick", description="Kick un membre")
    @app_commands.describe(utilisateur="Membre à kick", reason="Raison du kick")
    async def kick_slash(self, interaction: discord.Interaction, utilisateur: discord.Member, reason: str = None):

        can_proceed, error_msg = await self.check_sanction_possible(interaction, utilisateur, "kick")
        if not can_proceed:
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True) # <--- Privé

        self.add_sanction(utilisateur.id, "Kick", reason or "Aucune", interaction.user.name)


        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Kick", utilisateur, interaction.user, reason)
        # -----------------------

        # --- ENVOI DU MP (RESTAURÉ) ---
        embed_dm = discord.Embed(
            title="👞 KICK",
            description=f"Tu as été kick de **{interaction.guild.name}**.",
            color=discord.Color.red()
        )
        if reason: embed_dm.add_field(name="Raison", value=reason)
        await self.send_dm(utilisateur, "Tu as été kick !", embed_dm)
        # ---------------------------

        await utilisateur.kick(reason=reason)

        # Embed Unifié
        embed = discord.Embed(
            title="[KICK]",
            description=f"L'utilisateur **{utilisateur.name}** ({utilisateur.id}) a été kické du serveur.",
            color=discord.Color.red()
        )
        if reason: embed.add_field(name="Raison", value=reason)
        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE BAN (Design Unifié + Privé) ---
    @app_commands.command(name="ban", description="Ban un membre")
    @app_commands.describe(utilisateur="Membre (ID ou Mention)", reason="La raison du ban")
    async def ban_slash(self, interaction: discord.Interaction, utilisateur: discord.User, reason: str = None):

        if not await self.check_perm(interaction, "ban"):
            await interaction.response.send_message("Tu n'as pas la permission de ban.", ephemeral=True)
            return

        # Récupération auteur (Fix Cache)
        author_member = interaction.guild.get_member(interaction.user.id)
        if not author_member:
            try:
                author_member = await interaction.guild.fetch_member(interaction.user.id)
            except Exception as e:
                print(f">>> ERREUR FETCH AUTEUR (Ban) : {e}", flush=True)
                await interaction.response.send_message("Erreur interne.", ephemeral=True)
                return

        target_member = interaction.guild.get_member(utilisateur.id)

        if utilisateur.id == interaction.guild.owner_id:
            await interaction.response.send_message("Tu ne peux pas ban le propriétaire !", ephemeral=True)
            return

        if target_member:
            if author_member.top_role <= target_member.top_role:
                await interaction.response.send_message("Tu ne peux pas ban quelqu'un avec un rôle égal ou supérieur au tien.", ephemeral=True)
                return
            if interaction.guild.me.top_role <= target_member.top_role:
                await interaction.response.send_message("Je ne peux pas ban ce membre (rôle trop haut).", ephemeral=True)
                return

        # On envoie une réponse éphémère (privée) immédiate
        await interaction.response.defer(ephemeral=True)

        # Enregistrement
        self.add_sanction(utilisateur.id, "Ban", reason or "Aucune", interaction.user.name)

        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Ban", utilisateur, interaction.user, reason)
        # -----------------------

        # Exécution
        try:
            await interaction.guild.ban(discord.Object(id=utilisateur.id), reason=reason)
        except Exception as e:
            print(f">>> ERREUR BAN : {e}", flush=True)
            await interaction.followup.send("Une erreur est survenue.", ephemeral=True)
            return

        # Embed Unifié
        embed = discord.Embed(
            title="[BANNISSEMENT]",
            description=f"L'utilisateur **{utilisateur.name}** ({utilisateur.id}) a été banni du serveur.",
            color=discord.Color.dark_red()
        )
        if reason: embed.add_field(name="Raison", value=reason)
        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE UNBAN (CORRIGÉE TYPE) ---
    @app_commands.command(name="unban", description="Débannir un utilisateur par ID")
    @app_commands.describe(target_id="L'ID de la personne à débannir")
    async def unban_slash(self, interaction: discord.Interaction, target_id: str):

        # Vérification permission
        if not await self.check_perm(interaction, "unban"):
            await interaction.response.send_message("Tu n'as pas la permission de débannir.", ephemeral=True)
            return

        # --- CONVERSION EN ENTIER ---
        try:
            user_id = int(target_id)
        except ValueError:
            await interaction.response.send_message("L'ID doit être composé uniquement de chiffres.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # On essaie de récupérer les infos du bannissement
        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(id=user_id))
            user_to_unban = ban_entry.user
        except discord.NotFound:
            await interaction.followup.send("Cet utilisateur n'est pas banni (ou l'ID est invalide).", ephemeral=True)
            return

        # Exécution du unban
        try:
            await interaction.guild.unban(user_to_unban)
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du deban : {e}", ephemeral=True)
            return

        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Unban", user_to_unban, interaction.user, reason)
        # -----------------------

        # Confirmation
        embed = discord.Embed(
            title="✅ DÉBANNISSEMENT",
            description=f"L'utilisateur **{user_to_unban.name}** ({user_to_unban.id}) a été débanni du serveur.",
            color=discord.Color.green()
        )

        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE AVERTISSEMENT (Compatible ID) ---
    @app_commands.command(name="avert", description="Donne un avertissement à un utilisateur (ID ou Mention)")
    @app_commands.describe(utilisateur="Utilisateur (ID ou Mention)", reason="Raison de l'avertissement")
    async def avert_slash(self, interaction: discord.Interaction, utilisateur: discord.User, reason: str):

        can_proceed, error_msg = await self.check_sanction_possible(interaction, utilisateur, "avert")
        if not can_proceed:
            await interaction.response.send_message(error_msg, ephemeral=True)
            return

        if utilisateur.bot:
            await interaction.response.send_message("On peut pas avertir un bot.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        count = self.add_sanction(utilisateur.id, "Avertissement", reason, interaction.user.name)

        # <--- AJOUTER CECI ---
        logs_cog = self.bot.get_cog('Logs')
        if logs_cog:
            await logs_cog.send_log(interaction, "Avertissement", utilisateur, interaction.user, reason)
        # -----------------------

        # Envoi du MP (discord.User a une methode .send)
        embed_dm = discord.Embed(title="⚠️ AVERTISSEMENT", description=f"Tu as reçu un avertissement sur **{interaction.guild.name}**.", color=discord.Color.gold())
        embed_dm.add_field(name="Raison", value=reason)
        try:
            await utilisateur.send(embed=embed_dm)
        except:
            pass # MP fermé

        embed = discord.Embed(
            title="[AVERTISSEMENT]",
            description=f"L'utilisateur **{utilisateur.name}** ({utilisateur.id}) a été averti. (Total sanctions : {count})",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Par {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.followup.send(embed=embed)

    # --- COMMANDE SANCTION LISTE (NOUVELLE INTERFACE) ---
    @app_commands.command(name="sanctionliste", description="Voir et gérer les sanctions d'un utilisateur")
    @app_commands.describe(utilisateur="Utilisateur à vérifier")
    async def sanctionliste_slash(self, interaction: discord.Interaction, utilisateur: discord.User):

        if not await self.check_perm(interaction, "sanctionliste"):
            await interaction.response.send_message("Tu n'as pas la permission de voir la liste.", ephemeral=True)
            return

        data = self.load_data()
        user_id = str(utilisateur.id)

        embed = discord.Embed(title=f"Sanctions de {utilisateur.name}", color=discord.Color.purple())

        # On filtre l'affichage : Pas de Unmute
        allowed_types = ["Ban", "Kick", "Mute", "Avertissement"]

        display_sanctions = []
        if user_id in data and data[user_id]:
            for sanction in data[user_id]:
                if sanction.get("type") in allowed_types:
                    display_sanctions.append(sanction)

        if display_sanctions:
            # On inverse pour voir les plus récents
            display_sanctions.reverse()

            for sanction in display_sanctions[:10]:
                s_type = sanction.get("type")
                emoji = "📝"
                if s_type == "Kick": emoji = "👞"
                if s_type == "Ban": emoji = "⛔"
                if s_type == "Mute": emoji = "🔇"
                if s_type == "Avertissement": emoji = "⚠️"

                value = f"**Raison :** {sanction['reason']}\n**Par :** {sanction['moderator']} le {sanction['date']}"
                if sanction.get("duration"):
                    value += f"\n**Durée :** {sanction['duration']}"

                embed.add_field(name=f"{emoji} {s_type}", value=value, inline=False)
        else:
            embed.description = "Cet utilisateur n'a aucune sanction (Ban/Kick/Mute/Avert) enregistrée. 🎉"

        # Envoi de l'Embed + La Vue Principale (Boutons)
        view = MainSanctionView(self.bot, utilisateur.id, utilisateur.name)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Moderation(bot))