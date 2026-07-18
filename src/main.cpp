#include "attack.h"
#include "nnue.h"
#include "uci.h"

int main(){
  attack::init();
  if (!nnue::init()) return 1;
  search::init();
  zobrist::init();
  uci::init();
}
