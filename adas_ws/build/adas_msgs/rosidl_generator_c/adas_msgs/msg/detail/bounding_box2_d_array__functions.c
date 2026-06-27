// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/bounding_box2_d_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `boxes`
#include "adas_msgs/msg/detail/bounding_box2_d__functions.h"

bool
adas_msgs__msg__BoundingBox2DArray__init(adas_msgs__msg__BoundingBox2DArray * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    adas_msgs__msg__BoundingBox2DArray__fini(msg);
    return false;
  }
  // boxes
  if (!adas_msgs__msg__BoundingBox2D__Sequence__init(&msg->boxes, 0)) {
    adas_msgs__msg__BoundingBox2DArray__fini(msg);
    return false;
  }
  return true;
}

void
adas_msgs__msg__BoundingBox2DArray__fini(adas_msgs__msg__BoundingBox2DArray * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // boxes
  adas_msgs__msg__BoundingBox2D__Sequence__fini(&msg->boxes);
}

bool
adas_msgs__msg__BoundingBox2DArray__are_equal(const adas_msgs__msg__BoundingBox2DArray * lhs, const adas_msgs__msg__BoundingBox2DArray * rhs)
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
  // boxes
  if (!adas_msgs__msg__BoundingBox2D__Sequence__are_equal(
      &(lhs->boxes), &(rhs->boxes)))
  {
    return false;
  }
  return true;
}

bool
adas_msgs__msg__BoundingBox2DArray__copy(
  const adas_msgs__msg__BoundingBox2DArray * input,
  adas_msgs__msg__BoundingBox2DArray * output)
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
  // boxes
  if (!adas_msgs__msg__BoundingBox2D__Sequence__copy(
      &(input->boxes), &(output->boxes)))
  {
    return false;
  }
  return true;
}

adas_msgs__msg__BoundingBox2DArray *
adas_msgs__msg__BoundingBox2DArray__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2DArray * msg = (adas_msgs__msg__BoundingBox2DArray *)allocator.allocate(sizeof(adas_msgs__msg__BoundingBox2DArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(adas_msgs__msg__BoundingBox2DArray));
  bool success = adas_msgs__msg__BoundingBox2DArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
adas_msgs__msg__BoundingBox2DArray__destroy(adas_msgs__msg__BoundingBox2DArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    adas_msgs__msg__BoundingBox2DArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
adas_msgs__msg__BoundingBox2DArray__Sequence__init(adas_msgs__msg__BoundingBox2DArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2DArray * data = NULL;

  if (size) {
    data = (adas_msgs__msg__BoundingBox2DArray *)allocator.zero_allocate(size, sizeof(adas_msgs__msg__BoundingBox2DArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = adas_msgs__msg__BoundingBox2DArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        adas_msgs__msg__BoundingBox2DArray__fini(&data[i - 1]);
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
adas_msgs__msg__BoundingBox2DArray__Sequence__fini(adas_msgs__msg__BoundingBox2DArray__Sequence * array)
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
      adas_msgs__msg__BoundingBox2DArray__fini(&array->data[i]);
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

adas_msgs__msg__BoundingBox2DArray__Sequence *
adas_msgs__msg__BoundingBox2DArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2DArray__Sequence * array = (adas_msgs__msg__BoundingBox2DArray__Sequence *)allocator.allocate(sizeof(adas_msgs__msg__BoundingBox2DArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = adas_msgs__msg__BoundingBox2DArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
adas_msgs__msg__BoundingBox2DArray__Sequence__destroy(adas_msgs__msg__BoundingBox2DArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    adas_msgs__msg__BoundingBox2DArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
adas_msgs__msg__BoundingBox2DArray__Sequence__are_equal(const adas_msgs__msg__BoundingBox2DArray__Sequence * lhs, const adas_msgs__msg__BoundingBox2DArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!adas_msgs__msg__BoundingBox2DArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
adas_msgs__msg__BoundingBox2DArray__Sequence__copy(
  const adas_msgs__msg__BoundingBox2DArray__Sequence * input,
  adas_msgs__msg__BoundingBox2DArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(adas_msgs__msg__BoundingBox2DArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    adas_msgs__msg__BoundingBox2DArray * data =
      (adas_msgs__msg__BoundingBox2DArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!adas_msgs__msg__BoundingBox2DArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          adas_msgs__msg__BoundingBox2DArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!adas_msgs__msg__BoundingBox2DArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
