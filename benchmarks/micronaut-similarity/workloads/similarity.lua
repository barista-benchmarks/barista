wrk.method = "POST"
wrk.path = "/similarity/order"
wrk.headers["Content-Type"] = "application/json"
wrk.body = ""

function script_path()
  local str = debug.getinfo(2, "S").source:sub(2)
  return str:match("(.*/)")
end

payload = "{ \"texts\": ["
for i = 1, 16 do
  if i > 1 then
    payload = payload .. ", "
  end
  payload = payload .. "\""
  file = io.open(script_path() .. "essay" .. tostring(i) .. ".txt", "r")
  content = file:read("*all")
  content = content:gsub('\"', "\\\"")
  content = content:gsub('\n', "\\n")
  payload = payload .. content
  file:close()
  payload = payload .. "\""
end
payload = payload .. "] }"

-- print(payload)
-- wrk.body = "{ \"texts\": [] }"
wrk.body = payload

-- function response(status, headers, body)
--   print("code: " .. tostring(status) .. ", body: " .. body)
--   wrk.thread:stop()
-- end
