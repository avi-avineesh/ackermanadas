// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/vehicle_params.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__TRAITS_HPP_
#define ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "adas_msgs/msg/detail/vehicle_params__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace adas_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const VehicleParams & msg,
  std::ostream & out)
{
  out << "{";
  // member: max_speed
  {
    out << "max_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.max_speed, out);
    out << ", ";
  }

  // member: max_steer
  {
    out << "max_steer: ";
    rosidl_generator_traits::value_to_yaml(msg.max_steer, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const VehicleParams & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: max_speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "max_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.max_speed, out);
    out << "\n";
  }

  // member: max_steer
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "max_steer: ";
    rosidl_generator_traits::value_to_yaml(msg.max_steer, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const VehicleParams & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace adas_msgs

namespace rosidl_generator_traits
{

[[deprecated("use adas_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const adas_msgs::msg::VehicleParams & msg,
  std::ostream & out, size_t indentation = 0)
{
  adas_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use adas_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const adas_msgs::msg::VehicleParams & msg)
{
  return adas_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<adas_msgs::msg::VehicleParams>()
{
  return "adas_msgs::msg::VehicleParams";
}

template<>
inline const char * name<adas_msgs::msg::VehicleParams>()
{
  return "adas_msgs/msg/VehicleParams";
}

template<>
struct has_fixed_size<adas_msgs::msg::VehicleParams>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<adas_msgs::msg::VehicleParams>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<adas_msgs::msg::VehicleParams>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__TRAITS_HPP_
