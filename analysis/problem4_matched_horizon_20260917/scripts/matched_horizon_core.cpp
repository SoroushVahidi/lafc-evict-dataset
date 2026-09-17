#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr int kHorizons[4] = {16, 32, 64, 128};
constexpr int kPairs[4][2] = {{16, 32}, {32, 64}, {64, 128}, {16, 128}};

struct HorizonState {
  long long decisions = 0;
  long long all_tied = 0;
  long double sum_random_optimal = 0.0L;
  long double sum_random_regret = 0.0L;
  long double sum_optimal_fraction = 0.0L;
  long double sum_loss_range = 0.0L;
  long double sum_strict_density = 0.0L;
};

struct PairState {
  long long n = 0;
  long long tied_to_tied = 0;
  long long tied_to_disc = 0;
  long long disc_to_tied = 0;
  long long disc_to_disc = 0;
  long long info_increase = 0;
  long long info_decrease = 0;
  long long info_unchanged = 0;
  long double sum_delta_random_regret = 0.0L;
  long double sum_delta_optimal_fraction = 0.0L;
  long double sum_delta_loss_range = 0.0L;
};

struct MonoState {
  long long n = 0;
  long long h16_to_h128_increase = 0;
  long long h16_to_h128_decrease = 0;
  long long h16_to_h128_unchanged = 0;
  long long adjacent_all_nondecreasing = 0;
  long long adjacent_all_nonincreasing = 0;
  long long adjacent_mixed = 0;
};

struct DecisionMetrics {
  bool all_tied[4] = {false, false, false, false};
  double random_regret[4] = {0.0, 0.0, 0.0, 0.0};
  double optimal_fraction[4] = {0.0, 0.0, 0.0, 0.0};
  double loss_range[4] = {0.0, 0.0, 0.0, 0.0};
  double strict_density[4] = {0.0, 0.0, 0.0, 0.0};
  double random_optimal[4] = {0.0, 0.0, 0.0, 0.0};
};

std::string csv_escape(const std::string& s) {
  if (s.find_first_of(",\"\n") == std::string::npos) return s;
  std::string out = "\"";
  for (char c : s) {
    if (c == '"') out += "\"\"";
    else out += c;
  }
  out += '"';
  return out;
}

std::string extract_item_id(const std::string& line) {
  const std::string key = "\"item_id\":";
  size_t pos = line.find(key);
  if (pos == std::string::npos) {
    throw std::runtime_error("item_id not found in JSONL line");
  }
  pos = line.find('"', pos + key.size());
  if (pos == std::string::npos) {
    throw std::runtime_error("opening quote for item_id not found");
  }
  ++pos;
  std::string out;
  bool esc = false;
  for (; pos < line.size(); ++pos) {
    char c = line[pos];
    if (esc) {
      out.push_back(c);
      esc = false;
    } else if (c == '\\') {
      esc = true;
    } else if (c == '"') {
      return out;
    } else {
      out.push_back(c);
    }
  }
  throw std::runtime_error("closing quote for item_id not found");
}

std::vector<int> load_trace_ids(const std::string& path) {
  std::ifstream in(path);
  if (!in) {
    throw std::runtime_error("could not open trace: " + path);
  }
  std::unordered_map<std::string, int> ids;
  ids.reserve(60000);
  std::vector<int> reqs;
  reqs.reserve(50000);
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty()) continue;
    std::string item = extract_item_id(line);
    auto it = ids.find(item);
    if (it == ids.end()) {
      int id = static_cast<int>(ids.size()) + 1;
      ids.emplace(std::move(item), id);
      reqs.push_back(id);
    } else {
      reqs.push_back(it->second);
    }
  }
  return reqs;
}

int horizon_index(int h) {
  for (int i = 0; i < 4; ++i) {
    if (kHorizons[i] == h) return i;
  }
  return -1;
}

void update_pair(PairState& st, const DecisionMetrics& m, int left_idx, int right_idx) {
  st.n += 1;
  const bool lt = m.all_tied[left_idx];
  const bool rt = m.all_tied[right_idx];
  if (lt && rt) st.tied_to_tied += 1;
  else if (lt && !rt) st.tied_to_disc += 1;
  else if (!lt && rt) st.disc_to_tied += 1;
  else st.disc_to_disc += 1;

  const double delta_info = m.random_regret[right_idx] - m.random_regret[left_idx];
  if (delta_info > 1e-12) st.info_increase += 1;
  else if (delta_info < -1e-12) st.info_decrease += 1;
  else st.info_unchanged += 1;
  st.sum_delta_random_regret += delta_info;
  st.sum_delta_optimal_fraction += (m.optimal_fraction[right_idx] - m.optimal_fraction[left_idx]);
  st.sum_delta_loss_range += (m.loss_range[right_idx] - m.loss_range[left_idx]);
}

void update_mono(MonoState& st, const DecisionMetrics& m) {
  st.n += 1;
  const double d = m.random_regret[3] - m.random_regret[0];
  if (d > 1e-12) st.h16_to_h128_increase += 1;
  else if (d < -1e-12) st.h16_to_h128_decrease += 1;
  else st.h16_to_h128_unchanged += 1;

  bool nondec = true;
  bool noninc = true;
  for (int i = 0; i < 3; ++i) {
    if (m.random_regret[i + 1] + 1e-12 < m.random_regret[i]) nondec = false;
    if (m.random_regret[i + 1] > m.random_regret[i] + 1e-12) noninc = false;
  }
  if (nondec) st.adjacent_all_nondecreasing += 1;
  else if (noninc) st.adjacent_all_nonincreasing += 1;
  else st.adjacent_mixed += 1;
}

DecisionMetrics compute_decision_metrics(
    const std::vector<int>& reqs,
    int t,
    const std::vector<int>& base_cache,
    int incoming,
    std::vector<int>& stamp,
    std::vector<int>& pos,
    int& stamp_id,
    std::vector<int>& page,
    std::vector<int>& prev,
    std::vector<int>& next) {
  const int cap = static_cast<int>(base_cache.size());
  const int max_future = std::min(128, static_cast<int>(reqs.size()) - t - 1);
  DecisionMetrics out;
  std::array<std::vector<int>, 4> losses;
  for (int i = 0; i < 4; ++i) losses[i].reserve(cap);

  for (int evict_idx = 0; evict_idx < cap; ++evict_idx) {
    ++stamp_id;
    if (stamp_id == std::numeric_limits<int>::max()) {
      std::fill(stamp.begin(), stamp.end(), 0);
      stamp_id = 1;
    }
    int slot = 0;
    for (int i = 0; i < cap; ++i) {
      if (i == evict_idx) continue;
      page[slot] = base_cache[i];
      stamp[page[slot]] = stamp_id;
      pos[page[slot]] = slot;
      ++slot;
    }
    page[cap - 1] = incoming;
    stamp[incoming] = stamp_id;
    pos[incoming] = cap - 1;
    for (int i = 0; i < cap; ++i) {
      prev[i] = i - 1;
      next[i] = (i == cap - 1) ? -1 : i + 1;
    }
    int head = 0;
    int tail = cap - 1;
    int misses = 0;
    int loss_at[4] = {0, 0, 0, 0};

    for (int step = 1; step <= max_future; ++step) {
      const int q = reqs[t + step];
      int qslot = -1;
      if (q >= 0 && q < static_cast<int>(stamp.size()) && stamp[q] == stamp_id) {
        qslot = pos[q];
      }
      if (qslot >= 0) {
        if (qslot != tail) {
          const int a = prev[qslot];
          const int b = next[qslot];
          if (a >= 0) next[a] = b;
          else head = b;
          if (b >= 0) prev[b] = a;
          prev[qslot] = tail;
          next[qslot] = -1;
          next[tail] = qslot;
          tail = qslot;
        }
      } else {
        misses += 1;
        const int evict_slot = head;
        const int old_page = page[evict_slot];
        stamp[old_page] = 0;
        head = next[evict_slot];
        if (head >= 0) prev[head] = -1;
        page[evict_slot] = q;
        stamp[q] = stamp_id;
        pos[q] = evict_slot;
        prev[evict_slot] = tail;
        next[evict_slot] = -1;
        next[tail] = evict_slot;
        tail = evict_slot;
      }
      for (int hi = 0; hi < 4; ++hi) {
        if (step == kHorizons[hi]) loss_at[hi] = misses;
      }
    }
    for (int hi = 0; hi < 4; ++hi) {
      if (max_future < kHorizons[hi]) loss_at[hi] = misses;
      losses[hi].push_back(loss_at[hi]);
    }
  }

  const long double denom = static_cast<long double>(cap);
  const long double pair_denom = static_cast<long double>(cap) * static_cast<long double>(cap - 1) / 2.0L;
  for (int hi = 0; hi < 4; ++hi) {
    int min_loss = losses[hi][0];
    int max_loss = losses[hi][0];
    long long sum = 0;
    int hist[129] = {0};
    for (int loss : losses[hi]) {
      min_loss = std::min(min_loss, loss);
      max_loss = std::max(max_loss, loss);
      sum += loss;
      if (loss >= 0 && loss <= 128) hist[loss] += 1;
    }
    int opt_count = 0;
    long long equal_pairs = 0;
    for (int v = 0; v <= 128; ++v) {
      if (v == min_loss) opt_count = hist[v];
      equal_pairs += static_cast<long long>(hist[v]) * static_cast<long long>(hist[v] - 1) / 2;
    }
    const long double mean = static_cast<long double>(sum) / denom;
    out.all_tied[hi] = (min_loss == max_loss);
    out.random_regret[hi] = static_cast<double>(mean - min_loss);
    out.optimal_fraction[hi] = static_cast<double>(static_cast<long double>(opt_count) / denom);
    out.random_optimal[hi] = out.optimal_fraction[hi];
    out.loss_range[hi] = static_cast<double>(max_loss - min_loss);
    out.strict_density[hi] = pair_denom > 0.0L
      ? static_cast<double>((pair_denom - static_cast<long double>(equal_pairs)) / pair_denom)
      : 0.0;
  }
  return out;
}

void add_horizon_state(HorizonState& st, const DecisionMetrics& m, int hi) {
  st.decisions += 1;
  if (m.all_tied[hi]) st.all_tied += 1;
  st.sum_random_optimal += m.random_optimal[hi];
  st.sum_random_regret += m.random_regret[hi];
  st.sum_optimal_fraction += m.optimal_fraction[hi];
  st.sum_loss_range += m.loss_range[hi];
  st.sum_strict_density += m.strict_density[hi];
}

struct CellResult {
  std::string family;
  std::string trace_name;
  int capacity = 0;
  std::array<HorizonState, 4> horizons;
  std::array<PairState, 4> pairs;
  MonoState mono;
  int min_t = std::numeric_limits<int>::max();
  int max_t = -1;
};

CellResult process_cell(
    const std::string& trace_path,
    const std::string& family,
    const std::string& trace_name,
    int capacity) {
  const std::vector<int> reqs = load_trace_ids(trace_path);
  int max_id = 0;
  for (int id : reqs) max_id = std::max(max_id, id);
  std::vector<int> stamp(max_id + 2, 0), pos(max_id + 2, -1), page(capacity), prev(capacity), next(capacity);
  int stamp_id = 0;
  std::vector<int> cache;
  cache.reserve(capacity);

  CellResult result;
  result.family = family;
  result.trace_name = trace_name;
  result.capacity = capacity;

  for (int t = 0; t < static_cast<int>(reqs.size()); ++t) {
    const int pid = reqs[t];
    auto it = std::find(cache.begin(), cache.end(), pid);
    if (it != cache.end()) {
      int v = *it;
      cache.erase(it);
      cache.push_back(v);
      continue;
    }
    if (static_cast<int>(cache.size()) < capacity) {
      cache.push_back(pid);
      continue;
    }
    DecisionMetrics metrics = compute_decision_metrics(reqs, t, cache, pid, stamp, pos, stamp_id, page, prev, next);
    result.min_t = std::min(result.min_t, t);
    result.max_t = std::max(result.max_t, t);
    for (int hi = 0; hi < 4; ++hi) add_horizon_state(result.horizons[hi], metrics, hi);
    for (int pi = 0; pi < 4; ++pi) update_pair(result.pairs[pi], metrics, horizon_index(kPairs[pi][0]), horizon_index(kPairs[pi][1]));
    update_mono(result.mono, metrics);
    cache.erase(cache.begin());
    cache.push_back(pid);
  }
  return result;
}

void write_cell_metrics(const std::string& out_path, const std::vector<CellResult>& cells) {
  std::ofstream out(out_path);
  out << std::setprecision(17);
  out << "trace_family,trace_name,capacity,horizon,n_decisions,min_decision_t,max_decision_t,"
      << "all_tied_count,all_tied_fraction,discriminative_fraction,random_optimal_probability,"
      << "expected_random_regret,mean_optimal_set_fraction,mean_loss_range,mean_strict_preference_density\n";
  for (const auto& cell : cells) {
    for (int hi = 0; hi < 4; ++hi) {
      const HorizonState& s = cell.horizons[hi];
      const long double n = static_cast<long double>(s.decisions);
      out << csv_escape(cell.family) << "," << csv_escape(cell.trace_name) << "," << cell.capacity << "," << kHorizons[hi] << ","
          << s.decisions << "," << cell.min_t << "," << cell.max_t << ","
          << s.all_tied << "," << static_cast<double>(s.all_tied / n) << ","
          << static_cast<double>(1.0L - s.all_tied / n) << ","
          << static_cast<double>(s.sum_random_optimal / n) << ","
          << static_cast<double>(s.sum_random_regret / n) << ","
          << static_cast<double>(s.sum_optimal_fraction / n) << ","
          << static_cast<double>(s.sum_loss_range / n) << ","
          << static_cast<double>(s.sum_strict_density / n) << "\n";
    }
  }
}

void write_pair_metrics(const std::string& out_path, const std::vector<CellResult>& cells) {
  std::ofstream out(out_path);
  out << std::setprecision(17);
  out << "trace_family,trace_name,capacity,pair,n_decisions,tied_to_tied,tied_to_discriminative,"
      << "discriminative_to_tied,discriminative_to_discriminative,info_increase,info_decrease,"
      << "info_unchanged,mean_delta_expected_random_regret,mean_delta_optimal_set_fraction,mean_delta_loss_range\n";
  for (const auto& cell : cells) {
    for (int pi = 0; pi < 4; ++pi) {
      const PairState& s = cell.pairs[pi];
      const long double n = static_cast<long double>(s.n);
      std::ostringstream pair;
      pair << "H" << kPairs[pi][0] << "_to_H" << kPairs[pi][1];
      out << csv_escape(cell.family) << "," << csv_escape(cell.trace_name) << "," << cell.capacity << ","
          << pair.str() << "," << s.n << "," << s.tied_to_tied << "," << s.tied_to_disc << ","
          << s.disc_to_tied << "," << s.disc_to_disc << "," << s.info_increase << ","
          << s.info_decrease << "," << s.info_unchanged << ","
          << static_cast<double>(s.sum_delta_random_regret / n) << ","
          << static_cast<double>(s.sum_delta_optimal_fraction / n) << ","
          << static_cast<double>(s.sum_delta_loss_range / n) << "\n";
    }
  }
}

void write_mono_metrics(const std::string& out_path, const std::vector<CellResult>& cells) {
  std::ofstream out(out_path);
  out << "trace_family,trace_name,capacity,n_decisions,h16_to_h128_info_increase,h16_to_h128_info_decrease,"
      << "h16_to_h128_info_unchanged,adjacent_all_nondecreasing,adjacent_all_nonincreasing,adjacent_mixed\n";
  for (const auto& cell : cells) {
    const MonoState& s = cell.mono;
    out << csv_escape(cell.family) << "," << csv_escape(cell.trace_name) << "," << cell.capacity << ","
        << s.n << "," << s.h16_to_h128_increase << "," << s.h16_to_h128_decrease << ","
        << s.h16_to_h128_unchanged << "," << s.adjacent_all_nondecreasing << ","
        << s.adjacent_all_nonincreasing << "," << s.adjacent_mixed << "\n";
  }
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 6 || ((argc - 2) % 4) != 0) {
    std::cerr << "usage: " << argv[0] << " OUT_DIR family trace_name capacity trace_path [...]\n";
    return 2;
  }
  const std::string out_dir = argv[1];
  std::vector<CellResult> cells;
  for (int i = 2; i < argc; i += 4) {
    const std::string family = argv[i];
    const std::string trace_name = argv[i + 1];
    const int capacity = std::stoi(argv[i + 2]);
    const std::string trace_path = argv[i + 3];
    std::cerr << "PROCESS " << family << " cap=" << capacity << " trace=" << trace_path << std::endl;
    cells.push_back(process_cell(trace_path, family, trace_name, capacity));
    std::cerr << "DONE " << family << " cap=" << capacity
              << " decisions=" << cells.back().horizons[0].decisions << std::endl;
  }
  write_cell_metrics(out_dir + "/matched_cell_horizon_metrics_raw.csv", cells);
  write_pair_metrics(out_dir + "/matched_cell_pair_transitions_raw.csv", cells);
  write_mono_metrics(out_dir + "/matched_cell_monotonicity_raw.csv", cells);
  return 0;
}
