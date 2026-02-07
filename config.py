# -*- coding: utf-8 -*-
import os

# --- الإعدادات العامة ---
# يرجى تعيين هذه القيم في متغيرات البيئة أو استبدال النصوص أدناه
OWNER_ID = int(os.getenv("OWNER_ID", 6762940512))
BOT_TOKEN = os.getenv("BOT_TOKEN", "8520006260:AAGWatChzdHGXhZILav0gqX3Jn91NDzj1fg")

# --- إعدادات الحسابات ---
SESSIONS_CONFIG = [
    {
        'name': 'الجلسة 1',
        'id': int(os.getenv("SESSION_1_ID", 35234215)),
        'hash': os.getenv("SESSION_1_HASH", "2f560ad5ac9a1c11b8582e42471c403c"),
        'str': os.getenv("SESSION_1_STR", "1BJWap1sBu5QxQPXDKdwMTJiQfyh9KD8cRE4pUghL9slakYFyvUUFTRcnN4xvUPEd6F-y01Mv2EkwTonZJpWO7Dsm3eMYhx11hntNpTwAPMz--Jv2_nZLQMzWl62Ssdi7c2FlhtMvr5f3wyE5IW2ocnAtvfVzUTs59hTh9cXwlMuoHzyYCYYibA2AadPuLjIOflMfmHa-JrMdAvCwSUe0_T6TtA5D8USSW_4ps7Y_B7rjDLbHvsVxZtzcBjGzJmGytxV0kyzsE_8luEJvxdUganOtyeBMKboIIByfou_uLWuF7QyYaCKspW422iHlmIHByJ_GZeI_Rrsy6c2w5Atr4BgIwHQlQ6M=")
    },
    {
        'name': 'الجلسة 2',
        'id': int(os.getenv("SESSION_2_ID", 39838472)),
        'hash': os.getenv("SESSION_2_HASH", "39e0757f5b96e8a84c7797c17d28c29a"),
        'str': os.getenv("SESSION_2_STR", "1BJWap1sBu6F1feEVYtqx1o_ImLPmDXsjDKfL2q4nhfLm1BRYg_RpFRz-KHG9XV67qeBMmBuwusFA1YXF62GHSYDQtgx1fdy0eNy-_nQinIQHvnsMHEKdEpurPDuw9d_FmUTp2QrXj10qgWAs0XG6jRGAbqnzFNHJXnFHNgvm-tiIicwYflF_AeGiEZNc1mYZ832sQrReBdJ-g7eLYbpqSC7j3XLuylrZdxdc7eTJLURe78mHN1-y_4tPquvAULVtfl6REAaVR1zzYOfHiWojZzRPSGqAxj6dRZKGeM2lIpUL_1O6rAUUc49KJJlNgTBG5HF_xOx9qSa3DEQIhQlUiJpohQZBGuA=")
    }
]

# --- إعدادات الرد التلقائي ---
# النوع الأول: كلمات مفتاحية للخاص
KEYWORDS_KHAS = ["خاص"]
REPLIES_KHAS = [
    "وين رايحين، التبادلات مضيعة للوقت يخوي، عندي لك رابط بوت كله مقاطع نار نار، رابطو بوصف حسابي نار.",
    "ليش الخاص يحلوين، روحو البوت رابطوو بوصف حسابي",
    "ليش تتعب حالك بالخاص وهيك، روح البوت رابطو بوصف حسابي لاتفوت الفرصه شوي واحذفه"
]

# النوع الثاني: كلمات مفتاحية للتبادل
KEYWORDS_TABADEL = ["تبادل"]
REPLIES_TABADEL = [
    "التبادلات تعب، عندي لك بوت بوصف حسابي ببلاش مقاطع من كل الجنسيات",
    "مقاطع اخر موديل، البوت بوصف حسابي وقول للتبادلات باي باي",
    "خش البوت حقي من وصف حسابي وعيش الجو مع المقاطع اخر دقه"
]

# --- إعدادات التخزين ---
GROUPS_FILE = "groups.json"
MAX_PROCESSED_MESSAGES = 1000
REPLY_COOLDOWN = 7200 # ثانية
