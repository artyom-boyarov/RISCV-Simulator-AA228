#include "FaultConfig.h"

#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>

namespace {
std::string trim(const std::string &s) {
  const auto first = s.find_first_not_of(" \t\r\n");
  if (first == std::string::npos) return "";
  return s.substr(first, s.find_last_not_of(" \t\r\n") - first + 1);
}

FaultType parseType(const std::string &value) {
  if (value == "STUCK_AT_0") return FaultType::STUCK_AT_0;
  if (value == "STUCK_AT_1") return FaultType::STUCK_AT_1;
  if (value == "BIT_FLIP") return FaultType::BIT_FLIP;
  throw std::runtime_error("fault must be STUCK_AT_0, STUCK_AT_1, or BIT_FLIP");
}

unsigned parseBit(const std::string &value) {
  if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
    throw std::runtime_error("bit must be a decimal integer");
  unsigned long bit;
  try { bit = std::stoul(value); }
  catch (const std::exception &) { throw std::runtime_error("bit is out of range"); }
  return static_cast<unsigned>(bit);
}

FaultConfig makeConfig(const std::map<std::string, std::string> &properties) {
  auto require = [&](const std::string &key) -> std::string {
    auto it = properties.find(key);
    if (it == properties.end()) throw std::runtime_error("missing property '" + key + "'");
    return it->second;
  };
  const std::string type = require("type");
  FaultConfig result{};
  if (type == "memory") {
    result.location = FaultLocation::MEMORY_CONTROLLER;
    result.memory.location = result.location;
    result.memory.type = parseType(require("fault"));
    result.memory.bitPosition = parseBit(require("bit"));
  } else if (type == "cache") {
    result.location = FaultLocation::CACHE;
    result.cache.location = result.location;
    result.cache.type = parseType(require("fault"));
    const std::string field = require("field");
    if (field == "valid") result.cache.field = CacheFaultField::VALID;
    else if (field == "modified") result.cache.field = CacheFaultField::MODIFIED;
    else if (field == "tag") result.cache.field = CacheFaultField::TAG;
    else if (field == "id") result.cache.field = CacheFaultField::ID;
    else throw std::runtime_error("field must be valid, modified, tag, or id");
    result.cache.bitPosition = parseBit(require("bit"));
  } else if (type == "branch") {
    result.location = FaultLocation::BRANCH_PREDICTOR;
    result.branch.location = result.location;
    const std::string rate = require("rate");
    size_t consumed = 0;
    try { result.branch.rate = std::stod(rate, &consumed); }
    catch (const std::exception &) { throw std::runtime_error("rate must be a number between 0 and 1"); }
    if (consumed != rate.size())
      throw std::runtime_error("rate must be a number between 0 and 1");
  } else {
    throw std::runtime_error("type must be memory, cache, or branch");
  }
  return result;
}
}

std::vector<FaultConfig> readFaultConfig(const std::string &path) {
  std::ifstream input(path);
  if (!input) throw std::runtime_error("cannot open fault file '" + path + "'");
  std::vector<FaultConfig> result;
  std::map<std::string, std::string> properties;
  unsigned lineNumber = 0, blockLine = 0;
  auto finish = [&]() {
    if (properties.empty()) return;
    try {
      FaultConfig config = makeConfig(properties);
      result.push_back(config);
    } catch (const std::exception &e) {
      throw std::runtime_error(path + ":" + std::to_string(blockLine) + ": " + e.what());
    }
    properties.clear();
  };
  std::string line;
  while (std::getline(input, line)) {
    ++lineNumber;
    line = trim(line.substr(0, line.find('#')));
    if (line.empty()) continue;
    const auto equal = line.find('=');
    if (equal == std::string::npos) throw std::runtime_error(path + ":" + std::to_string(lineNumber) + ": expected key = value");
    const std::string key = trim(line.substr(0, equal));
    const std::string value = trim(line.substr(equal + 1));
    if (key.empty() || value.empty()) throw std::runtime_error(path + ":" + std::to_string(lineNumber) + ": empty key or value");
    if (key == "type") { finish(); blockLine = lineNumber; }
    if (properties.empty() && key != "type") throw std::runtime_error(path + ":" + std::to_string(lineNumber) + ": first property must be type");
    properties[key] = value;
  }
  if (input.bad()) throw std::runtime_error("error reading fault file '" + path + "'");
  finish();
  if (result.empty()) throw std::runtime_error(path + ": no faults specified");
  return result;
}
