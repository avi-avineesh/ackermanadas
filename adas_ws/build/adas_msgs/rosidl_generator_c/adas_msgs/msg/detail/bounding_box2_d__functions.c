// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/bounding_box2_d__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `class_name`
#include "rosidl_runtime_c/string_functions.h"

bool
adas_msgs__msg__BoundingBox2D__init(adas_msgs__msg__BoundingBox2D * msg)
{
  if (!msg) {
    return false;
  }
  // x
  // y
  // w
  // h
  // confidence
  // class_id
  // class_name
  if (!rosidl_runtime_c__String__init(&msg->class_name)) {
    adas_msgs__msg__BoundingBox2D__fini(msg);
    return false;
  }
  return true;
}

void
adas_msgs__msg__BoundingBox2D__fini(adas_msgs__msg__BoundingBox2D * msg)
{
  if (!msg) {
    return;
  }
  // x
  // y
  // w
  // h
  // confidence
  // class_id
  // class_name
  rosidl_runtime_c__String__fini(&msg->class_name);
}

bool
adas_msgs__msg__BoundingBox2D__are_equal(const adas_msgs__msg__BoundingBox2D * lhs, const adas_msgs__msg__BoundingBox2D * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // x
  if (lhs->x != rhs->x) {
    return false;
  }
  // y
  if (lhs->y != rhs->y) {
    return false;
  }
  // w
  if (lhs->w != rhs->w) {
    return false;
  }
  // h
  if (lhs->h != rhs->h) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // class_id
  if (lhs->class_id != rhs->class_id) {
    return false;
  }
  // class_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->class_name), &(rhs->class_name)))
  {
    return false;
  }
  return true;
}

bool
adas_msgs__msg__BoundingBox2D__copy(
  const adas_msgs__msg__BoundingBox2D * input,
  adas_msgs__msg__BoundingBox2D * output)
{
  if (!input || !output) {
    return false;
  }
  // x
  output->x = input->x;
  // y
  output->y = input->y;
  // w
  output->w = input->w;
  // h
  output->h = input->h;
  // confidence
  output->confidence = input->confidence;
  // class_id
  output->class_id = input->class_id;
  // class_name
  if (!rosidl_runtime_c__String__copy(
      &(input->class_name), &(output->class_name)))
  {
    return false;
  }
  return true;
}

adas_msgs__msg__BoundingBox2D *
adas_msgs__msg__BoundingBox2D__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2D * msg = (adas_msgs__msg__BoundingBox2D *)allocator.allocate(sizeof(adas_msgs__msg__BoundingBox2D), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(adas_msgs__msg__BoundingBox2D));
  bool success = adas_msgs__msg__BoundingBox2D__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
adas_msgs__msg__BoundingBox2D__destroy(adas_msgs__msg__BoundingBox2D * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    adas_msgs__msg__BoundingBox2D__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
adas_msgs__msg__BoundingBox2D__Sequence__init(adas_msgs__msg__BoundingBox2D__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2D * data = NULL;

  if (size) {
    data = (adas_msgs__msg__BoundingBox2D *)allocator.zero_allocate(size, sizeof(adas_msgs__msg__BoundingBox2D), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = adas_msgs__msg__BoundingBox2D__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        adas_msgs__msg__BoundingBox2D__fini(&data[i - 1]);
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
adas_msgs__msg__BoundingBox2D__Sequence__fini(adas_msgs__msg__BoundingBox2D__Sequence * array)
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
      adas_msgs__msg__BoundingBox2D__fini(&array->data[i]);
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

adas_msgs__msg__BoundingBox2D__Sequence *
adas_msgs__msg__BoundingBox2D__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__BoundingBox2D__Sequence * array = (adas_msgs__msg__BoundingBox2D__Sequence *)allocator.allocate(sizeof(adas_msgs__msg__BoundingBox2D__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = adas_msgs__msg__BoundingBox2D__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
adas_msgs__msg__BoundingBox2D__Sequence__destroy(adas_msgs__msg__BoundingBox2D__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    adas_msgs__msg__BoundingBox2D__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
adas_msgs__msg__BoundingBox2D__Sequence__are_equal(const adas_msgs__msg__BoundingBox2D__Sequence * lhs, const adas_msgs__msg__BoundingBox2D__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!adas_msgs__msg__BoundingBox2D__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
adas_msgs__msg__BoundingBox2D__Sequence__copy(
  const adas_msgs__msg__BoundingBox2D__Sequence * input,
  adas_msgs__msg__BoundingBox2D__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(adas_msgs__msg__BoundingBox2D);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    adas_msgs__msg__BoundingBox2D * data =
      (adas_msgs__msg__BoundingBox2D *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!adas_msgs__msg__BoundingBox2D__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          adas_msgs__msg__BoundingBox2D__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!adas_msgs__msg__BoundingBox2D__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
