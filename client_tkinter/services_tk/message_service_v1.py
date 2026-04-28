

#这是处理消息的缓存和未读消息的逻辑-消息状态服务
# 聊天缓存、未读数、会话key

class MessageService:
    def __init__(self):
        self.chat_cache = {}      #聊天内容的缓存
        self.unread_count = {}    #未读数量，内容

    def get_chat_key(self, chat_type, target_id):
        return f"{chat_type}_{target_id}"

    def save_message(self, chat_type, target_id, message):
        key = self.get_chat_key(chat_type, target_id)
        self.chat_cache.setdefault(key, []).append(message)

    def get_messages(self, chat_type, target_id):
        key = self.get_chat_key(chat_type, target_id)
        return self.chat_cache.get(key, [])

    def increase_unread(self, chat_type, target_id):
        key = self.get_chat_key(chat_type, target_id)
        self.unread_count[key] = self.unread_count.get(key, 0) + 1

    def clear_unread(self, chat_type, target_id):
        key = self.get_chat_key(chat_type, target_id)
        self.unread_count[key] = 0

    def get_unread(self, chat_type, target_id):
        key = self.get_chat_key(chat_type, target_id)
        return self.unread_count.get(key, 0)