from typing import Any
import discord
from discord.ext import commands
from discord.ui import Button, View, Select
from interactions import SlashCommand, slash_command
import os
# TODO: Sort out env

'''
This solver relies on there being three cases:
a² ⇌ b² + a ⇌ c² + b ⇌ c | Triples case 
a² ⇌ b + a ⇌ c | Single double case
a ⇌ b + b² ⇌ c OR a ⇌ b + a ⇌ c | No doubles case

For the no doubles case we will force the square variant
'''

SHAPES = [["triangle", "square"], ["circle", "square"], ["circle", "triangle"]]
SHAPEDEFINITIONS = {'prism' : ['triangle', 'square'], 'cylinder': ['circle', 'square'],
                    'cone': ['circle', 'triangle'], 'cube': ['square', 'square'],
                    'sphere': ['circle', 'circle'], 'pyramid' : ['triangle', 'triangle']}
inside = [0, 0, 0]
outside = [0, 0, 0]

class InnerSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(InnerSelection("left"))
        self.add_item(InnerSelection("middle"))
        self.add_item(InnerSelection("right"))


class OuterSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OuterSelection("left"))
        self.add_item(OuterSelection("middle"))
        self.add_item(OuterSelection("right"))
        self.add_item(SubmitButton())


class SubmitButton(Button):
    def __init__(self):
        super().__init__(label="Submit", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        message = await Solve()
        await interaction.response.send_message(message)
        


class InnerSelection(Select):
    def __init__(self, position):
        self.Position = position
        options = [
            discord.SelectOption(label="Circle", value="circle"),
            discord.SelectOption(label="Triangle", value="triangle"),
            discord.SelectOption(label="Square", value="square")
        ]
        super().__init__(placeholder=f"Select an option for the inner {position} statue...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        positions = {"left" : 0, "middle" : 1, "right" : 2}
        inside[positions[self.Position]] = interaction.data['values'][0]
        await interaction.response.defer()


class OuterSelection(Select):
    def __init__(self, position):
        self.Position = position
        options = [
            discord.SelectOption(label="Sphere", value='sphere'),
            discord.SelectOption(label="Pyramid", value='pyramid'),
            discord.SelectOption(label="Cube", value='cube'),
            discord.SelectOption(label="Cone", value='cone'),
            discord.SelectOption(label="Cylinder", value='cylinder'),
            discord.SelectOption(label='Triangular Prism', value='prism')
        ]
        super().__init__(placeholder=f"Select an option for the outer {position} statue...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        positions = {"left" : 0, "middle" : 1, "right" : 2}
        outside[positions[self.Position]] = interaction.data['values'][0]
        await interaction.response.defer()

# Define bot command prefix and intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Event when bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


@bot.command(name="solve", description="Solve dissection within the verity encounter!")
async def SolverStart(ctx):
    view = InnerSelectView()
    await ctx.send("Enter inner statue order:", view=view, ephemeral=True, delete_after=100)
    view = OuterSelectView()
    await ctx.send("Enter outer statue order:", view=view, ephemeral=True, delete_after=100)

    
@bot.command(name='vhelp')
async def VHelp(ctx):
    await ctx.send("Current Commands: \n/solve", ephemeral=True)


def GetShapeStructures():
    leftShapes = SHAPEDEFINITIONS[outside[0]]
    midShapes = SHAPEDEFINITIONS[outside[1]]
    rightShapes = SHAPEDEFINITIONS[outside[2]]
    # Unified is used in total count
    unified = leftShapes + midShapes + rightShapes

    if inside[0] not in leftShapes or inside[1] not in midShapes or inside[2] not in rightShapes:
        return False
    elif unified.count('triangle') != 2 or unified.count('square') != 2 or unified.count('circle') != 2:
        return False
    
    return True


async def Solve():
    # Check for doubles
    isDoubles = [False, False, False]
    for i in range(3):
        if outside[i] in  ["sphere", "cube", "pyramid"]:
            isDoubles[i] = True

    # Check for validity
    if inside[0] == inside[1] or inside[1] == inside[2] or inside[0] == inside[2]:
        return "Inside shapes cannot be duplicates!"
    elif not GetShapeStructures():
            return "Invalid shape combination!"


    # Case one (triple)
    if sum(isDoubles) == 3:
        message = f'Dissect left with {inside[0]}, then dissect mid with {inside[1]}. \nDissect left with {inside[0]}, then dissect right with {inside[2]}. \nFinally, dissect mid with {inside[1]}, and dissect right with {inside[2]}.'

    # Case two (one double)
    elif sum(isDoubles) == 1:
        # Identify which is double
        positions = {0 : 'left', 1 : 'middle', 2 : 'right'}
        index = isDoubles.index(True)
        ''' P->p+1 % 3 AND p->p-1 % 3 '''
        message = f'Dissect {positions[index]} with {inside[index]}, then dissect {positions[(index + 1) % 3]} with {inside[(index + 1) % 3]}.'
        message += f'\nDissect {positions[index]} with {inside[index]}, then dissect {positions[(index - 1) % 3]} with {inside[(index - 1) % 3]}.'

    else:
        # Get Shapes value
        left = outside[0]
        mid = outside[1]

        # Calculate and force square case
        duplicate = list(set(left).intersection(mid))
        if inside[0] == duplicate:
            message = f'Dissect left with {inside[0]}, then dissect mid with {inside[1]}. \nDissect mid with {inside[0]}, then dissect right with {inside[2]}.'
        else:
            message = f'Dissect left with {inside[0]}, then dissect mid with {inside[2]}. \nDissect left with {inside[1]}, then dissect right with {inside[2]}.'

    return message


# Start the bot
bot.run(os.environ['VERITY_BOT_KEY'])