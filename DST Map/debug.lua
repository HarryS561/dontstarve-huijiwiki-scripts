--用于检测缺少哪些全局变量
local mt = {}
local tbs = {}
local names = {}

function mt:__index(key)
    if type(key)=='string' or type(key)=='number' then
        local name
        if self==_G then
            name = key --假设不是number
        elseif type(key)=='string' then
            name = names[self]..'.'..key
        else
            name = names[self]..'['..key..']'
        end
        if tbs[name] then
            return tbs[name]
        else
            local tb = {}
            tbs[name] = tb
            names[tb] = name
            setmetatable(tb, mt)
            print('需要', tb)
            return tb
        end
    else
        print(self, '索引非常类型：', type(key))
        return
    end
end

function mt:__tostring()
    if self==_G then
        return '_G'
    else
        return names[self]
    end
end

function mt:__call()
    return self.__ret
end

setmetatable(_G, mt)
--return mt