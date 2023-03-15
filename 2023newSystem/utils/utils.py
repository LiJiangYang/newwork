

class AAA:
    def __init__(self):
        pass

    def acquire(self):
        return True

    def release(self):
        return True


#
is_use_json = False
if is_use_json:
    try:
        import json as json
    except:
        pass


def dict2str(dat):
    if is_use_json:
        return json.dumps(dat)
    else:
        return dat


def str2dict(dat):
    if is_use_json:
        return json.loads(dat)
    else:
        return dat