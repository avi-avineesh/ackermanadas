// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "adas_msgs/msg/detail/vehicle_params__functions.h"
#include "adas_msgs/msg/detail/vehicle_params__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace adas_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void VehicleParams_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) adas_msgs::msg::VehicleParams(_init);
}

void VehicleParams_fini_function(void * message_memory)
{
  auto typed_message = static_cast<adas_msgs::msg::VehicleParams *>(message_memory);
  typed_message->~VehicleParams();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember VehicleParams_message_member_array[2] = {
  {
    "max_speed",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs::msg::VehicleParams, max_speed),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "max_steer",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(adas_msgs::msg::VehicleParams, max_steer),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers VehicleParams_message_members = {
  "adas_msgs::msg",  // message namespace
  "VehicleParams",  // message name
  2,  // number of fields
  sizeof(adas_msgs::msg::VehicleParams),
  false,  // has_any_key_member_
  VehicleParams_message_member_array,  // message members
  VehicleParams_init_function,  // function to initialize message memory (memory has to be allocated)
  VehicleParams_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t VehicleParams_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &VehicleParams_message_members,
  get_message_typesupport_handle_function,
  &adas_msgs__msg__VehicleParams__get_type_hash,
  &adas_msgs__msg__VehicleParams__get_type_description,
  &adas_msgs__msg__VehicleParams__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace adas_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<adas_msgs::msg::VehicleParams>()
{
  return &::adas_msgs::msg::rosidl_typesupport_introspection_cpp::VehicleParams_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, adas_msgs, msg, VehicleParams)() {
  return &::adas_msgs::msg::rosidl_typesupport_introspection_cpp::VehicleParams_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
