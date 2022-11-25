#!lua name=mylib

local function sum(keys, args)
  local val = 0

  for i = 1, args[1] do
    val = val + i
  end

  return val
end

redis.register_function('calculator', sum)
