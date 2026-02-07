# -*- coding: utf-8 -*-
import asyncio, time, os, glob, random, json
from collections import deque
from telethon import TelegramClient, events, Button, utils, types
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, MessageNotModifiedError, UserDeactivatedError

# تنظيف الجلسات السابقة عند التشغيل
for f in glob.glob("*.session*"):
    if "bot_control_panel" in f or "army_control_panel" in f:
        try: os.remove(f)
        except: pass

class TelegramBotSystem:
    def __init__(self, system_name, display_name, owner_id, bot_token, sessions_config, groups_file, default_links, special_chat_id=None):
        self.system_name = system_name
        self.display_name = display_name
        self.owner_id = owner_id
        self.bot_token = bot_token
        self.sessions_config = sessions_config
        self.groups_file = groups_file
        self.default_links = default_links
        self.special_chat_id = special_chat_id

        self.is_paused = False
        self.reply_delay = 20
        self.account_logs = {}
        self.group_stats = {}
        self.last_success_list = []
        self.replied_users = {}
        self.reply_queue = asyncio.Queue()
        self.processed_msgs = deque(maxlen=1000)
        self.resolved_ids = set()
        if special_chat_id:
            self.resolved_ids.add(special_chat_id)
        self.waiting_for_group = {}
        self.my_ids = []
        self.clients = []
        self.control_bot = None

        self.target_links = self.load_groups()

        self.replies_khas = [
            "وين رايحين، التبادلات مضيعة للوقت يخوي، عندي لك رابط بوت كله مقاطع نار نار، رابطو بوصف حسابي نار.",
            "ليش الخاص يحلوين، روحو البوت رابطوو بوصف حسابي",
            "ليش تتعب حالك بالخاص وهيك، روح البوت رابطو بوصف حسابي لاتفوت الفرصه شوي واحذفه"
        ]
        self.replies_tabadel = [
            "تبغا مقاطع ورعان ياصاحبي، معي بوت بوصف حسابي فيه 30 الف مقطع",
            "التبادلات تعب، عندي لك بوت بوصف حسابي ببلاش ورعان من كل الجنسيات",
            "مقاطع ورعان اخر موديل، البوت بوصف حسابي وقول للتبادلات باي باي",
            "خش البوت حقي من وصف حسابي وعيش الجو مع الورعان اخر دقه",
            "ضفت اكثر من 31 الف مقطع ورع عندي بالبوت بوصف حسابي لو تريد"
        ]
        self.idx_khas = 0
        self.idx_tabadel = 0

    def load_groups(self):
        links = self.default_links.copy()
        if os.path.exists(self.groups_file):
            try:
                with open(self.groups_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    new_links = data if isinstance(data, list) else list(data.values()) if isinstance(data, dict) else []
                    for l in new_links:
                        if isinstance(l, str) and l not in links:
                            links.append(l)
            except: pass
        return links

    def save_groups(self):
        try:
            to_save = [l for l in self.target_links if isinstance(l, str)]
            with open(self.groups_file, "w", encoding="utf-8") as f:
                json.dump(list(set(to_save)), f, ensure_ascii=False, indent=4)
        except: pass

    async def join_group(self, client, link):
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

    def init_log(self, name):
        self.account_logs[name] = {
            'unique_ids': set(),
            'total_count': 0,
            'failed_count': 0,
            'last_fail_reason': 'لا يوجد',
            'status': 'نشط ✅',
            'pause_until': 0
        }

    async def worker(self, client, account_name):
        while True:
            item = await self.reply_queue.get()
            try:
                event, reply_text, retry_count = item
                if self.is_paused:
                    await asyncio.sleep(1); await self.reply_queue.put((event, reply_text, retry_count)); continue
                if time.time() < self.account_logs[account_name]['pause_until']:
                    await self.reply_queue.put((event, reply_text, retry_count)); await asyncio.sleep(2); continue

                sent_msg = await event.reply(reply_text)
                self.account_logs[account_name]['total_count'] += 1
                self.account_logs[account_name]['unique_ids'].add(event.sender_id)
                self.account_logs[account_name]['status'] = 'نشط ✅'

                try:
                    try: chat = await event.get_chat(); g_title = utils.get_display_name(chat)
                    except: chat = await client.get_entity(event.chat_id); g_title = utils.get_display_name(chat)
                    if hasattr(chat, 'username') and chat.username: msg_link = f"https://t.me/{chat.username}/{sent_msg.id}"
                    else: clean_id = str(event.chat_id).replace('-100', '', 1).lstrip('-'); msg_link = f"https://t.me/c/{clean_id}/{sent_msg.id}"
                except: g_title = f"قروب {event.chat_id}"; msg_link = "الرابط غير متاح"

                if g_title not in self.group_stats: self.group_stats[g_title] = {'count': 0}
                self.group_stats[g_title]['count'] += 1
                self.last_success_list.insert(0, f"🕒 {time.strftime('%H:%M')} | {account_name} ➜ {g_title}: {msg_link}")
                if len(self.last_success_list) > 10: self.last_success_list.pop()

                sleep_start = time.time(); jitter = random.uniform(0, 5)
                while (time.time() - sleep_start) < (self.reply_delay + jitter):
                    if self.is_paused: break
                    await asyncio.sleep(0.5)

            except FloodWaitError as e:
                self.account_logs[account_name]['status'] = f'مقيد ({e.seconds}ث)'; self.account_logs[account_name]['pause_until'] = time.time() + e.seconds
                await self.reply_queue.put((event, reply_text, retry_count))
            except Exception as e:
                if retry_count < 2: await self.reply_queue.put((event, reply_text, retry_count + 1))
                else:
                    self.account_logs[account_name]['failed_count'] += 1
                    self.account_logs[account_name]['last_fail_reason'] = str(e)
                    self.account_logs[account_name]['status'] = 'خطأ ⚠️'
            finally: self.reply_queue.task_done()

    async def message_handler(self, event):
        if self.is_paused or event.sender_id in self.my_ids or event.out: return
        if event.chat_id not in self.resolved_ids: return
        msg_key = (event.chat_id, event.id)
        if msg_key in self.processed_msgs: return
        self.processed_msgs.append(msg_key)

        if event.sender_id in self.replied_users and (time.time() - self.replied_users[event.sender_id] < 7200): return
        text = (event.text or "").strip(); reply_msg = None
        if "خاص" in text:
            reply_msg = self.replies_khas[self.idx_khas]
            self.idx_khas = (self.idx_khas + 1) % len(self.replies_khas)
        elif any(w in text for w in ["تبادل", "ورعان", "ورع", "صغار"]):
            reply_msg = self.replies_tabadel[self.idx_tabadel]
            self.idx_tabadel = (self.idx_tabadel + 1) % len(self.replies_tabadel)

        if reply_msg:
            self.replied_users[event.sender_id] = time.time()
            await self.reply_queue.put((event, reply_msg, 0))

    async def safe_edit(self, event, text, buttons=None):
        try:
            if len(text) > 4000: text = text[:3900] + "\n\n...(تم اختصار النص)"
            await event.edit(text, buttons=buttons)
        except: await event.respond(text[:4000], buttons=buttons)

    def get_buttons(self):
        return [
            [Button.inline("📊 تقرير الحسابات", b"report")],
            [Button.inline("🕒 آخر الردود", b"last_replies"), Button.inline("💎 إحصائيات القروبات", b"group_info")],
            [Button.inline("➕ إضافة قروب", b"add_group"), Button.inline("📋 قائمة القروبات", b"list_groups")],
            [Button.inline("⚙️ ضبط التأخير", b"delay_menu"), Button.inline("🧹 مسح الكل", b"clear_groups")],
            [Button.inline("🛑 إيقاف قراءة الرسائل" if not self.is_paused else "▶️ استئناف القراءة", b"toggle")]
        ]

    async def run(self):
        self.control_bot = TelegramClient(f"{self.system_name}_control_panel", self.sessions_config[0]['id'], self.sessions_config[0]['hash'])
        await self.control_bot.start(bot_token=self.bot_token)

        @self.control_bot.on(events.NewMessage(pattern='تحكم', from_users=self.owner_id))
        async def cmd_control(event):
            status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
            await event.reply(f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())

        @self.control_bot.on(events.CallbackQuery())
        async def catcher(event):
            if event.data == b"add_group":
                self.waiting_for_group[event.sender_id] = True
                await event.answer("📥 أرسل رابط أو ID القروب الآن", alert=True)
            elif event.data == b"report":
                text = f"📊 **تقرير حسابات {self.display_name}:**\n\n"
                for name, log in self.account_logs.items():
                    text += f"👤 **{name}**:\n   - الحالة: {log['status']}\n   - الردود: {log['total_count']}\n   - فريد: {len(log['unique_ids'])}\n   - فشل: {log['failed_count']}\n------------------\n"
                await self.safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
            elif event.data == b"last_replies":
                text = "🕒 **آخر الردود الناجحة:**\n\n" + ("\n".join(self.last_success_list) if self.last_success_list else "لا توجد ردود.")
                await self.safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
            elif event.data == b"group_info":
                text = "💎 **إحصائيات القروبات:**\n\n"
                if not self.group_stats: text += "لا توجد إحصائيات."
                else:
                    for title, stats in self.group_stats.items(): text += f"📍 **{title}**:\n   - الردود: {stats['count']}\n------------------\n"
                await self.safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
            elif event.data == b"list_groups":
                text = "📋 **قائمة القروبات المراقبة:**\n\n" + ("\n".join([f"{i}. {l}" for i,l in enumerate(self.target_links, 1)]) if self.target_links else "لا توجد.")
                text += f"\n\n🔢 المعرفات النشطة: {len(self.resolved_ids)}"
                await self.safe_edit(event, text, buttons=[Button.inline("🔙 رجوع", b"back")])
            elif event.data == b"toggle":
                self.is_paused = not self.is_paused; status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
                await event.answer(f"تغيير الحالة: {status_txt}", alert=True)
                await self.safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())
            elif event.data == b"delay_menu":
                buttons = [[Button.inline("15ث", b"d_15"), Button.inline("30ث", b"d_30")], [Button.inline("60ث", b"d_60"), Button.inline("120ث", b"d_120")], [Button.inline("400ث", b"d_400")], [Button.inline("🔙 رجوع", b"back")]]
                await self.safe_edit(event, f"⚙️ **التأخير الحالي: {self.reply_delay}ث**\nاختر مدة الاستراحة:", buttons=buttons)
            elif event.data.startswith(b"d_"):
                self.reply_delay = int(event.data.split(b"_")[1]); await event.answer(f"تم الضبط على {self.reply_delay}ث", alert=True)
                status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
                await self.safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())
            elif event.data == b"clear_groups":
                self.target_links = self.default_links.copy(); self.resolved_ids.clear()
                if self.special_chat_id: self.resolved_ids.add(self.special_chat_id)
                self.save_groups()
                for link in self.target_links:
                    for client in self.clients:
                        cid = await self.join_group(client, link)
                        if cid: self.resolved_ids.add(cid)
                await event.answer("🧹 تم استعادة الافتراضية", alert=True)
                status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
                await self.safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())
            elif event.data == b"back":
                status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
                await self.safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())

        @self.control_bot.on(events.NewMessage(from_users=self.owner_id))
        async def add_group_listener(event):
            if not self.waiting_for_group.get(event.sender_id): return
            link = event.text.strip(); self.waiting_for_group.pop(event.sender_id, None)
            found = False
            for client in self.clients:
                cid = await self.join_group(client, link)
                if cid: self.resolved_ids.add(cid); found = True
            if found:
                if link not in self.target_links: self.target_links.append(link); self.save_groups()
                await event.reply(f"✅ [{self.display_name}] تم إضافة القروب: {link}")
            else: await event.reply(f"❌ [{self.display_name}] فشل الانضمام: {link}")

        # تشغيل الحسابات
        for s_info in self.sessions_config:
            client = TelegramClient(StringSession(s_info['str']), s_info['id'], s_info['hash'])
            await client.start()
            me = await client.get_me(); self.my_ids.append(me.id); self.init_log(s_info['name'])
            self.clients.append(client); asyncio.create_task(self.worker(client, s_info['name']))
            client.add_event_handler(self.message_handler, events.NewMessage())

        print(f"🔄 [{self.system_name}] جاري تحميل {len(self.target_links)} قروب...")
        for link in self.target_links:
            res = False
            for client in self.clients:
                cid = await self.join_group(client, link)
                if cid: self.resolved_ids.add(cid); res = True
            if not res: print(f"⚠️ [{self.system_name}] فشل: {link}")
        print(f"✅ [{self.system_name}] المراقبة نشطة لـ {len(self.resolved_ids)} قروب.")

        await self.control_bot.run_until_disconnected()

async def main():
    # إعدادات البوت الأول
    bot1_config = {
        'system_name': "bot1",
        'display_name': "البوت الأول",
        'owner_id': 6762940512,
        'bot_token': "8520006260:AAGWatChzdHGXhZILav0gqX3Jn91NDzj1fg",
        'sessions_config': [
            {'name': 'الجلسة 1', 'id': 35234215, 'hash': '2f560ad5ac9a1c11b8582e42471c403c', 'str': '1BJWap1sBu5QxQPXDKdwMTJiQfyh9KD8cRE4pUghL9slakYFyvUUFTRcnN4xvUPEd6F-y01Mv2EkwTonZJpWO7Dsm3eMYhx11hntNpTwAPMz--Jv2_nZLQMzWl62Ssdi7c2FlhtMvr5f3wyE5IW2ocnAtvfVzUTs59hTh9cXwlMuoHzyYCYYibA2AadPuLjIOflMfmHa-JrMdAvCwSUe0_T6TtA5D8USSW_4ps7Y_B7rjDLbHvsVxZtzcBjGzJmGytxV0kyzsE_8luEJvxdUganOtyeBMKboIIByfou_uLWuF7QyYaCKspW422iHlmIHByJ_GZeI_Rrsy6c2w5Atr4BgIwHQlQ6M='},
            {'name': 'الجلسة 2', 'id': 39838472, 'hash': '39e0757f5b96e8a84c7797c17d28c29a', 'str': '1BJWap1sBu6F1feEVYtqx1o_ImLPmDXsjDKfL2q4nhfLm1BRYg_RpFRz-KHG9XV67qeBMmBuwusFA1YXF62GHSYDQtgx1fdy0eNy-_nQinIQHvnsMHEKdEpurPDuw9d_FmUTp2QrXj10qgWAs0XG6jRGAbqnzFNHJXnFHNgvm-tiIicwYflF_AeGiEZNc1mYZ832sQrReBdJ-g7eLYbpqSC7j3XLuylrZdxdc7eTJLURe78mHN1-y_4tPquvAULVtfl6REAaVR1zzYOfHiWojZzRPSGqAxj6dRZKGeM2lIpUL_1O6rAUUc49KJJlNgTBG5HF_xOx9qSa3DEQIhQlUiJpohQZBGuA='}
        ],
        'groups_file': "groups.json",
        'default_links': ['https://t.me/+z7K5sSzvWQU3NTAy', 'https://t.me/pewndgrop', 'https://t.me/M_R515', 'https://t.me/+wtGW0icU0pY2YWY0', 'https://t.me/krkokgrop']
    }

    # إعدادات الجيش
    army_config = {
        'system_name': "army",
        'display_name': "الجيش",
        'owner_id': 6762940512,
        'bot_token': "8207301806:AAH8aQwODSt7c0a8j-3-_0tZN4XHbqgCdmU",
        'sessions_config': [
            {'name': 'الرابع', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1wBu3ZURUHVmOYZgVtxDy7BxzCLlOHBFAg9qDkK5DDxGgBqV5keNxPIR5NEEgUtiINJGUPNBTMFaugwwQ1ZxzCtNl21lWFcMkI3aPxbOcoBbepkyK01d89-zvHaPIjL4vfGIQH3aRFZ3z6M8gFdGH_1dCqUFLSQQ6BWyXdNeW4m4bRDcubG1JJyPLxZi4Enhec6dgWgUVxJL24MwenfhrjKnONa4dFfEJGCAfa6WLOYcN_8RMN5YqtyWCq6ke1TsmMBs70TFY5nXJNsVQzCZRxQOTBul1MrLjv7cyynte2E3UdmtCPt_Dqp941hduR-ppPVYbhsKtkUVfGMhw9tSvs9Qp0='},
            {'name': 'الخامس', 'id': 34239992, 'hash': '6d62348439a8b0fc9c557000c002752a', 'str': '1BJWap1wBuzSrCs-rZx-pS4IzkY50rgar8C3Hpeg5j18JMrsG-JTwbx9XvgHKhnDKTt7FWXb39w7qPYntU6GBBuIk4I_d8pfpoFT7AfYaJlvvt_3Qo9e3XEB73ebqAD_dsSChEuURMi__Rznwf5sOpK8wX4D-kyCWxYOcbLxGqyZbNan6sWhlT2oszDfMtvOAg6TYh1MRMY5gm_4ihgdW1rCQEPn37kSKW1eMcMQUqOLBw7Q-JEYryS5RbRBoAqj04GHbZy_9LhHGGm7cUVszUw1tW1IeX1LjYc5ov0DlRouzznUgMtx_9_9CdPeiiLWXM4wyTxA9q6pNR_VsWzzTIY4pkHSfwhA='},
            {'name': 'السادس', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67', 'str': '1BJWap1wBuzFf0oRjZFWSoC8cfecKHHGe8rQ6OWnrJxeavVHbHbnofCNUGLtfurvoR4YomTA_-Z7L20slotqmjmC4ZvMAnz-Xm3Y7mHMR0Ld_Lq981XAxKc3IWJJawgsW5LBcmJeyu2sRklfUzfOGFmL6satq_T1HZGhTxKCdE6sVUchoHWdf3DswGJR3ksAxWgQtcXCV7pN1ggEXwY6gD2aEUME3bfSzzxqk20YQsQCRWNZsqqBgK_UycbWDf7D3VMICO4VH5yXqYufioqXqdo5YaIDPz_A58NlY8BjLrzZgyNuBvrqED75NBNJfTk6g22xXcDiYa2DOPU4SVwA-xShEuCgojoc='},
            {'name': 'السابع', 'id': 38615138, 'hash': 'a0eb2f816038c1cad154f47e9b8fba21', 'str': '1BJWap1sBu8WpQuA_B183Uv_sv0U3WeJrvrjGNBoZoiG3pQbSxsr7DyL1RF02KUJNut7nTh4QE71l5drjrO3lFyD5Cct0aHc1wGcv4Gfkq6d5NadP3mgA5U2quLLffL5mDx8e9ygCYdFD9cq1O9HTLjIDS2ry8FZg4h4Jb9Sw9PNT7vhDlCWn9Gllh3lbtPUV4801kxE2TXO_ZkFFX7dENNxpU9_2eUeZCWDlRjb7w8wRis6QbYjS1hwwdBGYBfT60_O4dkIqxgThJDcYFvrF7iQpKm71qvT2vWL_n9QpBfiPayPJrQ2yG03hx8sqQIqerMZ7rOP-gQiMltI1_aMe5XUxkouOsIw='},
            {'name': 'الثامن', 'id': 30018193, 'hash': '245b28a92f44ed44bfaafc4757ead9ea', 'str': '1BJWap1sBuzGd7ucxy7DmcZrPRTEd-tqYbXJ-OK0tahWOADkoKpMEM5JTCa5PEFArRxvA7LmGjgoaBtXdM_xDzhZE21HN7gd07rE4TH4yGvGD3deKX4uZxRlW2KzuD-eSAqJ_Pkyg8CnIpEkiSALk9lVCfmTYR_kR_QXAEittQG8DKWAEsQx64YM13DYHxQr6UhD2D8Xx6N_Jm61ZqRQAF1uXtm0JQDAiFZB35HHRNzvjXSV89qz0XDAujRA2TWTSM1fcI2l2-ZqAbi4e-1IS6QDt3tMTAq0lZMm6rShtWyIEN45bvvbP9FC0T7io-CjP5R4dl89chb_1DV3Gj463dYN0oDvx4IU='}
        ],
        'groups_file': "army_groups.json",
        'default_links': ['https://t.me/mwmwmnn', 'https://t.me/R_KA_N0', 'https://t.me/Nj_QU', 'https://t.me/L_A_m_e_s_0', 'https://t.me/lako0019', 'https://t.me/hwlwjwo', 'https://t.me/whsuxjw', 'https://t.me/AR_HDA', 'https://t.me/hanTii1'],
        'special_chat_id': -1003331495813
    }

    bot1 = TelegramBotSystem(**bot1_config)
    army_bot = TelegramBotSystem(**army_config)

    await asyncio.gather(bot1.run(), army_bot.run())

if __name__ == '__main__':
    asyncio.run(main())
