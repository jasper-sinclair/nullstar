#pragma once
#include <atomic>
#include <chrono>
#include "main.h"

struct chrono{
  std::atomic_bool stop {false};
  bool use_depth_limit = false;
  bool use_match_limit = false;
  bool use_move_limit = false;
  bool use_node_limit = false;
  i32 depth_limit = 0;
  time_point begin = 0;
  time_point match_time_limit = 0;
  time_point move_time_limit = 0;
  time_point time_to_use = 0;
  time_point time[n_colors] {};
  time_point inc[n_colors] {};
  [[nodiscard]] time_point elapsed() const;
  static time_point now();
  u64 node_limit = 0;
  void reset();
  void init_time(
    bool side_to_move);
  void start();
  void update(
    u64 node_cnt);
};
