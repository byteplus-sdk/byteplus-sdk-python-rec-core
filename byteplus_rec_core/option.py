import datetime
from abc import abstractmethod

from byteplus_rec_core.options import Options


class Option(object):
    @abstractmethod
    def fill(self, options: Options) -> None:
        raise NotImplementedError

    @staticmethod
    def conv_to_options(opts: tuple) -> Options:
        options: Options = Options()
        for opt in opts:
            opt.fill(options)
        return options

    # Specifies the timeout for this request
    @staticmethod
    def with_timeout(timeout: datetime.timedelta):
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                options.timeout = timeout

        return OptionImpl()

    # Specify the request_id manually. By default,
    # the SDK generates a unique request_id for each request using the UUID
    @staticmethod
    def with_request_id(request_id: str):
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                options.request_id = request_id

        return OptionImpl()

    # Add an HTTP header to the request.
    # In general, you do not need to care this.
    @staticmethod
    def with_http_header(key: str, value: str):
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                if options.headers is None:
                    options.headers = {}
                options.headers[key] = value
        return OptionImpl()

    # Add an HTTP query to the request.
    # In general, you do not need to care this.
    @staticmethod
    def with_http_query(key: str, value: str):
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                if options.queries is None:
                    options.queries = {}
                options.queries[key] = value

        return OptionImpl()

    # Specifies the maximum time it will take for
    # the server to process the request. The server will try to return
    # the result within this time, even if the task is not completed
    @staticmethod
    def with_server_timeout(timeout: datetime.timedelta):
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                options.server_timeout = timeout

        return OptionImpl()
