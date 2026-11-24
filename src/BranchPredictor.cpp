/*
 * Created by He, Hao on 2019-3-25
 */

#include "BranchPredictor.h"
#include "Debug.h"


BranchPredictor::BranchPredictor() {
  for (int i = 0; i < PRED_BUF_SIZE; ++i) {
    this->predbuf[i] = WEAK_TAKEN;
  }
}

BranchPredictor::~BranchPredictor() {}

bool BranchPredictor::predict(uint32_t pc, uint32_t insttype, int64_t op1,
                              int64_t op2, int64_t offset) {
  const bool prediction = predictNormally(pc, insttype, op1, op2, offset);
  return faultsEnabled && faultDistribution(randomGenerator) ? !prediction
                                                               : prediction;
}

void BranchPredictor::enableFaults(const Fault &fault) {
  faultDistribution = std::bernoulli_distribution(fault.rate);
  faultsEnabled = true;
}

void BranchPredictor::disableFaults() { faultsEnabled = false; }

bool BranchPredictor::predictNormally(uint32_t pc, uint32_t insttype, int64_t op1,
                                      int64_t op2, int64_t offset) {
  switch (this->strategy) {
  case NT:
    return false;
  case AT: {
    return takenDistribution(randomGenerator);
  }
    
  case BTFNT: {
    if (offset >= 0) {
      return false;
    } else {
      return true;
    }
  }
  break;
  case BPB: {
    PredictorState state = this->predbuf[pc % PRED_BUF_SIZE];
    if (state == STRONG_TAKEN || state == WEAK_TAKEN) {
      return true;
    } else if (state == STRONG_NOT_TAKEN || state == WEAK_NOT_TAKEN) {
      return false;
    } else {
      dbgprintf("Strange Prediction Buffer!\n");
    }   
  }
  break;
  default:
    dbgprintf("Unknown Branch Perdiction Strategy!\n");
    break;
  }
  return false;
}

void BranchPredictor::update(uint32_t pc, bool branch) {
  int id = pc % PRED_BUF_SIZE;
  PredictorState state = this->predbuf[id];
  if (branch) {
    if (state == STRONG_NOT_TAKEN) {
      this->predbuf[id] = WEAK_NOT_TAKEN;
    } else if (state == WEAK_NOT_TAKEN) {
      this->predbuf[id] = WEAK_TAKEN;
    } else if (state == WEAK_TAKEN) {
      this->predbuf[id] = STRONG_TAKEN;
    } // do nothing if STRONG_TAKEN
  } else { // not branch
    if (state == STRONG_TAKEN) {
      this->predbuf[id] = WEAK_TAKEN;
    } else if (state == WEAK_TAKEN) {
      this->predbuf[id] = WEAK_NOT_TAKEN;
    } else if (state == WEAK_NOT_TAKEN) {
      this->predbuf[id] = STRONG_NOT_TAKEN;
    } // do noting if STRONG_NOT_TAKEN
  }
}

std::string BranchPredictor::strategyName() {
  switch (this->strategy) {
  case NT:
    return "Always Not Taken";
  case AT:
    return "Random Taken (70%)";
  case BTFNT:
    return "Back Taken Forward Not Taken";
  case BPB:
    return "Branch Prediction Buffer";
  default:
    dbgprintf("Unknown Branch Perdiction Strategy!\n");
    break;
  }
  return "error"; // should not go here
}
