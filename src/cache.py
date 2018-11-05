import redis

class Cache:

    def __init__(self, util):
        kwargs = {
            'host': util.get_env_value("host", "redis"),
            'port': util.get_env_value("port", "redis"),
            'db': util.get_env_value("db", "redis"),
        }
        self.redisClient = redis.StrictRedis(**kwargs)

class ReverseAuthKeyCache(Cache):

    def __init__(self, util):
        super().__init__(util)

    def cache(self, user_id, auth_key):
        self.redisClient.set(auth_key, user_id)

    def get_user_id(self, auth_key):
        return self.redisClient.get(auth_key)

class AuthKeyCache(Cache):

    def __init__(self, util):
        super().__init__(util)

    def _get_cache_key(self, user_id):
        return "{}:{}".format("auth_key", user_id)

    def cache(self, user_id, auth_key):
        cache_key = self._get_cache_key(user_id)
        self.redisClient.set(cache_key, auth_key)

    def get_auth_key(self, user_id):
        cache_key = self._get_cache_key(user_id)
        return self.redisClient.get(cache_key)
