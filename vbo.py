# -*- coding: utf-8 -*-
import asyncio, time, os, glob, random, json, logging, sys
from datetime import datetime, timedelta
from collections import deque
from telethon import TelegramClient, events, Button as TButton, utils as tutils
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# إعداد السجلات
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظيف الجلسات السابقة المتعلقة بلوحة التحكم لتجنب تداخل الجلسات المؤقتة
for f in glob.glob("*.session*"):
    if "control_panel" in f:
        try: os.remove(f)
        except: pass

# =================================================================
# تذكير أمني: يفضل نقل التوكنات والجلسات إلى ملف .env أو متغيرات بيئة
# =================================================================

# ==========================================
# إعدادات النظام الأول (جيش البوتات - Telethon)
# ==========================================

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
            if link.lstrip('-').isdigit():
                try:
                    entity = await client.get_entity(int(link))
                    return tutils.get_peer_id(entity)
                except:
                    if not link.startswith('-'):
                        try:
                            entity = await client.get_entity(int(f"-100{link}"))
                            return tutils.get_peer_id(entity)
                        except: pass
            if 't.me/+' in link or 't.me/joinchat/' in link:
                invite_hash = link.split('/')[-1].replace('+', '')
                from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
                try:
                    check = await client(CheckChatInviteRequest(invite_hash))
                    if hasattr(check, 'chat'): return tutils.get_peer_id(check.chat)
                    await client(ImportChatInviteRequest(invite_hash))
                except: pass
            else:
                try:
                    from telethon.tl.functions.channels import JoinChannelRequest
                    entity = await client.get_entity(link)
                    await client(JoinChannelRequest(entity))
                    return tutils.get_peer_id(entity)
                except: pass
            entity = await client.get_entity(link)
            return tutils.get_peer_id(entity)
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
                    try: chat = await event.get_chat(); g_title = tutils.get_display_name(chat)
                    except: chat = await client.get_entity(event.chat_id); g_title = tutils.get_display_name(chat)
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
            finally:
                try: self.reply_queue.task_done()
                except ValueError: pass

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
            [TButton.inline("📊 تقرير الحسابات", b"report")],
            [TButton.inline("🕒 آخر الردود", b"last_replies"), TButton.inline("💎 إحصائيات القروبات", b"group_info")],
            [TButton.inline("➕ إضافة قروب", b"add_group"), TButton.inline("📋 قائمة القروبات", b"list_groups")],
            [TButton.inline("⚙️ ضبط التأخير", b"delay_menu"), TButton.inline("🧹 مسح الكل", b"clear_groups")],
            [TButton.inline("🛑 إيقاف قراءة الرسائل" if not self.is_paused else "▶️ استئناف القراءة", b"toggle")]
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
                await self.safe_edit(event, text, buttons=[TButton.inline("🔙 رجوع", b"back")])
            elif event.data == b"last_replies":
                text = "🕒 **آخر الردود الناجحة:**\n\n" + ("\n".join(self.last_success_list) if self.last_success_list else "لا توجد ردود.")
                await self.safe_edit(event, text, buttons=[TButton.inline("🔙 رجوع", b"back")])
            elif event.data == b"group_info":
                text = "💎 **إحصائيات القروبات:**\n\n"
                if not self.group_stats: text += "لا توجد إحصائيات."
                else:
                    for title, stats in self.group_stats.items(): text += f"📍 **{title}**:\n   - الردود: {stats['count']}\n------------------\n"
                await self.safe_edit(event, text, buttons=[TButton.inline("🔙 رجوع", b"back")])
            elif event.data == b"list_groups":
                text = "📋 **قائمة القروبات المراقبة:**\n\n" + ("\n".join([f"{i}. {l}" for i,l in enumerate(self.target_links, 1)]) if self.target_links else "لا توجد.")
                text += f"\n\n🔢 المعرفات النشطة: {len(self.resolved_ids)}"
                await self.safe_edit(event, text, buttons=[TButton.inline("🔙 رجوع", b"back")])
            elif event.data == b"toggle":
                self.is_paused = not self.is_paused; status_txt = "🔴 متوقف" if self.is_paused else "🟢 يعمل"
                await event.answer(f"تغيير الحالة: {status_txt}", alert=True)
                await self.safe_edit(event, f"🕹️ **لوحة التحكم المتقدمة ({self.display_name}):**\nالحالة: {status_txt}\nالتأخير: {self.reply_delay}ث", buttons=self.get_buttons())
            elif event.data == b"delay_menu":
                buttons = [[TButton.inline("15ث", b"d_15"), TButton.inline("30ث", b"d_30")], [TButton.inline("60ث", b"d_60"), TButton.inline("120ث", b"d_120")], [TButton.inline("400ث", b"d_400")], [TButton.inline("🔙 رجوع", b"back")]]
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

        for link in self.target_links:
            for client in self.clients:
                cid = await self.join_group(client, link)
                if cid: self.resolved_ids.add(cid); break

        # الانتظار لضمان بقاء البوت يعمل
        await self.control_bot.run_until_disconnected()

# ==========================================
# إعدادات النظام الثاني (بوت التفعيل - PTB)
# ==========================================

PTB_TOKEN = "8418452497:AAEh3qXiNi7lrC2j_GXDaUl-iE6_Ngl91t4"
ADMIN_USERNAME = "@i_z_000"
CORRECT_CODE = "55012"
DATA_FILE = "data.json"

# متغيرات النظام (سيتم تحميلها من data.json)
admin_chat_id = None
bot_config = {"photo1": None, "caption1": None, "photo2": None, "caption2": None}
fake_sub_count = 85010
nudged_users = set() # استخدام set للبحث السريع
user_data = {}
link_clicks = 0

def save_ptb_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'user_data': user_data,
                'link_clicks': link_clicks,
                'admin_chat_id': admin_chat_id,
                'bot_config': bot_config,
                'fake_sub_count': fake_sub_count,
                'nudged_users': list(nudged_users) # التحويل إلى قائمة للحفظ
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def load_ptb_data():
    global admin_chat_id, bot_config, fake_sub_count, nudged_users, user_data, link_clicks
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            user_data = {}
            for k, v in data.get('user_data', {}).items():
                try: user_data[int(k)] = v
                except: pass
            admin_chat_id = data.get('admin_chat_id')
            bot_config = data.get('bot_config', {"photo1": None, "caption1": None, "photo2": None, "caption2": None})
            fake_sub_count = data.get('fake_sub_count', 85010)
            nudged_users = set(data.get('nudged_users', []))
            link_clicks = data.get('link_clicks', 0)
        except Exception as e:
            logger.error(f"Error loading data: {e}")

load_ptb_data()

def get_main_keyboard(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🍑 قنوات ورعان خليجي", callback_data='final_ورعان'),
         InlineKeyboardButton("🔞 قنوات بنات صغار", callback_data='final_بنات')],
        [InlineKeyboardButton("💦 قنوات اولاد صغار", callback_data='final_اولاد'),
         InlineKeyboardButton("👩‍👦 قنوات امهات واطفال", callback_data='final_امهات')],
        [InlineKeyboardButton("🎥 قنوات عربي حصرية", callback_data='final_عربي'),
         InlineKeyboardButton("🔍 قنوات تجسس", callback_data='final_تجسس')],
        [InlineKeyboardButton("🔥 قنوات دياثة جديد", callback_data='final_دياثة'),
         InlineKeyboardButton("👥 قروبات تجمع ورعان", callback_data='final_قروبات')],
        [InlineKeyboardButton("💬 تكلم مع فتاتك", callback_data='age_girl'),
         InlineKeyboardButton("👦 تكلم مع ورع خاص", callback_data='age_boy')],
        [InlineKeyboardButton("👗 خلع الملابس بالذكاء", callback_data='final_الذكاء')],
        [InlineKeyboardButton("📈 الإحصائيات", callback_data='stats_info'),
         InlineKeyboardButton("🤝 الدعم الفني", callback_data='support_info')]
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👤 إجمالي المستخدمين", callback_data='admin_count_only'),
                         InlineKeyboardButton("📊 الضغطات", callback_data='admin_link_clicks')])
        keyboard.append([InlineKeyboardButton("✅ المفعلين بالكود", callback_data='admin_activated_count')])
        keyboard.append([InlineKeyboardButton("📊 إحصائيات غير المتفاعلين", callback_data='admin_nudge_users')])
        keyboard.append([InlineKeyboardButton("📢 إرسال رسالة للكل", callback_data='broadcast')])
        keyboard.append([InlineKeyboardButton("🛑 إيقاف تشغيل البوت", callback_data='stop_bot')])
    return InlineKeyboardMarkup(keyboard)

async def monitor_inactivity(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    for user_id, data in list(user_data.items()):
        if not data.get('activated') and len(data.get('links', [])) == 0 and user_id not in nudged_users:
            join_time_str = data.get('join_time')
            if not join_time_str:
                data['join_time'] = now.isoformat(); save_ptb_data(); continue
            try:
                join_time = datetime.fromisoformat(join_time_str)
                if (now - join_time) > timedelta(minutes=10):
                    if bot_config.get("photo2"):
                        try:
                            await context.bot.send_photo(chat_id=user_id, photo=bot_config["photo2"], caption=bot_config["caption2"])
                            nudged_users.add(user_id); data['code_enabled'] = True; save_ptb_data()
                        except: pass
            except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_chat_id
    user = update.effective_user
    user_id = user.id
    username_tagged = f"@{user.username}" if user.username else str(user_id)

    if user_id not in user_data:
        user_data[user_id] = {
            'activated': False, 'username': username_tagged, 'start_count': 0,
            'activation_step': 0, 'links': [], 'join_time': datetime.now().isoformat(),
            'code_enabled': False, 'received_inactivity_msg': False
        }

    username_clean = user.username.lower() if user.username else ""
    target_admin = ADMIN_USERNAME.lstrip('@').lower()
    if username_clean == target_admin:
        admin_chat_id = user_id
        save_ptb_data()

    is_admin = (admin_chat_id is not None and user_id == admin_chat_id)
    if is_admin:
        load_ptb_data()
        if not bot_config.get("photo1") or update.message.text == "/setup":
            context.user_data['setup_step'] = 'waiting_photo1'
            await update.message.reply_text("مرحباً أيها المدير. يرجى إرسال الصورة الأولى (التي ستظهر بعد إرسال الروابط) ⭐")
            return

    await update.message.reply_text("🔥 مرحباً بك في أضخم بوت عربي 2026 🔥", reply_markup=get_main_keyboard(is_admin))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global link_clicks, fake_sub_count, admin_chat_id
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    username_clean = query.from_user.username.lower() if query.from_user.username else ""
    if username_clean == ADMIN_USERNAME.lstrip('@').lower():
        admin_chat_id = user_id

    is_admin = (admin_chat_id is not None and user_id == admin_chat_id)

    if data == 'main':
        await query.edit_message_text("🔥 مرحباً بك في أضخم بوت عربي 2026 🔥", reply_markup=get_main_keyboard(is_admin))
        return

    if is_admin:
        if data == 'stop_bot':
            await query.message.reply_text("⚠️ يتم الآن إيقاف تشغيل البوت..."); sys.exit(0)
        elif data == 'broadcast':
            await query.message.reply_text("📥 أرسل الرسالة الآن ليتم توزيعها على الجميع:")
            context.user_data['waiting_broadcast'] = True; return
        elif data == 'admin_count_only':
            await query.message.reply_text(f"👤 إجمالي المستخدمين: {len(user_data)} (الفعلي)"); return
        elif data == 'admin_link_clicks':
            await query.message.reply_text(f"📊 إجمالي الضغطات: {link_clicks}"); return
        elif data == 'admin_activated_count':
            activated_total = sum(1 for u in user_data.values() if u.get('activated'))
            await query.message.reply_text(f"✅ عدد المفعلين: {activated_total}"); return
        elif data == 'admin_nudge_users':
            sent_count = 0
            for uid, u_info in user_data.items():
                if not u_info.get('activated') and len(u_info.get('links', [])) == 0 and uid not in nudged_users:
                    if bot_config.get("photo2"):
                        try:
                            await context.bot.send_photo(chat_id=uid, photo=bot_config["photo2"], caption=bot_config["caption2"])
                            nudged_users.add(uid); u_info['code_enabled'] = True; sent_count += 1
                        except: pass
            save_ptb_data()
            await query.message.reply_text(f"📊 تم إرسال الصورة لـ {sent_count} مستخدم جديد."); return
        elif data.startswith('adm_reply:'):
            target_uid = int(data.split(':')[1])
            context.user_data['waiting_admin_reply_for'] = target_uid
            await query.message.reply_text(f"📥 أرسل الرد للمستخدم {target_uid}:"); return
        elif data.startswith('adm_activate:'):
            target_uid = int(data.split(':')[1])
            user_data[target_uid]['activated'] = True; save_ptb_data()
            success_msg = f"تهانينا 🎉 عزيزي {user_data[target_uid].get('username', 'المستخدم')} تم تفعيل البوت استمتع بأفضل المقاطع 🔥"
            try:
                await context.bot.send_message(chat_id=target_uid, text=success_msg)
                await context.bot.send_message(chat_id=target_uid, text="🔥 الأقسام مفتوحة الآن:", reply_markup=get_main_keyboard())
                await query.message.reply_text(f"✅ تم تفعيل المستخدم {target_uid}")
            except: pass
            return

    if data == 'stats_info':
        fake_sub_count += random.randint(1, 5); save_ptb_data()
        status_txt = "✅ مفعل" if user_data.get(user_id, {}).get('activated') else "❌ غير مفعل"
        text = f"📈 **إحصائيات البوت:**\n\n👥 عدد المشتركين: {fake_sub_count:,} مشترك\n💎 حالة حسابك: {status_txt}"
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main')]])); return

    if data == 'support_info': return

    if data in ['age_girl', 'age_boy'] or data.startswith('final_'):
        if user_data.get(user_id, {}).get('activated'):
            await query.message.reply_text("جاري جلب معلومات القنوات من السرفر....")
        else:
            link_clicks += 1; user_data[user_id]['activation_step'] = 1; user_data[user_id]['links'] = []; save_ptb_data()
            msg = "من اجل تفعيل بوت فابب الــعرب يجب عليك ان ترسل ثلاث قروبات تبادل لايقل عدد المتصلين فيه عن 50 متصل، بعد ان ترسل الروابط انتظر وسيتم مراجعتها خلال عشر دقائق كحد اقصى ونقوم بتفعيل البوت لك لتستمتع بمئات القنوات 🔥"
            await query.message.reply_text(msg); await query.message.reply_text("ارسل رابط القروب الأول ⭐")
        return

    if data == 'notify_admin':
        if admin_chat_id:
            try:
                await query.message.reply_text("تم ابلاغ الإدارة وسيتم تفعيل الحساب بأقرب وقت ⭐")
                if bot_config["photo1"]:
                    await context.bot.send_photo(chat_id=user_id, photo=bot_config["photo1"], caption=bot_config["caption1"])
                user_data[user_id]['activation_step'] = 0; user_data[user_id]['code_enabled'] = True; save_ptb_data()
            except: pass
        else: await query.message.reply_text("❌ المسؤول غير متصل.")
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_chat_id, link_clicks
    user_id = update.effective_user.id
    message = update.message
    text = message.text.strip() if message.text else ""
    username_tagged = f"@{update.effective_user.username}" if update.effective_user.username else str(user_id)

    if user_id not in user_data:
        user_data[user_id] = {
            'activated': False, 'username': username_tagged, 'start_count': 0,
            'activation_step': 0, 'links': [], 'join_time': datetime.now().isoformat(),
            'code_enabled': False, 'received_inactivity_msg': False
        }

    username_clean = update.effective_user.username.lower() if update.effective_user.username else ""
    if username_clean == ADMIN_USERNAME.lstrip('@').lower():
        admin_chat_id = user_id
        save_ptb_data()

    is_admin = (admin_chat_id is not None and user_id == admin_chat_id)
    if is_admin:
        step = context.user_data.get('setup_step')
        if step == 'waiting_photo1' and message.photo:
            bot_config["photo1"] = message.photo[-1].file_id; bot_config["caption1"] = message.caption or "تم استلام الروابط"; save_ptb_data()
            context.user_data['setup_step'] = 'waiting_photo2'; await message.reply_text("تم حفظ الصورة 1. أرسل الصورة 2 ⭐"); return
        elif step == 'waiting_photo2' and message.photo:
            bot_config["photo2"] = message.photo[-1].file_id; bot_config["caption2"] = message.caption or "نحن بانتظارك"; save_ptb_data()
            context.user_data['setup_step'] = None; await message.reply_text("تم الإعداد! 🔥"); return

    if context.user_data.get('waiting_broadcast') and is_admin:
        sent = 0
        for uid in list(user_data.keys()):
            try: await context.bot.send_message(chat_id=uid, text=text); sent += 1
            except: pass
        await update.message.reply_text(f"✅ تم الإرسال لـ {sent}"); context.user_data['waiting_broadcast'] = False; return

    if context.user_data.get('waiting_admin_reply_for') and is_admin:
        target = context.user_data['waiting_admin_reply_for']
        try: await context.bot.send_message(chat_id=target, text=f"📩 رد من الإدارة:\n\n{text}"); await update.message.reply_text("✅ تم")
        except: await update.message.reply_text("❌ فشل")
        context.user_data['waiting_admin_reply_for'] = None; return

    u_step = user_data[user_id].get('activation_step', 0)
    admin_kb = InlineKeyboardMarkup([[InlineKeyboardButton("رد", callback_data=f"adm_reply:{user_id}"), InlineKeyboardButton("تفعيل", callback_data=f"adm_activate:{user_id}")]])

    if u_step in [1, 2, 3]:
        user_data[user_id]['links'].append(text); save_ptb_data()
        if admin_chat_id:
            try: await context.bot.send_message(chat_id=admin_chat_id, text=f"👤 {username_tagged} أرسل الرابط {u_step}: {text}", reply_markup=admin_kb)
            except: pass

        if u_step == 1:
            user_data[user_id]['activation_step'] = 2; await message.reply_text("ممتاز، الان ارسل رابط القروب الثاني ⭐")
        elif u_step == 2:
            user_data[user_id]['activation_step'] = 3; await message.reply_text("جيد الان ارسل رابط القروب الثالث ⭐")
        elif u_step == 3:
            user_data[user_id]['activation_step'] = 4; save_ptb_data()
            if admin_chat_id:
                links_str = "\n".join([f"{i+1}- {l}" for i, l in enumerate(user_data[user_id]['links'])])
                await context.bot.send_message(chat_id=admin_chat_id, text=f"🔔 تقرير مجمع لـ {username_tagged}:\n{links_str}", reply_markup=admin_kb)
            await message.reply_text("تم استلام الروابط. اضغط لإعلام الإدارة:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("اضغط هنا لإعلام الإدارة", callback_data='notify_admin')]]))
        return

    if text == CORRECT_CODE:
        if user_data[user_id].get('code_enabled'):
            user_data[user_id]['activated'] = True; save_ptb_data()
            await message.reply_text("✅ تم التفعيل بنجاح!")
        else: await message.reply_text("❌ غير متاح لك حالياً.")

# ==========================================
# تشغيل الأنظمة معاً
# ==========================================

async def main():
    # 1. إعداد بوتات Telethon (جيش البوتات)
    bot1_config = {
        'system_name': "bot1", 'display_name': "البوت الأول", 'owner_id': 6762940512,
        'bot_token': "8520006260:AAGWatChzdHGXhZILav0gqX3Jn91NDzj1fg",
        'sessions_config': [
            {'name': 'الجلسة 1', 'id': 35234215, 'hash': '2f560ad5ac9a1c11b8582e42471c403c', 'str': '1BJWap1sBu5QxQPXDKdwMTJiQfyh9KD8cRE4pUghL9slakYFyvUUFTRcnN4xvUPEd6F-y01Mv2EkwTonZJpWO7Dsm3eMYhx11hntNpTwAPMz--Jv2_nZLQMzWl62Ssdi7c2FlhtMvr5f3wyE5IW2ocnAtvfVzUTs59hTh9cXwlMuoHzyYCYYibA2AadPuLjIOflMfmHa-JrMdAvCwSUe0_T6TtA5D8USSW_4ps7Y_B7rjDLbHvsVxZtzcBjGzJmGytxV0kyzsE_8luEJvxdUganOtyeBMKboIIByfou_uLWuF7QyYaCKspW422iHlmIHByJ_GZeI_Rrsy6c2w5Atr4BgIwHQlQ6M='},
            {'name': 'الجلسة 2', 'id': 39838472, 'hash': '39e0757f5b96e8a84c7797c17d28c29a', 'str': '1BJWap1sBu6F1feEVYtqx1o_ImLPmDXsjDKfL2q4nhfLm1BRYg_RpFRz-KHG9XV67qeBMmBuwusFA1YXF62GHSYDQtgx1fdy0eNy-_nQinIQHvnsMHEKdEpurPDuw9d_FmUTp2QrXj10qgWAs0XG6jRGAbqnzFNHJXnFHNgvm-tiIicwYflF_AeGiEZNc1mYZ832sQrReBdJ-g7eLYbpqSC7j3XLuylrZdxdc7eTJLURe78mHN1-y_4tPquvAULVtfl6REAaVR1zzYOfHiWojZzRPSGqAxj6dRZKGeM2lIpUL_1O6rAUUc49KJJlNgTBG5HF_xOx9qSa3DEQIhQlUiJpohQZBGuA='}
        ],
        'groups_file': "groups.json",
        'default_links': ['https://t.me/+z7K5sSzvWQU3NTAy', 'https://t.me/pewndgrop', 'https://t.me/M_R515', 'https://t.me/+wtGW0icU0pY2YWY0', 'https://t.me/krkokgrop']
    }
    army_config = {
        'system_name': "army", 'display_name': "الجيش", 'owner_id': 6762940512,
        'bot_token': "8207301806:AAH8aQwODSt7c0a8j-3-_0tZN4XHbqgCdmU",
        'sessions_config': [
            {'name': 'الرابع', 'id': 31991412, 'hash': 'fc87b7c169a60030ea339ca5e6932f6a', 'str': '1BJWap1wBu3ZURUHVmOYZgVtxDy7BxzCLlOHBFAg9qDkK5DDxGgBqV5keNxPIR5NEEgUtiINJGUPNBTMFaugwwQ1ZxzCtNl21lWFcMkI3aPxbOcoBbepkyK01d89-zvHaPIjL4vfGIQH3aRFZ3z6M8gFdGH_1dCqUFLSQQ6BWyXdNeW4m4bRDcubG1JJyPLxZi4Enhec6dgWgUVxJL24MwenfhrjKnONa4dFfEJGCAfa6WLOYcN_8RMN5YqtyWCq6ke1TsmMBs70TFY5nXJNsVQzCZRxQOTBul1MrLjv7cyynte2E3UdmtCPt_Dqp941hduR-ppPVYbhsKtkUVfGMhw9tSvs9Qp0='},
            {'name': 'الخامس', 'id': 34239992, 'hash': '6d62348439a8b0fc9c557000c002752a', 'str': '1BJWap1wBuzSrCs-rZx-pS4IzkY50rgar8C3Hpeg5j18JMrsG-JTwbx9XvgHKhnDKTt7FWXb39w7qPYntU6GBBuIk4I_d8pfpoFT7AfYaJlvvt_3Qo9e3XEB73ebqAD_dsSChEuURMi__Rznwf5sOpK8wX4D-kyCWxYOcbLxGqyZbNan6sWhlT2oszDfMtvOAg6TYh1MRMY5gm_4ihgdW1rCQEPn37kSKW1eMcMQUqOLBw7Q-JEYryS5RbRBoAqj04GHbZy_9LhHGGm7cUVszUw1tW1IeX1LjYc5ov0DlRouzznUgMtx_9_9CdPeiiLWXM4wyTxA9q6pNR_VsWzzTIY4pkHSfwhA='},
            {'name': 'السادس', 'id': 18664910, 'hash': '40d543872803f600230c7415e5a41c67', 'str': '1BJWap1wBuzFf0oRjZFWSoC8cfecKHHGe8rQ6OWnrJxeavVHbHbnofCNUGLtfurvoR4YomTA_-Z7L20slotqmjmC4ZvMAnz-Xm3Y7mHMR0Ld_Lq981XAxKc3IWJJawgsW5LBcmJeyu2sRklfUzfOGFmL6satq_T1HZGhTxKCdE6sVUchoHWdf3DswGJR3ksAxWgQtcXCV7pN1ggEXwY6gD2aEUME3bfSzzxqk20YQsQCRWNZsqqBgK_UycbWDf7D3VMICO4VH5yXqYufioqXqdo5YaIDPz_A58NlY8BjLrzZgyNuBvrqED75NBNJfTk6g22xXcDiYa2DOPU4SVwA-xShEuCgojoc='},
            {'name': 'السابع', 'id': 38615138, 'hash': 'a0eb2f816038c1cad154f47e9b8fba21', 'str': '1BJWap1sBu8WpQuA_B183Uv_sv0U3WeJrvrjGNBoZoiG3pQbSxsr7DyL1RF02KUJNut7nTh4QE71l5drjrO3lFyD5Cct0aHc1wGcv4Gfkq6d5NadP3mgA5U2quLLffL5mDx8e9ygCYdFD9cq1O9HTLjIDS2ry8FZg4h4Jb9Sw9PNT7vhDlCWn9Gllh3lbtPUV4801kxE2TXO_ZkFFX7dENNxpU9_2eUeZCWDlRjb7w8wRis6QbYjS1hwwdBGYBfT60_O4dkIqxgThJDcYFvrF7iQpKm71qvT2vWL_n9QpBfiPayPJrQ2yG03hx8sqQIqerMZ7rOP-gQiMltI1_aMe5XUxkouOsIw='},
            {'name': 'الثامن', 'id': 30018193, 'hash': '245b28a92f44ed44bfaafc4757ead9ea', 'str': '1BJWap1sBuzGd7ucxy7DmcZrPRTEd-tqYbXJ-OK0tahWOADkoKpMEM5JTCa5PEFArRxvA7LmGjgoaBtXdM_xDzhZE21HN7gd07rE4TH4yGvGD3deKX4uZxRlW2KzuD-eSAqJ_Pkyg8CnIpEkiSALk9lVCfmTYR_kR_QXAEittQG8DKWAEsQx64YM13DYHxQr6UhD2D8Xx6N_Jm61ZqRQAF1uXtm0JQDAiFZB35HHRNzvjXSV89qz0XDAujRA2TWTSM1fcI2l2-ZqAbi4e-1IS6QDt3tMTAq0lZMm6rShtWyIEN45bvvbP9FC0T7io-CjP5R4dl89chb_1DV3Gj463dYN0oDvx4IU='}
        ],
        'groups_file': "army_groups.json",
        'default_links': ['https://t.me/mwmwmnn', 'https://t.me/R_KA_N0'],
        'special_chat_id': -1003331495813
    }

    bot1 = TelegramBotSystem(**bot1_config)
    army_bot = TelegramBotSystem(**army_config)

    # 2. إعداد بوت PTB
    ptb_app = Application.builder().token(PTB_TOKEN).build()

    if ptb_app.job_queue:
        ptb_app.job_queue.run_repeating(monitor_inactivity, interval=300, first=60)

    ptb_app.add_handler(CommandHandler("start", start))
    ptb_app.add_handler(CommandHandler("setup", start))
    ptb_app.add_handler(CallbackQueryHandler(handle_callback))
    ptb_app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, text_handler))

    # 3. التشغيل المتوازي
    logger.info("🚀 جاري تشغيل كافة الأنظمة في ملف واحد...")

    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.updater.start_polling()

    # استخدام asyncio.gather لتشغيل كافة البوتات بشكل متزامن وبقاء السكربت يعمل
    await asyncio.gather(
        bot1.run(),
        army_bot.run(),
        asyncio.Event().wait() # لضمان عدم توقف السكربت إذا لم توفر بوتات Telethon انتظاراً داخلياً
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
