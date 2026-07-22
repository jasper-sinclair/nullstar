#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

#include "../src/hash.h"

namespace{
  int failures = 0;

  void expect(
    const bool condition,
    const char* description){
    if (!condition){
      ++failures;
      std::cerr << "FAILED: " << description << '\n';
    }
  }

  int score_for(
    const u16 move){
    return static_cast<int>(move % 30001) - 15000;
  }

  int eval_for(
    const u16 move){
    return 15000 - static_cast<int>(move % 30001);
  }

  i32 depth_for(
    const u16 move){
    return move % 255;
  }

  node_type node_for(
    const u16 move){
    return static_cast<node_type>(1 + move % 3);
  }

  bool coherent(
    const hash_data& data){
    return data.score == score_for(data.move) &&
      data.eval == eval_for(data.move) &&
      data.depth == depth_for(data.move) &&
      data.nt == node_for(data.move);
  }
}

int main(){
  expect(sizeof(hash_entry) == 16,"hash entry must occupy 16 bytes");
  expect(alignof(hash_entry) == 16,"hash entry must be 16-byte aligned");
  expect(std::atomic<u64>::is_always_lock_free,"64-bit atomics must be lock-free");

  hash_table table;
  table.set_size(1);
  expect(table.size == 65536,"one MiB must contain 65536 packed entries");

  hash_data data;
  expect(!table.probe(0,data),"a cleared table must not report key zero");

  constexpr u64 key = 0x123456789ABCDEF0ULL;
  table.save(key,32255,-32001,65535,255,allnode);
  expect(table.probe(key,data),"saved extreme entry must probe successfully");
  expect(data.score == 32255,"positive packed score must round-trip");
  expect(data.eval == -32001,"negative packed evaluation must round-trip");
  expect(data.move == 65535,"packed move must round-trip");
  expect(data.depth == 255,"packed depth must round-trip");
  expect(data.nt == allnode,"packed node type must round-trip");

  table.save(key,100,200,1234,10,pvnode);
  table.save(key,300,400,4321,5,allnode);
  expect(table.probe(key,data),"preserved entry must remain available");
  expect(data.score == 100 && data.move == 1234 && data.depth == 10,
    "shallower non-PV entry must not replace a deeper entry");

  table.save(key,300,400,4321,7,allnode);
  expect(table.probe(key,data),"replacement entry must probe successfully");
  expect(data.score == 300 && data.move == 4321 && data.depth == 7,
    "entry within the replacement margin must replace");

  table.save(key,-500,-600,2222,0,pvnode);
  expect(table.probe(key,data),"PV replacement must probe successfully");
  expect(data.score == -500 && data.move == 2222 && data.depth == 0 && data.nt == pvnode,
    "PV entry must always replace");

  const u64 colliding_key = key + table.size;
  table.save(colliding_key,700,800,3333,1,cutnode);
  expect(!table.probe(key,data),"a colliding replacement must invalidate the old key");
  expect(table.probe(colliding_key,data),"a colliding replacement must retain the new key");

  hash_entry* slot = table.get(colliding_key);
  slot->data.fetch_xor(1,std::memory_order_relaxed);
  expect(!table.probe(colliding_key,data),
    "changing the packed move must invalidate the complete-entry guard");

  table.clear();
  expect(!table.probe(colliding_key,data),"clear must invalidate populated entries");

  constexpr u64 shared_key = 0xD6E8FEB86659FD93ULL;
  constexpr int thread_count = 16;
  constexpr int iterations = 200000;
  std::atomic<int> incoherent_reads = 0;
  std::atomic<u64> successful_reads = 0;
  std::vector<std::thread> threads;
  threads.reserve(thread_count);

  for (int thread = 0; thread < thread_count; ++thread){
    threads.emplace_back([&,thread]{
      for (int iteration = 0; iteration < iterations; ++iteration){
        const u16 move = static_cast<u16>(1 +
          (iteration * 251 + thread * 4051) % 65534);
        table.save(shared_key,score_for(move),eval_for(move),move,
          depth_for(move),node_for(move));
        hash_data observed;
        if (table.probe(shared_key,observed)){
          successful_reads.fetch_add(1,std::memory_order_relaxed);
          if (!coherent(observed))
            incoherent_reads.fetch_add(1,std::memory_order_relaxed);
        }
      }
    });
  }

  for (auto& thread : threads) thread.join();
  expect(successful_reads.load(std::memory_order_relaxed) > 0,
    "concurrency stress must obtain successful probes");
  expect(incoherent_reads.load(std::memory_order_relaxed) == 0,
    "concurrency stress must never expose a torn payload");

  for (const int score : {-31999,-31744,-100,0,100,31744,31999}){
    for (const i32 ply : {0,1,127,255}){
      const int stored = hash_table::score_to_hash(score,ply);
      const int restored = hash_table::score_from_hash(stored,ply);
      expect(restored == score,"mate-distance score conversion must round-trip");
    }
  }

  std::cout << "Entry bytes: " << sizeof(hash_entry) << '\n';
  std::cout << "Entries per MiB: " << table.size << '\n';
  std::cout << "Successful concurrent probes: "
    << successful_reads.load(std::memory_order_relaxed) << '\n';
  std::cout << "Incoherent concurrent probes: "
    << incoherent_reads.load(std::memory_order_relaxed) << '\n';
  std::cout << "Failures: " << failures << '\n';
  return failures == 0 ? 0 : 1;
}
