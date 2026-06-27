// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice
#include "adas_msgs/msg/detail/vehicle_params__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
adas_msgs__msg__VehicleParams__init(adas_msgs__msg__VehicleParams * msg)
{
  if (!msg) {
    return false;
  }
  // max_speed
  // max_steer
  return true;
}

void
adas_msgs__msg__VehicleParams__fini(adas_msgs__msg__VehicleParams * msg)
{
  if (!msg) {
    return;
  }
  // max_speed
  // max_steer
}

bool
adas_msgs__msg__VehicleParams__are_equal(const adas_msgs__msg__VehicleParams * lhs, const adas_msgs__msg__VehicleParams * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // max_speed
  if (lhs->max_speed != rhs->max_speed) {
    return false;
  }
  // max_steer
  if (lhs->max_steer != rhs->max_steer) {
    return false;
  }
  return true;
}

bool
adas_msgs__msg__VehicleParams__copy(
  const adas_msgs__msg__VehicleParams * input,
  adas_msgs__msg__VehicleParams * output)
{
  if (!input || !output) {
    return false;
  }
  // max_speed
  output->max_speed = input->max_speed;
  // max_steer
  output->max_steer = input->max_steer;
  return true;
}

adas_msgs__msg__VehicleParams *
adas_msgs__msg__VehicleParams__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__VehicleParams * msg = (adas_msgs__msg__VehicleParams *)allocator.allocate(sizeof(adas_msgs__msg__VehicleParams), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(adas_msgs__msg__VehicleParams));
  bool success = adas_msgs__msg__VehicleParams__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
adas_msgs__msg__VehicleParams__destroy(adas_msgs__msg__VehicleParams * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    adas_msgs__msg__VehicleParams__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
adas_msgs__msg__VehicleParams__Sequence__init(adas_msgs__msg__VehicleParams__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__VehicleParams * data = NULL;

  if (size) {
    data = (adas_msgs__msg__VehicleParams *)allocator.zero_allocate(size, sizeof(adas_msgs__msg__VehicleParams), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = adas_msgs__msg__VehicleParams__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        adas_msgs__msg__VehicleParams__fini(&data[i - 1]);
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
adas_msgs__msg__VehicleParams__Sequence__fini(adas_msgs__msg__VehicleParams__Sequence * array)
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
      adas_msgs__msg__VehicleParams__fini(&array->data[i]);
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

adas_msgs__msg__VehicleParams__Sequence *
adas_msgs__msg__VehicleParams__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  adas_msgs__msg__VehicleParams__Sequence * array = (adas_msgs__msg__VehicleParams__Sequence *)allocator.allocate(sizeof(adas_msgs__msg__VehicleParams__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = adas_msgs__msg__VehicleParams__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
adas_msgs__msg__VehicleParams__Sequence__destroy(adas_msgs__msg__VehicleParams__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    adas_msgs__msg__VehicleParams__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
adas_msgs__msg__VehicleParams__Sequence__are_equal(const adas_msgs__msg__VehicleParams__Sequence * lhs, const adas_msgs__msg__VehicleParams__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!adas_msgs__msg__VehicleParams__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
adas_msgs__msg__VehicleParams__Sequence__copy(
  const adas_msgs__msg__VehicleParams__Sequence * input,
  adas_msgs__msg__VehicleParams__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(adas_msgs__msg__VehicleParams);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    adas_msgs__msg__VehicleParams * data =
      (adas_msgs__msg__VehicleParams *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!adas_msgs__msg__VehicleParams__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          adas_msgs__msg__VehicleParams__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!adas_msgs__msg__VehicleParams__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
