from multiprocessing import current_process
from multiprocessing.shared_memory import SharedMemory
from typing import Optional

import numpy

TF_IDF_SM_NAME_WIDTH = 'TF-IDF width'
_width_sm: Optional[SharedMemory] = None
_width_array: Optional[numpy.ndarray] = None
TF_IDF_SM_NAME_HEIGHT = 'TF-IDF height'
_height_sm: Optional[SharedMemory] = None
_height_array: Optional[numpy.ndarray] = None
TF_IDF_SM_SIMILARITIES = 'TF-IDF android->ios'
_similarities_sm: Optional[SharedMemory] = None
_similarities_array: Optional[numpy.ndarray] = None

_is_root_process = current_process().name == 'MainProcess'

def get_width_sm():
  global _width_sm
  global _width_array
  if _width_array is not None:
    return _width_array
  _width_sm = SharedMemory(TF_IDF_SM_NAME_WIDTH, create=_is_root_process, size=numpy.int64().itemsize)
  _width_array = numpy.ndarray((1,), buffer=_width_sm.buf, dtype=numpy.int64)
  _width_array.nbytes
  return _width_array

def cleanup_width_sm():
  global _width_sm
  global _width_array
  if _width_sm is None:
    return
  _width_sm.close()
  if _is_root_process:
    _width_sm.unlink()
  _width_sm = None
  _width_array = None

def get_height_sm():
  global _height_sm
  global _height_array
  if _height_array is not None:
    return _height_array
  _height_sm = SharedMemory(TF_IDF_SM_NAME_HEIGHT, create=_is_root_process, size=numpy.int64().itemsize)
  _height_array = numpy.ndarray((1,), buffer=_height_sm.buf, dtype=numpy.int64)
  return _height_array

def cleanup_height_sm():
  global _height_sm
  global _height_array
  if _height_sm is None:
    return
  _height_sm.close()
  if _is_root_process:
    _height_sm.unlink()
  _height_sm = None
  _height_array = None

def get_similarities_sm():
  global _similarities_sm
  global _similarities_array
  if _similarities_array is not None:
    return _similarities_array
  width: int = get_width_sm()[0]
  height: int = get_height_sm()[0]
  _similarities_sm = SharedMemory(TF_IDF_SM_SIMILARITIES, create=_is_root_process, size=width * height * numpy.double().itemsize)
  _similarities_array = numpy.ndarray((width, height), dtype=numpy.double, buffer=_similarities_sm.buf)
  return _similarities_array

def cleanup_similarities_sm():
  global  _similarities_sm
  if _similarities_sm is None:
    return
  _similarities_sm.close()
  if _is_root_process:
    _similarities_sm.unlink()
  _similarities_sm = None

