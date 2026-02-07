# -*- coding: utf-8 -*-
import asyncio, time, os, glob, random
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, MessageNotModifiedError, UserDeactivatedError
from telethon.tl.functions.channels import JoinChannelRequest

# تنظيف الجلسات السابقة عند التشغيل (تحديث)
for f in glob.glob("bot_control_panel.session*"):
    try: os.remove(f)
    except: pass

# ===== إعدادات التحكم =====
OWNER_ID = 6762940512
bot_token = "8520006260:AAGWatChzdHGXhZILav0gqX3Jn91NDzj1fg"

is_paused = False
account_logs = {}
group_stats = {}
last_success_list = []
replied_users = {}
reply_queue = asyncio.Queue()

resolved_ids = set()
waiting_for_group = {}

async def join_group(client, link):
    try:
        if 't.me/+' in link or 't.me/joinchat/' in link:
            invite_hash = link.split('/')[-1].replace('+', '')
            from telethon.tl.functions.messages import ImportChatInviteRequest
            await client(ImportChatInviteRequest(invite_hash))
            entity = await client.get_entity(link)
            return entity.id
        else:
            from telethon.tl.functions.channels import JoinChannelRequest
            entity = await client.get_entity(link)
            await client(JoinChannelRequest(entity))
            return entity.id
    except Exception:
        try:
            entity = await client.get_entity(link)
            return entity.id
        except:
            return None

def init_log(name):
    account_logs[name] = {
        'unique_ids': set(),
        'total_count': 0,
        'failed_count': 0,
        'last_fail_reason': 'لا يوجد',
        'status': 'نشط ✅',
        'pause_until': 0
    }

# --- إعدادات الحسابات ---
sessions_config = [
    {
        'name': 'الجلسة الجديدة 1',
        'id': 35234215,
        'hash': '2f560ad5ac9a1c11b8582e42471c403c',
        'str': '1BJWap1sBu5QxQPXDKdwMTJiQfyh9KD8cRE4pUghL9slakYFyvUUFTRcnN4xvUPEd6F-y01Mv2EkwTonZJpWO7Dsm3eMYhx11hntNpTwAPMz--Jv2_nZLQMzWl62Ssdi7c2FlhtMvr5f3wyE5IW2ocnAtvfVzUTs59hTh9cXwlMuoHzyYCYYibA2AadPuLjIOflMfmHa-JrMdAvCwSUe0_T6TtA5D8USSW_4ps7Y_B7rjDLbHvsVxZtzcBjGzJmGytxV0kyzsE_8luEJvxdUganOtyeBMKboIIByfou_uLWuF7QyYaCKspW422iHlmIHByJ_GZeI_Rrsy6c2w5Atr4BgIwHQlQ6M='
    },
    {
        'name': 'الجلسة الجديدة 2',
        'id': 39838472,
        'hash': '39e0757f5b96e8a84c7797c17d28c29a',
        'str': '1BJWap1sBu6F1feEVYtqx1o_ImLPmDXsjDKfL2q4nhfLm1BRYg_RpFRz-KHG9XV67qeBMmBuwusFA1YXF62GHSYDQtgx1fdy0eNy-_nQinIQHvnsMHEKdEpurPDuw9d_FmUTp2QrXj10qgWAs0XG6jRGAbqnzFNHJXnFHNgvm-tiIicwYflF_AeGiEZNc1mYZ832sQrReBdJ-g7eLYbpqSC7j3XLuylrZdxdc7eTJLURe78mHN1-y_4tPquvAULVtfl6REAaVR1zzYOfHiWojZzRPSGqAxj6dRZKGeM2lIpUL_1O6rAUUc49KJJlNgTBG5HF_xOx9qSa3DEQIhQlUiJpohQZBGuA='
    }
]

MY_IDS = [int(s['id']) for s in sessions_config]

target_links = [
    'https://t.me/+z7K5sSzvWQU3NTAy',
    'https://t.me/pewndgrop',
    'https://t.me/M_R515',
    'https://t.me/+wtGW0icU0pY2YWY0',
    'https://t.me/krkokgrop'
]

replies_khas = [
    "وين رايحين، التبادلات مضيعة للوقت يخوي، عندي لك رابط بوت كله مقاطع نار نار، رابطو بوصف حسابي نار.",
    "ليش الخاص يحلوين، روحو البوت رابطوو بوصف حسابي",
    "ليش تتعب حالك بالخاص وهيك، روح البوت رابطو بوصف حسابي لاتفوت الفرصه شوي واحذفه"
]

replies_tabadel = [
    "تبغا مقاطع ورعان ياصاحبي، معي بوت بوصف حسابي فيه 30 الف مقطع",
    "التبادلات تعب، عندي لك بوت بوصف حسابي ببلاش ورعان من كل الجنسيات",
    "مقاطع ورعان اخر موديل، البوت بوصف حسابي وقول للتبادلات باي باي",
    "خش البوت حقي من وصف حسابي وعيش الجو مع الورعان اخر دقه",
    "ضفت اكثر من 31 الف مقطع ورع عندي بالبوت بوصف حسابي لو تريد"
]

idx_khas = 0
idx_tabadel = 0

async def worker(client, account_name):
    global is_paused, last_success_list, idx_khas, idx_tabadel, group_stats
    while True:
        try:
            event, reply_text, retry_count = await reply_queue.get()

            if is_paused:
                await asyncio.sleep(1)
                await reply_queue.put((event, reply_text, retry_count))
                reply_queue.task_done()
                continue

            if time.time() < account_logs[account_name]['pause_until']:
                await reply_queue.put((event, reply_text, retry_count))
                await asyncio.sleep(2)
                reply_queue.task_done()
                continue

            sent_msg = await client.send_message(event.chat_id, reply_text, reply_to=event.id)

            account_logs[account_name]['total_count'] += 1
            account_logs[account_name]['unique_ids'].add(event.sender_id)
            account_logs[account_name]['status'] = 'نشط ✅'

            try:
                chat = await client.get_entity(event.chat_id)
                g_title = chat.title if hasattr(chat, 'title') else "قروب"
                msg_link = f"https://t.me/{chat.username}/{sent_msg.id}" if hasattr(chat, 'username') and chat.username else f"https://t.me/c/{str(event.chat_id).replace('-100', '')}/{sent_msg.id}"
            except:
                g_title = "غير معروف"
                msg_link = "الرابط غير متاح"

            if g_title not in group_stats:
                group_stats[g_title] = {'count': 0, 'links': []}

            group_stats[g_title]['count'] += 1
            group_stats[g_title]['links'].append(f"{account_name}: {msg_link}")

            last_success_list.insert(0, f"🕒 {time.strftime('%H:%M')} | {account_name} ➜ {g_title}: {msg_link}")
            if len(last_success_list) > 5:
                last_success_list.pop()

            await asyncio.sleep(random.uniform(15, 20))

        except FloodWaitError as e:
            account_logs[account_name]['status'] = f'مقيد ({e.seconds}ث)'
            account_logs[account_name]['pause_until'] = time.time() + e.seconds
            await reply_queue.put((event, reply_text, retry_count))

        except Exception as e:
            if retry_count < 2:
                await reply_queue.put((event, reply_text, retry_count + 1))
            else:
                account_logs[account_name]['failed_count'] += 1
                account_logs[account_name]['last_fail_reason'] = str(e)
                account_logs[account_name]['status'] = 'خطأ ⚠️'

        finally:
            reply_queue.task_done()

async def handler(event):
    global idx_khas, idx_tabadel, is_paused
    if is_paused or event.sender_id in MY_IDS or event.out:
        return

    if event.chat_id not in resolved_ids:
        return

    if event.sender_id in replied_users and (time.time() - replied_users[event.sender_id] < 7200):
        return

    text = (event.text or "").strip()
    reply_msg = None

    if "خاص" in text:
        reply_msg = replies_khas[idx_khas]
        idx_khas = (idx_khas + 1) % len(replies_khas)
    elif any(w in text for w in ["تبادل", "ورعان", "ورع", "صغار"]):
        reply_msg = replies_tabadel[idx_tabadel]
        idx_tabadel = (idx_tabadel + 1) % len(replies_tabadel)

    if reply_msg:
        replied_users[event.sender_id] = time.time()
        await reply_queue.put((event, reply_msg, 0))

async def main():
    global resolved_ids
    clients = []

    control_bot = TelegramClient(StringSession(), sessions_config[0]['id'], sessions_config[0]['hash'])
    await control_bot.start(bot_token=bot_token)

    for s_info in sessions_config:
        client = TelegramClient(StringSession(s_info['str']), s_info['id'], s_info['hash'])
        await client.start()
        me = await client.get_me()
        init_log(me.first_name)
        clients.append(client)
        asyncio.create_task(worker(client, me.first_name))

    def get_buttons():
        return [
            [Button.inline("📊 تقرير عن الحسابات", b"report")],
            [Button.inline("🕒 آخر الردود بأي قروب", b"last_replies"), Button.inline("💎 إحصائيات القروبات", b"group_info")],
            [Button.inline("➕ إضافة قروب", b"add_group")],
            [Button.inline("🛑 توقف مؤقت" if not is_paused else "▶️ استئناف العمل", b"toggle")]
        ]

    @control_bot.on(events.NewMessage(pattern='تحكم', from_users=OWNER_ID))
    async def cmd_control(event):
        await event.reply("🕹️ **لوحة التحكم المتقدمة:**", buttons=get_buttons())

    @control_bot.on(events.CallbackQuery())
    async def catcher(event):
        global is_paused
        if event.data == b"add_group":
            waiting_for_group[event.sender_id] = True
            await event.answer("📥 أرسل رابط القروب الآن", alert=True)

        elif event.data == b"report":
            text = "📊 **تقرير الحسابات:**\n\n"
            if not account_logs:
                text += "لا توجد بيانات متاحة حالياً."
            for name, log in account_logs.items():
                text += f"👤 **{name}**:\n"
                text += f"   - الحالة: {log['status']}\n"
                text += f"   - الردود: {log['total_count']}\n"
                text += f"   - مستخدمين فريدين: {len(log['unique_ids'])}\n"
                text += f"   - فشل: {log['failed_count']}\n"
                text += "------------------\n"
            await event.edit(text, buttons=[Button.inline("🔙 رجوع", b"back")])

        elif event.data == b"last_replies":
            text = "🕒 **آخر الردود الناجحة:**\n\n"
            if not last_success_list:
                text += "لا يوجد أي ردود مسجلة بعد."
            else:
                text += "\n".join(last_success_list)
            await event.edit(text, buttons=[Button.inline("🔙 رجوع", b"back")])

        elif event.data == b"group_info":
            text = "💎 **إحصائيات القروبات:**\n\n"
            if not group_stats:
                text += "لا توجد إحصائيات للقروبات بعد."
            else:
                for g_title, stats in group_stats.items():
                    text += f"📍 **{g_title}**:\n"
                    text += f"   - عدد الردود: {stats['count']}\n"
                    text += "------------------\n"
            await event.edit(text, buttons=[Button.inline("🔙 رجوع", b"back")])

        elif event.data == b"toggle":
            is_paused = not is_paused
            status = "متوقف 🛑" if is_paused else "يعمل ▶️"
            await event.answer(f"تم تغيير الحالة إلى: {status}", alert=True)
            await event.edit("🕹️ **لوحة التحكم المتقدمة:**", buttons=get_buttons())

        elif event.data == b"back":
            await event.edit("🕹️ **لوحة التحكم المتقدمة:**", buttons=get_buttons())

    @control_bot.on(events.NewMessage(from_users=OWNER_ID))
    async def add_group_listener(event):
        if not waiting_for_group.get(event.sender_id):
            return

        link = event.text.strip()
        waiting_for_group.pop(event.sender_id, None)

        found = False
        for client in clients:
            cid = await join_group(client, link)
            if cid:
                resolved_ids.add(cid)
                found = True

        if found:
            await event.reply(f"✅ تم إضافة القروب وربطه بنجاح: {link}")
        else:
            await event.reply(f"❌ فشل الانضمام للقروب: {link}")

    for link in target_links:
        for client in clients:
            cid = await join_group(client, link)
            if cid:
                resolved_ids.add(cid)
                break

    for client in clients:
        client.add_event_handler(handler, events.NewMessage())

    await asyncio.gather(
        control_bot.run_until_disconnected(),
        *(c.run_until_disconnected() for c in clients)
    )

if __name__ == '__main__':
    asyncio.run(main())
