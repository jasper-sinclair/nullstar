#include "hash.h"
#include <algorithm>
#include <bit>
#include <cassert>
#include <limits>
#include <memory>
#include "main.h"

namespace{
  constexpr unsigned score_shift = 16;
  constexpr unsigned eval_shift = 32;
  constexpr unsigned depth_shift = 48;
  constexpr unsigned node_shift = 56;

  u16 pack_i16(
    const int value){
    constexpr int minimum = std::numeric_limits<i16>::min();
    constexpr int maximum = std::numeric_limits<i16>::max();
    const i16 packed = static_cast<i16>(std::clamp(value,minimum,maximum));
    return std::bit_cast<u16>(packed);
  }

  int unpack_i16(
    const u64 data,
    const unsigned shift){
    return std::bit_cast<i16>(static_cast<u16>(data >> shift));
  }

  u64 pack(
    const int score,
    const int static_eval,
    const u16 move,
    const i32 depth,
    const node_type nt){
    assert(depth >= 0 && depth < max_depth);
    assert(nt >= pvnode && nt <= allnode);
    return static_cast<u64>(move) |
      (static_cast<u64>(pack_i16(score)) << score_shift) |
      (static_cast<u64>(pack_i16(static_eval)) << eval_shift) |
      (static_cast<u64>(static_cast<u8>(std::clamp(depth,0,255))) << depth_shift) |
      (static_cast<u64>(nt) << node_shift);
  }

  hash_data unpack(
    const u64 data){
    return {
      .eval = unpack_i16(data,eval_shift),
      .score = unpack_i16(data,score_shift),
      .depth = static_cast<i32>(static_cast<u8>(data >> depth_shift)),
      .nt = static_cast<node_type>(static_cast<u8>(data >> node_shift)),
      .move = static_cast<u16>(data)
    };
  }
}

void hash_table::set_size(
  const u64 mb){
  const u64 bytes = mb * 1024 * 1024;
  const u64 max_size = bytes / sizeof(hash_entry);
  size = 1;
  for (;;){
    const u64 new_size = 2 * size;
    if (new_size > max_size) break;
    size = new_size;
  }
  mask = size - 1;
  entries = std::make_unique<hash_entry[]>(size);
  clear();
}

void hash_table::clear(){
  for (u64 i = 0; i < size; ++i){
    entries[i].data.store(0,std::memory_order_relaxed);
    entries[i].key.store(0,std::memory_order_relaxed);
  }
}

bool hash_table::probe(
  const u64 key,
  hash_data& entry){
  const hash_entry* slot = get(key);
  const u64 stored_key = slot->key.load(std::memory_order_acquire);
  const u64 data = slot->data.load(std::memory_order_relaxed);
  if ((stored_key ^ data) == key){
    entry = unpack(data);
    if (entry.nt >= pvnode && entry.nt <= allnode) return true;
  }
  entry = {};
  return false;
}

void hash_table::save(
  const u64 key,
  const int score,
  const int static_eval,
  const u16 move,
  const i32 depth,
  const node_type nt){
  hash_data previous;
  const bool hit = probe(key,previous);
  if (nt == pvnode || !hit || depth + 4 > previous.depth){
    hash_entry* slot = get(key);
    const u64 data = pack(score,static_eval,move,depth,nt);
    slot->data.store(data,std::memory_order_relaxed);
    slot->key.store(key ^ data,std::memory_order_release);
  }
}

int hash_table::score_to_hash(
  const int score,
  const i32 ply){
  return score >= min_mate_score
    ? score + ply
    : score <= -min_mate_score
    ? score - ply
    : score;
}

int hash_table::score_from_hash(
  const int score,
  const i32 ply){
  return score >= min_mate_score
    ? score - ply
    : score <= -min_mate_score
    ? score + ply
    : score;
}
