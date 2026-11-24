/*
 * The branch perdiction module with the following strategies
 *   Randomly Taken (70% probability)
 *   Always Not Taken
 *   Backward Taken, Forward Not Taken
 *   Branch Prediction Buffer with 2bit history information
 * 
 * Created by He, Hao on 2019-3-25
 */

#ifndef BRANCH_PREDICTOR_H
#define BRANCH_PREDICTOR_H

#include <cstdint>
#include <random>
#include <string>

#include "Faults.h"

const int PRED_BUF_SIZE = 4096;

class BranchPredictor {
public:
  enum Strategy {
    AT, // Taken with 70% probability
    NT, // Always Not Taken
    BTFNT, // Backward Taken, Forward Not Taken
    BPB, // Branch Prediction Buffer with 2bit history information
  } strategy;

  BranchPredictor();
  ~BranchPredictor();

  bool predict(uint32_t pc, uint32_t insttype, int64_t op1, int64_t op2,
               int64_t offset);

  // For Branch Prediction Buffer 
  void update(uint32_t pc, bool branch);

  void enableFaults(const Fault &fault);
  void disableFaults();

  std::string strategyName();
  
private:
  bool predictNormally(uint32_t pc, uint32_t insttype, int64_t op1,
                       int64_t op2, int64_t offset);
  bool faultsEnabled = false;
  std::bernoulli_distribution faultDistribution{0.0};
  std::mt19937 randomGenerator{std::random_device{}()};
  std::bernoulli_distribution takenDistribution{0.7};
  enum PredictorState {
    STRONG_TAKEN = 0, WEAK_TAKEN = 1,
    STRONG_NOT_TAKEN = 3, WEAK_NOT_TAKEN = 2,
  } predbuf[PRED_BUF_SIZE]; // initial state: WEAK_TAKEN
};

#endif
