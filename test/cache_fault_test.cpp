#include "Cache.h"

#include <cstdio>
#include <stdexcept>

static void check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

static CacheFault fault(CacheFaultField field, FaultType type, uint8_t bit = 0) {
  CacheFault result{};
  result.location = FaultLocation::CACHE;
  result.field = field;
  result.type = type;
  result.bitPosition = bit;
  return result;
}

int main() {
  MemoryManager memory;
  const uint32_t a = 0x1000, b = 0x1080;
  check(memory.addPage(a), "allocate page");
  memory.setByteNoCache(a, 0x11);
  memory.setByteNoCache(b, 0x22);
  Cache::Policy policy{128, 64, 2, 1, 0, 1};

  {
    Cache cache(&memory, policy);
    check(cache.getByte(a) == 0x11, "initial fill");
    cache.enableFaults(fault(CacheFaultField::VALID, FaultType::STUCK_AT_0));
    check(cache.getByte(a) == 0x11 && cache.statistics.numMiss == 2,
          "invalid metadata causes miss without abort");
    cache.disableFaults();
    check(cache.getByte(a) == 0x11 && cache.statistics.numHit == 1,
          "disabled fault restores stored valid bit");
  }
  {
    Cache cache(&memory, policy);
    cache.enableFaults(fault(CacheFaultField::VALID, FaultType::STUCK_AT_1));
    check(cache.getByte(0) == 0 && cache.statistics.numHit == 1,
          "stuck valid bit can cause false hit");
  }
  {
    Cache cache(&memory, policy);
    cache.getByte(a);
    cache.enableFaults(fault(CacheFaultField::TAG, FaultType::STUCK_AT_1));
    check(cache.getByte(b) == 0x11 && cache.statistics.numHit == 1,
          "faulty tag causes false hit");
    cache.disableFaults();
    check(cache.getByte(a) == 0x11, "disabled tag fault");
  }
  {
    Cache cache(&memory, policy);
    cache.getByte(a);
    cache.enableFaults(fault(CacheFaultField::ID, FaultType::STUCK_AT_1));
    check(cache.getByte(a) == 0x11 && cache.statistics.numMiss == 2,
          "faulty id causes miss without abort");
    cache.disableFaults();
    check(cache.getByte(a) == 0x11 && cache.statistics.numHit == 1,
          "disabled id fault");
  }
  {
    Cache cache(&memory, policy);
    cache.setByte(a, 0x99);
    cache.enableFaults(fault(CacheFaultField::MODIFIED, FaultType::STUCK_AT_0));
    cache.getByte(b);
    cache.disableFaults();
    check(memory.getByteNoCache(a) == 0x11, "stuck clean loses dirty writeback");
  }
  {
    Cache cache(&memory, policy);
    cache.getByte(a);
    cache.enableFaults(fault(CacheFaultField::MODIFIED, FaultType::STUCK_AT_1));
    memory.setByteNoCache(a, 0x77);
    cache.getByte(b);
    cache.disableFaults();
    check(memory.getByteNoCache(a) == 0x11, "stuck dirty writes back clean line");
  }
  {
    Cache cache(&memory, policy);
    cache.getByte(a);
    CacheFault flip = fault(CacheFaultField::TAG, FaultType::BIT_FLIP);
    flip.rate = 0.5;
    cache.enableFaults(flip);
    int hits = 0;
    for (int i = 0; i < 1000; ++i) hits += cache.inCache(a);
    check(hits > 400 && hits < 600, "tag flips approximately half of reads");
    flip.rate = 1.0;
    cache.enableFaults(flip);
    check(!cache.inCache(a), "tag flips every read at 100 percent");
    CacheFault stuck = fault(CacheFaultField::TAG, FaultType::STUCK_AT_1);
    stuck.rate = 0.5;
    cache.enableFaults(stuck);
    hits = 0;
    for (int i = 0; i < 1000; ++i) hits += cache.inCache(a);
    check(hits > 400 && hits < 600, "stuck tag fault applies approximately half the time");
    cache.disableFaults();
    check(cache.inCache(a), "disable restores tag");
  }
  std::puts("cache fault tests passed");
}
