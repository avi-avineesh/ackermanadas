// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d_array.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__BUILDER_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "adas_msgs/msg/detail/bounding_box2_d_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace adas_msgs
{

namespace msg
{

namespace builder
{

class Init_BoundingBox2DArray_boxes
{
public:
  explicit Init_BoundingBox2DArray_boxes(::adas_msgs::msg::BoundingBox2DArray & msg)
  : msg_(msg)
  {}
  ::adas_msgs::msg::BoundingBox2DArray boxes(::adas_msgs::msg::BoundingBox2DArray::_boxes_type arg)
  {
    msg_.boxes = std::move(arg);
    return std::move(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2DArray msg_;
};

class Init_BoundingBox2DArray_header
{
public:
  Init_BoundingBox2DArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BoundingBox2DArray_boxes header(::adas_msgs::msg::BoundingBox2DArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_BoundingBox2DArray_boxes(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2DArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::adas_msgs::msg::BoundingBox2DArray>()
{
  return adas_msgs::msg::builder::Init_BoundingBox2DArray_header();
}

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D_ARRAY__BUILDER_HPP_
