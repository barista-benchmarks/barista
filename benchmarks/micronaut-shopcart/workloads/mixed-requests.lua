local newUserRequest = "{ \"username\": \"%d\", \"name\": \"%dname\" }"
local addBananaRequest = "{ \"username\": \"%d\", \"name\": \"bananas\", \"amount\": \"7\" }"
local addJoghurtRequest = "{ \"username\": \"%d\", \"name\": \"joghurt\", \"amount\": \"12\" }"
local addJoghurtRequest = "{ \"username\": \"%d\", \"name\": \"joghurt\", \"amount\": \"12\" }"
local addCoffeeRequest = "{ \"username\": \"%d\", \"name\": \"coffee\", \"amount\": \"5\" }"
local addCheeseRequest = "{ \"username\": \"%d\", \"name\": \"cheese\", \"amount\": \"5\" }"
local addMeatRequest = "{ \"username\": \"%d\", \"name\": \"meat\", \"amount\": \"800\" }"
local viewCartPath = "/cart/%d"
local headers = {}
headers["content-type"] = "application/json"

local threadIdCounter = 1
function setup(thread)
   thread:set("threadId", threadIdCounter)
   threadIdCounter = threadIdCounter + 1
end

local userId
function init(args)
   userId = 1000000000000000 + 10000000000000 * threadId
end

local state = 0
function request()
    if state == 0 then 
        userId = userId + 1
        method = "POST"
        path = "/"
        body = string.format(newUserRequest, userId, userId)
    elseif state == 1 then
        path = "/cart"
        body = string.format(addBananaRequest, userId)
    elseif state == 2 then
        body = string.format(addJoghurtRequest, userId)
    elseif state == 3 then
        body = string.format(addCoffeeRequest, userId)
    elseif state == 4 then
        body = string.format(addCheeseRequest, userId)
    elseif state == 5 then
        body = string.format(addMeatRequest, userId)
    elseif state == 6 then
        method = "GET"
        path = string.format(viewCartPath, userId)
        body = ""
    end
    state = (state + 1) % 7
    return wrk.format(method, path, headers, body)
end
