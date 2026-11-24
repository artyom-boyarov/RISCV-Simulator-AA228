#include "BranchPredictor.h"

#include <stdexcept>

static void check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

static bool predict(BranchPredictor &predictor, int offset = 4) {
  return predictor.predict(0, 0, 0, 0, offset);
}

int main() {
  BranchPredictor predictor;
  predictor.strategy = BranchPredictor::NT;
  check(!predict(predictor), "faults start disabled");

  Fault fault{};
  fault.location = FaultLocation::BRANCH_PREDICTOR;
  fault.rate = 1.0;
  predictor.enableFaults(fault);
  check(predict(predictor), "invert not-taken prediction");
  predictor.strategy = BranchPredictor::BTFNT;
  check(!predict(predictor, -4) && predict(predictor, 4),
        "invert both backward and forward predictions");
  predictor.strategy = BranchPredictor::BPB;
  check(!predict(predictor), "invert buffer prediction");
  predictor.update(0, false);
  check(predict(predictor), "buffer update uses actual branch outcome");
  predictor.disableFaults();
  check(!predict(predictor), "disable restores normal prediction and preserves state");

  predictor.strategy = BranchPredictor::NT;
  fault.rate = 0.0;
  predictor.enableFaults(fault);
  check(!predict(predictor), "zero rate leaves prediction unchanged");
  fault.rate = 0.5;
  predictor.enableFaults(fault);
  int taken = 0;
  for (int i = 0; i < 1000; ++i) taken += predict(predictor);
  check(taken > 400 && taken < 600, "configured probability applies per prediction");

}
