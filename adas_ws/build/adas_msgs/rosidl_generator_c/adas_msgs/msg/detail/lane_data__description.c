// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from adas_msgs:msg/LaneData.idl
// generated code does not contain a copyright notice

#include "adas_msgs/msg/detail/lane_data__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_adas_msgs
const rosidl_type_hash_t *
adas_msgs__msg__LaneData__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x51, 0x65, 0xf2, 0xce, 0xa0, 0x8f, 0xab, 0x05,
      0x19, 0x2f, 0xd4, 0xf7, 0x69, 0x2d, 0x42, 0xba,
      0xd5, 0x97, 0x98, 0x21, 0xf9, 0xf0, 0x18, 0x5e,
      0x13, 0xab, 0x99, 0x3a, 0x3b, 0xd9, 0x10, 0x63,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "std_msgs/msg/detail/header__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
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

static char adas_msgs__msg__LaneData__TYPE_NAME[] = "adas_msgs/msg/LaneData";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char std_msgs__msg__Header__TYPE_NAME[] = "std_msgs/msg/Header";

// Define type names, field names, and default values
static char adas_msgs__msg__LaneData__FIELD_NAME__header[] = "header";
static char adas_msgs__msg__LaneData__FIELD_NAME__left_x[] = "left_x";
static char adas_msgs__msg__LaneData__FIELD_NAME__right_x[] = "right_x";
static char adas_msgs__msg__LaneData__FIELD_NAME__centre_x[] = "centre_x";
static char adas_msgs__msg__LaneData__FIELD_NAME__curvature[] = "curvature";
static char adas_msgs__msg__LaneData__FIELD_NAME__lateral_error_m[] = "lateral_error_m";
static char adas_msgs__msg__LaneData__FIELD_NAME__confidence[] = "confidence";
static char adas_msgs__msg__LaneData__FIELD_NAME__recovery_mode[] = "recovery_mode";

static rosidl_runtime_c__type_description__Field adas_msgs__msg__LaneData__FIELDS[] = {
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__header, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {std_msgs__msg__Header__TYPE_NAME, 19, 19},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__left_x, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__right_x, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__centre_x, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__curvature, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__lateral_error_m, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__confidence, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {adas_msgs__msg__LaneData__FIELD_NAME__recovery_mode, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription adas_msgs__msg__LaneData__REFERENCED_TYPE_DESCRIPTIONS[] = {
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
adas_msgs__msg__LaneData__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {adas_msgs__msg__LaneData__TYPE_NAME, 22, 22},
      {adas_msgs__msg__LaneData__FIELDS, 8, 8},
    },
    {adas_msgs__msg__LaneData__REFERENCED_TYPE_DESCRIPTIONS, 2, 2},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&std_msgs__msg__Header__EXPECTED_HASH, std_msgs__msg__Header__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[1].fields = std_msgs__msg__Header__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "std_msgs/Header header\n"
  "float32 left_x\n"
  "float32 right_x\n"
  "float32 centre_x\n"
  "float32 curvature\n"
  "float32 lateral_error_m\n"
  "float32 confidence\n"
  "string recovery_mode";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
adas_msgs__msg__LaneData__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {adas_msgs__msg__LaneData__TYPE_NAME, 22, 22},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 153, 153},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
adas_msgs__msg__LaneData__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[3];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 3, 3};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *adas_msgs__msg__LaneData__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *std_msgs__msg__Header__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
