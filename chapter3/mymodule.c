#include "redismodule.h"

/**
mymodule.hello <name>
*/
int HelloCommand(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
  RedisModule_AutoMemory(ctx);

  if (argc != 2) {
    return RedisModule_WrongArity(ctx);
  }

  RedisModuleString *message = RedisModule_CreateStringPrintf(ctx, "Welcome, %s!", RedisModule_StringPtrLen(argv[1], NULL));

  if (RedisModule_ReplyWithString(ctx, message) == REDISMODULE_ERR) {
    return REDISMODULE_ERR;
  }
  return REDISMODULE_OK;
}

int RedisModule_OnLoad(RedisModuleCtx *ctx, RedisModuleString **argv, int argc) {
  if (RedisModule_Init(ctx, "mymodule", 1, REDISMODULE_APIVER_1) == REDISMODULE_ERR) {
    return REDISMODULE_ERR;
  }

  if (RedisModule_CreateCommand(ctx, "mymodule.hello", HelloCommand, "readonly",
    1, 1, 1) == REDISMODULE_ERR) {
    return REDISMODULE_ERR;
  }

  return REDISMODULE_OK;
}
