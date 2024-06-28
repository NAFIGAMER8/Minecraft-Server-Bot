import discord
from discord.ext import commands
import subprocess
import time
import os
import requests

# Fetch the environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')

# Check if the environment variables are correctly set
if TOKEN is None:
    raise ValueError("Discord bot token is not set. Please set the DISCORD_BOT_TOKEN environment variable.")
if NGROK_AUTH_TOKEN is None:
    raise ValueError("ngrok auth token is not set. Please set the NGROK_AUTH_TOKEN environment variable.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables for server and ngrok processes
server_process = None
ngrok_process = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def start_server(ctx):
    global server_process, ngrok_process
    try:
        # Start the Minecraft server
        server_process = subprocess.Popen(['java', '-Xmx1024M', '-Xms1024M', '-jar', 'minecraft_server.jar', 'nogui'])
        await ctx.send('Minecraft server is starting!')

        # Give the server some time to start
        time.sleep(10)

        # Start ngrok to expose the server
        ngrok_process = subprocess.Popen(['ngrok', 'tcp', '--authtoken', NGROK_AUTH_TOKEN, '25565'])
        await ctx.send('ngrok tunnel is starting!')

        # Give ngrok some time to establish the tunnel
        time.sleep(5)

        # Retry fetching the ngrok URL until it's available
        retries = 0
        max_retries = 5
        tunnel_url = None

        while retries < max_retries:
            try:
                response = requests.get('http://localhost:4040/api/tunnels')
                response.raise_for_status()
                tunnel_info = response.json()
                tunnel_url = tunnel_info['tunnels'][0]['public_url']
                break
            except requests.exceptions.RequestException as e:
                retries += 1
                time.sleep(2)  # Wait before retrying
                if retries >= max_retries:
                    raise e

        if tunnel_url:
            await ctx.send(f'The server IP is {tunnel_url}')
        else:
            await ctx.send('Failed to retrieve the ngrok URL after multiple attempts.')

    except Exception as e:
        await ctx.send(f'Failed to start server: {e}')

@bot.command()
async def stop_server(ctx):
    global server_process, ngrok_process
    try:
        if server_process:
            server_process.terminate()
            server_process = None
            await ctx.send('Minecraft server has been stopped.')
        else:
            await ctx.send('Minecraft server is not running.')
        
        if ngrok_process:
            ngrok_process.terminate()
            ngrok_process = None
            await ctx.send('ngrok tunnel has been stopped.')
        else:
            await ctx.send('ngrok tunnel is not running.')
            
    except Exception as e:
        await ctx.send(f'Failed to stop server: {e}')

bot.run(TOKEN)
