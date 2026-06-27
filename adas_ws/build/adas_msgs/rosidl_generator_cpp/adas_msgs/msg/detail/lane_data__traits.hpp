// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/lane_data.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__LANE_DATA__TRAITS_HPP_
#define ADAS_MSGS__MSG__DETAIL__LANE_DATA__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "adas_msgs/msg/detail/lane_data__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace adas_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const LaneData & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: left_x
  {
    out << "left_x: ";
    rosidl_generator_traits::value_to_yaml(msg.left_x, out);
    out << ", ";
  }

  // member: right_x
  {
    out << "right_x: ";
    rosidl_generator_traits::value_to_yaml(msg.right_x, out);
    out << ", ";
  }

  // member: centre_x
  {
    out << "centre_x: ";
    rosidl_generator_traits::value_to_yaml(msg.centre_x, out);
    out << ", ";
  }

  // member: curvature
  {
    out << "curvature: ";
    rosidl_generator_traits::value_to_yaml(msg.curvature, out);
    out << ", ";
  }

  // member: lateral_error_m
  {
    out << "lateral_error_m: ";
    rosidl_generator_traits::value_to_yaml(msg.lateral_error_m, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: recovery_mode
  {
    out << "recovery_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.recovery_mode, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const LaneData & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: left_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_x: ";
    rosidl_generator_traits::value_to_yaml(msg.left_x, out);
    out << "\n";
  }

  // member: right_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_x: ";
    rosidl_generator_traits::value_to_yaml(msg.right_x, out);
    out << "\n";
  }

  // member: centre_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "centre_x: ";
    rosidl_generator_traits::value_to_yaml(msg.centre_x, out);
    out << "\n";
  }

  // member: curvature
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "curvature: ";
    rosidl_generator_traits::value_to_yaml(msg.curvature, out);
    out << "\n";
  }

  // member: lateral_error_m
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lateral_error_m: ";
    rosidl_generator_traits::value_to_yaml(msg.lateral_error_m, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: recovery_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "recovery_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.recovery_mode, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const LaneData & msg, bool use_flow_style = false)
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
  const adas_msgs::msg::LaneData & msg,
  std::ostream & out, size_t indentation = 0)
{
  adas_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use adas_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const adas_msgs::msg::LaneData & msg)
{
  return adas_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<adas_msgs::msg::LaneData>()
{
  return "adas_msgs::msg::LaneData";
}

template<>
inline const char * name<adas_msgs::msg::LaneData>()
{
  return "adas_msgs/msg/LaneData";
}

template<>
struct has_fixed_size<adas_msgs::msg::LaneData>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<adas_msgs::msg::LaneData>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<adas_msgs::msg::LaneData>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ADAS_MSGS__MSG__DETAIL__LANE_DATA__TRAITS_HPP_
