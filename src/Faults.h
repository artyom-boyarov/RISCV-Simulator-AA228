#pragma once
#include <cstdint>

enum class FaultLocation {
    CACHE,
    MEMORY_CONTROLLER,
    BRANCH_PREDICTOR,
};
enum class FaultType {
    BIT_FLIP,
    STUCK_AT_0,
    STUCK_AT_1,
};

enum class CacheFaultField {
    VALID,
    MODIFIED,
    TAG,
    ID,
};

struct Fault {
    FaultLocation location;
    double rate;
};

struct CacheFault : public Fault {
    uint32_t addr;
    bool isWrite;
    bool isHit;
    CacheFaultField field;
    uint8_t bitPosition;
    FaultType type;
};

struct MemoryFault : public Fault {
    uint8_t bitPosition;
    FaultType type;
};
