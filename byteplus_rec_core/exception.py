class BizException(Exception):
    def __init__(self, msg: str):
        Exception.__init__(self, msg)


class NetException(Exception):
    def __init__(self, msg: str):
        Exception.__init__(self, msg)
