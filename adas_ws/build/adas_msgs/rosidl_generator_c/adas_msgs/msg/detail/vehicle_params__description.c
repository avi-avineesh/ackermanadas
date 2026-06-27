// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from adas_msgs:msg/VehicleParams.idl
// generated code does not contain a copyright notice

#include "adas_msgs/msg/detail/vehicle_params__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_type_hash_t *
adas_msgs__msg__VehicleParams__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x14, 0x2a, 0xa1, 0x9c, 0xea, 0xb6, 0xb0, 0x3e,
      0x96, 0xa2, 0x06, 0xf4, 0xb3, 0x06, 0x0d, 0x43,
      0x9a, 0x45, 0xd0, 0x81, 0x17, 0xb2, 0x88, 0x92,
      0x2a, 0x0b, 0x7f, 0xd3, 0x69, 0x50, 0x93, 0x56,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char adas_msgs__msg__VehicleParams__TYPE_NAME[] = "adas_msgs/msg/VehicleParams";

// Define type names, field names, and default values
static char adas_msgs__msg__VehicleParams__FIELD_NAME__max_speed[] = "max_speed";
static char adas_msgs__msg__VehicleParams__FIELD_NAME__max_steer[] = "max_steer";

static rosidl_runtime_c__type_description__Field adas_msgs__msg__VehicleParams__FIELDS[] = {
  {
    {adas_msgs__msg__VehicleParams__FIELD_NAME__max_speed, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__VehicleParams__FIELD_NAME__max_steer, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
adas_msgs__msg__VehicleParams__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {adas_msgs__msg__VehicleParams__TYPE_NAME, 27, 27},
      {adas_msgs__msg__VehicleParams__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32 max_speed\n"
  "float32 max_steer";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
adas_msgs__msg__VehicleParams__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {adas_msgs__msg__VehicleParams__TYPE_NAME, 27, 27},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 36, 36},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
adas_msgs__msg__VehicleParams__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *adas_msgs__msg__VehicleParams__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
