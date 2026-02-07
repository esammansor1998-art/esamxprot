# -*- coding: utf-8 -*-
import unittest
import json
import os
import sys

# Mock config
class MockConfig:
    GROUPS_FILE = "test_groups.json"
    KEYWORDS_KHAS = ["خاص"]
    REPLIES_KHAS = ["reply_khas"]
    KEYWORDS_TABADEL = ["تبادل"]
    REPLIES_TABADEL = ["reply_tabadel"]
    SESSIONS_CONFIG = [{'id': 12345, 'hash': 'abc', 'str': 'session_str'}]
    BOT_TOKEN = "test_token"
    OWNER_ID = 6762940512
    MAX_PROCESSED_MESSAGES = 1000
    REPLY_COOLDOWN = 7200

sys.modules['config'] = MockConfig

class TestBotLogic(unittest.TestCase):
    def test_group_id_matching(self):
        resolved_ids = [123456789]

        def is_match(chat_id):
            if chat_id in resolved_ids: return True
            if chat_id in [int("-100" + str(abs(rid))) for rid in resolved_ids]: return True
            return False

        self.assertTrue(is_match(123456789))
        self.assertTrue(is_match(-100123456789))
        self.assertFalse(is_match(987654321))

    def test_keyword_matching(self):
        import config
        idx_khas = 0
        idx_tabadel = 0

        def get_reply(text):
            nonlocal idx_khas, idx_tabadel
            reply_msg = None
            if any(k in text for k in config.KEYWORDS_KHAS):
                reply_msg = config.REPLIES_KHAS[idx_khas]
                idx_khas = (idx_khas + 1) % len(config.REPLIES_KHAS)
            elif any(k in text for k in config.KEYWORDS_TABADEL):
                reply_msg = config.REPLIES_TABADEL[idx_tabadel]
                idx_tabadel = (idx_tabadel + 1) % len(config.REPLIES_TABADEL)
            return reply_msg

        self.assertEqual(get_reply("مرحبا بالخاص"), "reply_khas")
        self.assertEqual(get_reply("بدنا تبادل"), "reply_tabadel")
        self.assertIsNone(get_reply("مرحبا"))

if __name__ == '__main__':
    unittest.main()
