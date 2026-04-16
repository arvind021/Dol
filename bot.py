import requests
import re
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
import config
from database import Database

# Initialize database
db = Database()

broadcast_active = False

async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            chat_id=config.CHANNEL_USERNAME, 
            user_id=user_id
        )
        return member.status in ['member', 'creator', 'administrator']
    except TelegramError:
        return False

async def is_owner(user_id):
    return user_id == config.OWNER_ID

async def get_phone_from_api(query):
    """Fetch phone number from API"""
    try:
        response = requests.get(
            config.API_URL, 
            params={"key": config.API_KEY, "q": query}, 
            timeout=10
        )
        data = response.json()
        phone_info = data.get("phone_info", {})
        
        if phone_info.get("success"):
            return phone_info.get("number")
        else:
            return None
    except Exception:
        return None

# Group command: /num <user_id>
async def num_command(update, context):
    user_id = update.effective_user.id
    
    # Check if user joined channel (skip for groups if you want)
    if update.effective_chat.type == "private":
        if not await is_member(user_id, context):
            await update.message.reply_text(
                f"❌ Please join {config.CHANNEL_USERNAME} first!"
            )
            return
        
        # Check daily limit for private chat
        can_use, remaining = db.can_use_bot(user_id)
        if not can_use:
            await update.message.reply_text(
                "❌ **Daily Limit Reached!**\n\n"
                "You can only use this bot **10 times per day**.\n"
                "Your limit will reset at midnight (12:00 AM).\n\n"
                f"📊 Used: 10/10 today",
                parse_mode="Markdown"
            )
            return
    
    # Get user_id from command
    if context.args:
        target_id = context.args[0]
    else:
        await update.message.reply_text(
            "❌ Usage: `/num <user_id>`\nExample: `/num 8376408923`\n\n"
            "Or reply to any message with `/num`",
            parse_mode="Markdown"
        )
        return
    
    # Validate if it's a number
    if not target_id.isdigit():
        await update.message.reply_text("❌ User ID must be a number!")
        return
    
    phone = await get_phone_from_api(target_id)
    
    if phone:
        await update.message.reply_text(f"📞 **Phone Number:** `{phone}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Phone number not found for ID: `{target_id}`",
            parse_mode="Markdown"
        )
    
    # Show remaining uses for private chat
    if update.effective_chat.type == "private":
        remaining = db.get_remaining_uses(user_id)
        if remaining > 0:
            await update.message.reply_text(
                f"📊 **Remaining today:** {remaining}/10",
                parse_mode="Markdown"
            )

# Reply handler: reply to any message with /num
async def reply_num_handler(update, context):
    user_id = update.effective_user.id
    
    # Check if user joined channel (skip for groups)
    if update.effective_chat.type == "private":
        if not await is_member(user_id, context):
            await update.message.reply_text(f"❌ Please join {config.CHANNEL_USERNAME} first!")
            return
        
        # Check daily limit for private chat
        can_use, remaining = db.can_use_bot(user_id)
        if not can_use:
            await update.message.reply_text(
                "❌ **Daily Limit Reached!**\n\n"
                "You can only use this bot **10 times per day**.\n"
                "Your limit will reset at midnight (12:00 AM).\n\n"
                f"📊 Used: 10/10 today",
                parse_mode="Markdown"
            )
            return
    
    # Check if replying to a message
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ Reply to any message with `/num` to get their phone number!\n\n"
            "Or use: `/num <user_id>`",
            parse_mode="Markdown"
        )
        return
    
    # Get the replied user's ID
    replied_user = update.message.reply_to_message.from_user
    target_id = replied_user.id
    
    # For groups, show username as well
    username = f"@{replied_user.username}" if replied_user.username else replied_user.first_name
    
    # Show searching message
    searching_msg = await update.message.reply_text(f"🔍 Searching for {username}...")
    
    phone = await get_phone_from_api(str(target_id))
    
    if phone:
        await searching_msg.edit_text(
            f"📞 **Phone Number for {username}:**\n`{phone}`",
            parse_mode="Markdown"
        )
    else:
        await searching_msg.edit_text(
            f"❌ No phone number found for {username} (ID: `{target_id}`)",
            parse_mode="Markdown"
        )
    
    # Show remaining uses for private chat
    if update.effective_chat.type == "private":
        remaining = db.get_remaining_uses(user_id)
        if remaining > 0:
            await update.message.reply_text(
                f"📊 **Remaining today:** {remaining}/10",
                parse_mode="Markdown"
            )

# Normal private chat handler (send user_id directly)
async def private_chat_handler(update, context):
    user_id = update.effective_user.id
    
    if not await is_member(user_id, context):
        await update.message.reply_text(f"❌ Please join {config.CHANNEL_USERNAME} first!")
        return
    
    # Check daily limit
    can_use, remaining = db.can_use_bot(user_id)
    if not can_use:
        await update.message.reply_text(
            "❌ **Daily Limit Reached!**\n\n"
            "You can only use this bot **10 times per day**.\n"
            "Your limit will reset at midnight (12:00 AM).\n\n"
            f"📊 Used: 10/10 today",
            parse_mode="Markdown"
        )
        return
    
    input_text = update.message.text.strip()
    
    # Check if input is a number (user_id)
    if input_text.isdigit() and len(input_text) >= 8:
        phone = await get_phone_from_api(input_text)
        
        if phone:
            await update.message.reply_text(f"📞 **Phone Number:** `{phone}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"❌ Phone number not found for ID: `{input_text}`\n\n"
                f"💡 Tip: Try using `/num {input_text}` in groups!",
                parse_mode="Markdown"
            )
        
        # Show remaining uses
        if remaining > 0:
            await update.message.reply_text(
                f"📊 **Remaining today:** {remaining}/10",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "❌ Please send a valid User ID (numbers only)\n\n"
            "Example: `8376408923`\n\n"
            f"📊 **Remaining today:** {remaining}/10",
            parse_mode="Markdown"
        )

# Owner panel functions
async def owner_panel(update, context):
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("👥 Total Users", callback_data="users")],
        [InlineKeyboardButton("📈 Reset User Limits", callback_data="reset_limits")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(
            "🔧 **Owner Control Panel**\n\nChoose an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "🔧 **Owner Control Panel**\n\nChoose an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "broadcast":
        global broadcast_active
        broadcast_active = True
        await query.message.edit_text(
            "📢 **Broadcast Mode Active**\n\n"
            "Send me the message you want to broadcast.\n"
            "Type /cancel to stop."
        )
    elif query.data == "stats":
        await query.message.edit_text(
            f"📊 **Bot Statistics**\n\n"
            f"👑 Owner ID: `{config.OWNER_ID}`\n"
            f"📡 API Status: Active\n"
            f"🔑 API Key: {config.API_KEY[:5]}...\n\n"
            f"💡 Group Features:\n"
            f"• Reply with /num\n"
            f"• /num <user_id>\n\n"
            f"📊 Private Limit: 10 uses/day per user",
            parse_mode="Markdown"
        )
    elif query.data == "users":
        # Get total users from database
        cursor = db.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user_usage')
        total_users = cursor.fetchone()[0]
        
        await query.message.edit_text(
            f"👥 **User Statistics**\n\n"
            f"Total Users: {total_users}\n"
            f"Daily Limit: 10 uses/user/day\n\n"
            f"📊 All user data is saved in SQLite database",
            parse_mode="Markdown"
        )
    elif query.data == "reset_limits":
        # Reset all user limits (for testing)
        cursor = db.conn.cursor()
        cursor.execute('UPDATE user_usage SET usage_count = 0, last_used_date = "2000-01-01"')
        db.conn.commit()
        await query.message.edit_text(
            "✅ All user limits have been reset!\n"
            "Users can now use the bot again.",
            parse_mode="Markdown"
        )
    elif query.data == "close":
        await query.message.delete()

async def cancel_broadcast(update, context):
    global broadcast_active
    if await is_owner(update.effective_user.id):
        broadcast_active = False
        await update.message.reply_text("✅ Broadcast cancelled!")
    else:
        await update.message.reply_text("❌ You are not the owner!")

async def broadcast_message(update, context):
    global broadcast_active
    if not await is_owner(update.effective_user.id):
        return
    if not broadcast_active:
        return
    
    await update.message.reply_text("⚠️ Add full broadcast system with database!")
    broadcast_active = False

async def start(update, context):
    user_id = update.effective_user.id
    
    if update.effective_chat.type != "private":
        # Group message
        await update.message.reply_text(
            "🤖 **Bot is active in this group!**\n\n"
            "Usage:\n"
            "1️⃣ Reply to any message with `/num`\n"
            "2️⃣ Type `/num <user_id>`\n\n"
            "Example: `/num 8376408923`\n\n"
            "📊 Private chat: 10 uses/day",
            parse_mode="Markdown"
        )
        return
    
    # Private chat
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"❌ You must join our channel first!\n\n👉 Join: {config.CHANNEL_USERNAME}\n\nThen click /start again."
        )
        return
    
    # Get remaining uses
    remaining = db.get_remaining_uses(user_id)
    
    keyboard = []
    if await is_owner(user_id):
        keyboard.append([InlineKeyboardButton("🔧 Owner Panel", callback_data="owner_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        f"✅ **Welcome to Phone Number Bot!**\n\n"
        f"**Private Chat:**\n"
        f"• Send any User ID → Get phone number\n"
        f"• **Daily Limit:** 10 times per day\n"
        f"• **Remaining today:** {remaining}/10\n\n"
        f"**Groups:**\n"
        f"• Reply to a message with `/num`\n"
        f"• Type `/num <user_id>`\n\n"
        f"📢 Channel: {config.CHANNEL_USERNAME}",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def owner_button_handler(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "owner_panel":
        await owner_panel(update, context)

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", owner_panel))
    app.add_handler(CommandHandler("cancel", cancel_broadcast))
    app.add_handler(CommandHandler("num", num_command))
    
    # Reply handler (for /num in reply)
    app.add_handler(MessageHandler(
        filters.Regex(r'^/num$') & filters.REPLY, 
        reply_num_handler
    ))
    
    # Private chat handler (send user_id directly)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        private_chat_handler
    ))
    
    # Button handlers
    app.add_handler(CallbackQueryHandler(owner_button_handler, pattern="owner_panel"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(broadcast|stats|users|reset_limits|close)$"))
    
    # Broadcast handler
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_message), group=1)
    
    print("🤖 Bot is running...")
    print(f"👑 Owner ID: {config.OWNER_ID}")
    print("📊 Daily Limit: 10 uses per user in private chat")
    app.run_polling()

if __name__ == "__main__":
    main()
