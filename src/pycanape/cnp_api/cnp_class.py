import ctypes
from ctypes import wintypes

enum_type = ctypes.c_uint


class tAsap3Hdl(ctypes.Structure):
    _pack_ = 1


TAsap3Hdl = ctypes.POINTER(tAsap3Hdl)
TModulHdl = ctypes.c_ushort
TRecorderID = ctypes.POINTER(ctypes.c_ulong)
TTime = ctypes.c_ulong


class TTaskInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("description", ctypes.c_char_p),
        ("taskId", ctypes.c_ushort),
        ("taskCycle", ctypes.c_ulong),
    ]


class TTaskInfo2(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("description", ctypes.c_char_p),
        ("taskId", ctypes.c_ushort),
        ("taskCycle", ctypes.c_ulong),
        ("eventChannel", ctypes.c_ulong),
    ]


class s_value(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("value", ctypes.c_double),
    ]


class s_axis(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("dimension", ctypes.c_short),
        ("axis", ctypes.POINTER(ctypes.c_double)),
    ]


class s_ascii(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("len", ctypes.c_short),
        ("ascii", ctypes.c_char_p),
    ]


class s_curve(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("dimension", ctypes.c_short),
        ("axis", ctypes.POINTER(ctypes.c_double)),
        ("values", ctypes.POINTER(ctypes.c_double)),
    ]


class s_map(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("xDimension", ctypes.c_short),
        ("yDimension", ctypes.c_short),
        ("xAxis", ctypes.POINTER(ctypes.c_double)),
        ("yAxis", ctypes.POINTER(ctypes.c_double)),
        ("values", ctypes.POINTER(ctypes.c_double)),
    ]


class s_valblk(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("xDimension", ctypes.c_short),
        ("yDimension", ctypes.c_short),
        ("values", ctypes.POINTER(ctypes.c_double)),
    ]


class TCalibrationObjectValue(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("type", enum_type),
        ("value", s_value),
        ("axis", s_axis),
        ("ascii", s_ascii),
        ("curve", s_curve),
        ("map", s_map),
        ("valblk", s_valblk),
    ]


class DBObjectInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("DBObjecttype", enum_type),  # TObjectType  DBObjecttype
        ("type", enum_type),  # TValueType type
        ("min", ctypes.c_double),
        ("max", ctypes.c_double),
        ("minEx", ctypes.c_double),
        ("maxEx", ctypes.c_double),
        ("precision", wintypes.BYTE),
        ("unit", ctypes.c_char * wintypes.MAX_PATH),
    ]


class Appversion(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("MainVersion", ctypes.c_int),
        ("SubVersion", ctypes.c_int),
        ("ServicePack", ctypes.c_int),
        ("Application", ctypes.c_char * 30),
    ]


class TMeasurementListEntry(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("taskId", ctypes.c_ushort),
        ("rate", ctypes.c_ulong),
        ("SaveFlag", wintypes.BOOL),
        ("Disabled", wintypes.BOOL),
        ("ObjectName", ctypes.c_char_p),
    ]


class MeasurementListEntries(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ItemCount", ctypes.c_uint),
        ("Entries", ctypes.POINTER(ctypes.POINTER(TMeasurementListEntry))),
    ]
