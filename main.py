import discord
import random
import datetime
import os
import json

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Dictionary to store user balances
balances = {}

# Function to save data to data.json
def save_data():
    with open('data.json', 'w') as file:
        json.dump(balances, file, indent=4)

# Function to load data from data.json
def load_data():
    global balances
    try:
        with open('data.json', 'r') as file:
            balances = json.load(file)
    except FileNotFoundError:
        balances = {}

# Function to handle daily command
async def handle_daily(message):
    user_id = str(message.author.id)
    now = datetime.datetime.now()

    # Check if last_claim exists in balances[user_id]
    if user_id in balances and "last_claim" in balances[user_id]:
        last_claim = datetime.datetime.fromisoformat(balances[user_id]["last_claim"])
        time_since_claim = now - last_claim
        if time_since_claim.total_seconds() < 86400:
            await message.channel.send(f"You can claim your daily Đ coin again in {int((86400 - time_since_claim.total_seconds()) / 3600)} hours.")
            return

    # Generate random Đ coin reward
    reward = random.uniform(0.000, 5.000)
    rare_chance = random.randint(1, 100)
    if rare_chance <= 5:  # 5% chance of getting more than 2.500
        reward = random.uniform(2.500, 3.500)
    elif rare_chance <= 1:  # 1% chance of getting more than 3.500
        reward = random.uniform(3.500, 4.500)
    elif rare_chance <= 0.1:  # 0.1% chance of getting more than 4.500
        reward = random.uniform(4.500, 5.000)

    # Update user balance
    if user_id not in balances:
        balances[user_id] = {"balance": 0, "last_claim": now.isoformat()}
    else:
        balances[user_id]["last_claim"] = now.isoformat()

    balances[user_id]["balance"] += reward

    await message.channel.send(f"{message.author.mention}, you claimed **{reward:.3f}Đ**! Your current balance is **{balances[user_id]['balance']:.3f}Đ**.")

    # Save data after updating balance
    save_data()

# Function to handle balance command
async def handle_balance(message):
    args = message.content.split()
    if len(args) == 1:
        user_id = str(message.author.id)
        if user_id in balances:
            await message.channel.send(f"{message.author.mention}, your balance is `{balances[user_id]['balance']:.3f}Đ`")
        else:
            await message.channel.send(f"{message.author.mention}, your balance is `0.000Đ`")
    elif len(args) == 2:
        # Get the mentioned user
        mentioned_user = message.mentions[0]
        mentioned_user_id = str(mentioned_user.id)
        if mentioned_user_id in balances:
            await message.channel.send(f"{mentioned_user.name}, balance is `{balances[mentioned_user_id]['balance']:.3f}Đ`")
        else:
            await message.channel.send(f"{mentioned_user.name}, balance is `0.000Đ`")
    else:
        await message.channel.send("Invalid command. Please use `balance` or `balance [mention]`")

# Function to handle send command
async def handle_send(message):
    args = message.content.split()
    if len(args) < 3:
        await message.channel.send("Please mention the user you want to send Đ coin to and specify the amount.")
        return
    mentioned_user = message.mentions[0]
    amount = 0
    try:
        amount = float(args[2])
    except ValueError:
        await message.channel.send("Please enter a valid amount of Đ coin to send.")
        return

    if amount < 1:
        await message.channel.send("You cannot send less than 1 Đ coin.")
        return

    # Get the sender's user ID
    sender_id = str(message.author.id)

    if sender_id not in balances:
        await message.channel.send("You don't have any Đ coin to send.")
        return

    # Check if the sender has enough Đ coin
    if balances[sender_id]["balance"] < amount:
        await message.channel.send("You don't have enough Đ coin to send.")
        return

    # Confirm with the sender
    await message.channel.send(f"Are you sure you want to send **{amount:.3f}Đ** to **{mentioned_user.name}**? (yes/no)")

    def check(m):
        return m.author == message.author and m.channel == message.channel and m.content.lower() in ["yes", "no"]

    try:
        response = await client.wait_for("message", check=check, timeout=30)
    except TimeoutError:
        await message.channel.send("Request timed out.")
        return

    if response.content.lower() == "yes":
        # Update sender and receiver balances
        balances[sender_id]["balance"] -= amount
        mentioned_user_id = str(mentioned_user.id)
        if mentioned_user_id not in balances:
            balances[mentioned_user_id] = {"balance": 0}
        balances[mentioned_user_id]["balance"] += amount

        await message.channel.send(f"You have successfully sent **{amount:.3f}Đ** to **{mentioned_user.name}**!")

        # Save data after updating balance
        save_data()

    else:
        await message.channel.send("Transfer cancelled.")

# Event handler for messages
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check if the message is a command
    if message.content == "daily":
        await handle_daily(message)
    elif message.content.startswith("balance"):
        await handle_balance(message)
    elif message.content.startswith("send"):
        await handle_send(message)

# Bot start
@client.event
async def on_ready():
    # Load data when bot is ready
    load_data()
    print(f'We have logged in as {client.user}')

    # Set bot status
    await client.change_presence(activity=discord.Game(name="Inflation 📈"))

# Run the bot
client.run(os.getenv("TOKEN"))