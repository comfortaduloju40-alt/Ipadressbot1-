import os
import io
import logging
import requests
import socket
import json
from datetime import datetime
import telebot
from telebot import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN)

user_sessions = {}


def lookup_ip(ip: str) -> dict:
    try:
        url = f"https://ipapi.co/{ip}/json/"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "error" in data:
            return {"error": data.get("reason", "Invalid IP")}
        return data
    except Exception as e:
        return {"error": str(e)}


def lookup_my_ip(ip: str) -> dict:
    try:
        url = f"https://ipapi.co/{ip}/json/"
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_bot_ip() -> str:
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=10)
        return r.json().get("ip", "Unknown")
    except:
        return "Unknown"


def flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🌍"
    return "".join(chr(0x1F1E0 + ord(c) - ord("A"))
                   for c in country_code.upper())


def format_ip_info(data: dict, title="🔍 IP Lookup Result") -> str:
    if "error" in data:
        return f"❌ Error: {data['error']}"

    ip          = data.get("ip", "N/A")
    city        = data.get("city", "N/A")
    region      = data.get("region", "N/A")
    country     = data.get("country_name", "N/A")
    country_code= data.get("country_code", "")
    postal      = data.get("postal", "N/A")
    lat         = data.get("latitude", "N/A")
    lon         = data.get("longitude", "N/A")
    tz          = data.get("timezone", "N/A")
    utc_offset  = data.get("utc_offset", "N/A")
    org         = data.get("org", "N/A")
    asn         = data.get("asn", "N/A")
    isp         = data.get("org", "N/A")
    currency    = data.get("currency", "N/A")
    currency_name = data.get("currency_name", "N/A")
    languages   = data.get("languages", "N/A")
    calling_code= data.get("country_calling_code", "N/A")
    flag        = flag_emoji(country_code)

    text = (
        f"{title}\n"
        f"{'─' * 30}\n\n"
        f"🌐 *IP Address:* `{ip}`\n\n"
        f"📍 *Location*\n"
        f"  {flag} Country: {country} ({country_code})\n"
        f"  🏙 City: {city}\n"
        f"  🗺 Region: {region}\n"
        f"  📮 Postal: {postal}\n"
        f"  📞 Calling Code: {calling_code}\n\n"
        f"🗺 *Coordinates*\n"
        f"  📌 Lat: {lat} / Lon: {lon}\n\n"
        f"⏰ *Time*\n"
        f"  🕐 Timezone: {tz}\n"
        f"  🕰 UTC Offset: {utc_offset}\n\n"
        f"🏢 *Network*\n"
        f"  🔌 ASN: {asn}\n"
        f"  🏭 ISP/Org: {org}\n\n"
        f"💱 *Currency*\n"
        f"  💰 {currency_name} ({currency})\n\n"
        f"🗣 *Languages:* {languages}\n"
    )
    return text


def format_whois(data: dict) -> str:
    if "error" in data:
        return f"❌ Error: {data['error']}"

    ip           = data.get("ip", "N/A")
    asn          = data.get("asn", "N/A")
    org          = data.get("org", "N/A")
    country_code = data.get("country_code", "")
    country      = data.get("country_name", "N/A")
    flag         = flag_emoji(country_code)

    text = (
        f"📋 *Whois / ASN Info*\n"
        f"{'─' * 30}\n\n"
        f"🌐 IP: `{ip}`\n"
        f"🔌 ASN: `{asn}`\n"
        f"🏭 Organization: {org}\n"
        f"{flag} Country: {country}\n"
    )
    return text


def is_valid_ip(ip: str) -> bool:
    try:
        socket.inet_aton(ip)
        return True
    except:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except:
            return False


def resolve_domain(domain: str) -> str:
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        return None


# ---- Bot flow ----

def send_main_menu(cid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Lookup IP", callback_data="menu:lookup"),
        types.InlineKeyboardButton("📡 My IP Info", callback_data="menu:myip"),
        types.InlineKeyboardButton("🌐 Domain → IP", callback_data="menu:domain"),
        types.InlineKeyboardButton("📋 Whois / ASN", callback_data="menu:whois"),
        types.InlineKeyboardButton("🗺 IP on Map", callback_data="menu:map"),
        types.InlineKeyboardButton("⚡ Bulk Lookup", callback_data="menu:bulk"),
    )
    bot.send_message(
        cid,
        "🌐 *IP Address Bot*\n\n"
        "What would you like to do?",
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    cid = message.chat.id
    bot.send_message(
        cid,
        "👋 *IP Address Bot*\n\n"
        "Everything you need to know about any IP address!\n\n"
        "🔍 IP Lookup — full location and network info\n"
        "📡 My IP — look up your own IP\n"
        "🌐 Domain → IP — resolve any domain\n"
        "📋 Whois / ASN — network ownership info\n"
        "🗺 Map — see IP location on a map\n"
        "⚡ Bulk — look up multiple IPs at once\n\n"
        "Send /menu to open the menu\n"
        "Or just send any IP address directly!",
        parse_mode="Markdown",
    )
    send_main_menu(cid)


@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    send_main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("menu:"))
def handle_menu(call):
    cid = call.message.chat.id
    action = call.data.split(":")[1]
    session = user_sessions.setdefault(cid, {})
    bot.answer_callback_query(call.id)

    if action == "lookup":
        session["step"] = "lookup"
        bot.edit_message_text(
            "🔍 *IP Lookup*\n\nSend any IP address:\n_(e.g. 8.8.8.8 or 1.1.1.1)_",
            cid, call.message.message_id, parse_mode="Markdown",
        )

    elif action == "myip":
        bot.edit_message_text(
            "📡 *Your IP Info*\n\n"
            "Send me your IP address and I'll look it up!\n\n"
            "_(To find your IP, visit_ https://whatismyipaddress.com _on your device)_",
            cid, call.message.message_id, parse_mode="Markdown",
        )
        session["step"] = "myip"

    elif action == "domain":
        session["step"] = "domain"
        bot.edit_message_text(
            "🌐 *Domain → IP*\n\nSend a domain name:\n_(e.g. google.com or github.com)_",
            cid, call.message.message_id, parse_mode="Markdown",
        )

    elif action == "whois":
        session["step"] = "whois"
        bot.edit_message_text(
            "📋 *Whois / ASN Lookup*\n\nSend an IP address:",
            cid, call.message.message_id, parse_mode="Markdown",
        )

    elif action == "map":
        session["step"] = "map"
        bot.edit_message_text(
            "🗺 *IP on Map*\n\nSend an IP address to see its location on a map:",
            cid, call.message.message_id, parse_mode="Markdown",
        )

    elif action == "bulk":
        session["step"] = "bulk"
        bot.edit_message_text(
            "⚡ *Bulk IP Lookup*\n\n"
            "Send multiple IP addresses separated by new lines or spaces:\n\n"
            "Example:\n`8.8.8.8\n1.1.1.1\n208.67.222.222`",
            cid, call.message.message_id, parse_mode="Markdown",
        )


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    cid = message.chat.id
    text = message.text.strip()
    session = user_sessions.get(cid, {})
    step = session.get("step", "lookup")

    # Direct IP input with no session
    if is_valid_ip(text):
        do_lookup(cid, text)
        return

    if step == "lookup":
        if is_valid_ip(text):
            do_lookup(cid, text)
        else:
            resolved = resolve_domain(text)
            if resolved:
                msg = bot.send_message(
                    cid,
                    f"🌐 Resolved `{text}` → `{resolved}`\nLooking up…",
                    parse_mode="Markdown",
                )
                do_lookup(cid, resolved)
                bot.delete_message(cid, msg.message_id)
            else:
                bot.send_message(
                    cid,
                    "❌ Invalid IP address or domain.\nSend like: `8.8.8.8` or `google.com`",
                    parse_mode="Markdown",
                )

    elif step == "myip":
        if is_valid_ip(text):
            do_lookup(cid, text, title="📡 Your IP Info")
        else:
            bot.send_message(cid, "❌ Please send a valid IP address.", parse_mode="Markdown")

    elif step == "domain":
        domain = text.replace("https://", "").replace("http://", "").split("/")[0]
        resolved = resolve_domain(domain)
        if resolved:
            processing = bot.send_message(
                cid,
                f"✅ `{domain}` → `{resolved}`\n⏳ Looking up IP…",
                parse_mode="Markdown",
            )
            data = lookup_ip(resolved)
            result = format_ip_info(data, title=f"🌐 Domain: {domain}")
            bot.edit_message_text(
                result, cid, processing.message_id, parse_mode="Markdown"
            )
        else:
            bot.send_message(
                cid,
                f"❌ Could not resolve `{text}`.\nMake sure it's a valid domain.",
                parse_mode="Markdown",
            )

    elif step == "whois":
        if is_valid_ip(text):
            processing = bot.send_message(cid, "⏳ Looking up Whois…")
            data = lookup_ip(text)
            result = format_whois(data)
            bot.edit_message_text(
                result, cid, processing.message_id, parse_mode="Markdown"
            )
        else:
            bot.send_message(cid, "❌ Please send a valid IP address.")

    elif step == "map":
        ip = text
        if not is_valid_ip(ip):
            resolved = resolve_domain(text)
            if resolved:
                ip = resolved
            else:
                bot.send_message(cid, "❌ Invalid IP or domain.")
                return
        processing = bot.send_message(cid, "⏳ Getting location…")
        data = lookup_ip(ip)
        if "error" in data:
            bot.edit_message_text(
                f"❌ {data['error']}", cid, processing.message_id
            )
            return
        lat = data.get("latitude")
        lon = data.get("longitude")
        city = data.get("city", "Unknown")
        country = data.get("country_name", "Unknown")
        flag = flag_emoji(data.get("country_code", ""))
        if lat and lon:
            bot.delete_message(cid, processing.message_id)
            bot.send_location(cid, latitude=lat, longitude=lon)
            bot.send_message(
                cid,
                f"📍 *{ip}*\n{flag} {city}, {country}\n"
                f"Coordinates: `{lat}, {lon}`",
                parse_mode="Markdown",
            )
        else:
            bot.edit_message_text(
                "❌ Could not get coordinates.", cid, processing.message_id
            )

    elif step == "bulk":
        import re
        ips = re.split(r"[\s,\n]+", text)
        ips = [i.strip() for i in ips if i.strip()]
        valid = [i for i in ips if is_valid_ip(i)]

        if not valid:
            bot.send_message(cid, "❌ No valid IPs found. Send IPs separated by spaces or new lines.")
            return
        if len(valid) > 10:
            bot.send_message(cid, f"⚠️ Max 10 IPs at once. Using first 10 of {len(valid)}.")
            valid = valid[:10]

        processing = bot.send_message(
            cid, f"⏳ Looking up {len(valid)} IPs…"
        )
        results = []
        for ip in valid:
            data = lookup_ip(ip)
            if "error" not in data:
                country = data.get("country_name", "N/A")
                city = data.get("city", "N/A")
                org = data.get("org", "N/A")
                flag = flag_emoji(data.get("country_code", ""))
                results.append(
                    f"🌐 `{ip}`\n"
                    f"  {flag} {city}, {country}\n"
                    f"  🏭 {org}"
                )
            else:
                results.append(f"❌ `{ip}` — {data['error']}")

        output = f"⚡ *Bulk Lookup Results*\n{'─' * 28}\n\n" + "\n\n".join(results)
        bot.edit_message_text(
            output, cid, processing.message_id, parse_mode="Markdown"
        )

    else:
        send_main_menu(cid)


def do_lookup(cid, ip, title="🔍 IP Lookup Result"):
    processing = bot.send_message(cid, f"⏳ Looking up `{ip}`…", parse_mode="Markdown")
    data = lookup_ip(ip)
    result = format_ip_info(data, title=title)
    bot.edit_message_text(
        result, cid, processing.message_id, parse_mode="Markdown"
    )
    # Offer follow-up actions
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🗺 Show on Map", callback_data=f"action:map:{ip}"),
        types.InlineKeyboardButton("📋 Whois", callback_data=f"action:whois:{ip}"),
        types.InlineKeyboardButton("🔄 New Lookup", callback_data="menu:lookup"),
    )
    bot.send_message(
        cid,
        "What's next?",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("action:"))
def handle_action(call):
    cid = call.message.chat.id
    parts = call.data.split(":")
    action = parts[1]
    ip = parts[2] if len(parts) > 2 else ""
    bot.answer_callback_query(call.id)

    if action == "map":
        processing = bot.send_message(cid, "⏳ Getting location…")
        data = lookup_ip(ip)
        lat = data.get("latitude")
        lon = data.get("longitude")
        city = data.get("city", "Unknown")
        country = data.get("country_name", "Unknown")
        flag = flag_emoji(data.get("country_code", ""))
        if lat and lon:
            bot.delete_message(cid, processing.message_id)
            bot.send_location(cid, latitude=lat, longitude=lon)
            bot.send_message(
                cid,
                f"📍 *{ip}*\n{flag} {city}, {country}",
                parse_mode="Markdown",
            )
        else:
            bot.edit_message_text("❌ No coordinates.", cid, processing.message_id)

    elif action == "whois":
        processing = bot.send_message(cid, "⏳ Fetching Whois…")
        data = lookup_ip(ip)
        result = format_whois(data)
        bot.edit_message_text(result, cid, processing.message_id, parse_mode="Markdown")


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    cid = message.chat.id
    user_sessions.pop(cid, None)
    bot.send_message(cid, "❌ Cancelled.")
    send_main_menu(cid)


if __name__ == "__main__":
    logger.info(f"Token loaded: {'YES' if BOT_TOKEN else 'NO'}")
    logger.info("IP Address bot starting…")
    bot.infinity_polling()
