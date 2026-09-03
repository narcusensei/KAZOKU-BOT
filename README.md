# 👑 K4ZK-BOT

Bot Discord du serveur **KAZOKU** — modération, logs avancés et giveaways.

## 🌐 Rejoindre le serveur

- **Lien principal :** [discord.gg/K4ZOKU](https://discord.gg/K4ZOKU)
- **Lien de secours :** [discord.gg/mrUvBUKC23](https://discord.gg/mrUvBUKC23) *(au cas où le premier ne fonctionne pas)*

## ✨ Fonctionnalités

| Cog | Description |
|---|---|
| 🤖 **Base** | Commandes générales (ping, profil, aide) |
| 🛡️ **Modération** | Sanctions avec historique persistant (mutes, kicks, bans, avertissements) |
| 📋 **Logs** | Journalisation ultra-complète du serveur en embeds enrichis |
| 🎁 **Giveaways** | Création, gestion et reroll de cadeaux avec boutons |

### 📋 Logs couverts

Le cog de logs surveille la quasi-totalité des événements du serveur :

- **Membres** — arrivées/départs, changements de rôles, pseudos, boosts, avatar
- **Messages** — modifications, suppressions, suppressions en masse, réactions
- **Salons** — création/suppression/modification (texte, vocal, catégories, forums)
- **Rôles** — création, suppression, modifications de permissions
- **Fils (threads)** — création, archivage, suppression
- **Vocal** — connexions, déplacements, muets, caméra, streaming
- **Invitations** — création/suppression (avec traçabilité de l'inviteur)
- **Webhooks, emojis, stickers, soundboard**
- **Événements** — événements programmés, salons stage
- **Audit logs** — actions de modération avec auteur et raison

## 📜 Commandes

Préfixe : `+` (les commandes existent aussi en slash commands `/`)

### Général (`cogs/base.py`)
| Commande | Description |
|---|---|
| `+ping` | Affiche la latence du bot |
| `+profil [utilisateur]` | Profil détaillé (compatible par ID, même absent du serveur) |
| `+info` | Liste des commandes |
| `+sync` | Synchronise les commandes slash *(dev)* |

### Modération (`cogs/moderation.py`)
| Commande | Description |
|---|---|
| `+clear <nombre> [utilisateur]` | Supprime des messages (filtrable par utilisateur) |
| `+mute <utilisateur> [raison] [durée]` | Réduit au silence (durée en h/m/s) |
| `+unmute <utilisateur>` | Retire le mute |
| `+kick <utilisateur> [raison]` | Expulse un membre |
| `+ban <utilisateur> [raison]` | Bannit un utilisateur |
| `+unban <id> [raison]` | Débannit par ID |
| `+avert <utilisateur> <raison>` | Avertit un utilisateur |
| `+sanctionliste <utilisateur>` | Historique des sanctions |

### Giveaways (`cogs/giveaway.py`)
| Commande | Description |
|---|---|
| `+createg` | Créer un giveaway via formulaire |
| `+startg` | Créer un giveaway directement |
| `+endg` | Terminer un giveaway |
| `+deletedg` | Supprimer un giveaway |
| `+rerollg` | Tirer de nouveaux gagnants |

## ⚙️ Installation

### Prérequis

- **Python 3.12+**
- Un [bot Discord](https://discord.com/developers/applications) avec les **intents privilégiés** activés :
  - ✅ Server Members Intent
  - ✅ Message Content Intent
  - ✅ Presence Intent

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/narcusensei/KAZOKU-BOT.git
cd KAZOKU-BOT

# 2. Créer un environnement virtuel
python -m venv venv
venv/Scripts/activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer le token
# Créer un fichier .env à la racine :
# DISCORD_TOKEN=votre_token_ici

# 5. Lancer le bot
python main.py
```

## 🔧 Configuration

Tout est centralisé dans [`settings.py`](settings.py) :

- **Général** — préfixe, activité/statut du bot
- **Salons de logs** — `LOG_CHANNELS` (IDs des salons par catégorie)
- **Couleurs** — un embed coloré par type d'événement
- **Textes** — tous les libellés FR des embeds
- **Timezone** — fuseau horaire des timestamps

Les données d'exécution (`data/*.json`) sont générées automatiquement et **ignorées par git** (elles peuvent contenir des informations de membres).

## 📁 Structure

```
KAZOKU-BOT/
├── main.py              # Point d'entrée, chargement des cogs
├── settings.py          # Configuration centralisée
├── requirements.txt     # Dépendances Python
├── cogs/
│   ├── base.py          # Commandes générales
│   ├── moderation.py    # Sanctions + historique
│   ├── logs.py          # Journalisation complète
│   └── giveaway.py      # Système de giveaways
└── data/                # Données runtime (auto-généré, ignoré)
```

## 📜 Licence

Projet personnel du serveur KAZOKU — tous droits réservés.
