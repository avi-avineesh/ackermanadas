// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/lane_data.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_HPP_
#define ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__adas_msgs__msg__LaneData __attribute__((deprecated))
#else
# define DEPRECATED__adas_msgs__msg__LaneData __declspec(deprecated)
#endif

namespace adas_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct LaneData_
{
  using Type = LaneData_<ContainerAllocator>;

  explicit LaneData_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->left_x = 0.0f;
      this->right_x = 0.0f;
      this->centre_x = 0.0f;
      this->curvature = 0.0f;
      this->lateral_error_m = 0.0f;
      this->confidence = 0.0f;
      this->recovery_mode = "";
    }
  }

  explicit LaneData_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    recovery_mode(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->left_x = 0.0f;
      this->right_x = 0.0f;
      this->centre_x = 0.0f;
      this->curvature = 0.0f;
      this->lateral_error_m = 0.0f;
      this->confidence = 0.0f;
      this->recovery_mode = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _left_x_type =
    float;
  _left_x_type left_x;
  using _right_x_type =
    float;
  _right_x_type right_x;
  using _centre_x_type =
    float;
  _centre_x_type centre_x;
  using _curvature_type =
    float;
  _curvature_type curvature;
  using _lateral_error_m_type =
    float;
  _lateral_error_m_type lateral_error_m;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _recovery_mode_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _recovery_mode_type recovery_mode;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__left_x(
    const float & _arg)
  {
    this->left_x = _arg;
    return *this;
  }
  Type & set__right_x(
    const float & _arg)
  {
    this->right_x = _arg;
    return *this;
  }
  Type & set__centre_x(
    const float & _arg)
  {
    this->centre_x = _arg;
    return *this;
  }
  Type & set__curvature(
    const float & _arg)
  {
    this->curvature = _arg;
    return *this;
  }
  Type & set__lateral_error_m(
    const float & _arg)
  {
    this->lateral_error_m = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__recovery_mode(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->recovery_mode = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    adas_msgs::msg::LaneData_<ContainerAllocator> *;
  using ConstRawPtr =
    const adas_msgs::msg::LaneData_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<adas_msgs::msg::LaneData_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<adas_msgs::msg::LaneData_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::LaneData_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::LaneData_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::LaneData_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::LaneData_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<adas_msgs::msg::LaneData_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<adas_msgs::msg::LaneData_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__adas_msgs__msg__LaneData
    std::shared_ptr<adas_msgs::msg::LaneData_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__adas_msgs__msg__LaneData
    std::shared_ptr<adas_msgs::msg::LaneData_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const LaneData_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->left_x != other.left_x) {
      return false;
    }
    if (this->right_x != other.right_x) {
      return false;
    }
    if (this->centre_x != other.centre_x) {
      return false;
    }
    if (this->curvature != other.curvature) {
      return false;
    }
    if (this->lateral_error_m != other.lateral_error_m) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->recovery_mode != other.recovery_mode) {
      return false;
    }
    return true;
  }
  bool operator!=(const LaneData_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct LaneData_

// alias to use template instance with default allocator
using LaneData =
  adas_msgs::msg::LaneData_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__LANE_DATA__STRUCT_HPP_
