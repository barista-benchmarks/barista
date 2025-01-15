function script_path()
    local str = debug.getinfo(2, "S").source:sub(2)
    return str:match("(.*/)")
end

local odt_content = io.open(script_path() .."quarkus.odt", "rb"):read("*a")
local pdf_content = io.open(script_path() .."quarkus.pdf", "rb"):read("*a")

local state = 0
function request()
    local method = "POST"
    local path = "/parse/text"
    local headers = {}
    local body

    if state == 0 then
        -- odt request
        headers["Content-Type"] = "application/vnd.oasis.opendocument.text"
        body = odt_content
    elseif state == 1 then
        -- pdf request
        headers["Content-Type"] = "application/pdf"
        body = pdf_content
    end

    state = (state + 1) % 2
    return wrk.format(method, path, headers, body)
end
