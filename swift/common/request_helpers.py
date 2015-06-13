


def get_sys_meta_prefix(server_type):
    return 'x-%s-%s-'%(server_type.lower(),'meta')



def remove_items(headers,condition):
    removed = {}
    keys = filter(condition,headers)
    removed.update((key,headers.pop(key)) for key in keys)
    return removed