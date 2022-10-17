from typing import Union

import numpy as np

StagDataTypes = Union[str, bool, int, float, bytes, dict, np.ndarray, list]
StagDataReturnTypes = Union[
    str, bool, int, float, bytes, dict, list, np.ndarray, None]
