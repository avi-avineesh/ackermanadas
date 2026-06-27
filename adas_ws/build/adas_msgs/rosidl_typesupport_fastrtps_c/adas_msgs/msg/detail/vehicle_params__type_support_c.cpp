// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/vehicle_params__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "adas_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "adas_msgs/msg/detail/vehicle_params__struct.h"
#include "adas_msgs/msg/detail/vehicle_params__functions.h"
#include "fastcdr/Cdr.h"

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

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _VehicleParams__ros_msg_type = adas_msgs__msg__VehicleParams;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_serialize_adas_msgs__msg__VehicleParams(
  const adas_msgs__msg__VehicleParams * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: max_speed
  {
    cdr << ros_message->max_speed;
  }

  // Field name: max_steer
  {
    cdr << ros_message->max_steer;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_deserialize_adas_msgs__msg__VehicleParams(
  eprosima::fastcdr::Cdr & cdr,
  adas_msgs__msg__VehicleParams * ros_message)
{
  // Field name: max_speed
  {
    cdr >> ros_message->max_speed;
  }

  // Field name: max_steer
  {
    cdr >> ros_message->max_steer;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t get_serialized_size_adas_msgs__msg__VehicleParams(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _VehicleParams__ros_msg_type * ros_message = static_cast<const _VehicleParams__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: max_speed
  {
    size_t item_size = sizeof(ros_message->max_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: max_steer
  {
    size_t item_size = sizeof(ros_message->max_steer);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t max_serialized_size_adas_msgs__msg__VehicleParams(
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

  // Field name: max_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: max_steer
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
    using DataType = adas_msgs__msg__VehicleParams;
    is_plain =
      (
      offsetof(DataType, max_steer) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
bool cdr_serialize_key_adas_msgs__msg__VehicleParams(
  const adas_msgs__msg__VehicleParams * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: max_speed
  {
    cdr << ros_message->max_speed;
  }

  // Field name: max_steer
  {
    cdr << ros_message->max_steer;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t get_serialized_size_key_adas_msgs__msg__VehicleParams(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _VehicleParams__ros_msg_type * ros_message = static_cast<const _VehicleParams__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: max_speed
  {
    size_t item_size = sizeof(ros_message->max_speed);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: max_steer
  {
    size_t item_size = sizeof(ros_message->max_steer);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_adas_msgs
size_t max_serialized_size_key_adas_msgs__msg__VehicleParams(
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
  // Field name: max_speed
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Field name: max_steer
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
    using DataType = adas_msgs__msg__VehicleParams;
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
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const adas_msgs__msg__VehicleParams * ros_message = static_cast<const adas_msgs__msg__VehicleParams *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_adas_msgs__msg__VehicleParams(ros_message, cdr);
}

static bool _VehicleParams__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  adas_msgs__msg__VehicleParams * ros_message = static_cast<adas_msgs__msg__VehicleParams *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_adas_msgs__msg__VehicleParams(cdr, ros_message);
}

static uint32_t _VehicleParams__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_adas_msgs__msg__VehicleParams(
      untyped_ros_message, 0));
}

static size_t _VehicleParams__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_adas_msgs__msg__VehicleParams(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_VehicleParams = {
  "adas_msgs::msg",
  "VehicleParams",
  _VehicleParams__cdr_serialize,
  _VehicleParams__cdr_deserialize,
  _VehicleParams__get_serialized_size,
  _VehicleParams__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _VehicleParams__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_VehicleParams,
  get_message_typesupport_handle_function,
  &adas_msgs__msg__VehicleParams__get_type_hash,
  &adas_msgs__msg__VehicleParams__get_type_description,
  &adas_msgs__msg__VehicleParams__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, adas_msgs, msg, VehicleParams)() {
  return &_VehicleParams__type_support;
}

#if defined(__cplusplus)
}
#endif
