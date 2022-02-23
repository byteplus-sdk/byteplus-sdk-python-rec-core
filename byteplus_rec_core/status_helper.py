from byteplus_rec_core.constant import STATUS_CODE_SUCCESS, STATUS_CODE_TOO_MANY_REQUEST, STATUS_CODE_OPERATION_LOSS, \
    STATUS_CODE_IDEMPOTENT


def is_upload_success(code: int) -> bool:
    return code == STATUS_CODE_SUCCESS or code == STATUS_CODE_IDEMPOTENT


def is_success(code: int) -> bool:
    return code == STATUS_CODE_SUCCESS or code == 200


def is_server_overload(code: int) -> bool:
    return code == STATUS_CODE_TOO_MANY_REQUEST


def is_loss_operation(code: int) -> bool:
    return code == STATUS_CODE_OPERATION_LOSS
