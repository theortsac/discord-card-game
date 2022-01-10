# region Imports
from nextcord.ext import commands, menus
import nextcord
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pymongo
import asyncio
bot = commands.Bot(command_prefix="nfg!",
                   case_insensitive=True)
allCards = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"]
client = MongoClient()
load_dotenv()
token = os.getenv('TOKEN')
username = os.getenv('MONGO_USER')
password = os.getenv('PASSWORD')
mongoClient = pymongo.MongoClient(f"mongodb://{username}:{password}@localhost")
db = mongoClient.NonFungibleGame
# endregion
# region Connect Print


@ bot.event
async def on_ready():
    print("Connected.")
# endregion
# region Help Command


class MyHelp(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = nextcord.Embed(
            title=":white_check_mark: Here's an explanation of each command:", color=0x87CEEB)
        embed.add_field(name=":gift: Claim command:",
                        value="Claim the cards for the 1 day test, use:\nnfg!claim")
        embed.add_field(name=":package: Add Card Command:",
                        value="Only admins can use this command. It adds a card to the selected user. Use:\nnfg!add @member card_number", inline=False)
        embed.add_field(
            name=":card_box: Check Card Command:", value="Check the details of a card, use:\nnfg!card card_number", inline=False)
        embed.add_field(
            name=":bookmark_tabs: Rules Command:", value="See the rules of the game, use:\nnfg!rules", inline=False)
        embed.add_field(
            name=":crossed_swords: Challenge Command:", value="Battle against someone! Mention the user you want to challenge. Use:\nnfg!challenge @mention", inline=False)
        embed.add_field(
            name=":bank: Owned Command:", value="Check the cards you own, use:\nnfg!owned", inline=False)
        embed.add_field(
            name=":trophy: Rank Command:", value="See the ranking of people with the most victories, use:\nnfg!ranking", inline=False)
        embed.add_field(
            name=":arrows_counterclockwise: Update Command:", value="Update your name on the rankings, use:\nnfg!update", inline=False)

        await self.context.reply(embed=embed)


bot.help_command = MyHelp()

# endregion
# region Dropdown View


class Dropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
        ]
        super().__init__(placeholder='Choose your cards...',
                         min_values=3, max_values=3, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="The cards were selected!", color=0x00FF00)
        await interaction.message.edit("", embed=embed, view=None)
        self.view.stop()


class DropdownBattle(nextcord.ui.Select):
    def __init__(self):
        options = [
        ]
        super().__init__(placeholder='Battle Time! Choose your movement.',
                         min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Movement Selected!", color=0x00FF00)
        await interaction.message.edit("", embed=embed, view=None)
        self.view.stop()

# endregion
# region Confirm View


class Confirm(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @ nextcord.ui.button(label='Confirm', style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="Accepted!", color=0x00FF00)
        await interaction.message.edit("", embed=embed, view=None)
        self.value = True
        self.stop()

    @ nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        embed = nextcord.Embed(title="Refused.", color=0xFF0000)
        await interaction.message.edit("", embed=embed, view=None)
        self.value = False
        self.stop()
# endregion
# region Pages Owned View


class MyButtonMenuPages(menus.ButtonMenuPages):
    def __init__(self, ctx, **kwargs):
        super().__init__(**kwargs)
        self.ctx = ctx

    async def interaction_check(self, interaction):
        return self.ctx.author.id == interaction.user.id


class CardPageSource(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        embed = nextcord.Embed(
            title=f"Cards you got!", color=0x87CEEB)
        embed.set_author(name="The Mysterious Game Master",
                         icon_url="https://cdn.discordapp.com/attachments/857638688942587954/895323462695018496/Questlord.png")
        for entry in entries:
            embed.add_field(name=entry["Emoji"] + " " + entry["Name"] +
                            " #" + entry["_id"], value=entry["Description"], inline=False)
        embed.set_footer(
            text=f"Wow! You got such cool cards! Page: {menu.current_page + 1}", icon_url="https://cdn.discordapp.com/emojis/754736642761424986.png")
        return embed

# endregion
# region Functions


def removeRepeated(list):
    l = []
    for i in list:
        if i not in l:
            l.append(i)
    return l


def cardsPlayerHave(playerId):
    if (db.playersData.count_documents({'_id': playerId}) > 0):
        cardsPlayerHas = db["playersData"].find_one({'_id': playerId})["Cards"]
        if (len(cardsPlayerHas) > 0):
            cardsPlayerHas = list(
                map(str, sorted(list(map(int, cardsPlayerHas)))))
            return cardsPlayerHas
        else:
            return None
    else:
        return None


def whichPlayerWon(type1, power1, type2, power2):
    if (type1 == type2):
        if (int(power1) > int(power2)):
            return 1
        elif (int(power1) < int(power2)):
            return 2
        else:
            return 3
    elif (type1 == "Strength" and type2 == "Intelligence"):
        return 1
    elif (type2 == "Strength" and type1 == "Intelligence"):
        return 2
    elif (type1 == "Intelligence" and type2 == "Agility"):
        return 1
    elif (type2 == "Intelligence" and type1 == "Agility"):
        return 2
    elif (type1 == "Agility" and type2 == "Strength"):
        return 1
    elif (type2 == "Agility" and type1 == "Strength"):
        return 2


def addCard(playerId, cardId, playerName):
    if db.cardsData.count_documents({'_id': cardId}) == 0:
        return "CDE"
    else:
        if db.playersData.count_documents({'_id': playerId}) > 0:
            if cardId not in db["playersData"].find_one({'_id': playerId})["Cards"]:
                db.playersData.update_one(
                    {"_id": playerId}, {"$push": {"Cards": cardId}})
                return 1
            else:
                return None
        else:
            db.playersData.insert_one(
                {"_id": playerId, "Cards": [cardId], "Wins": 0,  "Name": playerName})
            return 1

# endregion
# region Add Card Command


@ bot.command()
@ commands.has_guild_permissions(administrator=True)
async def add(ctx, user: nextcord.Member, cardId: str):
    add_value = addCard(str(user.id), cardId, user.name)
    if add_value == None:
        await ctx.reply(embed=nextcord.Embed(title="The player already has the card.", color=0xFF0000))
    elif add_value == "CDE":
        await ctx.reply(embed=nextcord.Embed(title="This card don't exist! Baka!", color=0xFF0000))
    elif add_value == 1:
        await ctx.reply(embed=nextcord.Embed(title="Card Added!", color=0x00FF00))
# endregion
# region Check Owned Cards Command


@bot.command()
async def owned(ctx):
    cards = cardsPlayerHave(str(ctx.message.author.id))
    if (cards == None):
        await ctx.reply("You have no cards.")
        return
    card_data = list(db["cardsData"].find({'_id': {'$in': cards}}))
    card_data.sort(key=lambda card: cards.index(card['_id']))
    pages = MyButtonMenuPages(
        ctx=ctx,
        source=CardPageSource(card_data),
        clear_buttons_after=True,
        timeout=60.0
    )
    await pages.start(ctx)

# endregion
# region Check Card Command


@ bot.command()
async def card(ctx, message):
    split_message = message.split()
    try:
        cardData = db["cardsData"].find_one({'_id': split_message[0]})
        embed = nextcord.Embed(
            title=cardData["Emoji"] + " " + cardData["Name"], color=0xFFFF00)
        embed.set_thumbnail(
            url=cardData["Image"])
        embed.set_author(name="The Mysterious Game Master",
                         icon_url="https://cdn.discordapp.com/attachments/857638688942587954/895323462695018496/Questlord.png")
        embed.add_field(name="📔 Description",
                        value=cardData["Description"], inline=False)
        embed.add_field(
            name="🌟 Rarity", value=cardData["Rarity"], inline=False)
        for x in cardData["Movements"]:
            embed.add_field(name=db["cardsData"].find_one({'_id': "Types"})[cardData["Movements"][x]["Type"]] + " " + x, value="Type: " +
                            cardData["Movements"][x]["Type"] + "\nPower: " + cardData["Movements"][x]["Power"], inline=False)
        embed.set_footer(
            text="That's a cool card, as expected from the Game Dev.", icon_url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/282/fire_1f525.png")
        await ctx.reply(embed=embed)
    except:
        await ctx.reply(embed=nextcord.Embed(
            title="This card doesn't exist.", color=0xFF0000))
# endregion
# region Challenge Command Verification


@ bot.command()
async def challenge(ctx, user: nextcord.Member):
    if user.bot:
        await ctx.reply(embed=nextcord.Embed(title="You can't play against a bot.", color=0xFF0000))
        return
    elif (user.id == ctx.message.author.id):
        await ctx.reply(embed=nextcord.Embed(title="You can't play against yourself.", color=0xFF0000))
        return
    elif (cardsPlayerHave(str(user.id)) == None):
        await ctx.reply(embed=nextcord.Embed(title="The player has no cards.", color=0xFF0000))
        return
    elif (cardsPlayerHave(str(ctx.message.author.id)) == None):
        await ctx.reply(embed=nextcord.Embed(title="You have no cards.", color=0xFF0000))
        return

# endregion
# region Confirm To Play
    view = Confirm()
    embed_quest = nextcord.Embed(title="Do you want to play against " +
                                 ctx.message.author.name + "?", color=0xFFFF00)
    try:
        await user.send(embed=embed_quest, view=view)
    except:
        await ctx.reply(embed=nextcord.Embed(
            title="Can't send a message to the user!", color=0xFF0000))
        return
    await view.wait()
    if view.value is None:
        await ctx.reply(embed=nextcord.Embed(title="Timed Out! The opponent needs to be faster next time.", color=0xFF0000))
        return
    elif view.value == False:
        await ctx.reply(embed=nextcord.Embed(title="The player refused the challenge!", color=0xFF0000))
        return
    elif view.value:
        await ctx.reply(embed=nextcord.Embed(title="The Opponent Accepted the Challenge! The Match between " +
                        ctx.message.author.name + " and " + user.name + " starts now! Check your messages!", color=0x00FF00))
# endregion
# region Select Cards you Will Play
        drop = Dropdown()
        view = nextcord.ui.View()
        drop2 = Dropdown()
        view2 = nextcord.ui.View()
        player1cards = cardsPlayerHave(str(ctx.message.author.id))
        player2cards = cardsPlayerHave(str(user.id))
        if (player1cards == None):
            ctx.reply("You have no more cards.")
        elif (player2cards == None):
            ctx.reply("The opponent has no more cards.")
        else:
            if len(player1cards) < 4:
                player1HasLessThan3 = True
                dropValue = []
                for x in player1cards:
                    xValue = db["cardsData"].find_one({'_id': x})
                    dropValue.append(xValue["Name"])
            else:
                player1HasLessThan3 = False
            if len(player2cards) < 4:
                player2HasLessThan3 = True
                drop2Value = []
                for x in player2cards:
                    xValue = db["cardsData"].find_one({'_id': x})
                    drop2Value.append(xValue["Name"])
            else:
                player2HasLessThan3 = False
            if player1HasLessThan3 == False:
                for x in player1cards:
                    xValue = db["cardsData"].find_one({'_id': x})
                    drop.append_option(option=nextcord.SelectOption(
                        label=xValue["Name"], description=xValue["Description"], emoji=xValue["Emoji"]))
                view.add_item(drop)
                embed = nextcord.Embed(
                    title="Select your cards in your battle against " + user.name + "!", color=0x87CEEB)
                try:
                    await ctx.message.author.send(embed=embed, view=view)
                except:
                    await ctx.reply(embed=nextcord.Embed(
                        title="Can't send a message to you!", color=0xFF0000))
                    return
            if player2HasLessThan3 == False:
                for x in player2cards:
                    xValue = db["cardsData"].find_one({'_id': x})
                    drop2.append_option(option=nextcord.SelectOption(
                        label=xValue["Name"], description=xValue["Description"], emoji=xValue["Emoji"]))
                view2.add_item(drop2)
                embed2 = nextcord.Embed(
                    title="Select your cards in your battle against " + ctx.message.author.name + "!", color=0x87CEEB)
                await user.send(embed=embed2, view=view2)
            if (player1HasLessThan3 == False):
                await view.wait()
                dropValue = drop.values
            if (player2HasLessThan3 == False):
                await view2.wait()
                drop2Value = drop2.values
            if dropValue == None or drop2Value == None:
                await user.send("Time Ran Out!")
                await ctx.message.author.send("Time Ran Out!")
                return
# endregion
# region Doing all the battle stuff and saying who wins
            round = 1
            while (len(dropValue) > 0 and len(drop2Value) > 0):
                embedBattle = nextcord.Embed(
                    title="Round " + str(round) + ": " + dropValue[0] + " VS " + drop2Value[0] + "!", color=0xFFFF00)
                dropdownBattle = DropdownBattle()
                dropdownBattle2 = DropdownBattle()
                viewBattle = nextcord.ui.View()
                viewBattle2 = nextcord.ui.View()
                card1 = db["cardsData"].find_one(
                    {"Name": dropValue[0]})
                card2 = db["cardsData"].find_one(
                    {"Name": drop2Value[0]})
                for x in card1["Movements"]:
                    dropdownBattle.append_option(option=nextcord.SelectOption(
                        label=x, description="Power: " + card1["Movements"][x]["Power"], emoji=db["cardsData"].find_one({'_id': "Types"})[card1["Movements"][x]["Type"]]))
                viewBattle.add_item(dropdownBattle)
                for x in card2["Movements"]:
                    dropdownBattle2.append_option(option=nextcord.SelectOption(
                        label=x, description="Power: " + card2["Movements"][x]["Power"], emoji=db["cardsData"].find_one({'_id': "Types"})[card2["Movements"][x]["Type"]]))
                viewBattle2.add_item(dropdownBattle2)
                await ctx.message.author.send(embed=embedBattle, view=viewBattle)
                await user.send(embed=embedBattle, view=viewBattle2)
                await asyncio.gather(viewBattle.wait(), viewBattle2.wait())
                movement1 = dropdownBattle.values[0]
                movement2 = dropdownBattle2.values[0]
                if (movement1 == None or movement2 == None):
                    ctx.reply("Timed out!")
                    return
                playerwon = whichPlayerWon(
                    card1["Movements"][movement1]["Type"], card1["Movements"][movement1]["Power"], card2["Movements"][movement2]["Type"], card2["Movements"][movement2]["Power"])
                emoji1 = db["cardsData"].find_one({'_id': "Types"})[
                    card1["Movements"][movement1]["Type"]]
                emoji2 = db["cardsData"].find_one({'_id': "Types"})[
                    card2["Movements"][movement2]["Type"]]
                if (playerwon == 1):
                    await user.send(embed=nextcord.Embed(title=ctx.message.author.name + " won the round! " + emoji1 + " VS " + emoji2, color=0xFF0000))
                    await ctx.message.author.send(embed=nextcord.Embed(title=ctx.message.author.name + " won the round! " + emoji1 + " VS " + emoji2, color=0x00FF00))
                    drop2Value.pop(0)
                elif(playerwon == 2):
                    await ctx.message.author.send(embed=nextcord.Embed(title=user.name + " won the round! " + emoji2 + " VS " + emoji1, color=0xFF0000))
                    await user.send(embed=nextcord.Embed(title=user.name + " won the round! " + emoji2 + " VS " + emoji1, color=0x00FF00))
                    dropValue.pop(0)
                else:
                    await ctx.message.author.send(embed=nextcord.Embed(title="Draw!", color=0xFFFF00))
                    await user.send(embed=nextcord.Embed(title="Draw!", color=0xFFFF00))
                round += 1
            if (len(dropValue) == 0):
                await ctx.message.author.send(embed=nextcord.Embed(title=user.name + " won the challenge! Try harder next time!", color=0xFF0000))
                await user.send(embed=nextcord.Embed(title=user.name + " won the challenge! Congrats bro! You are :100:", color=0x00FF00))
                await ctx.send(embed=nextcord.Embed(title=user.name + " won against " +
                                                    ctx.message.author.name + ". Congrats to the winner!",  color=0x00FF00))
                db.playersData.update_one({"_id": str(user.id)}, {
                    '$inc': {"Wins": 1}})
            if(len(drop2Value) == 0):
                await ctx.message.author.send(embed=nextcord.Embed(title=ctx.message.author.name + " won the challenge! Congrats bro! You are :100:!", color=0x00FF00))
                await user.send(embed=nextcord.Embed(title=ctx.message.author.name + " won the challenge! Try harder next time!", color=0xFF0000))
                await ctx.send(embed=nextcord.Embed(title=ctx.message.author.name + " won against " +
                                                    user.name + ". Congrats to the winner!", color=0x00FF00))
                db.playersData.update_one({"_id": str(ctx.author.id)}, {
                    '$inc': {"Wins": 1}})
# endregion
# region Ranks Command


@ bot.command()
async def ranking(ctx):
    top5 = db.playersData.find().sort("Wins", -1).limit(5)
    embed = nextcord.Embed(
        title="Top 5 players best players!", color=0x87CEEB)
    position = 1
    for x in top5:
        if position == 1:
            embed.add_field(
                name="🥇 - "+x["Name"], value="Victories: " + str(x["Wins"]), inline=False)
        if position == 2:
            embed.add_field(
                name="🥈 - "+x["Name"], value="Victories: " + str(x["Wins"]), inline=False)
        if position == 3:
            embed.add_field(
                name="🥉 - "+x["Name"], value="Victories: " + str(x["Wins"]), inline=False)
        if position > 3:
            embed.add_field(
                name=str(position) + "° - "+x["Name"], value="Victories: " + str(x["Wins"]), inline=False)
        position += 1
    embed.set_footer(
        text="Congrats to everyone! You are awesome!", icon_url="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/282/fire_1f525.png")
    await ctx.reply(embed=embed)
# endregion
# region Update Name


@ bot.command()
async def update(ctx):
    if db.playersData.count_documents({'_id': str(ctx.author.id)}) > 0:
        db.playersData.update_one({"_id": str(ctx.author.id)}, {
                                  "$set": {"Name": ctx.author.name}})
    else:
        db.playersData.insert_one(
            {"_id": str(ctx.author.id), "Cards": [], "Wins": 0,  "Name": ctx.author.name})
    await ctx.reply(embed=nextcord.Embed(
        title=":white_check_mark: Name updated successfully!", color=0x00FF00))

# endregion
# region Rules Command


@ bot.command()
async def rules(ctx):
    embed = nextcord.Embed(
        title=":white_check_mark: How to Play!", color=0x87CEEB)
    embed.add_field(
        name=":question: Help Command:", value="Check the commands mentioned with the command nfg!help", inline=False)
    embed.add_field(name=":card_box: Cards:",
                    value="Cards are heroes or villains that you can play with, they have movements that you use. Check their details with the card command.", inline=False)
    embed.add_field(name=":movie_camera: Movements:",
                    value="Movements have types, which can determine which one wins against each one. Here's how it works: 👊🏻 > 🧠 > 🦵🏻 > 👊🏻. In case of a draw, the one with the most power wins.", inline=False)
    embed.add_field(name=":crossed_swords: Challenge:",
                    value="Challenge someone with the challenge command.", inline=False)
    embed.add_field(name="😎 That's All Folks!",
                    value="Collect your favorite cards, win matches, become the number one on the rank!", inline=False)
    await ctx.reply(embed=embed)
# endregion
# region Test Claim


@ bot.command()
async def claim(ctx):
    if db.playersData.count_documents({'_id': str(ctx.author.id)}) > 0:
        cardsYouGot = db["playersData"].find_one(
            {'_id': str(ctx.author.id)})["Cards"]
        if len(cardsYouGot) == 0:
            db.playersData.insert_one(
                {"_id": str(ctx.author.id), "Cards": allCards, "Wins": 0,  "Name": ctx.author.name})
            await ctx.reply(embed=nextcord.Embed(
                title=":white_check_mark: Cards Claimed!", color=0x00FF00))
        else:
            await ctx.reply(embed=nextcord.Embed(
                title="Cards already claimed.", color=0xFF0000))
    else:
        db.playersData.insert_one({"_id": str(
            ctx.author.id), "Cards": allCards, "Wins": 0,  "Name": ctx.author.name})
        await ctx.reply(embed=nextcord.Embed(
            title=":white_check_mark: Cards Claimed!", color=0x00FF00))
# endregion
bot.run(token)
