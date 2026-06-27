// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/vehicle_params.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_HPP_
#define ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__adas_msgs__msg__VehicleParams __attribute__((deprecated))
#else
# define DEPRECATED__adas_msgs__msg__VehicleParams __declspec(deprecated)
#endif

namespace adas_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct VehicleParams_
{
  using Type = VehicleParams_<ContainerAllocator>;

  explicit VehicleParams_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->max_speed = 0.0f;
      this->max_steer = 0.0f;
    }
  }

  explicit VehicleParams_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->max_speed = 0.0f;
      this->max_steer = 0.0f;
    }
  }

  // field types and members
  using _max_speed_type =
    float;
  _max_speed_type max_speed;
  using _max_steer_type =
    float;
  _max_steer_type max_steer;

  // setters for named parameter idiom
  Type & set__max_speed(
    const float & _arg)
  {
    this->max_speed = _arg;
    return *this;
  }
  Type & set__max_steer(
    const float & _arg)
  {
    this->max_steer = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    adas_msgs::msg::VehicleParams_<ContainerAllocator> *;
  using ConstRawPtr =
    const adas_msgs::msg::VehicleParams_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::VehicleParams_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::VehicleParams_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__adas_msgs__msg__VehicleParams
    std::shared_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__adas_msgs__msg__VehicleParams
    std::shared_ptr<adas_msgs::msg::VehicleParams_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const VehicleParams_ & other) const
  {
    if (this->max_speed != other.max_speed) {
      return false;
    }
    if (this->max_steer != other.max_steer) {
      return false;
    }
    return true;
  }
  bool operator!=(const VehicleParams_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct VehicleParams_

// alias to use template instance with default allocator
using VehicleParams =
  adas_msgs::msg::VehicleParams_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__VEHICLE_PARAMS__STRUCT_HPP_
