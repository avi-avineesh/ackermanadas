// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/vehicle_params.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__BUILDER_HPP_
#define ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "adas_msgs/msg/detail/vehicle_params__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace adas_msgs
{

namespace msg
{

namespace builder
{

class Init_VehicleParams_max_steer
{
public:
  explicit Init_VehicleParams_max_steer(::adas_msgs::msg::VehicleParams & msg)
  : msg_(msg)
  {}
  ::adas_msgs::msg::VehicleParams max_steer(::adas_msgs::msg::VehicleParams::_max_steer_type arg)
  {
    msg_.max_steer = std::move(arg);
    return std::move(msg_);
  }

private:
  ::adas_msgs::msg::VehicleParams msg_;
};

class Init_VehicleParams_max_speed
{
public:
  Init_VehicleParams_max_speed()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VehicleParams_max_steer max_speed(::adas_msgs::msg::VehicleParams::_max_speed_type arg)
  {
    msg_.max_speed = std::move(arg);
    return Init_VehicleParams_max_steer(msg_);
  }

private:
  ::adas_msgs::msg::VehicleParams msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::adas_msgs::msg::VehicleParams>()
{
  return adas_msgs::msg::builder::Init_VehicleParams_max_speed();
}

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__BUILDER_HPP_
