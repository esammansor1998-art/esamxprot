# -*- coding: utf-8 -*-
import asyncio, time, os, random, sys
from collections import deque
from telethon import TelegramClient, events, Button, utils
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from datetime import datetime
import json
# ===== إعدادات التحكم =====
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
bot_token = os.environ.get("BOT_TOKEN", "")
CONTROL_BOT_API_ID = int(os.environ.get("CONTROL_BOT_API_ID", 0))
CONTROL_BOT_API_HASH = os.environ.get("CONTROL_BOT_API_HASH", "")
is_paused = False
account_logs = {}
last_messages = [] # سيحتوي على آخر 10 رسائل
group_reply_counts_global = {}
group_keyword_counts_global = {}
group_names_map = {}
chat_queues = {}
chat_locks = {}
global_dispatch_queue = asyncio.Queue()
owner_reply_state = {} # للحفاظ على حالة الرد الخاص بالمالك
target_links = [
    'https://t.me/R_KA_N0', 'https://t.me/Nj_QU','https://t.me/krav33v','https://t.me/kakaka865gshh','https://t.me/irrrjx', 'https://t.me/L_A_m_e_s_0',
    'https://t.me/lako0019', 'https://t.me/hwlwjwo', 'https://t.me/whsuxjw', 'https://t.me/AR_HDA',
    'https://t.me/hanTii1', 'https://t.me/ca_sw', 'https://t.me/M_a_n_o_x_1_2_3', 'https://t.me/qo_ao',
    'https://t.me/Q_X1_Q', 'https://t.me/vy_gf', 'https://t.me/leeeeets', 'https://t.me/lyttti',
    'https://t.me/JH_CN', 'https://t.me/sjjrmb', 'https://t.me/wuvbshf', 'https://t.me/BP_OV',
    'https://t.me/O_7_Q7', 'https://t.me/egygays11', 'https://t.me/c_e_r0', 'https://t.me/hggjjkknbhhhbhjkjj',
    'https://t.me/hgulylm', 'https://t.me/xxhjfifhdv', 'https://t.me/gfgfghghf', 'https://t.me/syriangays0111',
    'https://t.me/femboy_ar', 'https://t.me/jjskksnb', 'https://t.me/llllloxxxloo', 'https://t.me/+PmfFWzu-mL4yZDNk',
    'https://t.me/UO_D4', 'https://t.me/V0_1YY', 'https://t.me/Gaypeopleofsyria',
    'https://t.me/VC_R6', 'https://t.me/Baby_boys_2008', 'https://t.me/egyptgays0'
]
# الردود المستهدفة
replies_khas = ["وين رايحين، التبادلات مضيعة للوقت يخوي، عندي لك رابط بوت كله مقاطع نار نار، رابطو بوصف حسابي نار", "ليش الخاص يحلوين، روحو البوت رابطوو بوصف حسابي", "ليش تتعب حالك بالخاص وهيك، روح البوت رابطو بوصف حسابي لاتفوت الفرصه شوي واحذفه"]
replies_tabadel = ["تبغا مقاطع ورعان ياصاحبي، معي بوت بوصف حسابي فيه 30 الف مقطع", "التبادلات تعب، عندي لك بوت بوصف حسابي ببلاش ورعان من كل الجنسيات", "مقاطع ورعان اخر موديل، البوت بوصف حسابي وقول للتبادلات باي باي", "خش البوت حقي من وصف حسابي وعيش الجو مع الورعان اخر دقه", "ضفت اكثر من 31 الف مقطع ورع عندي بالبوت بوصف حسابي لو تريد"]
replies_saleb = ["اذا تبـي قروبات سوالب من منطقتك خش ع البـــوت بـــوصف حـسابــي بتلاقي قائمة قروبات تجمع ورعان خش واختر اي قروب يناسب منطقتك", "اذا تبــي قروبات سوالب من منطقتك خش ع بوتـي فيه روابـط لاكثر من 250 قـروب سوالب من منطقتك", "لاتوجع راسك بالرسائل هنا، حطيت لك بوت بوصف حسابي ادخله وتلاقي قروبات سوالب هناك وخلاص اتعرف عليهم"]
ALL_MY_REPLIES = replies_khas + replies_tabadel + replies_saleb

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# تحميل السشنات من متغير البيئة SESSIONS_JSON
sessions_json_str = os.environ.get("SESSIONS_JSON")
if sessions_json_str:
    sessions = json.loads(sessions_json_str)
else:
    # لتجنب رفع المفاتيح للـ Repository
    sessions = []
MY_ACCOUNT_IDS = []
idx_khas = idx_tabadel = idx_saleb = 0
replied_users = {}
for s in sessions:
    account_logs[s['name']] = {'total_count': 0, 'status': '⏳  متصل', 'pause_until': 0}
async def fair_distribution_engine():
    """محرك التوزيع العادل - يضمن الرد بالتساوي سطر بسطر بين القروبات بنظام Round-Robin"""
    try:
        while True:
            keys = list(chat_queues.keys())
            if not keys:
                await asyncio.sleep(0.5)
                continue

            # نمر على كل القروبات بالترتيب، نأخذ رسالة واحدة من كل قروب
            for chat_id in keys:
                q = chat_queues[chat_id]
                # إذا كان القروب لديه رسائل ومنتظر دوره (ليس مقفلاً حالياً)
                if not q.empty() and not chat_locks.get(chat_id, False):
                    item = await q.get()
                    await global_dispatch_queue.put(item)
                    chat_locks[chat_id] = True # قفل القروب حتى يتم إرسال الرسالة من قبل أحد الحسابات
                    # انتظار بسيط جداً لضمان سلاسة التوزيع
                    await asyncio.sleep(0.1)

            await asyncio.sleep(0.2)
    except asyncio.CancelledError: pass
async def worker(client, account_name):
    global is_paused
    try:
        while True:
            event, reply_text, retry_count = await global_dispatch_queue.get()
            chat_id = event.chat_id
            try:
                while is_paused: await asyncio.sleep(1)
                if time.time() < account_logs[account_name]['pause_until']:
                    await asyncio.sleep(0.1)
                    await global_dispatch_queue.put((event, reply_text, retry_count))
                    continue
                sent_msg = await client.send_message(chat_id, reply_text, reply_to=event.id)
                # تحديث العدادات
                account_logs[account_name]['total_count'] += 1
                group_reply_counts_global[chat_id] = group_reply_counts_global.get(chat_id, 0) + 1
                # جلب وتحديث الاسم الحقيقي إذا لم يكن موجوداً
                if chat_id not in group_names_map or group_names_map[chat_id].startswith("ID:"):
                    try:
                        chat = await event.get_chat()
                        group_names_map[chat_id] = getattr(chat, 'title', 'غير معروف').strip()
                    except: pass
                # تحديث قائمة آخر 10 رسائل
                title = group_names_map.get(chat_id, f"ID: {chat_id}")
                link = f"https://t.me/c/{str(chat_id)[4:]}/{sent_msg.id}" if str(chat_id).startswith("-100") else f"https://t.me/msg_{chat_id}_{sent_msg.id}"
                last_messages.insert(0, f"📍 {title}\n🔗 {link}")
                if len(last_messages) > 10: last_messages.pop() # الاحتفاظ بـ 10 فقط
                account_logs[account_name]['pause_until'] = time.time() + random.uniform(60, 70)
            except FloodWaitError as e:
                account_logs[account_name]['status'] = '⛔  مقيد'
                account_logs[account_name]['pause_until'] = time.time() + e.seconds + 60
                await global_dispatch_queue.put((event, reply_text, retry_count))
            except Exception:
                if retry_count < 1: await global_dispatch_queue.put((event, reply_text, retry_count + 1))
            finally:
                chat_locks[chat_id] = False
                global_dispatch_queue.task_done()
    except asyncio.CancelledError: pass
def get_main_buttons():
    return [
        [Button.inline("📊 حالة الجيش", b"st")],
        [Button.inline("📁 إحصائيات المجموعات", b"grp_stats")],
        [Button.inline("📩 آخر 10 ردود", b"last_msg")],
        [Button.inline("⏸️ إيقاف/تشغيل", b"tg")],
        [Button.inline("🛑 إغلاق نهائي", b"stop_bot")]
    ]
async def run_bot():
    global is_paused, MY_ACCOUNT_IDS, idx_khas, idx_tabadel, idx_saleb
    device_props = {"device_model": "Samsung Galaxy S23 Ultra", "system_version": "Android 13.0", "app_version": "10.1.1"}
    # Use an in-memory session (StringSession("")) for the control bot so it always uses the provided bot_token
    # and doesn't conflict with existing .session files on disk.
    control_bot = TelegramClient(StringSession(""), CONTROL_BOT_API_ID, CONTROL_BOT_API_HASH, **device_props)
    await control_bot.start(bot_token=bot_token)
    @control_bot.on(events.NewMessage(pattern='تحكم', from_users=OWNER_ID))
    async def cmd_control(event):
        await event.reply("🕹️ **لوحة التحكم المحدثة (10 ردود):**", buttons=get_main_buttons())
    @control_bot.on(events.CallbackQuery())
    async def handler_cb(event):
        data = event.data
        if data == b"st":
            msg = "📝 **حالة الحسابات:**\n"
            for s in sessions:
                n = s['name']
                l = account_logs.get(n, {'status': '❌ ', 'total_count': 0})
                msg += f"👤 {n}: {l.get('status','✅ ')} ({l['total_count']})\n"
            msg += f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await event.edit(msg, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif data == b"grp_stats":
            msg = "📁 **إحصائيات المجموعات:**\n\n"
            all_cids = set(group_reply_counts_global.keys()) | set(group_keyword_counts_global.keys())
            stats_list = []
            total_k = 0
            total_r = 0
            for cid in all_cids:
                r_count = group_reply_counts_global.get(cid, 0)
                k_count = group_keyword_counts_global.get(cid, 0)
                name = group_names_map.get(cid, f"ID: {cid}")
                stats_list.append((k_count, r_count, name))
                total_k += k_count
                total_r += r_count

            if stats_list:
                # ترتيب حسب عدد الكلمات ثم الردود
                stats_list.sort(key=lambda x: (x[0], x[1]), reverse=True)
                for k, r, name in stats_list:
                    msg += f"💬 {k} | ✅ {r} -> {name}\n"
                msg += f"\n📊 **الإجمالي:**\nكلمات: {total_k} | ردود: {total_r}"
            else:
                msg += "لا توجد بيانات بعد."

            if len(msg) > 4000: msg = msg[:3900] + "\n...(تكملة القائمة طويلة)"
            await event.edit(msg, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif data == b"last_msg":
            msg = "📩 **آخر 10 ردود تم إرسالها:**\n\n"
            msg += "\n\n".join(last_messages) if last_messages else "لا توجد بيانات حالياً."
            await event.edit(msg, buttons=[Button.inline("🔙 رجوع", b"back")])
        elif data == b"tg":
            is_paused = not is_paused
            await event.answer(f"الجيش: {'توقف ⏸️' if is_paused else 'يعمل ▶️'}", alert=True)
        elif data == b"back":
            await event.edit("🕹️ **لوحة التحكم المحدثة (10 ردود):**", buttons=get_main_buttons())
        elif data == b"stop_bot":
            os._exit(0)
        elif data.startswith(b"reply_"):
            # استخراج اسم الحساب وايدي المرسل
            try:
                parts = data.decode('utf-8').split('_', 2)
                if len(parts) == 3:
                    acc_name = parts[1]
                    target_id = int(parts[2])
                    owner_reply_state[OWNER_ID] = {'account_name': acc_name, 'target_id': target_id}
                    await event.answer("✍️ أرسل ردك الآن (نص، صورة، فيديو)...", alert=True)
                    await event.edit(f"أنت الآن ترد على المستخدم (ID: `{target_id}`) عبر الحساب **{acc_name}**.\nأرسل رسالتك الآن، أو أرسل `إلغاء` للإلغاء.")
            except Exception as e:
                await event.answer("❌ حدث خطأ أثناء معالجة زر الرد.", alert=True)

    @control_bot.on(events.NewMessage(from_users=OWNER_ID))
    async def owner_reply_handler(event):
        # التحقق مما إذا كان المالك في حالة رد على مستخدم
        if OWNER_ID in owner_reply_state:
            state = owner_reply_state[OWNER_ID]

            if event.text and event.text.strip() == "إلغاء":
                del owner_reply_state[OWNER_ID]
                await event.reply("تم إلغاء الرد.")
                return

            if event.text and event.text.strip() == "تحكم":
                return # تجاهل امر التحكم

            acc_name = state['account_name']
            target_id = state['target_id']

            # البحث عن الحساب المعني
            target_client = None
            for s in sessions:
                if s['name'] == acc_name and '_client' in s:
                    target_client = s['_client']
                    break

            if target_client:
                try:
                    if event.media:
                        # تنزيل الميديا مؤقتاً لحل مشكلة cross-client
                        file_path = await event.client.download_media(event.media)
                        if file_path:
                            try:
                                await target_client.send_message(target_id, event.text or "", file=file_path)
                            finally:
                                os.remove(file_path)
                        else:
                            await event.reply("❌ فشل تنزيل الميديا.")
                    else:
                        await target_client.send_message(target_id, event.text)
                    await event.reply("✅ تم إرسال الرد بنجاح.")
                except Exception as e:
                    await event.reply(f"❌ فشل الإرسال: {e}")
            else:
                await event.reply("❌ لم يتم العثور على الحساب أو أنه غير متصل.")

            # إنهاء حالة الرد
            del owner_reply_state[OWNER_ID]

    clients = []
    for s in sessions:
        try:
            cl = TelegramClient(StringSession(s['str']), s['id'], s['hash'], **device_props)
            await cl.connect()
            if await cl.is_user_authorized():
                me = await cl.get_me()
                MY_ACCOUNT_IDS.append(me.id)
                account_logs[s['name']]['status'] = '✅ '
                clients.append(cl)
                # حفظ المراجع لتسهيل معرفة اسم الحساب لاحقاً
                s['_client'] = cl
                s['_me_id'] = me.id
                asyncio.create_task(worker(cl, s['name']))
        except: pass
    if clients:
        asyncio.create_task(fair_distribution_engine())
        resolved_ids = []
        # محاولة جلب أسماء المجموعات مسبقاً من جميع الحسابات لضمان التغطية
        for link in target_links:
            for cl in clients:
                try:
                    ent = await cl.get_entity(link)
                    peer_id = utils.get_peer_id(ent)
                    if peer_id not in resolved_ids:
                        resolved_ids.append(peer_id)
                        group_reply_counts_global[peer_id] = 0
                        group_keyword_counts_global[peer_id] = 0
                        group_names_map[peer_id] = getattr(ent, 'title', f"ID: {peer_id}").strip()
                        chat_queues[peer_id] = asyncio.Queue()
                    break # نجحنا في جلب الكيان، ننتقل للرابط التالي
                except: continue

        processed_msg_ids = set()

        async def handler_msg(event):
            global idx_khas, idx_tabadel, idx_saleb
            # منع التكرار بين الحسابات
            msg_unique_id = f"{event.chat_id}_{event.id}"
            if msg_unique_id in processed_msg_ids: return
            processed_msg_ids.add(msg_unique_id)
            if len(processed_msg_ids) > 1000: processed_msg_ids.clear()

            if event.sender_id in MY_ACCOUNT_IDS: return
            text = (event.text or "").lower().strip()
            if any(r in text for r in ALL_MY_REPLIES): return

            # تحديد الكلمات المفتاحية
            is_match = False
            msg_to_send = None

            if any(w in text for w in ["خاص", "تعال خاص", "نقطة", "نقطه", "خااص", "خاااص"]):
                is_match = True
                msg_to_send = replies_khas[idx_khas]; idx_khas = (idx_khas + 1) % len(replies_khas)
            elif any(w in text for w in ["سالب", "موجب", "ديوث", "تحرر", "نيج", "شاذ", "سوالب", "سالبة", "موجبة"]):
                is_match = True
                msg_to_send = replies_saleb[idx_saleb]; idx_saleb = (idx_saleb + 1) % len(replies_saleb)
            elif any(w in text for w in ["تبادل", "ورعان", "ورع", "صغار", "حلوين", "ميقا", "روابط", "قاطع", "تسطير", "مقاطع", "تسطيبر", "ميقاا", "رابط", "ورعن", "وروعان"]):
                is_match = True
                msg_to_send = replies_tabadel[idx_tabadel]; idx_tabadel = (idx_tabadel + 1) % len(replies_tabadel)

            if is_match:
                # عد الكلمة حتى لو لم يتم الرد بسبب الكولداون
                group_keyword_counts_global[event.chat_id] = group_keyword_counts_global.get(event.chat_id, 0) + 1

                # التحقق من الكولداون قبل وضع الرسالة في طابور الرد (7 ساعات = 25200 ثانية)
                if event.sender_id in replied_users and (time.time() - replied_users[event.sender_id] < 25200): return

                if msg_to_send:
                    replied_users[event.sender_id] = time.time()
                    if event.chat_id not in chat_queues:
                        chat_queues[event.chat_id] = asyncio.Queue()
                    await chat_queues[event.chat_id].put((event, msg_to_send, 0))

        # تسجيل المستمع لكل الحسابات لضمان وصول الرسائل من كل المجموعات
        for cl in clients:
            cl.add_event_handler(handler_msg, events.NewMessage(chats=resolved_ids))

        # === مراقبة الرسائل الخاصة (Private Messages) ===
        async def private_msg_handler(event):
            # التأكد من أنها رسالة خاصة (وليست من البوت نفسه أو مجموعات)
            if not event.is_private or event.sender_id in MY_ACCOUNT_IDS:
                return

            client = event.client
            account_name = None
            # تحديد الحساب الذي استقبل الرسالة
            for s in sessions:
                try:
                    if s.get('_client') == client:
                        account_name = s['name']
                        break
                except: pass

            # محاولة بديلة لمعرفة اسم الحساب
            if not account_name:
                me = await client.get_me()
                for s in sessions:
                    if s.get('_me_id') == me.id:
                        account_name = s['name']
                        break
            if not account_name:
                account_name = "غير معروف"

            sender = await event.get_sender()
            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'title', f'ID: {event.sender_id}')

            # إعداد الرسالة للمالك
            msg_header = f"📩 **رسالة خاصة جديدة**\n👤 من: [{sender_name}](tg://user?id={event.sender_id})\n🆔 ايدي: `{event.sender_id}`\n🤖 الحساب المستقبل: **{account_name}**\n\n"

            # إعداد زر الرد
            reply_button = Button.inline("✍️ رد", data=f"reply_{account_name}_{event.sender_id}")

            try:
                # تحويل الرسالة للمالك
                if event.media:
                    # تنزيل الميديا لحل مشكلة cross-client reference
                    file_path = await event.client.download_media(event.media)
                    if file_path:
                        try:
                            await control_bot.send_message(OWNER_ID, msg_header + (event.text or ""), file=file_path, buttons=[reply_button])
                        finally:
                            os.remove(file_path)
                    else:
                        print("Error: Could not download media")
                else:
                    await control_bot.send_message(OWNER_ID, msg_header + (event.text or ""), buttons=[reply_button])
            except Exception as e:
                print(f"Error forwarding private message: {e}")

        # تسجيل مستمع الرسائل الخاصة لكل حساب
        for cl in clients:
            cl.add_event_handler(private_msg_handler, events.NewMessage(func=lambda e: e.is_private))

    await asyncio.gather(control_bot.run_until_disconnected(), *(c.run_until_disconnected() for c in clients))
if __name__ == '__main__':
    asyncio.run(run_bot())
