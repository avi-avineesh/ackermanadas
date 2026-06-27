// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/lane_data.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__LANE_DATA__BUILDER_HPP_
#define ADAS_MSGS__MSG__DETAIL__LANE_DATA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "adas_msgs/msg/detail/lane_data__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace adas_msgs
{

namespace msg
{

namespace builder
{

class Init_LaneData_recovery_mode
{
public:
  explicit Init_LaneData_recovery_mode(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  ::adas_msgs::msg::LaneData recovery_mode(::adas_msgs::msg::LaneData::_recovery_mode_type arg)
  {
    msg_.recovery_mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_confidence
{
public:
  explicit Init_LaneData_confidence(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_recovery_mode confidence(::adas_msgs::msg::LaneData::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_LaneData_recovery_mode(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_lateral_error_m
{
public:
  explicit Init_LaneData_lateral_error_m(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_confidence lateral_error_m(::adas_msgs::msg::LaneData::_lateral_error_m_type arg)
  {
    msg_.lateral_error_m = std::move(arg);
    return Init_LaneData_confidence(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_curvature
{
public:
  explicit Init_LaneData_curvature(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_lateral_error_m curvature(::adas_msgs::msg::LaneData::_curvature_type arg)
  {
    msg_.curvature = std::move(arg);
    return Init_LaneData_lateral_error_m(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_centre_x
{
public:
  explicit Init_LaneData_centre_x(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_curvature centre_x(::adas_msgs::msg::LaneData::_centre_x_type arg)
  {
    msg_.centre_x = std::move(arg);
    return Init_LaneData_curvature(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_right_x
{
public:
  explicit Init_LaneData_right_x(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_centre_x right_x(::adas_msgs::msg::LaneData::_right_x_type arg)
  {
    msg_.right_x = std::move(arg);
    return Init_LaneData_centre_x(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_left_x
{
public:
  explicit Init_LaneData_left_x(::adas_msgs::msg::LaneData & msg)
  : msg_(msg)
  {}
  Init_LaneData_right_x left_x(::adas_msgs::msg::LaneData::_left_x_type arg)
  {
    msg_.left_x = std::move(arg);
    return Init_LaneData_right_x(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

class Init_LaneData_header
{
public:
  Init_LaneData_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_LaneData_left_x header(::adas_msgs::msg::LaneData::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_LaneData_left_x(msg_);
  }

private:
  ::adas_msgs::msg::LaneData msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::adas_msgs::msg::LaneData>()
{
  return adas_msgs::msg::builder::Init_LaneData_header();
}

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__LANE_DATA__BUILDER_HPP_
