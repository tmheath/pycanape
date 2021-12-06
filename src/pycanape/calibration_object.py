import ctypes
import sys
import typing

# compatibility fix for python 3.6 and 3.7
if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property

import numpy as np

from . import ObjectType, ValueType
from .cnp_api import cnp_class, cnp_constants

try:
    from .cnp_api import cnp_prototype
except FileNotFoundError:
    cnp_prototype = None

if typing.TYPE_CHECKING:
    import numpy.typing as npt


class BaseCalibrationObject:
    def __init__(
        self,
        asap3_handle: cnp_class.TAsap3Hdl,
        module_handle: typing.Union[cnp_class.TModulHdl, int],
        name: str,
        object_info: cnp_class.DBObjectInfo,
    ):
        if cnp_prototype is None:
            raise FileNotFoundError(
                "CANape API not found. Add CANape API location to environment variable `PATH`."
            )

        self._asap3_handle = asap3_handle
        self._module_handle = module_handle
        self._name = name
        self._object_info = object_info
        self._datatype = self._read_datatype()

    def _read_datatype(self) -> cnp_constants.TAsap3DataType:
        _dtype = cnp_class.enum_type(0)
        _address = ctypes.c_ulong(0)
        _min = ctypes.c_double(0)
        _max = ctypes.c_double(0)
        _increment = ctypes.c_double(0)
        cnp_prototype.Asap3ReadObjectParameter(
            self._asap3_handle,
            self._module_handle,
            self._name.encode("ascii"),
            cnp_constants.TFormat.PHYSICAL_REPRESENTATION,
            ctypes.byref(_dtype),
            ctypes.byref(_address),
            ctypes.byref(_min),
            ctypes.byref(_max),
            ctypes.byref(_increment),
        )
        return cnp_constants.TAsap3DataType(_dtype.value)

    def _read_calibration_object_value(self) -> cnp_class.TCalibrationObjectValue:
        cov = cnp_class.TCalibrationObjectValue()
        cnp_prototype.Asap3ReadCalibrationObject2(
            self._asap3_handle,
            self._module_handle,
            self._name.encode("ascii"),
            cnp_constants.TFormat.PHYSICAL_REPRESENTATION,
            True,
            ctypes.byref(cov),
        )
        return cov

    def _write_calibration_object_value(self, cov: cnp_class.TCalibrationObjectValue):
        if self.object_type != ObjectType.OTT_CALIBRATE:
            raise TypeError("Cannot set value to a Measurement Object.")
        cnp_prototype.Asap3WriteCalibrationObject(
            self._asap3_handle,
            self._module_handle,
            self._name.encode("ascii"),
            cnp_constants.TFormat.PHYSICAL_REPRESENTATION,
            ctypes.byref(cov),
        )

    @property
    def object_type(self) -> ObjectType:
        return ObjectType(self._object_info.DBObjecttype)

    @property
    def name(self) -> str:
        return self._name

    @property
    def max(self) -> float:
        return self._object_info.max

    @property
    def min(self) -> float:
        return self._object_info.min

    @property
    def max_ex(self) -> float:
        return self._object_info.maxEx

    @property
    def min_ex(self) -> float:
        return self._object_info.minEx

    @property
    def precision(self):
        return self._object_info.precision

    @property
    def value_type(self) -> ValueType:
        return ValueType(self._object_info.type)

    @property
    def unit(self) -> str:
        return self._object_info.unit.decode("ascii")


class ScalarCalibrationObject(BaseCalibrationObject):
    """0D calibration object"""

    @property
    def value(self) -> typing.Union[float, np.number]:
        cov = self._read_calibration_object_value()

        try:
            np_dtype = self._datatype.dtype
        except KeyError:
            return cov.value.value
        return np_dtype(cov.value.value)

    @value.setter
    def value(self, new_value: float):
        cov = self._read_calibration_object_value()
        cov.value.value = new_value
        self._write_calibration_object_value(cov)


class AxisCalibrationObject(BaseCalibrationObject):
    """1D calibration object"""

    @cached_property
    def dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.axis.dimension

    @property
    def axis(self) -> "npt.NDArray":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.axis.axis, ctypes.POINTER(ctypes.c_double * cov.axis.dimension)
        )
        try:
            np_dtype = self._datatype.dtype
        except KeyError:
            return np.array(ptr.contents, dtype=float)

        return np.array(ptr.contents, dtype=np_dtype)

    @axis.setter
    def axis(self, new_axis: typing.Sequence[float]) -> None:
        axis = (ctypes.c_double * len(new_axis))(*new_axis)
        cov = self._read_calibration_object_value()
        cov.axis.axis = ctypes.cast(axis, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)


class CurveCalibrationObject(BaseCalibrationObject):
    """2D Calibration Object"""

    @cached_property
    def dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.curve.dimension

    @property
    def axis(self) -> "npt.NDArray[float]":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.curve.axis, ctypes.POINTER(ctypes.c_double * cov.curve.dimension)
        )
        return np.array(ptr.contents, dtype=float)

    @axis.setter
    def axis(self, new_axis: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        axis = (ctypes.c_double * cov.curve.dimension)(*new_axis)
        cov.curve.axis = ctypes.cast(axis, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)

    @property
    def values(self) -> "npt.NDArray":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.curve.values, ctypes.POINTER(ctypes.c_double * cov.curve.dimension)
        )
        try:
            np_dtype = self._datatype.dtype
        except KeyError:
            return np.array(ptr.contents, dtype=float)

        return np.array(ptr.contents, dtype=np_dtype)

    @values.setter
    def values(self, values: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        array = (ctypes.c_double * cov.curve.dimension)(*values)
        cov.curve.values = ctypes.cast(array, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)


class MapCalibrationObject(BaseCalibrationObject):
    """3D calibration object"""

    @cached_property
    def x_dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.map.xDimension

    @cached_property
    def y_dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.map.yDimension

    @property
    def x_axis(self) -> "npt.NDArray[float]":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.map.xAxis, ctypes.POINTER(ctypes.c_double * cov.map.xDimension)
        )
        return np.array(ptr.contents, dtype=float)

    @x_axis.setter
    def x_axis(self, new_x_axis: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        array = (ctypes.c_double * cov.map.xDimension)(*new_x_axis)
        cov.map.xAxis = ctypes.cast(array, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)

    @property
    def y_axis(self) -> "npt.NDArray[float]":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.map.yAxis, ctypes.POINTER(ctypes.c_double * cov.map.yDimension)
        )
        return np.array(ptr.contents, dtype=float)

    @y_axis.setter
    def y_axis(self, new_y_axis: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        array = (ctypes.c_double * cov.map.yDimension)(*new_y_axis)
        cov.map.yAxis = ctypes.cast(array, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)

    @property
    def values(self) -> "npt.NDArray":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.map.values,
            ctypes.POINTER(ctypes.c_double * (cov.map.xDimension * cov.map.yDimension)),
        )
        try:
            np_dtype = self._datatype.dtype
        except KeyError:
            np_array = np.array(ptr.contents, dtype=float)
        else:
            np_array = np.array(ptr.contents, dtype=np_dtype)

        return np_array.reshape((cov.map.xDimension, cov.map.yDimension))

    @values.setter
    def values(self, new_values: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        array = (ctypes.c_double * (cov.map.xDimension * cov.map.yDimension))(
            *new_values
        )
        cov.map.values = ctypes.cast(array, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)


class AsciiCalibrationObject(BaseCalibrationObject):
    @cached_property
    def len(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.ascii.len

    @property
    def ascii(self) -> str:
        cov = self._read_calibration_object_value()
        return cov.ascii.ascii.decode("ascii")

    @ascii.setter
    def ascii(self, new_ascii: str) -> None:
        cov = self._read_calibration_object_value()
        cov.ascii.ascii = new_ascii.encode("ascii")
        self._write_calibration_object_value(cov)


class ValueBlockCalibrationObject(BaseCalibrationObject):
    @cached_property
    def x_dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.valblk.xDimension

    @cached_property
    def y_dimension(self) -> int:
        cov = self._read_calibration_object_value()
        return cov.valblk.yDimension

    @property
    def values(self) -> "npt.NDArray":
        cov = self._read_calibration_object_value()
        ptr = ctypes.cast(
            cov.valblk.values,
            ctypes.POINTER(
                ctypes.c_double * (cov.valblk.xDimension * cov.valblk.yDimension)
            ),
        )
        try:
            np_dtype = self._datatype.dtype
        except KeyError:
            np_array = np.array(ptr.contents, dtype=float)
        else:
            np_array = np.array(ptr.contents, dtype=np_dtype)

        return np_array.reshape((cov.valblk.xDimension, cov.valblk.yDimension))

    @values.setter
    def values(self, new_values: typing.Sequence[float]) -> None:
        cov = self._read_calibration_object_value()
        array = (ctypes.c_double * (cov.valblk.xDimension * cov.valblk.yDimension))(
            *new_values
        )
        cov.valblk.values = ctypes.cast(array, ctypes.POINTER(ctypes.c_double))
        self._write_calibration_object_value(cov)


CalibrationObject = typing.Union[
    ScalarCalibrationObject,
    AxisCalibrationObject,
    CurveCalibrationObject,
    MapCalibrationObject,
    AsciiCalibrationObject,
    ValueBlockCalibrationObject,
]


def get_calibration_object(
    asap3_handle: cnp_class.TAsap3Hdl,
    module_handle: typing.Union[cnp_class.TModulHdl, int],
    name: str,
) -> CalibrationObject:
    object_info = cnp_class.DBObjectInfo()
    found = cnp_prototype.Asap3GetDBObjectInfo(
        asap3_handle, module_handle, name.encode("ascii"), ctypes.byref(object_info)
    )
    if not found:
        raise KeyError(f"{name} not found.")

    cal_obj_map = {
        ValueType.VALUE: ScalarCalibrationObject,
        ValueType.CURVE: CurveCalibrationObject,
        ValueType.MAP: MapCalibrationObject,
        ValueType.AXIS: AxisCalibrationObject,
        ValueType.ASCII: AsciiCalibrationObject,
        ValueType.VAL_BLK: ValueBlockCalibrationObject,
    }
    try:
        cal_obj_type = cal_obj_map[object_info.type]
    except KeyError:
        raise TypeError(f"Calibration object {name} has unknown value type.")

    return cal_obj_type(asap3_handle, module_handle, name, object_info)
