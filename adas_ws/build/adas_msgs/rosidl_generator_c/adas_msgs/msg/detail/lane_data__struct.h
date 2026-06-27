// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/lane_data.h"


#ifndef ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_H_
#define ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'recovery_mode'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/LaneData in the package adas_msgs.
typedef struct adas_msgs__msg__LaneData
{
  std_msgs__msg__Header header;
  float left_x;
  float right_x;
  float centre_x;
  float curvature;
  float lateral_error_m;
  float confidence;
  rosidl_runtime_c__String recovery_mode;
} adas_msgs__msg__LaneData;

// Struct for a sequence of adas_msgs__msg__LaneData.
typedef struct adas_msgs__msg__LaneData__Sequence
{
  adas_msgs__msg__LaneData * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} adas_msgs__msg__LaneData__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_H_
