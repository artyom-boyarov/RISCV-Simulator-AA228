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

  {
    MemoryManager instructions;
    check(instructions.addPage(base), "allocate instruction page");
    instructions.setInt(base, 0x12345678);
    instructions.setInt(base + 8, 0xabcdef01);
    instructions.setInt(base + 0x100, 0x11223344);
    instructions.setInt(base + 0x108, 0x55667788);
    MemoryFault fetchFault{};
    fetchFault.location = FaultLocation::MEMORY_CONTROLLER;
    fetchFault.bitPosition = 3;
    fetchFault.type = FaultType::STUCK_AT_1;
    instructions.enableFaults(fetchFault);
    check(instructions.getInstruction(base) == 0x12345678,
          "uncached instruction fetch bypasses faults");
    check(instructions.getInt(base + 0x100) == 0x55667788,
          "fault restored after instruction fetch");
    instructions.disableFaults();
    check(instructions.getInstruction(base) == 0x12345678 &&
          instructions.getInt(base + 0x100) == 0x11223344,
          "instruction fetch preserves disabled state");

    Cache::Policy instructionPolicy{64, 64, 1, 1, 0, 1};
    Cache instructionCache(&instructions, instructionPolicy);
    instructions.setCache(&instructionCache);
    instructions.enableFaults(fetchFault);
    check(instructions.getInstruction(base) == 0x12345678,
          "instruction cache fill bypasses memory faults");
    check(instructions.getInt(base + 0x100) == 0x55667788,
          "data cache fill retains memory faults");
  }

  {
    MemoryManager instructions;
    check(instructions.addPage(base), "allocate cache instruction page");
    instructions.setInt(base, 0x12345678);
    Cache::Policy policy{64, 64, 1, 1, 0, 1};
    Cache lower(&instructions, policy);
    Cache upper(&instructions, policy, &lower);
    instructions.setCache(&upper);
    CacheFault validFault{};
    validFault.location = FaultLocation::CACHE;
    validFault.field = CacheFaultField::VALID;
    validFault.type = FaultType::STUCK_AT_0;
    upper.enableFaults(validFault);
    lower.enableFaults(validFault);
    check(instructions.getInstruction(base) == 0x12345678,
          "instruction fetch suppresses cache faults at every level");
    check(!upper.inCache(base) && !lower.inCache(base),
          "instruction fetch restores cache faults");
    const uint32_t missesBefore = upper.statistics.numMiss;
    check(instructions.getInt(base) == 0x12345678 &&
          upper.statistics.numMiss > missesBefore,
          "data reads still observe cache faults after instruction fetch");
    upper.disableFaults();
    lower.disableFaults();
    check(upper.inCache(base) && lower.inCache(base),
          "fetch filled both caches without metadata faults");
    check(instructions.getInstruction(base) == 0x12345678 && upper.inCache(base),
          "instruction fetch preserves disabled cache fault state");
  }

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
  fault.rate = 0.5;
  memory.enableFaults(fault);
  int flipped = 0;
  for (int i = 0; i < 1000; ++i) {
    const uint8_t value = memory.getByte(base);
    check(value == 0xab || value == 0xcd, "bit flip targets one offset bit");
    flipped += value == 0xcd;
  }
  check(flipped > 400 && flipped < 600, "bit flips occur approximately half the time");
  fault.rate = 1.0;
  memory.enableFaults(fault);
  check(memory.getByte(base) == 0xcd, "bit flip at 100 percent");
  fault.type = FaultType::STUCK_AT_1;
  fault.rate = 0.5;
  memory.enableFaults(fault);
  int forced = 0;
  for (int i = 0; i < 1000; ++i) forced += memory.getByte(base) == 0xcd;
  check(forced > 400 && forced < 600, "stuck-at fault applies approximately half the time");
  memory.disableFaults();
  check(memory.getByte(base) == 0xab, "disable restores normal addressing");

  Cache::Policy policy{64, 64, 1, 1, 0, 1};
  Cache cache(&memory, policy);
  memory.setCache(&cache);
  fault.bitPosition = 3;
  fault.type = FaultType::STUCK_AT_1;
  fault.rate = 1.0;
  memory.enableFaults(fault);
  check(memory.getByte(base) == 0xcd, "cache fill uses faulty backing memory");
  memory.disableFaults();
  check(memory.getByte(base) == 0xcd, "disable does not invalidate cached data");
  std::puts("memory fault tests passed");
}
