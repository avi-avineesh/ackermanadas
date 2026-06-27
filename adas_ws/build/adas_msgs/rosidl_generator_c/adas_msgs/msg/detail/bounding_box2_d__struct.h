// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d.h"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_H_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'class_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/BoundingBox2D in the package adas_msgs.
typedef struct adas_msgs__msg__BoundingBox2D
{
  float x;
  float y;
  float w;
  float h;
  float confidence;
  int32_t class_id;
  rosidl_runtime_c__String class_name;
} adas_msgs__msg__BoundingBox2D;

// Struct for a sequence of adas_msgs__msg__BoundingBox2D.
typedef struct adas_msgs__msg__BoundingBox2D__Sequence
{
  adas_msgs__msg__BoundingBox2D * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} adas_msgs__msg__BoundingBox2D__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_H_
