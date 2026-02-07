# -*- coding: utf-8 -*-
import asyncio, time, os, glob, random, json
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, MessageNotModifiedError, UserDeactivatedError
import config

# --- التخزين الدائم ---
def load_groups():
    if os.path.exists(config.GROUPS_FILE):
        try:
            with open(config.GROUPS_FILE, "r") as f:
                data = json.load(f)
                return data.get("links", []), data.get("ids", [])
        except: pass
    return [], []

def save_groups(links, ids):
    with open(config.GROUPS_FILE, "w") as f:
        json.dump({"links": links, "ids": ids}, f)

# تنظيف الجلسات
for f in glob.glob("bot_control_panel.session*"):
    try: os.remove(f)
    except: pass

# --- الحالة ---
is_paused = False
waiting_for_group = False
account_logs = {}
group_stats = {}
last_success_list = []
replied_users = {}
reply_queue = asyncio.Queue()
processed_messages = set()

def init_log(name):
    account_logs[name] = {
        'unique_ids': set(), 'total_count': 0, 'failed_count': 0,
        'status': 'نشط ✅', 'pause_until': 0
    }

# تحميل البيانات
saved_links, saved_ids = load_groups()
target_links = list(set(['https://t.me/+z7K5sSzvWQU3NTAy', 'https://t.me/pewndgrop', 'https://t.me/M_R515', 'https://t.me/+wtGW0icU0pY2YWY0', 'https://t.me/krkokgrop'] + saved_links))
resolved_ids = list(set(saved_ids))

idx_khas = 0
idx_tabadel = 0

async def worker(client, account_name):
    global is_paused, last_success_list, group_stats
    while True:
        try:
            event, reply_text, retry_count = await reply_queue.get()
            if is_paused:
                await asyncio.sleep(1); await reply_queue.put((event, reply_text, retry_count)); reply_queue.task_done(); continue

            if time.time() < account_logs[account_name].get('pause_until', 0):
                await asyncio.sleep(2); await reply_queue.put((event, reply_text, retry_count)); reply_queue.task_done(); continue

            sent_msg = await client.send_message(event.chat_id, reply_text, reply_to=event.id)
            account_logs[account_name]['total_count'] += 1
            account_logs[account_name]['unique_ids'].add(event.sender_id)
            account_logs[account_name]['status'] = 'نشط ✅'

            try:
                chat = await client.get_entity(event.chat_id); g_title = chat.title if hasattr(chat, 'title') else "قروب"
                msg_link = f"https://t.me/{chat.username}/{sent_msg.id}" if hasattr(chat, 'username') and chat.username else f"https://t.me/c/{str(event.chat_id).replace('-100', '')}/{sent_msg.id}"
            except: g_title = "غير معروف"; msg_link = "غير متاح"

            if g_title not in group_stats: group_stats[g_title] = {'count': 0, 'links': []}
            group_stats[g_title]['count'] += 1
            group_stats[g_title]['links'].append(f"{account_name}: {msg_link}")

            last_success_list.insert(0, f"🕒 {time.strftime('%H:%M')} | {account_name} ➜ {g_title}: {msg_link}")
            if len(last_success_list) > 5: last_success_list.pop()

            print(f"✅ [{account_name}] نجح في الرد."); await asyncio.sleep(random.uniform(15, 20))
        except FloodWaitError as e:
            account_logs[account_name]['status'] = f'مقيد ({e.seconds}ث)'; account_logs[account_name]['pause_until'] = time.time() + e.seconds
            await reply_queue.put((event, reply_text, retry_count))
        except Exception:
            account_logs[account_name]['failed_count'] += 1
            if retry_count < 2: await reply_queue.put((event, reply_text, retry_count + 1))
        finally: reply_queue.task_done()

async def main():
    global is_paused, waiting_for_group, resolved_ids, idx_khas, idx_tabadel
    clients = []

    control_bot = TelegramClient(StringSession(), config.SESSIONS_CONFIG[0]['id'], config.SESSIONS_CONFIG[0]['hash'])
    await control_bot.start(bot_token=config.BOT_TOKEN)

    for s_info in config.SESSIONS_CONFIG:
        client = TelegramClient(StringSession(s_info['str']), s_info['id'], s_info['hash'])
        try:
            await client.start()
            me = await client.get_me(); real_name = f"{me.first_name} {me.last_name or ''}".strip() or "."
            init_log(real_name); clients.append(client); asyncio.create_task(worker(client, real_name))
            print(f"🚀 متصل الآن: [{real_name}]")
        except Exception as e: print(f"❌ خطأ في {s_info['name']}: {e}")

    @control_bot.on(events.CallbackQuery())
    async def catcher(event):
        global is_paused, waiting_for_group
        try:
            data = event.data
            if data == b"report":
                report_msg = "📝 **التقرير التفصيلي**\n━━━━━━━━━━━━━━━━━━\n"
                all_uniques = set(); all_totals = 0
                for name, log in account_logs.items():
                    uniques = len(log['unique_ids']); all_uniques.update(log['unique_ids']); all_totals += log['total_count']
                    status = log['status']
                    if log['pause_until'] > time.time(): status = f"مقيد ({int(log['pause_until']-time.time())}ث)"
                    report_msg += f"👤 **{name}**\n  ├ {status}\n  └ فريد: {uniques} | كلي: {log['total_count']}\n"
                report_msg += f"━━━━━━━━━━━━━━━━━━\n🏆 فريد: {len(all_uniques)} | 📈 إجمالي: {all_totals}"
                await event.edit(report_msg, buttons=[[Button.inline("🔄 تحديث", b"report")], [Button.inline("🔙 رجوع", b"back")]])
            elif data == b"add_group":
                waiting_for_group = True
                await event.edit("📩 أرسل رابط القروب وايدي القروب:\n`الرابط | الايدي`", buttons=[[Button.inline("🔙 إلغاء", b"back")]])
            elif data == b"group_info":
                if not group_stats: await event.answer("⚠️ لا توجد بيانات مسجلة.", alert=True); return
                msg = "💎 **إحصائيات القروبات:**\n━━━━━━━━━━━━━━\n"
                for g_name, data_g in group_stats.items():
                    msg += f"📍 **{g_name}**\n   └ عدد الردود: {data_g['count']}\n"
                    for link in data_g['links'][-3:]: msg += f"   • {link}\n"
                await event.edit(msg, buttons=[[Button.inline("🔄 تحديث", b"group_info")], [Button.inline("🔙 رجوع", b"back")]])
            elif data == b"last_replies":
                msg = "🕒 **آخر 5 ردود:**\n━━━━━━━━━━━━━━\n" + ("\n\n".join(last_success_list) if last_success_list else "لا يوجد.")
                await event.edit(msg, buttons=[[Button.inline("🔄 تحديث", b"last_replies")], [Button.inline("🔙 رجوع", b"back")]])
            elif data == b"toggle":
                is_paused = not is_paused; await event.answer(f"تم {'الإيقاف' if is_paused else 'الاستئناف'}")
                await cmd_control(event)
            elif data == b"back":
                waiting_for_group = False; await cmd_control(event)
        except Exception: pass

    @control_bot.on(events.NewMessage(from_users=config.OWNER_ID))
    async def owner_handler(event):
        global waiting_for_group, target_links, resolved_ids
        if waiting_for_group:
            try:
                parts = event.text.split("|")
                if len(parts) == 2:
                    link = parts[0].strip(); gid = int(parts[1].strip())
                    if gid not in resolved_ids:
                        target_links.append(link); resolved_ids.append(gid); save_groups(target_links, resolved_ids)
                        waiting_for_group = False; await event.reply(f"✅ تم الإضافة بنجاح: {link}")
                    else: await event.reply("⚠️ مضاف بالفعل.")
                else: await event.reply("❌ تنسيق خاطئ: `الرابط | الايدي`")
            except Exception as e: await event.reply(f"❌ خطأ: {e}")

    @control_bot.on(events.NewMessage(pattern='تحكم', from_users=config.OWNER_ID))
    async def cmd_control(event):
        buttons = [
            [Button.inline("📊 التقرير", b"report"), Button.inline("💎 إحصائيات", b"group_info")],
            [Button.inline("➕ إضافة قروب", b"add_group"), Button.inline("🕒 آخر الردود", b"last_replies")],
            [Button.inline("🛑 توقف مؤقت" if not is_paused else "▶️ استئناف", b"toggle")]
        ]
        if isinstance(event, events.CallbackQuery.Event): await event.edit("🕹️ **لوحة التحكم:**", buttons=buttons)
        else: await event.reply("🕹️ **لوحة التحكم:**", buttons=buttons)

    for link in target_links:
        for client in clients:
            try:
                entity = await client.get_entity(link)
                if entity.id not in resolved_ids: resolved_ids.append(entity.id)
                break
            except: continue
    save_groups(target_links, resolved_ids)

    async def handler(event):
        global idx_khas, idx_tabadel, is_paused
        msg_uid = f"{event.chat_id}_{event.id}"
        if msg_uid in processed_messages: return
        processed_messages.add(msg_uid)
        if len(processed_messages) > config.MAX_PROCESSED_MESSAGES: processed_messages.clear()
        if is_paused or event.sender_id in [int(s['id']) for s in config.SESSIONS_CONFIG] or event.out: return
        if event.sender_id in replied_users and (time.time() - replied_users[event.sender_id] < config.REPLY_COOLDOWN): return
        if event.chat_id not in resolved_ids: return

        text = (event.text or "").strip(); reply_msg = None
        if any(k in text for k in config.KEYWORDS_KHAS):
            reply_msg = config.REPLIES_KHAS[idx_khas]; idx_khas = (idx_khas + 1) % len(config.REPLIES_KHAS)
        elif any(k in text for k in config.KEYWORDS_TABADEL):
            reply_msg = config.REPLIES_TABADEL[idx_tabadel]; idx_tabadel = (idx_tabadel + 1) % len(config.REPLIES_TABADEL)

        if reply_msg:
            replied_users[event.sender_id] = time.time(); await reply_queue.put((event, reply_msg, 0))

    for client in clients: client.add_event_handler(handler, events.NewMessage())

    print("✅ النظام يعمل الآن."); await asyncio.gather(control_bot.run_until_disconnected(), *(c.run_until_disconnected() for c in clients))

if __name__ == '__main__':
    asyncio.run(main())
