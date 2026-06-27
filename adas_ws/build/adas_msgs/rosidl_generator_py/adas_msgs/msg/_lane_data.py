# generated from rosidl_generator_py/resource/_idl.py.em
# with input from adas_msgs:msg/LaneData.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_LaneData(type):
    """Metaclass of message 'LaneData'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('adas_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'adas_msgs.msg.LaneData')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__lane_data
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__lane_data
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__lane_data
            cls._TYPE_SUPPORT = module.type_support_msg__msg__lane_data
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__lane_data

            from std_msgs.msg import Header
            if Header.__class__._TYPE_SUPPORT is None:
                Header.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class LaneData(metaclass=Metaclass_LaneData):
    """Message class 'LaneData'."""

    __slots__ = [
        '_header',
        '_left_x',
        '_right_x',
        '_centre_x',
        '_curvature',
        '_lateral_error_m',
        '_confidence',
        '_recovery_mode',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'header': 'std_msgs/Header',
        'left_x': 'float',
        'right_x': 'float',
        'centre_x': 'float',
        'curvature': 'float',
        'lateral_error_m': 'float',
        'confidence': 'float',
        'recovery_mode': 'string',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['std_msgs', 'msg'], 'Header'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
    )

    def __init__(self, **kwargs):
        if 'check_fields' in kwargs:
            self._check_fields = kwargs['check_fields']
        else:
            self._check_fields = ros_python_check_fields == '1'
        if self._check_fields:
            assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
                'Invalid arguments passed to constructor: %s' % \
                ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from std_msgs.msg import Header
        self.header = kwargs.get('header', Header())
        self.left_x = kwargs.get('left_x', float())
        self.right_x = kwargs.get('right_x', float())
        self.centre_x = kwargs.get('centre_x', float())
        self.curvature = kwargs.get('curvature', float())
        self.lateral_error_m = kwargs.get('lateral_error_m', float())
        self.confidence = kwargs.get('confidence', float())
        self.recovery_mode = kwargs.get('recovery_mode', str())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.get_fields_and_field_types().keys(), self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    if self._check_fields:
                        assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.header != other.header:
            return False
        if self.left_x != other.left_x:
            return False
        if self.right_x != other.right_x:
            return False
        if self.centre_x != other.centre_x:
            return False
        if self.curvature != other.curvature:
            return False
        if self.lateral_error_m != other.lateral_error_m:
            return False
        if self.confidence != other.confidence:
            return False
        if self.recovery_mode != other.recovery_mode:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def header(self):
        """Message field 'header'."""
        return self._header

    @header.setter
    def header(self, value):
        if self._check_fields:
            from std_msgs.msg import Header
            assert \
                isinstance(value, Header), \
                "The 'header' field must be a sub message of type 'Header'"
        self._header = value

    @builtins.property
    def left_x(self):
        """Message field 'left_x'."""
        return self._left_x

    @left_x.setter
    def left_x(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'left_x' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'left_x' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._left_x = value

    @builtins.property
    def right_x(self):
        """Message field 'right_x'."""
        return self._right_x

    @right_x.setter
    def right_x(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'right_x' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'right_x' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._right_x = value

    @builtins.property
    def centre_x(self):
        """Message field 'centre_x'."""
        return self._centre_x

    @centre_x.setter
    def centre_x(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'centre_x' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'centre_x' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._centre_x = value

    @builtins.property
    def curvature(self):
        """Message field 'curvature'."""
        return self._curvature

    @curvature.setter
    def curvature(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'curvature' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'curvature' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._curvature = value

    @builtins.property
    def lateral_error_m(self):
        """Message field 'lateral_error_m'."""
        return self._lateral_error_m

    @lateral_error_m.setter
    def lateral_error_m(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'lateral_error_m' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'lateral_error_m' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._lateral_error_m = value

    @builtins.property
    def confidence(self):
        """Message field 'confidence'."""
        return self._confidence

    @confidence.setter
    def confidence(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'confidence' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'confidence' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._confidence = value

    @builtins.property
    def recovery_mode(self):
        """Message field 'recovery_mode'."""
        return self._recovery_mode

    @recovery_mode.setter
    def recovery_mode(self, value):
        if self._check_fields:
            assert \
                isinstance(value, str), \
                "The 'recovery_mode' field must be of type 'str'"
        self._recovery_mode = value
