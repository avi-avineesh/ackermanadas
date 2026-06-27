// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "adas_msgs/msg/detail/bounding_box2_d__rosidl_typesupport_introspection_c.h"
#include "adas_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "adas_msgs/msg/detail/bounding_box2_d__functions.h"
#include "adas_msgs/msg/detail/bounding_box2_d__struct.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  adas_msgs__msg__BoundingBox2D__init(message_memory);
}

void adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_fini_function(void * message_memory)
{
  adas_msgs__msg__BoundingBox2D__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_member_array[7] = {
  {
    "x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "w",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, w),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "h",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, h),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "confidence",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, confidence),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "class_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, class_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "class_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2D, class_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_members = {
  "adas_msgs__msg",  // message namespace
  "BoundingBox2D",  // message name
  7,  // number of fields
  sizeof(adas_msgs__msg__BoundingBox2D),
  false,  // has_any_key_member_
  adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_member_array,  // message members
  adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_init_function,  // function to initialize message memory (memory has to be allocated)
  adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_type_support_handle = {
  0,
  &adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_members,
  get_message_typesupport_handle_function,
  &adas_msgs__msg__BoundingBox2D__get_type_hash,
  &adas_msgs__msg__BoundingBox2D__get_type_description,
  &adas_msgs__msg__BoundingBox2D__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_adas_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, adas_msgs, msg, BoundingBox2D)() {
  if (!adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_type_support_handle.typesupport_identifier) {
    adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &adas_msgs__msg__BoundingBox2D__rosidl_typesupport_introspection_c__BoundingBox2D_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
