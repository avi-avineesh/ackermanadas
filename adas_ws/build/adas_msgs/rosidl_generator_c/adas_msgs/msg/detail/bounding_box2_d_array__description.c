// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from adas_msgs:msg/BoundingBox2DArray.idl
// generated code does not contain a copyright notice

#include "adas_msgs/msg/detail/bounding_box2_d_array__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_type_hash_t *
adas_msgs__msg__BoundingBox2DArray__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x1e, 0x45, 0x65, 0x8d, 0x8c, 0x16, 0xaf, 0x0c,
      0xb4, 0x4f, 0x92, 0xe3, 0xfc, 0xd9, 0xdb, 0xb7,
      0x2c, 0x62, 0x73, 0xec, 0x6f, 0xb7, 0xcf, 0x8c,
      0x0e, 0x82, 0xaf, 0x14, 0xb3, 0xff, 0x1d, 0x21,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "adas_msgs/msg/detail/bounding_box2_d__functions.h"
#include "std_msgs/msg/detail/header__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t adas_msgs__msg__BoundingBox2D__EXPECTED_HASH = {1, {
    0x85, 0x27, 0x55, 0x17, 0x00, 0x82, 0x06, 0x9b,
    0x67, 0x89, 0x2a, 0xca, 0x9f, 0xf8, 0x17, 0x3d,
    0xf2, 0x80, 0xd8, 0x37, 0x5a, 0xf9, 0x7e, 0x8b,
    0x4d, 0x2d, 0x6d, 0x38, 0x97, 0x58, 0x3b, 0xa7,
  }};
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t std_msgs__msg__Header__EXPECTED_HASH = {1, {
    0xf4, 0x9f, 0xb3, 0xae, 0x2c, 0xf0, 0x70, 0xf7,
    0x93, 0x64, 0x5f, 0xf7, 0x49, 0x68, 0x3a, 0xc6,
    0xb0, 0x62, 0x03, 0xe4, 0x1c, 0x89, 0x1e, 0x17,
    0x70, 0x1b, 0x1c, 0xb5, 0x97, 0xce, 0x6a, 0x01,
  }};
#endif

static char adas_msgs__msg__BoundingBox2DArray__TYPE_NAME[] = "adas_msgs/msg/BoundingBox2DArray";
static char adas_msgs__msg__BoundingBox2D__TYPE_NAME[] = "adas_msgs/msg/BoundingBox2D";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char std_msgs__msg__Header__TYPE_NAME[] = "std_msgs/msg/Header";

// Define type names, field names, and default values
static char adas_msgs__msg__BoundingBox2DArray__FIELD_NAME__header[] = "header";
static char adas_msgs__msg__BoundingBox2DArray__FIELD_NAME__boxes[] = "boxes";

static rosidl_runtime_c__type_description__Field adas_msgs__msg__BoundingBox2DArray__FIELDS[] = {
  {
    {adas_msgs__msg__BoundingBox2DArray__FIELD_NAME__header, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__BoundingBox2DArray__FIELD_NAME__boxes, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {adas_msgs__msg__BoundingBox2D__TYPE_NAME, 27, 27},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription adas_msgs__msg__BoundingBox2DArray__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {adas_msgs__msg__BoundingBox2D__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
adas_msgs__msg__BoundingBox2DArray__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {adas_msgs__msg__BoundingBox2DArray__TYPE_NAME, 32, 32},
      {adas_msgs__msg__BoundingBox2DArray__FIELDS, 2, 2},
    },
    {adas_msgs__msg__BoundingBox2DArray__REFERENCED_TYPE_DESCRIPTIONS, 3, 3},
  };
  if (!constructed) {
    assert(0 == memcmp(&adas_msgs__msg__BoundingBox2D__EXPECTED_HASH, adas_msgs__msg__BoundingBox2D__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = adas_msgs__msg__BoundingBox2D__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&std_msgs__msg__Header__EXPECTED_HASH, std_msgs__msg__Header__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[2].fields = std_msgs__msg__Header__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "std_msgs/Header header\n"
  "BoundingBox2D[] boxes";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
adas_msgs__msg__BoundingBox2DArray__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {adas_msgs__msg__BoundingBox2DArray__TYPE_NAME, 32, 32},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 45, 45},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
adas_msgs__msg__BoundingBox2DArray__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[4];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 4, 4};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *adas_msgs__msg__BoundingBox2DArray__get_individual_type_description_source(NULL),
    sources[1] = *adas_msgs__msg__BoundingBox2D__get_individual_type_description_source(NULL);
    sources[2] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[3] = *std_msgs__msg__Header__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
