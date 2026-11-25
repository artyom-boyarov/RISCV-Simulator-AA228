#pragma once

#include "Faults.h"
#include <string>
#include <vector>

struct FaultConfig {
  FaultLocation location;
  MemoryFault memory{};
  CacheFault cache{};
  BranchResolutionFault branchResolution{};
};

// Throws std::runtime_error with file and line information on invalid input.
std::vector<FaultConfig> readFaultConfig(const std::string &path);
