// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "adas_msgs/msg/detail/bounding_box2_d__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace adas_msgs
{

namespace msg
{

namespace builder
{

class Init_BoundingBox2D_class_name
{
public:
  explicit Init_BoundingBox2D_class_name(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  ::adas_msgs::msg::BoundingBox2D class_name(::adas_msgs::msg::BoundingBox2D::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_class_id
{
public:
  explicit Init_BoundingBox2D_class_id(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox2D_class_name class_id(::adas_msgs::msg::BoundingBox2D::_class_id_type arg)
  {
    msg_.class_id = std::move(arg);
    return Init_BoundingBox2D_class_name(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_confidence
{
public:
  explicit Init_BoundingBox2D_confidence(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox2D_class_id confidence(::adas_msgs::msg::BoundingBox2D::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_BoundingBox2D_class_id(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_h
{
public:
  explicit Init_BoundingBox2D_h(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox2D_confidence h(::adas_msgs::msg::BoundingBox2D::_h_type arg)
  {
    msg_.h = std::move(arg);
    return Init_BoundingBox2D_confidence(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_w
{
public:
  explicit Init_BoundingBox2D_w(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox2D_h w(::adas_msgs::msg::BoundingBox2D::_w_type arg)
  {
    msg_.w = std::move(arg);
    return Init_BoundingBox2D_h(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_y
{
public:
  explicit Init_BoundingBox2D_y(::adas_msgs::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  Init_BoundingBox2D_w y(::adas_msgs::msg::BoundingBox2D::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_BoundingBox2D_w(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_x
{
public:
  Init_BoundingBox2D_x()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BoundingBox2D_y x(::adas_msgs::msg::BoundingBox2D::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_BoundingBox2D_y(msg_);
  }

private:
  ::adas_msgs::msg::BoundingBox2D msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::adas_msgs::msg::BoundingBox2D>()
{
  return adas_msgs::msg::builder::Init_BoundingBox2D_x();
}

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_
