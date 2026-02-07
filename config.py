# -*- coding: utf-8 -*-
import os

# --- الإعدادات العامة ---
# يرجى تعيين هذه القيم في متغيرات البيئة أو استبدال النصوص أدناه
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- إعدادات الحسابات ---
# تنبيه: لا تشارك سلاسل الجلسات (Session Strings) مع أي شخص
SESSIONS_CONFIG = [
    {
        'name': 'Account 1',
        'id': int(os.getenv("SESSION_1_ID", 0)),
        'hash': os.getenv("SESSION_1_HASH", ""),
        'str': os.getenv("SESSION_1_STR", "")
    }
]

# --- إعدادات الرد التلقائي ---
# النوع الأول: كلمات مفتاحية عامة
KEYWORDS_KHAS = ["مساعدة", "معلومات"]
REPLIES_KHAS = [
    "أهلاً بك، كيف يمكنني مساعدتك؟",
    "يمكنك العثور على مزيد من المعلومات في وصف الحساب."
]

# النوع الثاني: كلمات مفتاحية أخرى
KEYWORDS_TABADEL = ["تبادل", "تواصل"]
REPLIES_TABADEL = [
    "شكراً لتواصلك، سنقوم بالرد عليك في أقرب وقت.",
    "يرجى مراجعة القواعد الخاصة بالمجموعة قبل البدء."
]

# --- إعدادات النظام ---
GROUPS_FILE = "groups.json"
MAX_PROCESSED_MESSAGES = 1000
REPLY_COOLDOWN = 7200 # ثانية (ساعتين)
