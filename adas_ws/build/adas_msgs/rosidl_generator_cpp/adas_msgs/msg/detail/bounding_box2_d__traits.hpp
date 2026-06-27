// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__TRAITS_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "adas_msgs/msg/detail/bounding_box2_d__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace adas_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const BoundingBox2D & msg,
  std::ostream & out)
{
  out << "{";
  // member: x
  {
    out << "x: ";
    rosidl_generator_traits::value_to_yaml(msg.x, out);
    out << ", ";
  }

  // member: y
  {
    out << "y: ";
    rosidl_generator_traits::value_to_yaml(msg.y, out);
    out << ", ";
  }

  // member: w
  {
    out << "w: ";
    rosidl_generator_traits::value_to_yaml(msg.w, out);
    out << ", ";
  }

  // member: h
  {
    out << "h: ";
    rosidl_generator_traits::value_to_yaml(msg.h, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: class_id
  {
    out << "class_id: ";
    rosidl_generator_traits::value_to_yaml(msg.class_id, out);
    out << ", ";
  }

  // member: class_name
  {
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const BoundingBox2D & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "x: ";
    rosidl_generator_traits::value_to_yaml(msg.x, out);
    out << "\n";
  }

  // member: y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "y: ";
    rosidl_generator_traits::value_to_yaml(msg.y, out);
    out << "\n";
  }

  // member: w
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "w: ";
    rosidl_generator_traits::value_to_yaml(msg.w, out);
    out << "\n";
  }

  // member: h
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "h: ";
    rosidl_generator_traits::value_to_yaml(msg.h, out);
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

  // member: class_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "class_id: ";
    rosidl_generator_traits::value_to_yaml(msg.class_id, out);
    out << "\n";
  }

  // member: class_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "class_name: ";
    rosidl_generator_traits::value_to_yaml(msg.class_name, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const BoundingBox2D & msg, bool use_flow_style = false)
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
  const adas_msgs::msg::BoundingBox2D & msg,
  std::ostream & out, size_t indentation = 0)
{
  adas_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use adas_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const adas_msgs::msg::BoundingBox2D & msg)
{
  return adas_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<adas_msgs::msg::BoundingBox2D>()
{
  return "adas_msgs::msg::BoundingBox2D";
}

template<>
inline const char * name<adas_msgs::msg::BoundingBox2D>()
{
  return "adas_msgs/msg/BoundingBox2D";
}

template<>
struct has_fixed_size<adas_msgs::msg::BoundingBox2D>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<adas_msgs::msg::BoundingBox2D>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<adas_msgs::msg::BoundingBox2D>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__TRAITS_HPP_
