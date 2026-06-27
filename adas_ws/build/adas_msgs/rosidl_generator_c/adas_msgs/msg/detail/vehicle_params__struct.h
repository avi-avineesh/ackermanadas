// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/vehicle_params.h"


#ifndef ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_H_
#define ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/VehicleParams in the package adas_msgs.
typedef struct adas_msgs__msg__VehicleParams
{
  float max_speed;
  float max_steer;
} adas_msgs__msg__VehicleParams;

// Struct for a sequence of adas_msgs__msg__VehicleParams.
typedef struct adas_msgs__msg__VehicleParams__Sequence
{
  adas_msgs__msg__VehicleParams * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} adas_msgs__msg__VehicleParams__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_H_
