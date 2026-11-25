#pragma once

#include "Faults.h"
#include <random>

// Models a fault on the resolved taken/not-taken signal of conditional branches.
class BranchResolution {
public:
  void enableFaults(const BranchResolutionFault &fault) {
    type = fault.type;
    distribution = std::bernoulli_distribution(fault.rate);
    enabled = true;
  }
  void disableFaults() { enabled = false; }
  bool resolve(bool taken) {
    if (!enabled || !distribution(generator)) return taken;
    switch (type) {
    case FaultType::STUCK_AT_0: return false;
    case FaultType::STUCK_AT_1: return true;
    case FaultType::BIT_FLIP: return !taken;
    }
    return taken;
  }

private:
  bool enabled = false;
  FaultType type = FaultType::BIT_FLIP;
  std::mt19937 generator{std::random_device{}()};
  std::bernoulli_distribution distribution{0.0};
};
