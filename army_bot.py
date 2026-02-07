# -*- coding: utf-8 -*-
import asyncio, time, os, glob, random, json
from collections import deque
from telethon import TelegramClient, events, Button, utils, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, MessageNotModifiedError, UserDeactivatedError

# تنظيف الجلسات السابقة عند التشغيل
for f in glob.glob("army_control_panel.session*"):
    try: os.remove(f)
    except: pass

# ===== إعدادات التحكم المتقدمة للجيش =====
OWNER_ID = 6762940512
bot_token = "8207301806:AAH8aQwODSt7c0a8j-3-_0tZN4XHbqgCdmU"

is_paused = False
reply_delay = 20
account_logs = {}
group_stats = {}
last_success_list = []
replied_users = {}
reply_queue = asyncio.Queue()
processed_msgs = deque(maxlen=1000)

resolved_ids = set()
waiting_for_group = {}

# --- إعدادات الحسابات (الجيش) ---
MY_IDS = []
sessions_config = [
    {'name': 'الرابع', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1wBu3ZURUHVmOYZgVtxDy7BxzCLlOHBFAg9qDkK5DDxGgBqV5keNxPIR5NEEgUtiINJGUPNBTMFaugwwQ1ZxzCtNl21lWFcMkI3aPxbOcoBbepkyK01d89-zvHaPIjL4vfGIQH3aRFZ3z6M8gFdGH_1dCqUFLSQQ6BWyXdNeW4m4bRDcubG1JJyPLxZi4Enhec6dgWgUVxJL24MwenfhrjKnONa4dFfEJGCAfa6WLOYcN_8RMN5YqtyWCq6ke1TsmMBs70TFY5nXJNsVQzCZRxQOTBul1MrLjv7cyynte2E3UdmtCPt_Dqp941hduR-ppPVYbhsKtkUVfGMhw9tSvs9Qp0='},
    {'name': 'الخامس', 'id': 34239992, 'hash': '6d62348439a8b0fc9c557000c002752a', 'str': '1BJWap1wBuzSrCs-rZx-pS4IzkY50rgar8C3Hpeg5j18JMrsG-JTwbx9XvgHKhnDKTt7FWXb39w7qPYntU6GBBuIk4I_d8pfpoFT7AfYaJlvvt_3Qo9e3XEB73ebqAD_dsSChEuURMi__Rznwf5sOpK8wX4D-kyCWxYOcbLxGqyZbNan6sWhlT2oszDfMtvOAg6TYh1MRMY5gm_4ihgdW1rCQEPn37kSKW1eMcMQUqOLBw7Q-JEYryS5RbRBoAqj04GHbZy_9LhHGGm7cUVszUw1tW1IeX1LjYc5ov0DlRouzznUgMtx_9_9CdPeiiLWXM4wyTxA9q6pNR_VsWzzTIY4pkHSfwhA='},
    {'name': 'السادس', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67', 'str': '1BJWap1wBuzFf0oRjZFWSoC8cfecKHHGe8rQ6OWnrJxeavVHbHbnofCNUGLtfurvoR4YomTA_-Z7L20slotqmjmC4ZvMAnz-Xm3Y7mHMR0Ld_Lq981XAxKc3IWJJawgsW5LBcmJeyu2sRklfUzfOGFmL6satq_T1HZGhTxKCdE6sVUchoHWdf3DswGJR3ksAxWgQtcXCV7pN1ggEXwY6gD2aEUME3bfSzzxqk20YQsQCRWNZsqqBgK_UycbWDf7D3VMICO4VH5yXqYufioqXqdo5YaIDPz_A58NlY8BjLrzZgyNuBvrqED75NBNJfTk6g22xXcDiYa2DOPU4SVwA-xShEuCgojoc='},
    {'name': 'السابع', 'id': 38615138, 'hash': 'a0eb2f816038c1cad154f47e9b8fba21', 'str': '1BJWap1sBu8WpQuA_B183Uv_sv0U3WeJrvrjGNBoZoiG3pQbSxsr7DyL1RF02KUJNut7nTh4QE71l5drjrO3lFyD5Cct0aHc1wGcv4Gfkq6d5NadP3mgA5U2quLLffL5mDx8e9ygCYdFD9cq1O9HTLjIDS2ry8FZg4h4Jb9Sw9PNT7vhDlCWn9Gllh3lbtPUV4801kxE2TXO_ZkFFX7dENNxpU9_2eUeZCWDlRjb7w8wRis6QbYjS1hwwdBGYBfT60_O4dkIqxgThJDcYFvrF7iQpKm71qvT2vWL_n9QpBfiPayPJrQ2yG03hx8sqQIqerMZ7rOP-gQiMltI1_aMe5XUxkouOsIw='},
    {'name': 'الثامن', 'id': 30018193, 'hash': '245b28a92f44ed44bfaafc4757ead9ea', 'str': '1BJWap1sBuzGd7ucxy7DmcZrPRTEd-tqYbXJ-OK0tahWOADkoKpMEM5JTCa5PEFArRxvA7LmGjgoaBtXdM_xDzhZE21HN7gd07rE4TH4yGvGD3deKX4uZxRlW2KzuD-eSAqJ_Pkyg8CnIpEkiSALk9lVCfmTYR_kR_QXAEittQG8DKWAEsQx64YM13DYHxQr6UhD2D8Xx6N_Jm61ZqRQAF1uXtm0JQDAiFZB35HHRNzvjXSV89qz0XDAujRA2TWTSM1fcI2l2-ZqAbi4e-1IS6QDt3tMTAq0lZMm6rShtWyIEN45bvvbP9FC0T7io-CjP5R4dl89chb_1DV3Gj463dYN0oDvx4IU='}
]

GROUPS_FILE = "army_groups.json"
DEFAULT_LINKS = ['https://t.me/mwmwmnn', 'https://t.me/R_KA_N0', 'https://t.me/Nj_QU', 'https://t.me/L_A_m_e_s_0', 'https://t.me/lako0019', 'https://t.me/hwlwjwo', 'https://t.me/whsuxjw', 'https://t.me/AR_HDA', 'https://t.me/hanTii1']
SPECIAL_CHAT_ID = -1003331495813

def load_groups():
    links = DEFAULT_LINKS.copy()
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                new_links = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
                for l in new_links:
                    if isinstance(l, str) and l not in links: links.append(l)
        except: pass
    return links

def save_groups(links):
    try:
        to_save = [l for l in links if isinstance(l, str)]
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(set(to_save)), f, ensure_ascii=False, indent=4)
    except: pass

target_links = load_groups()

async def join_group(client, link):
    if not isinstance(link, str): return None
    link = link.strip()
    try:
        # دعم إضافة المعرفات الرقمية (IDs)
        if link.lstrip('-').isdigit():
            try:
                entity = await client.get_entity(int(link))
                return utils.get_peer_id(entity)
            except:
                if not link.startswith('-'):
                    try:
                        entity = await client.get_entity(int(f"-100{link}"))
                        return utils.get_peer_id(entity)
                    except: pass

        if 't.me/+' in link or 't.me/joinchat/' in link:
            invite_hash = link.split('/')[-1].replace('+', '')
            from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
            try:
                check = await client(CheckChatInviteRequest(invite_hash))
                if hasattr(check, 'chat'): return utils.get_peer_id(check.chat)
                await client(ImportChatInviteRequest(invite_hash))
            except: pass
        else:
            try:
                from telethon.tl.functions.channels import JoinChannelRequest
                entity = await client.get_entity(link)
                await client(JoinChannelRequest(entity))
                return utils.get_peer_id(entity)
            except: pass
        entity = await client.get_entity(link)
        return utils.get_peer_id(entity)
    except: return None

def init_log(name):
    account_logs[name] = {'unique_ids': set(), 'total_count': 0, 'failed_count': 0, 'last_fail_reason': 'لا يوجد', 'status': 'نشط ✅', 'pause_until': 0}

replies_khas = ["وين رايحين، التبادلات مضيعة للوقت يخوي، عندي لك رابط بوت كله مقاطع نار نار، رابطو بوصف حسابي نار.", "ليش الخاص يحلوين، روحو البوت رابطوو بوصف حسابي", "ليش تتعب حالك بالخاص وهيك، روح البوت رابطو بوصف حسابي لاتفوت الفرصه شوي واحذفه"]
replies_tabadel = ["تبغا مقاطع ورعان ياصاحبي، معي بوت بوصف حسابي فيه 30 الف مقطع", "التبادلات تعب، عندي لك بوت بوصف حسابي ببلاش ورعان من كل الجنسيات", "مقاطع ورعان اخر موديل، البوت بوصف حسابي وقول للتبادلات باي باي", "خش البوت حقي من وصف حسابي وعيش الجو مع الورعان اخر دقه", "ضفت اكثر من 31 الف مقطع ورع عندي بالبوت بوصف حسابي لو تريد"]

idx_khas = 0
idx_tabadel = 0

async def worker(client, account_name):
    global is_paused, last_success_list, idx_khas, idx_tabadel, group_stats, reply_delay
    while True:
        item = await reply_queue.get()
        try:
            event, reply_text, retry_count = item
            if is_paused:
                await asyncio.sleep(1); await reply_queue.put((event, reply_text, retry_count)); continue
            if time.time() < account_logs[account_name]['pause_until']:
                await reply_queue.put((event, reply_text, retry_count)); await asyncio.sleep(2); continue

            sent_msg = await event.reply(reply_text)
            account_logs[account_name]['total_count'] += 1
            account_logs[account_name]['unique_ids'].add(event.sender_id)
            account_logs[account_name]['status'] = 'نشط ✅'

            try:
                try: chat = await event.get_chat(); g_title = utils.get_display_name(chat)
                except: chat = await client.get_entity(event.chat_id); g_title = utils.get_display_name(chat)
                if hasattr(chat, 'username') and chat.username: msg_link = f"https://t.me/{chat.username}/{sent_msg.id}"
                else: clean_id = str(event.chat_id).replace('-100', '', 1).lstrip('-'); msg_link = f"https://t.me/c/{clean_id}/{sent_msg.id}"
            except: g_title = f"قروب {event.chat_id}"; msg_link = "الرابط غير متاح"

            if g_title not in group_stats: group_stats[g_title] = {'count': 0}
            group_stats[g_title]['count'] += 1
            last_success_list.insert(0, f"🕒 {time.strftime('%H:%M')} | {account_name} ➜ {g_title}: {msg_link}")
            if len(last_success_list) > 10: last_success_list.pop()

            sleep_start = time.time(); jitter = random.uniform(0, 5)
            while (time.time() - sleep_start) < (reply_delay + jitter):
                if is_paused: break
                await asyncio.sleep(0.5)

        except FloodWaitError as e:
            account_logs[account_name]['status'] = f'مقيد ({e.seconds}ث)'; account_logs[account_name]['pause_until'] = time.time() + e.seconds
            await reply_queue.put((event, reply_text, retry_count))
        except Exception as e:
            if retry_count < 2: await reply_queue.put((event, reply_text, retry_count + 1))
            else: account_logs[account_name]['failed_count'] += 1; account_logs[account_name]['last_fail_reason'] = str(e); account_logs[account_name]['status'] = 'خطأ ⚠️'
        finally: reply_queue.task_done()

async def handler(event):
    global idx_khas, idx_tabadel, is_paused
    if is_paused or event.sender_id in MY_IDS or event.out: return
    if event.chat_id not in resolved_ids: return
    msg_key = (event.chat_id, event.id)
    if msg_key in processed_msgs: return
    processed_msgs.append(msg_key)

    if event.sender_id in replied_users and (time.time() - replied_users[event.sender_id] < 7200): return
    text = (event.text or "").strip(); reply_msg = None
    if "خاص" in text: reply_msg = replies_khas[idx_khas]; idx_khas = (idx_khas + 1) % len(replies_khas)
    elif any(w in text for w in ["تبادل", "ورعان", "ورع", "صغار"]): reply_msg = replies_tabadel[idx_tabadel]; idx_tabadel = (idx_tabadel + 1) % len(replies_tabadel)
    if reply_msg: replied_users[event.sender_id] = time.time(); await reply_queue.put((event, reply_msg, 0))

async def main():
    global resolved_ids, MY_IDS, target_links
    clients = []
    control_bot = TelegramClient('army_control_panel', sessions_config[0]['id'], sessions_config[0]['hash'])
    await control_bot.start(bot_token=bot_token)

    for s_info in sessions_config:
        client = TelegramClient(StringSession(s_info['str']), s_info['id'], s_info['hash'])
        await client.start()
        me = await client.get_me(); MY_IDS.append(me.id); init_log(s_info['name'])
        clients.append(client); asyncio.create_task(worker(client, s_info['name']))

    def get_buttons():
        return [
            [Button.inline("📊 تقرير الحسابات", b"report")],
            [Button.inline("🕒 آخر الردود", b"last_replies"), Button.inline("💎 إحصائيات القروبات", b"group_info")],
            [Button.inline("➕ إضافة قروب", b"add_group"), Button.inline("📋 قائمة القروبات", b"list_groups")],
            [Button.inline("⚙️ ضبط التأخير", b"delay_menu"), Button.inline("🧹 مسح الكل", b"clear_groups")],
            [Button.inline("🛑 إيقاف قراءة الرسائل" if not is_paused else "▶️ استئناف القراءة", b"toggle")]
        ]

    async def safe_edit(event, text, buttons=None):
        try:
            if len(text) > 4000: text = text[:3900] + "\n\n...(تم اختصار النص)"
            await event.edit(text, buttons=buttons)
        except: await event.respond(text[:4000], buttons=buttons)

    @control_bot.on(events.NewMessage(pattern='تحكم', from_users=OWNER_ID))
    async def cmd_control(event):
        status_txt = "🔴 متوقف" if is_paused else "🟢 يعمل"
        await event.reply(f"🕹️ **لوحة التحكم المتقدمة للجيش:**\nالحالة: {status_txt}\nالتأخير: {reply_delay}ث", buttons=get_buttons())

    @control_bot.on(events.CallbackQuery())
    async def catcher(event):
        global is_paused, reply_delay, target_links, resolved_ids
        if event.data == b"add_group":
            waiting_for_group[event.sender_id] = True
            await event.answer("📥 أرسل رابط القروب الآن", alert=True)
        elif event.data == b"report":
            text = "📊 **تقرير الحسابات:**\n\n"
            for name, log in account_logs.items():
                text += f"👤 **{name}**:\n   - الحالة: {log['status']}\n   - الردود: {log['total_count']}\n   - فريد: {len(log['unique_ids'])}\n   - فشل: {log['failed_count']}\n------------------\n"
            await safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif event.data == b"last_replies":
            text = "🕒 **آخر الردود الناجحة:**\n\n" + ("\n".join(last_success_list) if last_success_list else "لا توجد ردود.")
            await safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif event.data == b"group_info":
            text = "💎 **إحصائيات القروبات:**\n\n"
            if not group_stats: text += "لا توجد إحصائيات."
            else:
                for title, stats in group_stats.items(): text += f"📍 **{title}**:\n   - الردود: {stats['count']}\n------------------\n"
            await safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif event.data == b"list_groups":
            text = "📋 **قائمة القروبات المراقبة:**\n\n" + ("\n".join([f"{i}. {l}" for i,l in enumerate(target_links, 1)]) if target_links else "لا توجد.")
            text += f"\n\n🔢 المعرفات النشطة: {len(resolved_ids)}"
            await safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif event.data == b"toggle":
            is_paused = not is_paused; status_txt = "🔴 متوقف" if is_paused else "🟢 يعمل"
            await event.answer(f"تغيير الحالة: {status_txt}", alert=True)
            await safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة:**\nالحالة: {status_txt}\nالتأخير: {reply_delay}ث", buttons=get_buttons())
        elif event.data == b"delay_menu":
            buttons = [[Button.inline("15ث", b"d_15"), Button.inline("30ث", b"d_30")], [Button.inline("60ث", b"d_60"), Button.inline("120ث", b"d_120")], [Button.inline("400ث", b"d_400")], [Button.inline("🔙 رجوع", b"back")]]
            await safe_edit(event, f"⚙️ **التأخير الحالي: {reply_delay}ث**\nاختر مدة الاستراحة:", buttons=buttons)
        elif event.data.startswith(b"d_"):
            reply_delay = int(event.data.split(b"_")[1]); await event.answer(f"تم الضبط على {reply_delay}ث", alert=True)
            status_txt = "🔴 متوقف" if is_paused else "🟢 يعمل"
            await safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة:**\nالحالة: {status_txt}\nالتأخير: {reply_delay}ث", buttons=get_buttons())
        elif event.data == b"clear_groups":
            target_links = DEFAULT_LINKS.copy(); resolved_ids.clear(); resolved_ids.add(SPECIAL_CHAT_ID); save_groups(target_links)
            for link in target_links:
                for client in clients:
                    cid = await join_group(client, link)
                    if cid: resolved_ids.add(cid)
            await event.answer("🧹 تم استعادة الافتراضية", alert=True)
            status_txt = "🔴 متوقف" if is_paused else "🟢 يعمل"
            await safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة:**\nالحالة: {status_txt}\nالتأخير: {reply_delay}ث", buttons=get_buttons())
        elif event.data == b"back":
            status_txt = "🔴 متوقف" if is_paused else "🟢 يعمل"
            await safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة:**\nالحالة: {status_txt}\nالتأخير: {reply_delay}ث", buttons=get_buttons())

    @control_bot.on(events.NewMessage(from_users=OWNER_ID))
    async def add_group_listener(event):
        global resolved_ids, target_links
        if not waiting_for_group.get(event.sender_id): return
        link = event.text.strip(); waiting_for_group.pop(event.sender_id, None)
        found = False
        for client in clients:
            cid = await join_group(client, link)
            if cid: resolved_ids.add(cid); found = True
        if found:
            if link not in target_links: target_links.append(link); save_groups(target_links)
            await event.reply(f"✅ تم إضافة القروب: {link}")
        else: await event.reply(f"❌ فشل الانضمام: {link}")

    resolved_ids.add(SPECIAL_CHAT_ID)
    print(f"🔄 جاري تحميل {len(target_links)} قروب...")
    for link in target_links:
        res = False
        for client in clients:
            cid = await join_group(client, link)
            if cid: resolved_ids.add(cid); res = True
        if not res: print(f"⚠️ فشل: {link}")
    print(f"✅ المراقبة نشطة لـ {len(resolved_ids)} قروب.")

    for client in clients: client.add_event_handler(handler, events.NewMessage())
    await asyncio.gather(control_bot.run_until_disconnected(), *(c.run_until_disconnected() for c in clients))

if __name__ == '__main__':
    asyncio.run(main())
