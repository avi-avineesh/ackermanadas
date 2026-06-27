// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice
#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "adas_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "adas_msgs/msg/detail/bounding_box2_d__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_serialize_adas_msgs__msg__BoundingBox2D(
  const adas_msgs__msg__BoundingBox2D * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_deserialize_adas_msgs__msg__BoundingBox2D(
  eprosima::fastcdr::Cdr &,
  adas_msgs__msg__BoundingBox2D * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t get_serialized_size_adas_msgs__msg__BoundingBox2D(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t max_serialized_size_adas_msgs__msg__BoundingBox2D(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_serialize_key_adas_msgs__msg__BoundingBox2D(
  const adas_msgs__msg__BoundingBox2D * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t get_serialized_size_key_adas_msgs__msg__BoundingBox2D(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t max_serialized_size_key_adas_msgs__msg__BoundingBox2D(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, adas_msgs, msg, BoundingBox2D)();

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
