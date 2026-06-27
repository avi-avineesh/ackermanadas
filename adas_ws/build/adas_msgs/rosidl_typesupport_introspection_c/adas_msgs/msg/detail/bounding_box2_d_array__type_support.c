// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "adas_msgs/msg/detail/bounding_box2_d_array__rosidl_typesupport_introspection_c.h"
#include "adas_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "adas_msgs/msg/detail/bounding_box2_d_array__functions.h"
#include "adas_msgs/msg/detail/bounding_box2_d_array__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `boxes`
#include "adas_msgs/msg/bounding_box2_d.h"
// Member `boxes`
#include "adas_msgs/msg/detail/bounding_box2_d__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  adas_msgs__msg__BoundingBox2DArray__init(message_memory);
}

void adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_fini_function(void * message_memory)
{
  adas_msgs__msg__BoundingBox2DArray__fini(message_memory);
}

size_t adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__size_function__BoundingBox2DArray__boxes(
  const void * untyped_member)
{
  const adas_msgs__msg__BoundingBox2D__Sequence * member =
    (const adas_msgs__msg__BoundingBox2D__Sequence *)(untyped_member);
  return member->size;
}

const void * adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_const_function__BoundingBox2DArray__boxes(
  const void * untyped_member, size_t index)
{
  const adas_msgs__msg__BoundingBox2D__Sequence * member =
    (const adas_msgs__msg__BoundingBox2D__Sequence *)(untyped_member);
  return &member->data[index];
}

void * adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_function__BoundingBox2DArray__boxes(
  void * untyped_member, size_t index)
{
  adas_msgs__msg__BoundingBox2D__Sequence * member =
    (adas_msgs__msg__BoundingBox2D__Sequence *)(untyped_member);
  return &member->data[index];
}

void adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__fetch_function__BoundingBox2DArray__boxes(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const adas_msgs__msg__BoundingBox2D * item =
    ((const adas_msgs__msg__BoundingBox2D *)
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_const_function__BoundingBox2DArray__boxes(untyped_member, index));
  adas_msgs__msg__BoundingBox2D * value =
    (adas_msgs__msg__BoundingBox2D *)(untyped_value);
  *value = *item;
}

void adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__assign_function__BoundingBox2DArray__boxes(
  void * untyped_member, size_t index, const void * untyped_value)
{
  adas_msgs__msg__BoundingBox2D * item =
    ((adas_msgs__msg__BoundingBox2D *)
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_function__BoundingBox2DArray__boxes(untyped_member, index));
  const adas_msgs__msg__BoundingBox2D * value =
    (const adas_msgs__msg__BoundingBox2D *)(untyped_value);
  *item = *value;
}

bool adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__resize_function__BoundingBox2DArray__boxes(
  void * untyped_member, size_t size)
{
  adas_msgs__msg__BoundingBox2D__Sequence * member =
    (adas_msgs__msg__BoundingBox2D__Sequence *)(untyped_member);
  adas_msgs__msg__BoundingBox2D__Sequence__fini(member);
  return adas_msgs__msg__BoundingBox2D__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2DArray, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "boxes",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs__msg__BoundingBox2DArray, boxes),  // bytes offset in struct
    NULL,  // default value
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__size_function__BoundingBox2DArray__boxes,  // size() function pointer
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_const_function__BoundingBox2DArray__boxes,  // get_const(index) function pointer
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__get_function__BoundingBox2DArray__boxes,  // get(index) function pointer
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__fetch_function__BoundingBox2DArray__boxes,  // fetch(index, &value) function pointer
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__assign_function__BoundingBox2DArray__boxes,  // assign(index, value) function pointer
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__resize_function__BoundingBox2DArray__boxes  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_members = {
  "adas_msgs__msg",  // message namespace
  "BoundingBox2DArray",  // message name
  2,  // number of fields
  sizeof(adas_msgs__msg__BoundingBox2DArray),
  false,  // has_any_key_member_
  adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_member_array,  // message members
  adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_init_function,  // function to initialize message memory (memory has to be allocated)
  adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_type_support_handle = {
  0,
  &adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_members,
  get_message_typesupport_handle_function,
  &adas_msgs__msg__BoundingBox2DArray__get_type_hash,
  &adas_msgs__msg__BoundingBox2DArray__get_type_description,
  &adas_msgs__msg__BoundingBox2DArray__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_adas_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, adas_msgs, msg, BoundingBox2DArray)() {
  adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, adas_msgs, msg, BoundingBox2D)();
  if (!adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_type_support_handle.typesupport_identifier) {
    adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &adas_msgs__msg__BoundingBox2DArray__rosidl_typesupport_introspection_c__BoundingBox2DArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
