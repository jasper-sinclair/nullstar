#pragma once
#include "main.h"
struct board;

namespace nnue{
  constexpr int input_size = 768;
  constexpr int l1_size = 256;
  bool init();
  void refresh_accumulator(
    const board& pos,
    i16 acc[2][l1_size]);
  void add_feature(
    i16 acc[2][l1_size],
    int pc,
    int sq);
  void sub_feature(
    i16 acc[2][l1_size],
    int pc,
    int sq);
  int evaluate(
    const board& pos);
  [[nodiscard]] bool verify_accumulator(
    const board& pos);
}
