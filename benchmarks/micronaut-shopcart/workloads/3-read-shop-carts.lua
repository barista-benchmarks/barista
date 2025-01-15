local viewCartPath = "/cart/%d"
local headers = {}
headers["content-type"] = "application/json"

function parseUserIdLimits()
    local result = {}
    for line in io.lines("shopcart-userids.txt") do
        local userIdLimit = {}
        for str in string.gmatch(line, "([^;]+)") do
          table.insert(userIdLimit, tonumber(str))
        end
        table.insert(result, userIdLimit)
    end
    return result
end

local userIdLimits = parseUserIdLimits()
local threadIdCounter = 1
function setup(thread)
    local userIdLimit = userIdLimits[threadIdCounter]
    thread:set("firstUserId", userIdLimit[1])
    thread:set("lastUserId", userIdLimit[2])
    threadIdCounter = threadIdCounter + 1
end

local userId
function init(args)
    userId = firstUserId
end

function incrementUserId()
    userId = userId + 1
    if userId > lastUserId then
        userId = firstUserId
    end
end

function request()
    method = "GET"
    path = string.format(viewCartPath, userId)
    body = ""
    incrementUserId()
    return wrk.format(method, path, headers, body)
end

