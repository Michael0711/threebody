#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

def get_in(data, b, e=None, start=0, flag=False):
    if data is None:
        return None
    b1 = data.find(b, start)
    if b1 == -1:
        return None
    b1 += len(b)
    if e is None:
        return data[b1:]
    if isinstance(e, list):
        e1 = -1
        for i in range(b1 + 1, len(data)):
            if data[i] in e:
                e1 = i
                break
    else:
        e1 = data.find(e, b1)
    if e1 == -1:
        if flag:
            return data[b1:]
        return None
    return data[b1:e1]


def get_in_list(data, b, e, start=0):
    if data is None:
        return
    while True:
        b1 = data.find(b, start)
        if b1 == -1:
            return
        b1 += len(b)
        e1 = data.find(e, b1)
        if e1 == -1:
            return
        yield data[b1:e1]
        start = e1


def get_input(page, type='hidden', name='name'):
    data = {}
    for input in get_in_list(page, '<input', '>'):
        input = input.replace("'", '"')
        if input.lower().find('type="%s"' % type) == -1:
            continue
        name = get_in(input, '%s="' % name, '"')
        value = get_in(input, 'value="', '"')
        if name is None:
            name = get_in(input, '%s=' % name, ' ')
            if name is None:
                continue
            continue
        if value is None:
            value = get_in(input, 'value=', ' ')
            if value is None:
                value = ''
        data[name] = value
    return data


