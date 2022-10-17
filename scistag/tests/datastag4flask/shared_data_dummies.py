import numpy as np
from scistag.imagestag.image import Image


def get_dummy_np_array(fill_value=1):
    dummy_array = np.zeros((32, 32, 3), dtype=np.uint8)
    for index in range(32):
        dummy_array[index, index] = fill_value
    return dummy_array


def get_dummy_dict() -> dict:
    return {"value": 123, "nested": {"anotherValue": "123", "aList": [456, 789]}}


def get_dummy_jpg():
    dummy_array = get_dummy_np_array()
    image = Image(source=dummy_array)
    data = image.encode("jpg", quality=90)
    return data
