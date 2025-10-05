# DiscordCleanUp

A Discord bot that automatically manages user ranks based on database status. When a user's status is set to 2 in the database, the bot removes all their current ranks and assigns a specific target rank.

## Features

- 🔄 Automatic rank management based on database status
- 🐘 PostgreSQL database integration
- 🐳 Fully containerized with Docker
- ⏰ Configurable check interval
- 🎯 Slash commands for manual checks and status

## Prerequisites

- Docker and Docker Compose installed
- Discord bot token with the following permissions:
  - Manage Roles
  - View Server Members (Member Intent enabled)
- Discord Developer Portal settings:
  - Enable "Server Members Intent" in Bot settings

## Setup

1. Clone the repository:
```bash
git clone https://github.com/PhyrWall/DiscordCleanUp.git
cd DiscordCleanUp
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit `.env` and add your configuration:
```env
DISCORD_TOKEN=your_discord_bot_token_here
DB_PASSWORD=your_secure_password_here
TARGET_RANK_ID=123  # The role ID to assign
CHECK_INTERVAL_SECONDS=300  # Check every 5 minutes
```

4. Start the services:
```bash
docker-compose up -d
```

5. Check logs:
```bash
docker-compose logs -f bot
```

## Database Schema

The bot uses a `users` table with the following structure:

| Column     | Type      | Description                          |
|------------|-----------|--------------------------------------|
| id         | SERIAL    | Primary key                          |
| user_id    | BIGINT    | Discord user ID                      |
| guild_id   | BIGINT    | Discord guild (server) ID            |
| status     | INTEGER   | User status (2 triggers rank change) |
| created_at | TIMESTAMP | Record creation timestamp            |
| updated_at | TIMESTAMP | Record update timestamp              |

## How It Works

1. The bot runs a periodic check (default: every 5 minutes)
2. Queries the database for users where `status = 2`
3. For each user found:
   - Removes all current roles (except @everyone)
   - Adds the configured target rank
4. Logs all actions for monitoring

## Slash Commands

- `/check_ranks` - Manually trigger the rank check process
- `/status` - Display bot status and configuration

## Managing Users

To mark a user for rank cleanup, insert or update their record in the database:

```sql
INSERT INTO users (user_id, guild_id, status)
VALUES (123456789012345678, 987654321098765432, 2)
ON CONFLICT (user_id, guild_id)
DO UPDATE SET status = 2;
```

## Accessing the Database

Connect to the PostgreSQL database:
```bash
docker-compose exec postgres psql -U bot_user -d discord_bot
```

## Stopping the Bot

```bash
docker-compose down
```

To also remove the database volume:
```bash
docker-compose down -v
```

## Configuration

Environment variables:

| Variable                | Default      | Description                    |
|-------------------------|--------------|--------------------------------|
| DISCORD_TOKEN           | (required)   | Discord bot token              |
| DB_NAME                 | discord_bot  | Database name                  |
| DB_USER                 | bot_user     | Database user                  |
| DB_PASSWORD             | (required)   | Database password              |
| TARGET_RANK_ID          | 123          | Role ID to assign              |
| CHECK_INTERVAL_SECONDS  | 300          | How often to check (seconds)   |

## Troubleshooting

**Bot not starting:**
- Check `docker-compose logs bot`
- Verify Discord token is correct
- Ensure Member Intent is enabled in Discord Developer Portal

**Ranks not updating:**
- Check bot has "Manage Roles" permission
- Ensure bot's role is higher than roles it needs to manage
- Verify database connection with `/status` command

**Database connection failed:**
- Check `docker-compose logs postgres`
- Verify DB_PASSWORD is set in .env

## License

MIT
