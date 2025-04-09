local hostUrl = "http://localhost:8006";
local hostUrlLength = string.len(hostUrl)
local petTypes = {"bird", "cat", "dog", "hamster", "lizard", "snake"}

local newOwnerRequest = 'firstName=F%d&lastName=L%d&address=A%d&city=C%d&telephone=%d'
local newPetRequest = 'name=Pet%d&birthDate=2010-10-05&type=%s'
local newVisitRequest = 'date=2021-02-23&description=Broken+leg'

local getHeaders = {}
getHeaders["Host"] = "localhost:8006"

local postHeaders = {}
postHeaders["Content-Type"] = "application/x-www-form-urlencoded"
postHeaders["Host"] = "localhost:8006"

local threadIdCounter = 1
function setup(thread)
    thread:set("threadId", threadIdCounter)
    threadIdCounter = threadIdCounter + 1
end

local ownerCounter
local petCounter
local loopCounter
function init(args)
   ownerCounter = 1000000000000000 + 10000000000000 * threadId
   petCounter = ownerCounter
   loopCounter = ownerCounter
end

local ownerPath
local petId
local state = -5
function request()
    -- Setup steps
    if state == -5 then
        -- workaround as the response handler is not invoked for the very first request
        method = "GET"
        path = "/"
        headers = getHeaders
        body = ""
    elseif state == -4 then
        -- create a new owner at http://localhost:8006/owners/new
        ownerCounter = ownerCounter + 1
        method = "POST"
        path = "/owners/new"
        headers = postHeaders
        body = string.format(newOwnerRequest, ownerCounter, ownerCounter, ownerCounter, ownerCounter, ownerCounter / 10000000)
    elseif state == -3 then
        -- create a new pet for the current owner at http://localhost:8006/owners/%d/pets/new
        petCounter = petCounter + 1
        method = "POST"
        path = ownerPath .. "/pets/new"
        headers = postHeaders
        body = string.format(newPetRequest, petCounter, petTypes[(petCounter % #petTypes) + 1])
    elseif state == -2 then
        -- navigate to http://localhost:8006/owners/%d
        method = "GET"
        path = ownerPath
        headers = getHeaders
        body = ""
    elseif state == -1 then
        -- create a new visit for the current pet at http://localhost:8006/owners/%d/pets/%d/visits/new
        method = "POST"
        path = ownerPath .. "/pets/" .. petId .. "/visits/new"
        headers = postHeaders
        body = string.format(newVisitRequest)
    -- Main loop
    elseif state == 0 then
        -- navigate to http://localhost:8006/owners/%d
        method = "GET"
        path = ownerPath
        headers = getHeaders
        body = ""
    elseif state == 1 then
        -- navigate to http://localhost:8006/owners/%d/edit
        method = "POST"
        path = ownerPath .. "/edit"
        headers = postHeaders
        body = string.format(newOwnerRequest, loopCounter, loopCounter, loopCounter, loopCounter, loopCounter / 10000000)
    elseif state == 2 then
        -- navigate to http://localhost:8006/owners/%d/pets/%d/edit
        method = "POST"
        path = ownerPath .. "/pets/" .. petId .. "/edit"
        headers = postHeaders
        body = string.format(newPetRequest, loopCounter, petTypes[(loopCounter % #petTypes) + 1])
        loopCounter = loopCounter + 1
    end
    
    state = state + 1
    if state > 0 then
        state = state % 3
    end
    return wrk.format(method, path, headers, body)
end

function response(status, headers, body)
    if state == -3 then
        ownerPath = string.sub(headers["Location"], hostUrlLength + 1, -1)
    elseif state == -1 then
        petId = string.match(body, 'pets/(%d+)/visits/new')
    end
end

