// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/vehicle_params__rosidl_typesupport_fastrtps_cpp.hpp"
#include "adas_msgs/msg/detail/vehicle_params__functions.h"
#include "adas_msgs/msg/detail/vehicle_params__struct.hpp"

#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace adas_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{


bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_serialize(
  const adas_msgs::msg::VehicleParams & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: max_speed
  cdr << ros_message.max_speed;

  // Member: max_steer
  cdr << ros_message.max_steer;

  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  adas_msgs::msg::VehicleParams & ros_message)
{
  // Member: max_speed
  cdr >> ros_message.max_speed;

  // Member: max_steer
  cdr >> ros_message.max_steer;

  return true;
}  // NOLINT(readability/fn_size)


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
get_serialized_size(
  const adas_msgs::msg::VehicleParams & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: max_speed
  {
    size_t item_size = sizeof(ros_message.max_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Member: max_steer
  {
    size_t item_size = sizeof(ros_message.max_steer);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
max_serialized_size_VehicleParams(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Member: max_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // Member: max_steer
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = adas_msgs::msg::VehicleParams;
    is_plain =
      (
      offsetof(DataType, max_steer) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
cdr_serialize_key(
  const adas_msgs::msg::VehicleParams & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: max_speed
  cdr << ros_message.max_speed;

  // Member: max_steer
  cdr << ros_message.max_steer;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
get_serialized_size_key(
  const adas_msgs::msg::VehicleParams & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: max_speed
  {
    size_t item_size = sizeof(ros_message.max_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Member: max_steer
  {
    size_t item_size = sizeof(ros_message.max_steer);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_adas_msgs
max_serialized_size_key_VehicleParams(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Member: max_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: max_steer
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = adas_msgs::msg::VehicleParams;
    is_plain =
      (
      offsetof(DataType, max_steer) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}


static bool _VehicleParams__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const adas_msgs::msg::VehicleParams *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _VehicleParams__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<adas_msgs::msg::VehicleParams *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _VehicleParams__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const adas_msgs::msg::VehicleParams *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _VehicleParams__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_VehicleParams(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _VehicleParams__callbacks = {
  "adas_msgs::msg",
  "VehicleParams",
  _VehicleParams__cdr_serialize,
  _VehicleParams__cdr_deserialize,
  _VehicleParams__get_serialized_size,
  _VehicleParams__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _VehicleParams__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_VehicleParams__callbacks,
  get_message_typesupport_handle_function,
  &adas_msgs__msg__VehicleParams__get_type_hash,
  &adas_msgs__msg__VehicleParams__get_type_description,
  &adas_msgs__msg__VehicleParams__get_type_description_sources,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace adas_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_adas_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<adas_msgs::msg::VehicleParams>()
{
  return &adas_msgs::msg::typesupport_fastrtps_cpp::_VehicleParams__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, adas_msgs, msg, VehicleParams)() {
  return &adas_msgs::msg::typesupport_fastrtps_cpp::_VehicleParams__handle;
}

#ifdef __cplusplus
}
#endif
