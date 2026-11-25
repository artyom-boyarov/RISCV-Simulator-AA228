#pragma once
#include <cstdint>

enum class FaultLocation {
    CACHE,
    MEMORY_CONTROLLER,
    BRANCH_RESOLUTION,
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
    double rate = 1.0;
};

struct CacheFault : public Fault {
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

struct BranchResolutionFault : public Fault {
    FaultType type;
};
