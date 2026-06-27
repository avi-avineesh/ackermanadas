// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include <cstddef>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "adas_msgs/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "adas_msgs/msg/detail/bounding_box2_d_array__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace adas_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_serialize(
  const adas_msgs::msg::BoundingBox2DArray & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  adas_msgs::msg::BoundingBox2DArray & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
get_serialized_size(
  const adas_msgs::msg::BoundingBox2DArray & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
max_serialized_size_BoundingBox2DArray(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_serialize_key(
  const adas_msgs::msg::BoundingBox2DArray & ros_message,
  eprosima::fastcdr::Cdr &);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
get_serialized_size_key(
  const adas_msgs::msg::BoundingBox2DArray & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
max_serialized_size_key_BoundingBox2DArray(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace adas_msgs

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, adas_msgs, msg, BoundingBox2DArray)();

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
