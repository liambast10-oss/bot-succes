import discord
from discord import app_commands
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_STAFF = os.getenv("ROLE_STAFF")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def load_data():
    with open("succes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open("succes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    print(f"Bot connecté en tant que {bot.user}")

# /succès
@tree.command(name="succès", description="Voir les succès d’un joueur", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(joueur="Voir les succès d’un autre joueur")
async def succes(interaction: discord.Interaction, joueur: discord.Member = None):
    data = load_data()
    user = joueur or interaction.user
    user_id = str(user.id)

    obtenus = data["players"].get(user_id, [])
    tous = list(data["successes"].keys())

    description = ""
    for s in tous:
        info = data["successes"][s]

        if s in obtenus:
            description += f"✅ {s} - {info['description']}\n"
        else:
            description += f"❌ {s} - {info['description']}\n"

    embed = discord.Embed(
        title=f"🏆 Succès de {user.display_name}",
        description=description,
        color=0xF1C40F
    )

    embed.set_footer(text=f"{len(obtenus)} / {len(tous)} succès débloqués")
    await interaction.response.send_message(embed=embed)

# /succès valider
@tree.command(
    name="succès_valider",
    description="Valider un succès pour un joueur",
    guild=discord.Object(id=GUILD_ID)
)
async def succes_valider(interaction: discord.Interaction, joueur: discord.Member, succes: str):

    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ Permission refusée", ephemeral=True)
        return

    data = load_data()
    user_id = str(joueur.id)

    # Vérifie si le succès existe
    if succes not in data["successes"]:
        await interaction.response.send_message("❌ Succès inconnu", ephemeral=True)
        return

    data["players"].setdefault(user_id, [])

    if succes in data["players"][user_id]:
        await interaction.response.send_message("⚠️ Déjà validé", ephemeral=True)
        return

    data["players"][user_id].append(succes)
    save_data(data)

    await interaction.response.send_message(
        f"✅ Succès **{succes}** donné à {joueur.mention}"
    )
# /profil
@tree.command(
    name="profil",
    description="Afficher le profil succès d’un joueur",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(joueur="Le joueur à afficher")
async def profil(interaction: discord.Interaction, joueur: discord.Member = None):
    data = load_data()
    user = joueur or interaction.user
    user_id = str(user.id)

    tous = list(data["successes"].keys())
    obtenus = data["players"].get(user_id, [])

    total = len(tous)
    done = len(obtenus)
    percent = int((done / total) * 100) if total > 0 else 0

    # Choix du rang selon progression
    if percent == 100:
        rank = "🌟 Légende"
    elif percent >= 50:
        rank = "⚔️ Aventurier"
    elif percent >= 20:
        rank = "🪓 Explorateur"
    else:
        rank = "🌱 Débutant"

    description = ""

    for s in tous:
        if s in obtenus:
            description += f"✅ {s}\n"
        else:
            description += f"❌ {s}\n"

    embed = discord.Embed(
        title=f"🧑 Profil joueur — {user.display_name}",
        description=description,
        color=0x3498db
    )

    embed.add_field(name="🏆 Succès", value=f"{done} / {total}", inline=True)
    embed.add_field(name="📊 Progression", value=f"{percent}%", inline=True)
    embed.add_field(name="⭐ Rang", value=rank, inline=False)

    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    embed.set_footer(text="Système de succès du serveur")

    await interaction.response.send_message(embed=embed)
    
# suprime succée
@tree.command(
    name="succès_retirer",
    description="Retirer un succès à un joueur",
    guild=discord.Object(id=GUILD_ID)
)
async def succes_retirer(interaction: discord.Interaction, joueur: discord.Member, succes: str):
    
    # Permission staff (comme avant)
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "❌ Permission refusée (staff uniquement)",
            ephemeral=True
        )
        return

    data = load_data()
    user_id = str(joueur.id)

    # Vérifie si le joueur existe
    if user_id not in data["players"]:
        data["players"][user_id] = []

    # Si le succès n'est pas présent
    if succes not in data["players"][user_id]:
        await interaction.response.send_message(
            "⚠️ Ce joueur n'a pas ce succès",
            ephemeral=True
        )
        return

    # Retirer le succès
    data["players"][user_id].remove(succes)
    save_data(data)

    await interaction.response.send_message(
        f"🗑️ Succès **{succes}** retiré à {joueur.mention}"
    )
    
# succès detail
@tree.command(
    name="succès_detail",
    description="Voir les détails d’un succès",
    guild=discord.Object(id=GUILD_ID)
)
async def succes_detail(interaction: discord.Interaction, succes: str):

    data = load_data()

    if succes not in data["successes"]:
        await interaction.response.send_message(
            "❌ Succès inconnu",
            ephemeral=True
        )
        return

    info = data["successes"][succes]

    # Couleur selon rareté
    couleur = {
        "commun": 0x2ecc71,
        "rare": 0x3498db,
        "épique": 0x9b59b6,
        "légendaire": 0xf1c40f
    }.get(info["rarete"], 0x95a5a6)

    embed = discord.Embed(
        title=f"🏆 {succes}",
        description=info["description"],
        color=couleur
    )

    embed.add_field(name="⭐ Rareté", value=info["rarete"], inline=True)

    await interaction.response.send_message(embed=embed)
    
import os
bot.run(os.getenv("TOKEN"))
