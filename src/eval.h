#pragma once
#include<array>
#include "nnue.h"

namespace eval{
  inline int evaluate(
    const board& pos){
    return nnue::evaluate(pos);
  }

  constexpr std::array pt_values = {0,100,330,350,525,1100,8000};
  constexpr std::array piece_values = {
    0,pt_values[1],pt_values[2],pt_values[3],pt_values[4],pt_values[5],pt_values[6],0,
    0,pt_values[1],pt_values[2],pt_values[3],pt_values[4],pt_values[5],pt_values[6],0,
  };
}
