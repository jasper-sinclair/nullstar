#pragma once
#include <atomic>
#include <memory>
#include "main.h"

enum node : u8{
  none_node, pvnode, cutnode, allnode
};

struct hash_data{
  int eval = 0;
  int score = 0;
  i32 depth = 0;
  node_type nt = none_node;
  u16 move = 0;
};

struct alignas(16) hash_entry{
  std::atomic<u64> key {0};
  std::atomic<u64> data {0};
};

static_assert(sizeof(hash_entry) == 16);
static_assert(alignof(hash_entry) == 16);
static_assert(std::atomic<u64>::is_always_lock_free);

constexpr size_t max_hash_size = 1 << 20;

struct hash_table{
  hash_entry* get(
    const u64 key){
    return &entries[key & mask];
  }

  bool probe(
    u64 key,
    hash_data& entry);
  static int score_from_hash(
    int score,
    i32 ply);
  static int score_to_hash(
    int score,
    i32 ply);
  std::unique_ptr<hash_entry[]> entries;
  u64 mask = 0;
  u64 size = 0;
  void clear();
  void save(
    u64 key,
    int score,
    int static_eval,
    u16 move,
    i32 depth,
    node_type nt);
  void set_size(
    u64 mb);
};
