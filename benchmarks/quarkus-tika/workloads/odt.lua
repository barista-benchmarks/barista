function script_path()
   local str = debug.getinfo(2, "S").source:sub(2)
   return str:match("(.*/)")
end

local file = io.open(script_path() .."quarkus.odt", "rb")

local headers = {}
wrk.path = "/parse/text"
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/vnd.oasis.opendocument.text"
wrk.body = file:read("*a")

