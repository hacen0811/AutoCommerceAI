import uuid


def new_uuid():
    """
    CapCut에서 사용하는 UUID 형식 생성
    예:
    970676A8-D75C-4809-AA6B-37C01255822D
    """
    return str(uuid.uuid4()).upper()