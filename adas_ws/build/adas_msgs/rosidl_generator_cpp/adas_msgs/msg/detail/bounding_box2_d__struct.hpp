// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d.hpp"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_HPP_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__adas_msgs__msg__BoundingBox2D __attribute__((deprecated))
#else
# define DEPRECATED__adas_msgs__msg__BoundingBox2D __declspec(deprecated)
#endif

namespace adas_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct BoundingBox2D_
{
  using Type = BoundingBox2D_<ContainerAllocator>;

  explicit BoundingBox2D_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->x = 0.0f;
      this->y = 0.0f;
      this->w = 0.0f;
      this->h = 0.0f;
      this->confidence = 0.0f;
      this->class_id = 0l;
      this->class_name = "";
    }
  }

  explicit BoundingBox2D_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : class_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->x = 0.0f;
      this->y = 0.0f;
      this->w = 0.0f;
      this->h = 0.0f;
      this->confidence = 0.0f;
      this->class_id = 0l;
      this->class_name = "";
    }
  }

  // field types and members
  using _x_type =
    float;
  _x_type x;
  using _y_type =
    float;
  _y_type y;
  using _w_type =
    float;
  _w_type w;
  using _h_type =
    float;
  _h_type h;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _class_id_type =
    int32_t;
  _class_id_type class_id;
  using _class_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _class_name_type class_name;

  // setters for named parameter idiom
  Type & set__x(
    const float & _arg)
  {
    this->x = _arg;
    return *this;
  }
  Type & set__y(
    const float & _arg)
  {
    this->y = _arg;
    return *this;
  }
  Type & set__w(
    const float & _arg)
  {
    this->w = _arg;
    return *this;
  }
  Type & set__h(
    const float & _arg)
  {
    this->h = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__class_id(
    const int32_t & _arg)
  {
    this->class_id = _arg;
    return *this;
  }
  Type & set__class_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->class_name = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    adas_msgs::msg::BoundingBox2D_<ContainerAllocator> *;
  using ConstRawPtr =
    const adas_msgs::msg::BoundingBox2D_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::BoundingBox2D_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      adas_msgs::msg::BoundingBox2D_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__adas_msgs__msg__BoundingBox2D
    std::shared_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__adas_msgs__msg__BoundingBox2D
    std::shared_ptr<adas_msgs::msg::BoundingBox2D_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BoundingBox2D_ & other) const
  {
    if (this->x != other.x) {
      return false;
    }
    if (this->y != other.y) {
      return false;
    }
    if (this->w != other.w) {
      return false;
    }
    if (this->h != other.h) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->class_id != other.class_id) {
      return false;
    }
    if (this->class_name != other.class_name) {
      return false;
    }
    return true;
  }
  bool operator!=(const BoundingBox2D_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BoundingBox2D_

// alias to use template instance with default allocator
using BoundingBox2D =
  adas_msgs::msg::BoundingBox2D_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace adas_msgs

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__STRUCT_HPP_
