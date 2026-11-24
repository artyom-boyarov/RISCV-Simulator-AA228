#include "MemoryManager.h"

#include <cstdio>
#include <stdexcept>

static void check(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

int main() {
  MemoryManager memory;
  const uint32_t base = 0x1000;
  check(memory.addPage(base), "allocate page");
  check(memory.addPage(base + 0x1000), "allocate adjacent page");
  memory.setByte(base, 0x12);
  memory.setByte(base + 8, 0x34);
  memory.setByte(base + 0x800, 0x56);
  memory.setByte(base + 0x1000, 0x78);

  MemoryFault fault{};
  fault.location = FaultLocation::MEMORY_CONTROLLER;
  fault.bitPosition = 3;
  fault.type = FaultType::STUCK_AT_0;
  memory.enableFaults(fault);
  check(memory.getByte(base + 8) == 0x12, "stuck-at-0 read");
  memory.setByte(base + 8, 0xab);
  memory.disableFaults();
  check(memory.getByte(base) == 0xab && memory.getByte(base + 8) == 0x34,
        "stuck-at-0 write and disable");

  fault.type = FaultType::STUCK_AT_1;
  memory.enableFaults(fault);
  check(memory.getByteNoCache(base) == 0x34, "stuck-at-1 read");
  memory.setByteNoCache(base, 0xcd);
  memory.disableFaults();
  check(memory.getByteNoCache(base) == 0xab &&
        memory.getByteNoCache(base + 8) == 0xcd, "stuck-at-1 write");

  fault.bitPosition = 11;
  memory.enableFaults(fault);
  check(memory.getByte(base) == 0x56 && memory.getByte(base + 0x1000) == 0,
        "highest offset bit does not change page");
  memory.disableFaults();
  check(memory.getByte(base + 0x1000) == 0x78, "adjacent page unchanged");

  fault.bitPosition = 3;
  fault.type = FaultType::BIT_FLIP;
  memory.enableFaults(fault);
  int flipped = 0;
  for (int i = 0; i < 1000; ++i) {
    const uint8_t value = memory.getByte(base);
    check(value == 0xab || value == 0xcd, "bit flip targets one offset bit");
    flipped += value == 0xcd;
  }
  check(flipped > 400 && flipped < 600, "bit flips occur approximately half the time");
  memory.disableFaults();
  check(memory.getByte(base) == 0xab, "disable restores normal addressing");

  Cache::Policy policy{64, 64, 1, 1, 0, 1};
  Cache cache(&memory, policy);
  memory.setCache(&cache);
  fault.bitPosition = 3;
  fault.type = FaultType::STUCK_AT_1;
  memory.enableFaults(fault);
  check(memory.getByte(base) == 0xcd, "cache fill uses faulty backing memory");
  memory.disableFaults();
  check(memory.getByte(base) == 0xcd, "disable does not invalidate cached data");
  std::puts("memory fault tests passed");
}
