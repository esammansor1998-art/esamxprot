# -*- coding: utf-8 -*-
import asyncio, time, os, random, sys
from telethon import TelegramClient, events, Button, utils
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from datetime import datetime
# ===== إعدادات التحكم =====
OWNER_ID = 5584264085
bot_token = "8713183015:AAHQaYSyk3FdSFa6PXvzVKdM9Uz-2N-JdN0"
is_paused = False
account_logs = {}
last_messages = [] # سيحتوي على آخر 10 رسائل
group_reply_counts_global = {}
group_keyword_counts_global = {}
group_names_map = {}
chat_queues = {}
chat_locks = {}
global_dispatch_queue = asyncio.Queue()
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
sessions = [
    {'name': 'الرابع', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1sBuwjr36vLUfP-P0pz-_kZJXe0wDXbLo9jCUbar8fbYjwFxXZH9tEAPM7tG0uj7Lgr3LnDLnKeQnBdtPO7nv4FOkQ2-c_6DYtLJCNw2r-CRH2O1w0ccIAfL69JTnudv6RukOHnENOfZBMDBoLGbWHqg3PwgUigbLO352Cool494hjXt3qeDcd3bFOL_P-6SVkxQuNnhpSrt8mj6bEslBX69Nt1ooX-bMIdK_-OR7tUlREtikaY0G8r4jX97telE-Yiy4zuCQPemBkesogVil71N3hvi4lAuh_W4oKR0NaaZa8KwYW8PKdXKGyDurfm_ltb4fpzM_BPcPZiNwvNI3sz49k='},
    {'name': 'الخامس', 'id': 34239992, 'hash': '6d62348439a8b0fc9c557000c002752a', 'str': '1BJWap1sBuxzaPSmopzvgb0MOju4RDSTsxpPv-ZUo6SfDAt_I7BV7Dle8fDQpZ32uVNUH4IOSMKFDjncZP6UvrYt4yL4CV2Dwn9jusJ12jCeDzQAlxlvIP6wbOTWM-vVKDSeaTRuRlSfVRpnNYxNlaP8i-_wJmwNWOOWTuaAYIHHlv4C3Nzx3Q2MsHIJF0ojlTlsxSX1v3OJTtrgIs6-UgN0d7JKxvmBc6vxVsy2l61Kvp1ssgNI7PfybqF6bAnVJSp_E0UeNGEBsaRakx5rVPR18GRGgw5LDcUryH8Ur-CnPr15Ps483IkMMPg5xSPnC-92P7i6taTYSXyiLBzj1F-Z0cJADswI='},
    {'name': 'السادس', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67', 'str': '1BJWap1sBu6AsHAODsetXkk5IP_A4pxchCDZNISMdXE140rDzr8yiYXkv4NgBXtTqwN7EKwUyHJHrv2j6kZ46eNXSy4fUeK5P-oUfKHqQo_gGZw_5YhF5Kx8-mbKAhDrL8M9jWMxuqnMNjxkNkTMMTRhmDd6eBiEKUWMWxYPpVJuV74Hn96osixnBlMqQeD6CBPYRM6257JyOm341tVu5oMLI93clHDUlEkbDNcyEBulqKeAzyFWQDTA6DUDerEq8Cr7KVVrBg2Fe9fA0c1QuL7PBkQCDoiB81-CLa-0C1e-ljN9uGuS6Lbgp6qK7vrxJl7iDyBEyy3a1hcsPw-Sgmf-8IoDRQlw='},
    {'name': 'مهند', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1sBuxYEORERAAS2xeqwaZJhE5xK0DVjTNoKsddq3RmPr3802SMhH7KwNVYkQLK-WwobN0eLDx_h4k6cWqv3vvXWS8k4l4ZUVw010i47XFS0K3bcNjGzWhJf2tV3sUiI-ZILx69gMMtH99qN1nXwg_iH_ZJOzo28idh04PlaeJTlqo-Pr9o83vCnOo261_LcUCpfnsCz_K9CFh_58uUQIQjA3E96nUV5OB_kDrwmOL-8paOwnZDiv93L2cuoK-l2UrePSyrN1_EkRL76W_4XK1DxsTrMRtE4QEqXD7L71wRPSRNflaRVRt_VLG4HFUocjeecd1I6ZFC5RiCTeWG092z3bXw='},
    {'name': 'رامي', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1sBu4SAyQw55YiWTLopG2MpM3Lyz5J2YUQo7csBwVF8TW6p6d7aAKajLd4HcalKr0UlbMfAKzGzUy2XVQWKPtfcxJethFALEApM0LcUQrkFJtIAatBxLahzKTdnoIgjopgaW13_NqAfAzD066sqAWL4BEE9bFZeST8uRr7WNcAonodwAHWhYWtoI7wp-WouQxAjnG4im2I7mndt8ztnaNC63OgAYHVJDwe4WXMO_xBRmqostl-r26eC5aEJATmzFWiQTDxFSvjugHqA9rNHMCQe2HLGa7kvk1toHGLgtq6o6-OtHqQzddV3Qnm9eJN38RElQCHm_H_SFq4dl1J8N9Fx7Oo='},
    {'name': 'عامر', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1sBu5xxxOZQ2d2Ig1QwUsdhYeVQxVMVCdBF23J4fHUtzNYNO-jw4Q4t7zwaBlCpHbYmy8sfiLciQ6gNpLbW47XeX7WhtXCAvPNJNzQkhnfU1INrTH31CrSAH7atDUyQl2oGPJ7ZcxTtQ5s4C_DMZzjNiICFnSJ_IIg3S94YNCliAuLKnhW-MfRZ4UW9oQw7TABL3lrj0VOtVTw7RaA652oB9MpZr0vw_hyRR3LN5WrWmXg08uKH2S0rNpVCokB5GQcjoyMjXbS10rof-rjR_5rWQ4f5yOEuDVJEoRcJRxNLMvJ--o_4CSrqQ_zbpk3koQg8t3Mle0sP_CqQxLL4tGU9RRg='},
    {'name': 'سعد', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67',
'str': '1BJWap1sBu0BWcK4wVw8NLqSnGsQw6KW350AfNcfamH_WOsLRSrITGqmjGfExatcZE9jtf1DZeHN2v-RhrxMTxc7Fp-4o9O22lwpCh6eb_rIAlMJ-59M4rJklcYgFTsSxj4NPnaJ5gJ-RJfPxkpSbxp3k3Fq9VoXdYnH0cPHqDA5x5V-SkPq2lXlMeKVVemTwvgfVNgUDhde4Q1CaZ3PkQjcNiBF_8v2TmdLnrdYFzyP7i_p5wxku2RDOg2BM_6G6qxG6iI4_6a-plvT0hcuk_aOVpilkUbitaKwv2VEU3S4YbMqYJiw9PD9EBcsKYpfITjWZMls-Z2sgeohN4PNPwhdnssYdz2A='},
    {'name': 'نقطة', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67', 'str': '1BJWap1sBuwoSuHeD_lWRA804QC-Cc-MDdV7L9N8wcHDttigfe9OeHj6J0VCNhwk7_mNgPExxSYuZgpAwTEcTDIC1iVS0jjrOfbJm2pXame0MnzscY6iQ7q11lNDM_ERWC3qUTy3lU-o3-SsoQqSHp2Mq1VvXfanHXFy82587lqt6vQbdSANGcdl8oTx7YgToafDql6knsQOU7iIRlaY-SBhBv5wjiqamqOW3npcKR5no8Zo67ecDU-CcEINVf-QrppCEvHv9pfVF1aAsVnSH5rapKJSyMNJchHO3SmG3PLGOXIHBZiDXzi0uZKvPa_QD4GDu8MkQ4WFTskBhdufsWPhQ2C1c-tU='}
]
MY_ACCOUNT_IDS = []
idx_khas = idx_tabadel = idx_saleb = 0
replied_users = {}
for s in sessions:
    account_logs[s['name']] = {'total_count': 0, 'status': '⏳  متصل', 'pause_until': 0}
async def fair_distribution_engine():
    try:
        while True:
            keys = list(chat_queues.keys())
            if not keys:
                await asyncio.sleep(1)
                continue
            for chat_id in keys:
                q = chat_queues[chat_id]
                if not q.empty() and not chat_locks.get(chat_id, False):
                    item = await q.get()
                    await global_dispatch_queue.put(item)
                    chat_locks[chat_id] = True
                    await asyncio.sleep(0.3)
            await asyncio.sleep(0.5)
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
    control_bot = TelegramClient('bot_control', sessions[0]['id'], sessions[0]['hash'], **device_props)
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
                        group_names_map[peer_id] = getattr(ent, 'title', f"ID: {peer_id}").strip()
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

            if any(w in text for w in ["خاص", "تعال خاص", "نقطة", "نقطه"]):
                is_match = True
                msg_to_send = replies_khas[idx_khas]; idx_khas = (idx_khas + 1) % len(replies_khas)
            elif any(w in text for w in ["سالب", "موجب", "ديوث", "تحرر", "نيج", "شاذ", "سوالب"]):
                is_match = True
                msg_to_send = replies_saleb[idx_saleb]; idx_saleb = (idx_saleb + 1) % len(replies_saleb)
            elif any(w in text for w in ["تبادل", "ورعان", "ورع", "صغار", "حلوين", "ميقا", "روابط", "قاطع", "تسطير", "مقاطع"]):
                is_match = True
                msg_to_send = replies_tabadel[idx_tabadel]; idx_tabadel = (idx_tabadel + 1) % len(replies_tabadel)

            if is_match:
                # عد الكلمة حتى لو لم يتم الرد بسبب الكولداون
                group_keyword_counts_global[event.chat_id] = group_keyword_counts_global.get(event.chat_id, 0) + 1

                # التحقق من الكولداون قبل وضع الرسالة في طابور الرد
                if event.sender_id in replied_users and (time.time() - replied_users[event.sender_id] < 14400): return

                if msg_to_send:
                    replied_users[event.sender_id] = time.time()
                    if event.chat_id not in chat_queues:
                        chat_queues[event.chat_id] = asyncio.Queue()
                    await chat_queues[event.chat_id].put((event, msg_to_send, 0))

        # تسجيل المستمع لكل الحسابات لضمان وصول الرسائل من كل المجموعات
        for cl in clients:
            cl.add_event_handler(handler_msg, events.NewMessage(chats=resolved_ids))
    await asyncio.gather(control_bot.run_until_disconnected(), *(c.run_until_disconnected() for c in clients))
if __name__ == '__main__':
    asyncio.run(run_bot())
