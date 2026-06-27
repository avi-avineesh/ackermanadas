// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/lane_data__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `recovery_mode`
#include "rosidl_runtime_c/string_functions.h"

bool
adas_msgs__msg__LaneData__init(adas_msgs__msg__LaneData * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    adas_msgs__msg__LaneData__fini(msg);
    return false;
  }
  // left_x
  // right_x
  // centre_x
  // curvature
  // lateral_error_m
  // confidence
  // recovery_mode
  if (!rosidl_runtime_c__String__init(&msg->recovery_mode)) {
    adas_msgs__msg__LaneData__fini(msg);
    return false;
  }
  return true;
}

void
adas_msgs__msg__LaneData__fini(adas_msgs__msg__LaneData * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // left_x
  // right_x
  // centre_x
  // curvature
  // lateral_error_m
  // confidence
  // recovery_mode
  rosidl_runtime_c__String__fini(&msg->recovery_mode);
}

bool
adas_msgs__msg__LaneData__are_equal(const adas_msgs__msg__LaneData * lhs, const adas_msgs__msg__LaneData * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // left_x
  if (lhs->left_x != rhs->left_x) {
    return false;
  }
  // right_x
  if (lhs->right_x != rhs->right_x) {
    return false;
  }
  // centre_x
  if (lhs->centre_x != rhs->centre_x) {
    return false;
  }
  // curvature
  if (lhs->curvature != rhs->curvature) {
    return false;
  }
  // lateral_error_m
  if (lhs->lateral_error_m != rhs->lateral_error_m) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // recovery_mode
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->recovery_mode), &(rhs->recovery_mode)))
  {
    return false;
  }
  return true;
}

bool
adas_msgs__msg__LaneData__copy(
  const adas_msgs__msg__LaneData * input,
  adas_msgs__msg__LaneData * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // left_x
  output->left_x = input->left_x;
  // right_x
  output->right_x = input->right_x;
  // centre_x
  output->centre_x = input->centre_x;
  // curvature
  output->curvature = input->curvature;
  // lateral_error_m
  output->lateral_error_m = input->lateral_error_m;
  // confidence
  output->confidence = input->confidence;
  // recovery_mode
  if (!rosidl_runtime_c__String__copy(
      &(input->recovery_mode), &(output->recovery_mode)))
  {
    return false;
  }
  return true;
}

adas_msgs__msg__LaneData *
adas_msgs__msg__LaneData__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__LaneData * msg = (adas_msgs__msg__LaneData *)allocator.allocate(sizeof(adas_msgs__msg__LaneData), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(adas_msgs__msg__LaneData));
  bool success = adas_msgs__msg__LaneData__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
adas_msgs__msg__LaneData__destroy(adas_msgs__msg__LaneData * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    adas_msgs__msg__LaneData__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
adas_msgs__msg__LaneData__Sequence__init(adas_msgs__msg__LaneData__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__LaneData * data = NULL;

  if (size) {
    data = (adas_msgs__msg__LaneData *)allocator.zero_allocate(size, sizeof(adas_msgs__msg__LaneData), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = adas_msgs__msg__LaneData__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        adas_msgs__msg__LaneData__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
adas_msgs__msg__LaneData__Sequence__fini(adas_msgs__msg__LaneData__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      adas_msgs__msg__LaneData__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

adas_msgs__msg__LaneData__Sequence *
adas_msgs__msg__LaneData__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__LaneData__Sequence * array = (adas_msgs__msg__LaneData__Sequence *)allocator.allocate(sizeof(adas_msgs__msg__LaneData__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = adas_msgs__msg__LaneData__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
adas_msgs__msg__LaneData__Sequence__destroy(adas_msgs__msg__LaneData__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    adas_msgs__msg__LaneData__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
adas_msgs__msg__LaneData__Sequence__are_equal(const adas_msgs__msg__LaneData__Sequence * lhs, const adas_msgs__msg__LaneData__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!adas_msgs__msg__LaneData__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
adas_msgs__msg__LaneData__Sequence__copy(
  const adas_msgs__msg__LaneData__Sequence * input,
  adas_msgs__msg__LaneData__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(adas_msgs__msg__LaneData);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    adas_msgs__msg__LaneData * data =
      (adas_msgs__msg__LaneData *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!adas_msgs__msg__LaneData__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          adas_msgs__msg__LaneData__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!adas_msgs__msg__LaneData__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
