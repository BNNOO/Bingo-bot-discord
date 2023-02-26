from os import name
import discord
import sqlite3
from discord.ext import commands
from flask import ctx
import random
import asyncio
import ast
import config

# Connect to the database
conn = sqlite3.connect('bingo113.db')
c = conn.cursor()

# Create the games table if it does not exist
c.execute(
    '''CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, name TEXT, max_players INTEGER, started INTEGER, current_players INTEGER, called_numbers TEXT)''')

# Create the leaderboard table if it does not exist
c.execute(
    '''CREATE TABLE IF NOT EXISTS leaderboard (id INTEGER PRIMARY KEY, game_id INTEGER, player_id INTEGER, player_name TEXT, bingos INTEGER, cards TEXT)''')

# c.execute("ALTER TABLE leaderboard ADD COLUMN number INTEGER;")
# c.execute("ALTER TABLE leaderboard ADD COLUMN numbers TEXT;")
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)
help_command = None
bot.owner_id = 1039117653559742474

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Incorrect command used. Use `!help` to know the available commands.")


@bot.command()
async def create_game(ctx, name: str, max_players: int):
    # Connect to the database
    conn = sqlite3.connect('bingo113.db')
    c = conn.cursor()
    # Check if the game already exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    if c.fetchone() is not None:
        await ctx.send(f"A game with the name '{name}' already exists.")
        return

    # Create the game in the database
    c.execute(
        f"INSERT INTO games (name, max_players, started, current_players, called_numbers) VALUES ('{name}', {max_players}, 0, 0, '')")
    conn.commit()
    await ctx.send(f"Game '{name}' with a maximum of {max_players} players has been created.")


@bot.command()
async def delete_game(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return

    # Delete the game and its leaderboard from the database
    c.execute(f"DELETE FROM games WHERE name='{name}'")
    c.execute(f"DELETE FROM leaderboard WHERE game_id={game[0]}")
    conn.commit()
    await ctx.send(f"Game '{name}' has been deleted.")


def get_current_game_id():
    c.execute("SELECT * FROM games ORDER BY id DESC LIMIT 1")
    game = c.fetchone()
    if game is None:
        return None
    return game[0]


@bot.command()
async def join_game(ctx, name: str):
    game_id = get_current_game_id()
    if game_id is None:
        raise Exception("No game found to join.")

    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return

    # Check if the game has already started
    if game[3] == 1:
        await ctx.send(f"The game '{name}' has already started and cannot accept new players.")
        return

    # Check if the game is full
    if game[4] >= game[2]:
        await ctx.send(f"The game '{name}' is full and cannot accept new players.")
        return

    # Add the player to the game and the leaderboard
    c.execute(f"UPDATE games SET current_players = current_players + 1 WHERE name='{name}'")
    # Add the player to the leaderboard with bingos = 0
    c.execute(
        f"INSERT INTO leaderboard (game_id, player_id, player_name, bingos)   VALUES ({game_id}, {ctx.author.id}, '{ctx.author.name}', 0)")
    conn.commit()
    await ctx.send(f"{ctx.author.name} has joined the game '{name}'.")


@bot.command()
async def leave_game(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return
    else:
        # Check if the player is in the game
        c.execute(f"SELECT * FROM leaderboard WHERE game_id={game[0]} AND player_id={ctx.author.id}")
        player = c.fetchone()
        if player is None:
            await ctx.send(f"{ctx.author.name} is not in the game '{name}'.")
            pass
            return
        else:
            # Remove the player from the game and the leaderboard
            c.execute(f"UPDATE games SET current_players = current_players - 1 WHERE name='{name}'")
            c.execute(f"DELETE FROM leaderboard WHERE game_id={game[0]} AND player_id={ctx.author.id}")
            conn.commit()
            await ctx.send(f"{ctx.author.name} has left the game '{name}'.")

            await ctx.send(f"{ctx.author.name} has left the game '{name}'.")


@bot.command()
async def leaderboard(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return

    # Retrieve the players in the game
    c.execute(f"SELECT player_name, bingos FROM leaderboard WHERE game_id={game[0]} ORDER BY bingos DESC")
    players = c.fetchall()

    # Build the leaderboard message
    leaderboard_message = f"``` Leaderboard for '{name}':\n\n"
    for player in players:
        leaderboard_message += f"{player[0]}: {player[1]} bingos\n"
    leaderboard_message += "```"

    await ctx.send(leaderboard_message)


@bot.command()
async def help(ctx):
    help_embed = discord.Embed(title="Bingo Bot Help", description="List of available commands:")
    help_embed.add_field(name="!create_game [name] [max_players]",
                         value="Creates a new game with the given name and maximum number of players.", inline=False)
    help_embed.add_field(name="!delete_game [name]", value="Deletes the game with the given name.", inline=False)
    help_embed.add_field(name="!join_game [name]", value="Joins the player to the game with the given name.",
                         inline=False)
    help_embed.add_field(name="!leave_game [name]", value="Removes the player from the game with the given name.",
                         inline=False)
    help_embed.add_field(name="!leaderboard [name]", value="Displays the leaderboard for the game with the given name.",
                         inline=False)
    help_embed.add_field(name="!called_numbers [name]",
                         value="Displays the current list of called numbers for the game with the given name.",
                         inline=False)

    help_embed.add_field(name="!generate_cards [name]",
                         value="Generate bingo cards who are in game and start the game.",
                         inline=False)
    help_embed.add_field(name="!call [game name][number]",
                         value="Call the number which is generated in bingo card.",
                         inline=False)

    help_embed.add_field(name="!current_players [name]",
                         value="Displays the current players in the game with the given name.", inline=False)
    help_embed.add_field(name="SUPPORT SERVER]",
                         value="https://discord.gg/jhcCnEdeDM", inline=False)

    await ctx.send(embed=help_embed)


@bot.command()
async def called_numbers(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
    else:
        # Get the called numbers for the game
        called_numbers = game[5].split(',')

        # Build the called numbers message
        numbers_message = f"``` Called Numbers for '{name}':\n\n"
        for number in called_numbers:
            numbers_message += f"{number}\n"
        numbers_message += "```"

        await ctx.send(numbers_message)


import random


def generate_bingo_card():
    bingo_card_list = [[random.randint(1, 100) for _ in range(5)] for _ in range(5)]
    return bingo_card_list


bingo_card = generate_bingo_card()
print(bingo_card[0])


@bot.command()
async def claim_bingo(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return
    else:
        # Check if the player is in the game
        c.execute(f"SELECT * FROM leaderboard WHERE game_id={game[0]} AND player_id={ctx.author.id}")
        player = c.fetchone()
        if player is None:
            await ctx.send(f"{ctx.author.name} is not in the game '{name}'.")
            return
        else:
            # Check if the player has a valid bingo
            if not has_valid_bingo(player):
                await ctx.send(f"{ctx.author.name} does not have a valid bingo.")
                return
            else:
                # Update the player's bingos in the leaderboard
                c.execute(
                    f"UPDATE leaderboard SET bingos = bingos + 1 WHERE game_id={game[0]} AND player_id={ctx.author.id}")
                conn.commit()
                await ctx.send(f"{ctx.author.name} has claimed bingo in the game '{name}'.")
                # Animate the bingo card and mark the player's bingo in the leaderboard
                await ctx.send(f"{ctx.author.name}'s bingo card is being animated...")
                c.execute(
                    f"UPDATE leaderboard SET bingos = bingos + 1 WHERE game_id={game[0]} AND player_id={ctx.author.id}")
                conn.commit()
                await ctx.send(f"{ctx.author.name} has claimed bingo for the game '{name}'!")


def has_valid_bingo(player):
    # Logic to check if the player has
    pass



@bot.command()
async def generate_cards(ctx, game_name: str):
    num_of_numbers = 25
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{game_name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{game_name}' does not exist.")
        return
    # Check if the player is in the game
    c.execute(f"SELECT * FROM leaderboard WHERE game_id={game[0]}")
    players = c.fetchall()
    if not players:
        await ctx.send(f"No players in the game.")
        return
    if num_of_numbers not in [25, 50, 100]:
        await ctx.send(f"Invalid number of numbers. Please choose 25, 50 or 100.")
        return
    for player in players:
        if player[4]:
            await ctx.send(f"{player[3]} already generated the card.")
        else:
            numbers = random.sample(range(1, num_of_numbers + 1), num_of_numbers)
            c.execute(f"UPDATE leaderboard SET numbers = '{numbers}' WHERE game_id={game[0]} and player_id={player[2]}")
            conn.commit()
            bingo_card = "\n".join(" ".join(map(str, numbers[i:i + 5])) for i in range(0, 25, 5))
            embed = discord.Embed(title=f"{player[3]}'s Bingo Card for {game_name}", color=0x00ff00)
            embed.add_field(name="Bingo Card", value=bingo_card, inline=False)
            embed.set_footer(text="Get a row, column or diagonal and claim bingo!")
            await ctx.send(embed=embed)
        c.execute(f"UPDATE games SET started = 1 WHERE name='{game_name}'")
        conn.commit()
        await ctx.send("All players in the game have generated their bingo cards and the game has been started.")


c.execute('''CREATE TABLE IF NOT EXISTS numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    number INTEGER NOT NULL,
    called INTEGER NOT NULL
)''')
conn.commit()


# c.execute("ALTER TABLE leaderboard ADD COLUMN turn INTEGER")




def call(dict_arg, x):
    if type(dict_arg) == dict:
        try:
            return dict_arg[x]
        except KeyError:
            return 'Key not found'
    else:
        return 'Input is not a dictionary'


a = {1: 'one', 2: 'two', 3: 'three'}
print(call(a, 1))


def call(a, b):
    a = [a]
    c = a[b]
    return c


def check_winner(board):
    # Check horizontal rows
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != " ":
            return row[0]

    # Check vertical rows
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != " ":
            return board[0][col]

    # Check diagonal rows
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]

    # No winner
    return None


def play_game():
    board = [['-' for _ in range(3)] for _ in range(3)]
    turn = 'X'
    while True:
        print_board(board)
        row, col = get_move(board, turn)
        board[row][col] = turn
        winner = check_winner(board)
        if winner:
            print(winner + ' won!')
            break
        turn = 'O' if turn == 'X' else 'X'
    print_board(board)


@bot.command()
async def call(ctx, game_name: str, number: int):
    # Check if the game exists
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM games WHERE name='{game_name}'")
    game = cursor.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{game_name}' does not exist.")
        return
    # Check if the game has started
    if not game[3]:
        await ctx.send(f"The game '{game_name}' has not started yet.")
        return
    # Check if the number has been called
    cursor.execute(f"SELECT * FROM numbers WHERE game_id={game[0]} and number={number}")
    number_data = cursor.fetchone()
    if number_data is not None:
        await ctx.send(f"The number {number} has already been called in the game '{game_name}'.")
        return
    # Check if player is in the game
    cursor.execute(f"SELECT * FROM leaderboard WHERE game_id={game[0]} and player_id={ctx.author.id}")
    current_player = cursor.fetchone()
    if current_player is None:
        await ctx.send(f"You are not a player in the game '{game_name}'.")
        return
    # Check if it's the calling player's turn
    cursor.execute(f"SELECT * FROM leaderboard WHERE game_id={game[0]}")
    players = cursor.fetchall()
    current_turn_player_idx = game[2] % len(players)
    current_turn_player = players[current_turn_player_idx]
    if current_turn_player[1] != current_player[1]:
        await ctx.send(
            f"It is not your turn to call numbers in the game '{game_name}'. It is currently {current_turn_player[3]}'s turn.")
        return
    # Call the number
    cursor.execute(f"INSERT INTO numbers (game_id, number, called) VALUES ({game[0]}, {number}, {current_player[1]})")
    conn.commit()
    await ctx.send(f"{ctx.author.name} called the number {number} in the game '{game_name}'.")
    # Check if any player has won
    # Check if any player has won
    for player in players:
        cursor.execute(f"SELECT * FROM numbers WHERE game_id={game[0]} and called={player[1]}")
        called_numbers = [number[2] for number in cursor.fetchall()]
        bingo_card = [int(x) for x in str(player[4])]
        for i in range(5):
            row = bingo_card[i * 5:(i + 1) * 5]
            if all(num in called_numbers for num in row):
                # Code to handle the winning condition here
                cursor.execute(f"UPDATE games SET ended=1 WHERE id={game[0]}")
                conn.commit()
                await ctx.send(f"{player[3]} has won the game '{game_name}' with a row!")
                return

                # Update the turn
                cursor.execute(f"UPDATE games SET turn=turn+1 WHERE id={game[0]}")
                conn.commit()
                await ctx.send(f"It is now {players[(current_turn_player_idx + 1) % len(players)][3]}'s turn.")
                cursor.execute(f"DELETE FROM games WHERE name='{game_name}'")
                cursor.execute(f"DELETE FROM leaderboard WHERE game_id={game[0]}")
                cursor.execute(f"DELETE FROM numbers WHERE game_id={game[0]}")
                conn.commit()
                return
            col = [row[i] for row in bingo_card[i::5] if type(row) == list]
            if all(num in called_numbers for num in col):
                await ctx.send(f"{player[3]} has won the game '{game_name}' with a column!")
    cursor.execute(f"DELETE FROM games WHERE name='{game_name}'")
    cursor.execute(f"DELETE FROM leaderboard WHERE game_id={game[0]}")
    cursor.execute(f"DELETE FROM numbers WHERE game_id={game[0]}")
    conn.commit()
    return
    diag1 = [bingo_card[i] for i in range(0, 26, 6)]
    diag2 = [bingo_card[i] for i in range(4, 20, 4)]
    if all(num in called_numbers for num in diag1) or all(num in called_numbers for num in diag2):
        await ctx.send(f"{player[3]} has won the game '{game_name}' with a diagonal!")
    c.execute(f"DELETE FROM games WHERE name='{game_name}'")
    c.execute(f"DELETE FROM leaderboard WHERE game_id={game[0]}")
    c.execute(f"DELETE FROM numbers WHERE game_id={game[0]}")
    conn.commit()
    return
    # Update turn
    c.execute(f"UPDATE games SET turn={game[2] + 1} WHERE name='{game_name}'")
    conn.commit()


# called_numbers = []


@bot.command()
async def calls(ctx, game_name: str):
    game = get_game(game_name)
    if not game or not game[2]:
        await ctx.send(f"The game '{game_name}' does not exist or has not started.")
        return
    players = get_players(game[0])
    if not players:
        await ctx.send(f"No players in the game.")
        return
    called_numbers = []

    # Get the total number of cards and numbers in each card
    total_cards = get_total_cards(game[0])
    total_numbers = get_total_numbers(game[0])

    for i in range(total_cards * total_numbers):
        cards = get_cards(game[0])
        numbers = [num for card in cards for num in card[0]]
        available_numbers = list(set(numbers) - set(called_numbers))
        if not available_numbers:
            await ctx.send("All numbers have been called, the game is over.")
            update_game_status(game_name, False)
            return
        number = random.choice(available_numbers)
        called_numbers.append(number)
        for player in players:
            card = get_card(game[0], player[2])
            if number in card:
                card[card.index(number)] = "X"
                update_card(game[0], player[2], card)
                if all(num == "X" for num in card):
                    await ctx.send(f"{player[3]} has won the game!")
                    update_game_status(game_name, False)
                    return
        await ctx.send(f"The number called is: {number}")
        await asyncio.sleep(3)
        for player in players:
            card = get_card(game[0], player[2])
            # Display the card




@bot.command()
async def current_players(ctx, name: str):
    # Check if the game exists
    c.execute(f"SELECT * FROM games WHERE name='{name}'")
    game = c.fetchone()
    if game is None:
        await ctx.send(f"A game with the name '{name}' does not exist.")
        return

    # Retrieve the current players for the game
    c.execute(f"SELECT player_name FROM leaderboard WHERE game_id={game[0]}")
    players = c.fetchall()

    # Build the current players message
    players_message = f"``` Current Players for '{name}':\n\n"
    for player in players:
        players_message += f"{player[0]}\n"
    players_message += "```"

    await ctx.send(players_message)
    return




@bot.command()
async def servers(ctx):
    if ctx.author.id == bot.owner_id:
        # your code here
        guilds = bot.guilds
        num_guilds = len(guilds)
        guild_names = [guild.name for guild in guilds]
        embed = discord.Embed(title="Servers", description=f"Bot is connected to {num_guilds} servers.")
        embed.add_field(name="Server Names", value="\n".join(guild_names), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You are not the bot owner.")

bot.run(config.TOKEN)
