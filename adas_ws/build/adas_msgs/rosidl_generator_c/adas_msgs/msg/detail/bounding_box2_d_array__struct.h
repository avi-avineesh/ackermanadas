// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d_array.h"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__STRUCT_H_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__STRUCT_H_

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
// Member 'boxes'
#include "adas_msgs/msg/detail/bounding_box2_d__struct.h"

/// Struct defined in msg/BoundingBox2DArray in the package adas_msgs.
typedef struct adas_msgs__msg__BoundingBox2DArray
{
  std_msgs__msg__Header header;
  adas_msgs__msg__BoundingBox2D__Sequence boxes;
} adas_msgs__msg__BoundingBox2DArray;

// Struct for a sequence of adas_msgs__msg__BoundingBox2DArray.
typedef struct adas_msgs__msg__BoundingBox2DArray__Sequence
{
  adas_msgs__msg__BoundingBox2DArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} adas_msgs__msg__BoundingBox2DArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__STRUCT_H_
