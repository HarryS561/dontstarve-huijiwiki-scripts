LOCKS={}
KEYS={}

local datas={}
local room_to_task={}
function RoomToTask(r,t)
    ROOM_NEEDED[r]=true
    CreateInsert(room_to_task,r,t)
end

function AddTask(name,data)
    if not TASK_NEEDED[name] then
        return
    end
    local entr=data.entrance_room
    if entr then
        if type(entr)=='table' then
            for _,room in ipairs(entr) do
                RoomToTask(room,name)
            end
        else
            RoomToTask(entr,name)
        end
    end

    datas[name]=data
    for k,v in pairs(data.room_choices) do
        if type(v)=='function' then
            data.room_choices[k]='#function'
        end
        RoomToTask(k,name)
    end
    RoomToTask(data.background_room,name)
end

require("map/tasks/dst_tasks_forestworld")
--require("map/tasks/forest")
--require("map/tasks/moonisland_tasks")
require("map/tasks/caves")
require("map/tasks/ruins")
--require("map/tasks/DLCtasks")
--require("map/tasks/lavaarena")
--require("map/tasks/quagmire")

return {datas, room_to_task}