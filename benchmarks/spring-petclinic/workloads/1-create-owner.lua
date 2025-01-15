local newOwnerRequest = 'firstName=F%d&lastName=L%d&address=A%d&city=C%d&telephone=%d'
local postHeaders = {}
postHeaders["Content-Type"] = "application/x-www-form-urlencoded"
postHeaders["Host"] = "localhost:8006"

local threads = {}
local threadIdCounter = 1
function setup(thread)
    thread:set("threadId", threadIdCounter)
    thread:set("firstOwnerId", -1)
    thread:set("lastOwnerId", -1)
    threadIdCounter = threadIdCounter + 1
    table.insert(threads, thread)
end

local ownerCounter
function init(args)
    ownerCounter = 1000000000000000 + 10000000000000 * threadId
end

function request()
    local method = "POST"
    local path = "/owners/new"
    local body = string.format(newOwnerRequest, ownerCounter, ownerCounter, ownerCounter, ownerCounter, ownerCounter / 10000000)
    ownerCounter = ownerCounter + 1
    return wrk.format(method, path, postHeaders, body)
end

function response(status, headers, body)
    lastOwnerId = string.match(headers["Location"], "http://localhost:8006/owners/(%d+)")
    if firstOwnerId == -1 then
        firstOwnerId = lastOwnerId
    end
end

function done(summary, latency, requests)
    file = io.open("petclinic-ownerids.txt", "w")
    for index, thread in ipairs(threads) do
        local firstOwnerId = thread:get("firstOwnerId")
        local lastOwnerId = thread:get("lastOwnerId")
        file:write(string.format("%d;%d\n", firstOwnerId, lastOwnerId))
    end
    file:close()
end
