// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "adas_msgs/msg/bounding_box2_d.h"


#ifndef ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__FUNCTIONS_H_
#define ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/action_type_support_struct.h"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_runtime_c/service_type_support_struct.h"
#include "rosidl_runtime_c/type_description/type_description__struct.h"
#include "rosidl_runtime_c/type_description/type_source__struct.h"
#include "rosidl_runtime_c/type_hash.h"
#include "rosidl_runtime_c/visibility_control.h"
#include "adas_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "adas_msgs/msg/detail/bounding_box2_d__struct.h"

/// Initialize msg/BoundingBox2D message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * adas_msgs__msg__BoundingBox2D
 * )) before or use
 * adas_msgs__msg__BoundingBox2D__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__init(adas_msgs__msg__BoundingBox2D * msg);

/// Finalize msg/BoundingBox2D message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
void
adas_msgs__msg__BoundingBox2D__fini(adas_msgs__msg__BoundingBox2D * msg);

/// Create msg/BoundingBox2D message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * adas_msgs__msg__BoundingBox2D__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
adas_msgs__msg__BoundingBox2D *
adas_msgs__msg__BoundingBox2D__create(void);

/// Destroy msg/BoundingBox2D message.
/**
 * It calls
 * adas_msgs__msg__BoundingBox2D__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
void
adas_msgs__msg__BoundingBox2D__destroy(adas_msgs__msg__BoundingBox2D * msg);

/// Check for msg/BoundingBox2D message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__are_equal(const adas_msgs__msg__BoundingBox2D * lhs, const adas_msgs__msg__BoundingBox2D * rhs);

/// Copy a msg/BoundingBox2D message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__copy(
  const adas_msgs__msg__BoundingBox2D * input,
  adas_msgs__msg__BoundingBox2D * output);

/// Retrieve pointer to the hash of the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_type_hash_t *
adas_msgs__msg__BoundingBox2D__get_type_hash(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_runtime_c__type_description__TypeDescription *
adas_msgs__msg__BoundingBox2D__get_type_description(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the single raw source text that defined this type.
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_runtime_c__type_description__TypeSource *
adas_msgs__msg__BoundingBox2D__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support);

/// Retrieve pointer to the recursive raw sources that defined the description of this type.
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_runtime_c__type_description__TypeSource__Sequence *
adas_msgs__msg__BoundingBox2D__get_type_description_sources(
  const rosidl_message_type_support_t * type_support);

/// Initialize array of msg/BoundingBox2D messages.
/**
 * It allocates the memory for the number of elements and calls
 * adas_msgs__msg__BoundingBox2D__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__Sequence__init(adas_msgs__msg__BoundingBox2D__Sequence * array, size_t size);

/// Finalize array of msg/BoundingBox2D messages.
/**
 * It calls
 * adas_msgs__msg__BoundingBox2D__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
void
adas_msgs__msg__BoundingBox2D__Sequence__fini(adas_msgs__msg__BoundingBox2D__Sequence * array);

/// Create array of msg/BoundingBox2D messages.
/**
 * It allocates the memory for the array and calls
 * adas_msgs__msg__BoundingBox2D__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
adas_msgs__msg__BoundingBox2D__Sequence *
adas_msgs__msg__BoundingBox2D__Sequence__create(size_t size);

/// Destroy array of msg/BoundingBox2D messages.
/**
 * It calls
 * adas_msgs__msg__BoundingBox2D__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
void
adas_msgs__msg__BoundingBox2D__Sequence__destroy(adas_msgs__msg__BoundingBox2D__Sequence * array);

/// Check for msg/BoundingBox2D message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__Sequence__are_equal(const adas_msgs__msg__BoundingBox2D__Sequence * lhs, const adas_msgs__msg__BoundingBox2D__Sequence * rhs);

/// Copy an array of msg/BoundingBox2D messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
bool
adas_msgs__msg__BoundingBox2D__Sequence__copy(
  const adas_msgs__msg__BoundingBox2D__Sequence * input,
  adas_msgs__msg__BoundingBox2D__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // ADAS_MSGS__MSG__DETAIL__BOUNDING_BOX2_D__FUNCTIONS_H_
