function script_path()
   local str = debug.getinfo(2, "S").source:sub(2)
   return str:match("(.*/)")
end

local file = io.open(script_path() .."quarkus.pdf", "rb")

local headers = {}
wrk.path = "/parse/text"
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/pdf"
wrk.body = file:read("*a")

