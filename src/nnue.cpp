#include "nnue.h"
#include <algorithm>
#include <cstring>
#include <iostream>
#include "bitboard.h"
#include "net.h"

namespace nnue{
  namespace{
    struct network{
      i16 in_weights[768][l1_size];
      i16 in_biases[l1_size];
      i16 out_weights[2][l1_size];
      i16 out_bias;
    };

    network net_storage;
    const network* net = nullptr;

    int feature_index(
      const int pc,
      const int sq,
      const int perspective){
      const int piece_color = make(pc);
      const int piece_type = ptmake(pc);
      const int index_color = piece_color != perspective;
      const int index_piece = piece_type - 1;
      const int relative_sq = perspective == white ? sq : sq ^ 56;
      return 384 * index_color + 64 * index_piece + relative_sq;
    }
  }

  bool init(){
    if (g_default_net_size != sizeof(network)){
      std::cerr << "Invalid embedded NNUE size: expected " << sizeof(network)
        << ", got " << g_default_net_size << '\n';
      return false;
    }

    std::memcpy(&net_storage,g_default_net,sizeof(net_storage));
    net = &net_storage;
    return true;
  }

  void add_feature(
    i16 acc[2][l1_size],
    const int pc,
    const int sq){
    for (int p = 0; p < 2; ++p){
      const int idx = feature_index(pc,sq,p);
      for (int i = 0; i < l1_size; ++i)
        acc[p][i] = static_cast<i16>(acc[p][i] + net->in_weights[idx][i]);
    }
  }

  void sub_feature(
    i16 acc[2][l1_size],
    const int pc,
    const int sq){
    for (int p = 0; p < 2; ++p){
      const int idx = feature_index(pc,sq,p);
      for (int i = 0; i < l1_size; ++i)
        acc[p][i] = static_cast<i16>(acc[p][i] - net->in_weights[idx][i]);
    }
  }

  void refresh_accumulator(
    const board& pos,
    i16 acc[2][l1_size]){
    for (int p = 0; p < 2; ++p)
      for (int i = 0; i < l1_size; ++i)
        acc[p][i] = net->in_biases[i];

    for (u8 sq = 0; sq < 64; ++sq){
      const int pc = pos.piece_on(sq);
      if (!pc) continue;

      add_feature(acc,pc,sq);
    }
  }

  namespace{
    int evaluate_from_acc(
      const board& pos,
      const i16 acc[2][l1_size]){
      const int stm = pos.side_to_move;
      const int nstm = !stm;

      int64_t score = 0;

      for (int i = 0; i < l1_size; ++i){
        int x = acc[stm][i];
        x = std::clamp(x,0,quantization_scale);
        score += static_cast<int64_t>(x) * x * net->out_weights[0][i];
      }

      for (int i = 0; i < l1_size; ++i){
        int x = acc[nstm][i];
        x = std::clamp(x,0,quantization_scale);
        score += static_cast<int64_t>(x) * x * net->out_weights[1][i];
      }

      constexpr int64_t activation_scale =
        static_cast<int64_t>(quantization_scale) * quantization_scale;
      constexpr int64_t network_scale =
        activation_scale * quantization_scale;

      score += static_cast<int64_t>(net->out_bias) * activation_scale;
      return static_cast<int>(score * centipawn_scale / network_scale);
    }
  }

  int evaluate(
    const board& pos){
    return evaluate_from_acc(pos,pos.st->acc);
  }

  bool verify_accumulator(
    const board& pos){
    alignas(32) i16 expected[2][l1_size];
    refresh_accumulator(pos,expected);
    return std::equal(&expected[0][0],&expected[0][0] + 2 * l1_size,
      &pos.st->acc[0][0]);
  }
}
