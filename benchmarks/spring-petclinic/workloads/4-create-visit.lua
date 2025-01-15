local newVisitRequest = 'date=2021-02-23&description=Broken+leg'
local postHeaders = {}
postHeaders["Content-Type"] = "application/x-www-form-urlencoded"
postHeaders["Host"] = "localhost:8006"

local threads = {}
local threadCount = 1
function setup(thread)
    thread:set("threadId", threadCount)
    threadCount = threadCount + 1
    table.insert(threads, thread)
end

local ownersAndPets = {}
local maxIndex
function parseOwnersAndPets()
    for line in io.lines(string.format("petclinic-petids-%d.txt", threadId)) do
        for str in string.gmatch(line, "([^;]+)") do
          table.insert(ownersAndPets, str)
        end
    end
    maxIndex = #ownersAndPets
end

local petId
local firstPetId
local lastPetId
local index
function init(args)
    parseOwnersAndPets()
    index = 1
end

function incrementIndex()
    index = index + 2
    if index > maxIndex then
        index = 1
    end
end

function request()
    local ownerId = ownersAndPets[index]
    local petId = ownersAndPets[index + 1]

    local path = string.format("/owners/%s/pets/%s/visits/new", ownerId, petId)
    local req = wrk.format("POST", path, postHeaders, newVisitRequest)

    incrementIndex()
    return req
end
