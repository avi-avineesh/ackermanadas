// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d_array.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__TRAITS_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "adas_msgs/msg/detail/bounding_box2_d_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'boxes'
#include "adas_msgs/msg/detail/bounding_box2_d__traits.hpp"

namespace adas_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const BoundingBox2DArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: boxes
  {
    if (msg.boxes.size() == 0) {
      out << "boxes: []";
    } else {
      out << "boxes: [";
      size_t pending_items = msg.boxes.size();
      for (auto item : msg.boxes) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const BoundingBox2DArray & msg,
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

  // member: boxes
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.boxes.size() == 0) {
      out << "boxes: []\n";
    } else {
      out << "boxes:\n";
      for (auto item : msg.boxes) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const BoundingBox2DArray & msg, bool use_flow_style = false)
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
  const adas_msgs::msg::BoundingBox2DArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  adas_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use adas_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const adas_msgs::msg::BoundingBox2DArray & msg)
{
  return adas_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<adas_msgs::msg::BoundingBox2DArray>()
{
  return "adas_msgs::msg::BoundingBox2DArray";
}

template<>
inline const char * name<adas_msgs::msg::BoundingBox2DArray>()
{
  return "adas_msgs/msg/BoundingBox2DArray";
}

template<>
struct has_fixed_size<adas_msgs::msg::BoundingBox2DArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<adas_msgs::msg::BoundingBox2DArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<adas_msgs::msg::BoundingBox2DArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__TRAITS_HPP_
