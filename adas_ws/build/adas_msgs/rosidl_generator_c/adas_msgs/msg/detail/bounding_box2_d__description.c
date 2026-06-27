// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from adas_msgs:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

#include "adas_msgs/msg/detail/bounding_box2_d__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_type_hash_t *
adas_msgs__msg__BoundingBox2D__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x85, 0x27, 0x55, 0x17, 0x00, 0x82, 0x06, 0x9b,
      0x67, 0x89, 0x2a, 0xca, 0x9f, 0xf8, 0x17, 0x3d,
      0xf2, 0x80, 0xd8, 0x37, 0x5a, 0xf9, 0x7e, 0x8b,
      0x4d, 0x2d, 0x6d, 0x38, 0x97, 0x58, 0x3b, 0xa7,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char adas_msgs__msg__BoundingBox2D__TYPE_NAME[] = "adas_msgs/msg/BoundingBox2D";

// Define type names, field names, and default values
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__x[] = "x";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__y[] = "y";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__w[] = "w";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__h[] = "h";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__confidence[] = "confidence";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__class_id[] = "class_id";
static char adas_msgs__msg__BoundingBox2D__FIELD_NAME__class_name[] = "class_name";

static rosidl_runtime_c__type_description__Field adas_msgs__msg__BoundingBox2D__FIELDS[] = {
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__x, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__y, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__w, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__h, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__confidence, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__class_id, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2D__FIELD_NAME__class_name, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
adas_msgs__msg__BoundingBox2D__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {adas_msgs__msg__BoundingBox2D__TYPE_NAME, 27, 27},
      {adas_msgs__msg__BoundingBox2D__FIELDS, 7, 7},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "float32 x\n"
  "float32 y\n"
  "float32 w\n"
  "float32 h\n"
  "float32 confidence\n"
  "int32 class_id\n"
  "string class_name";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
adas_msgs__msg__BoundingBox2D__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {adas_msgs__msg__BoundingBox2D__TYPE_NAME, 27, 27},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 92, 92},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
adas_msgs__msg__BoundingBox2D__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *adas_msgs__msg__BoundingBox2D__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
