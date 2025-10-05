import os
import asyncio
import discord
from discord.ext import tasks
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Configuration
TOKEN = os.getenv('DISCORD_TOKEN')
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'discord_bot')
DB_USER = os.getenv('DB_USER', 'bot_user')
DB_PASSWORD = os.getenv('DB_PASSWORD')
TARGET_RANK_ID = int(os.getenv('TARGET_RANK_ID', '123'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL_SECONDS', '300'))  # 5 minutes default

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = discord.Bot(intents=intents)
db_pool = None


async def init_db():
    """Initialize database connection pool"""
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        min_size=1,
        max_size=10
    )
    print("Database connection pool established")


async def close_db():
    """Close database connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        print("Database connection pool closed")


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_and_update_ranks():
    """Check database for users with status=2 and update their ranks"""
    if not db_pool:
        print("Database pool not initialized")
        return

    try:
        # Get all users with status = 2
        async with db_pool.acquire() as conn:
            users_to_update = await conn.fetch(
                "SELECT user_id, guild_id FROM users WHERE status = 2"
            )

        if not users_to_update:
            print("No users with status=2 found")
            return

        print(f"Found {len(users_to_update)} users to update")

        for record in users_to_update:
            user_id = record['user_id']
            guild_id = record['guild_id']

            try:
                guild = bot.get_guild(guild_id)
                if not guild:
                    print(f"Guild {guild_id} not found")
                    continue

                member = guild.get_member(user_id)
                if not member:
                    # Try fetching the member
                    try:
                        member = await guild.fetch_member(user_id)
                    except discord.NotFound:
                        print(f"Member {user_id} not found in guild {guild_id}")
                        continue

                # Get current roles (excluding @everyone)
                current_roles = [role for role in member.roles if role != guild.default_role]

                # Remove all current roles
                if current_roles:
                    await member.remove_roles(*current_roles, reason="Status 2 - Rank cleanup")
                    print(f"Removed {len(current_roles)} roles from user {user_id}")

                # Add the target rank
                target_role = guild.get_role(TARGET_RANK_ID)
                if target_role:
                    await member.add_roles(target_role, reason="Status 2 - Assigned target rank")
                    print(f"Added rank {TARGET_RANK_ID} to user {user_id}")
                else:
                    print(f"Target role {TARGET_RANK_ID} not found in guild {guild_id}")

                # Update status in database to prevent re-processing (optional)
                # async with db_pool.acquire() as conn:
                #     await conn.execute(
                #         "UPDATE users SET status = 3 WHERE user_id = $1 AND guild_id = $2",
                #         user_id, guild_id
                #     )

            except discord.Forbidden:
                print(f"Missing permissions to modify roles for user {user_id}")
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")

    except Exception as e:
        print(f"Error in check_and_update_ranks: {e}")


@check_and_update_ranks.before_loop
async def before_check_ranks():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()
    print("Rank check task started")


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

    if not check_and_update_ranks.is_running():
        check_and_update_ranks.start()


@bot.slash_command(name="check_ranks", description="Manually trigger rank check")
async def manual_check(ctx):
    """Manual command to trigger rank checking"""
    await ctx.defer()

    if not db_pool:
        await ctx.respond("Database connection not established", ephemeral=True)
        return

    await check_and_update_ranks()
    await ctx.respond("Rank check completed!", ephemeral=True)


@bot.slash_command(name="status", description="Check bot status")
async def status(ctx):
    """Check bot status"""
    db_status = "Connected" if db_pool else "Disconnected"
    task_status = "Running" if check_and_update_ranks.is_running() else "Stopped"

    embed = discord.Embed(title="Bot Status", color=discord.Color.blue())
    embed.add_field(name="Database", value=db_status, inline=True)
    embed.add_field(name="Rank Check Task", value=task_status, inline=True)
    embed.add_field(name="Check Interval", value=f"{CHECK_INTERVAL}s", inline=True)
    embed.add_field(name="Target Rank ID", value=TARGET_RANK_ID, inline=True)

    await ctx.respond(embed=embed, ephemeral=True)


async def main():
    """Main function to run the bot"""
    await init_db()

    try:
        await bot.start(TOKEN)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
