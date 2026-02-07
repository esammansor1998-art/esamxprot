# -*- coding: utf-8 -*-
import logging
import json
import os
import asyncio
import sys
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

# --- الإعدادات الثابتة ---
TOKEN = "8418452497:AAEh3qXiNi7lrC2j_GXDaUl-iE6_Ngl91t4"
# تم تحديث حساب المسؤول بناءً على طلبك
ADMIN_USERNAME = "@i_z_000"
CORRECT_CODE = "55012"
DATA_FILE = "data.json"
admin_chat_id = None

# --- إدارة البيانات ---
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'user_data': user_data,
            'link_clicks': link_clicks,
            'admin_chat_id': admin_chat_id
        }, f)

def load_data():
    global admin_chat_id
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            u_data = {int(k): v for k, v in data['user_data'].items()}
            admin_chat_id = data.get('admin_chat_id')
            return u_data, data.get('link_clicks', 0)
        except: return {}, 0
    return {}, 0

user_data, link_clicks = load_data()

# --- واجهة الإدخال عند التشغيل ---
print("\n" + "="*30)
CODE_LINK = input("أدخل رابط الحصول على الكود (أو رابط خارجي): ").strip()
SUB_CHANNEL_LINK = input("أدخل رابط قناة الاشتراك: ").strip()
ENABLE_SUB_CHECK = input("تفعيل رسالة الاشتراك مرتين؟ (yes/no): ").strip().lower()
print("="*30 + "\n")

# --- لوحة المفاتيح الرئيسية ---
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
        keyboard.append([InlineKeyboardButton("📢 إرسال رسالة للكل", callback_data='broadcast')])
        keyboard.append([InlineKeyboardButton("🛑 إيقاف تشغيل البوت", callback_data='stop_bot')])
    return InlineKeyboardMarkup(keyboard)

# --- المعالجات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_chat_id
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "بدون_معرف"

    if user_id not in user_data:
        user_data[user_id] = {
            'activated': False,
            'username': username,
            'start_count': 0,
            'activation_step': 0,
            'links': []
        }

    user_data[user_id]['username'] = username

    # التقاط ID المسؤول
    if username == ADMIN_USERNAME:
        admin_chat_id = user_id

    save_data()

    if ENABLE_SUB_CHECK == "yes" and username != ADMIN_USERNAME:
        current_count = user_data[user_id].get('start_count', 0)
        if current_count == 0:
            user_data[user_id]['start_count'] = 1
            save_data()
            return await update.message.reply_text(f"يجب عليك الاشتراك بالقناة للمواصلة:\n{SUB_CHANNEL_LINK}\n\nبعد الاشتراك ارسل /start")
        elif current_count == 1:
            user_data[user_id]['start_count'] = 2
            save_data()
            return await update.message.reply_text(f"تأكد انك مشترك بالقناة واعد المحاوله عبر ارسال /start\n\nرابط القناة: {SUB_CHANNEL_LINK}")

    is_admin = (username == ADMIN_USERNAME)
    await update.message.reply_text("🔥 مرحباً بك في أضخم بوت عربي 2026 🔥", reply_markup=get_main_keyboard(is_admin))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global link_clicks
    query = update.callback_query
    user_id = query.from_user.id
    username = f"@{query.from_user.username}" if query.from_user.username else str(user_id)
    data = query.data
    await query.answer()

    is_admin = (username == ADMIN_USERNAME)

    if data == 'main':
        await query.edit_message_text("🔥 مرحباً بك في أضخم بوت عربي 2026 🔥", reply_markup=get_main_keyboard(is_admin))
        return

    if data == 'stop_bot' and is_admin:
        await query.message.reply_text("⚠️ يتم الآن إيقاف تشغيل البوت...")
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        sys.exit(0)

    if data == 'broadcast' and is_admin:
        await query.message.reply_text("📥 أرسل الرسالة الآن ليتم توزيعها على الجميع:")
        context.user_data['waiting_broadcast'] = True
        return

    if is_admin:
        if data == 'admin_count_only':
            await query.message.reply_text(f"👤 إجمالي المستخدمين: {len(user_data)}")
            return
        elif data == 'admin_link_clicks':
            await query.message.reply_text(f"📊 إجمالي الضغطات: {link_clicks}")
            return
        elif data == 'admin_activated_count':
            activated_total = sum(1 for u in user_data.values() if u.get('activated'))
            await query.message.reply_text(f"✅ عدد المفعلين: {activated_total}")
            return
        elif data.startswith('adm_reply:'):
            target_uid = int(data.split(':')[1])
            context.user_data['waiting_admin_reply_for'] = target_uid
            await query.message.reply_text(f"📥 أرسل الرسالة التي تريد إرسالها للمستخدم {target_uid}:")
            return
        elif data.startswith('adm_activate:'):
            target_uid = int(data.split(':')[1])
            user_data[target_uid]['activated'] = True
            save_data()
            target_name = user_data[target_uid].get('username', str(target_uid))
            success_msg = f"تهانينا 🎉 عزيزي {target_name} تم تفعيل البوت استمتع بأفضل المقاطع 🔥"
            try:
                await context.bot.send_message(chat_id=target_uid, text=success_msg)
                await context.bot.send_message(chat_id=target_uid, text="🔥 يمكنك الآن استخدام كافة الأقسام:", reply_markup=get_main_keyboard())
                await query.message.reply_text(f"✅ تم تفعيل البوت للمستخدم {target_name} بنجاح.")
            except:
                await query.message.reply_text(f"❌ فشل إرسال رسالة التفعيل للمستخدم {target_uid}.")
            return

    if data == 'stats_info':
        activated_total = sum(1 for u in user_data.values() if u.get('activated'))
        text = (
            f"📈 **إحصائيات البوت:**\n\n"
            f"👤 عدد المستخدمين: {len(user_data)}\n"
            f"✅ عدد الحسابات المفعلة: {activated_total}\n"
            f"📊 إجمالي التفاعلات: {link_clicks}\n\n"
            f"حالة حسابك: {'✅ مفعل' if user_data.get(user_id, {}).get('activated') else '❌ غير مفعل'}"
        )
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main')]]))
        return

    if data == 'support_info':
        text = (
            f"🤝 **الدعم الفني:**\n\n"
            f"إذا واجهت أي مشكلة أو كان لديك استفسار، يرجى التواصل مع المسؤول:\n"
            f"👤 {ADMIN_USERNAME}"
        )
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 عودة", callback_data='main')]]))
        return

    if data in ['age_girl', 'age_boy']:
        if user_data.get(user_id, {}).get('activated'):
            target = "فتاتك" if data == 'age_girl' else "الورع"
            await query.message.reply_text(f"✅ تم فتح الدردشة مع {target}! جاري التحميل...")
        else:
            await query.edit_message_text("❌ هذا القسم يتطلب تفعيل البوت أولاً.")
            # تحفيز التفعيل
            user_data[user_id]['activation_step'] = 1
            user_data[user_id]['links'] = []
            save_data()
            msg = "من اجل تفعيل البوت يجب عليك ارسال ثلاث قروبات تبادل...\nارسل رابط القروب الأول ⭐"
            await query.message.reply_text(msg)
        return

    if data == 'notify_admin':
        if admin_chat_id:
            links = user_data[user_id].get('links', [])
            links_str = "\n".join([f"{i+1}- {l}" for i, l in enumerate(links)])
            admin_msg = (
                f"🔔 **طلب تفعيل جديد**\n\n"
                f"👤 المستخدم: {username} ({user_id})\n"
                f"🔗 الروابط المرسلة:\n{links_str}"
            )
            kb = [
                [InlineKeyboardButton("ارسال رد للمستخدم", callback_data=f"adm_reply:{user_id}")],
                [InlineKeyboardButton("تفعيل البوت للمستخدم", callback_data=f"adm_activate:{user_id}")]
            ]
            try:
                await context.bot.send_message(chat_id=admin_chat_id, text=admin_msg, reply_markup=InlineKeyboardMarkup(kb))
                await query.message.reply_text("تم ابلاغ الإدارة وسيتم تفعيل القروب بإقرب وقت ⭐")
                user_data[user_id]['activation_step'] = 0 # إعادة التعيين
                save_data()
            except:
                await query.message.reply_text("❌ حدث خطأ أثناء إعلام الإدارة. تأكد من أن المسؤول قد قام بتشغيل البوت.")
        else:
            await query.message.reply_text("❌ لم يتم تحديد ID المسؤول بعد. يرجى انتظار دخول المسؤول.")
        return

    if data.startswith('final_'):
        if user_data.get(user_id, {}).get('activated'):
            await query.message.reply_text("✅ تم التحقق! جاري عرض المحتوى...")
        else:
            link_clicks += 1
            save_data()
            user_data[user_id]['activation_step'] = 1
            user_data[user_id]['links'] = []
            save_data()

            msg = (
                "من اجل تفعيل بوت فابب الــعرب يجب عليك ان ترسل ثلاث قروبات تبادل لايقل عدد المتصلين فيه عن 50 متصل، "
                "بعد ان ترسل الروابط انتظر وسيتم مراجعتها خلال عشر دقائق كحد اقصى ونقوم بتفعيل البوت لك لتستمتع بمئات القنوات "
                "واكثر من 100 الف مقطع حصري 🔥"
            )
            await query.message.reply_text(msg)
            await query.message.reply_text("ارسل رابط القروب الأول ⭐")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    username = f"@{update.effective_user.username}" if update.effective_user.username else str(user_id)

    # التحقق من أن المستخدم مسجل في البيانات
    if user_id not in user_data:
        user_data[user_id] = {'activated': False, 'username': username, 'start_count': 0, 'activation_step': 0, 'links': []}

    if context.user_data.get('waiting_broadcast') and username == ADMIN_USERNAME:
        sent, blocked = 0, 0
        await update.message.reply_text("⏳ جاري الإذاعة...")
        for uid in list(user_data.keys()):
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                sent += 1
                await asyncio.sleep(0.05)
            except: blocked += 1
        await update.message.reply_text(f"✅ تم الإرسال لـ {sent} مستخدم.")
        context.user_data['waiting_broadcast'] = False
        return

    if context.user_data.get('waiting_admin_reply_for') and username == ADMIN_USERNAME:
        target_uid = context.user_data['waiting_admin_reply_for']
        try:
            await context.bot.send_message(chat_id=target_uid, text=f"📩 رسالة من الإدارة:\n\n{text}")
            await update.message.reply_text(f"✅ تم إرسال ردك للمستخدم {target_uid}.")
        except:
            await update.message.reply_text(f"❌ فشل إرسال الرسالة للمستخدم {target_uid}.")
        context.user_data['waiting_admin_reply_for'] = None
        return

    # منطق تجميع الروابط
    step = user_data[user_id].get('activation_step', 0)

    if step == 1:
        user_data[user_id]['links'].append(text)
        user_data[user_id]['activation_step'] = 2
        save_data()
        await update.message.reply_text("ممتاز، الان ارسل رابط القروب الثاني ⭐")
        return

    elif step == 2:
        user_data[user_id]['links'].append(text)
        user_data[user_id]['activation_step'] = 3
        save_data()
        await update.message.reply_text("جيد الان ارسل رابط القروب الثالث ليتم ارسالهم للإدارة وتفعيل البوت")
        return

    elif step == 3:
        user_data[user_id]['links'].append(text)
        user_data[user_id]['activation_step'] = 4
        save_data()
        kb = [[InlineKeyboardButton("اضغط هنا لإعلام الإدارة", callback_data='notify_admin')]]
        await update.message.reply_text("تم استلام الروابط الثلاثة. اضغط على الزر أدناه لإعلام الإدارة.",
                                       reply_markup=InlineKeyboardMarkup(kb))
        return

    # الكود القديم (للاحتياط أو التوافق)
    if text == CORRECT_CODE:
        user_data[user_id]['activated'] = True
        save_data()
        await update.message.reply_text("✅ مبروك! تم تفعيل الحساب بنجاح. يمكنك الآن استخدام جميع الأقسام.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🚀 البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
