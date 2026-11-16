// runner.cpp - back-test driver for the MQL5 emulator.
// Build: see build.sh (the translated EA is injected with -DEA_SOURCE="file").
#include "mql5.h"
#include EA_SOURCE
#include "emu_impl.h"

struct SymPreset { const char* name; const char* base; const char* quote; int digits; double contract; double spread; double comm; double swl; double sws; };
static const SymPreset PRESETS[] = {
  // spread in points, commission per lot round trip (USD), swaps per lot per night (USD, conservative)
  {"XAUUSD", "XAU", "USD", 2, 100, 25, 7.0, -35.0, -5.0},
  {"EURUSD", "EUR", "USD", 5, 100000, 3, 7.0, -7.0, -2.0},
  {"GBPUSD", "GBP", "USD", 5, 100000, 7, 7.0, -6.0, -3.0},
  {"AUDUSD", "AUD", "USD", 5, 100000, 5, 7.0, -4.0, -3.0},
  {"USDCAD", "USD", "CAD", 5, 100000, 7, 7.0, -3.0, -4.0},
  {"USDJPY", "USD", "JPY", 3, 100000, 5, 7.0, -2.0, -10.0},
};

static datetime parse_date(const std::string& s) {
  MqlDateTime d{}; int y = 0, m = 0, dd = 0, hh = 0, mi = 0;
  if (sscanf(s.c_str(), "%d-%d-%d %d:%d", &y, &m, &dd, &hh, &mi) < 3) { fprintf(stderr, "bad date %s\n", s.c_str()); exit(2); }
  d.year = y; d.mon = m; d.day = dd; d.hour = hh; d.min = mi; return StructToTime(d);
}

int main(int argc, char** argv) {
  std::string data, trades_out, equity_out, log_out; std::vector<std::pair<std::string, std::string>> sets;
  std::string from_s, to_s, stop_s, save_state, load_state; bool spread_set = false, comm_set = false, swap_set = false;
  double spread = 0, comm = 0, swl = 0, sws = 0;
  for (int i = 1; i < argc; i++) {
    std::string a = argv[i];
    auto next = [&]() -> std::string { if (i + 1 >= argc) { fprintf(stderr, "missing value for %s\n", a.c_str()); exit(2); } return argv[++i]; };
    if (a == "--data") data = next();
    else if (a == "--symbol") E.cfg.symbol = next();
    else if (a == "--from") from_s = next();
    else if (a == "--to") to_s = next();
    else if (a == "--deposit") E.cfg.deposit = std::stod(next());
    else if (a == "--leverage") E.cfg.leverage = std::stod(next());
    else if (a == "--spread") { spread = std::stod(next()); spread_set = true; }
    else if (a == "--commission") { comm = std::stod(next()); comm_set = true; }
    else if (a == "--swap") { swl = std::stod(next()); sws = std::stod(next()); swap_set = true; }
    else if (a == "--stops-level") E.cfg.stops_level = std::stol(next());
    else if (a == "--freeze-level") E.cfg.freeze_level = std::stol(next());
    else if (a == "--filling") {
      std::string f = next(); E.cfg.filling_flags = 0; E.cfg.allow_return = false;
      if (f.find("FOK") != std::string::npos) E.cfg.filling_flags |= SYMBOL_FILLING_FOK;
      if (f.find("IOC") != std::string::npos) E.cfg.filling_flags |= SYMBOL_FILLING_IOC;
      if (f.find("RETURN") != std::string::npos) E.cfg.allow_return = true;
    }
    else if (a == "--vmin") E.cfg.vmin = std::stod(next());
    else if (a == "--vstep") E.cfg.vstep = std::stod(next());
    else if (a == "--netting") E.cfg.hedging = false;
    else if (a == "--requote-prob") E.cfg.requote_prob = std::stod(next());
    else if (a == "--ignore-sltp-on-open") E.cfg.ignore_sltp_on_open = true;
    else if (a == "--reject-sltp") E.cfg.reject_sltp = true;
    else if (a == "--algo-off") E.cfg.algo_allowed = false;
    else if (a == "--live") E.cfg.tester = false;
    else if (a == "--visual") E.cfg.visual = true;
    else if (a == "--news") E.cfg.news_file = next();
    else if (a == "--warmup-days") E.cfg.warmup_days = std::stol(next());
    else if (a == "--trades") trades_out = next();
    else if (a == "--stop-at") stop_s = next();
    else if (a == "--save-state") save_state = next();
    else if (a == "--load-state") load_state = next();
    else if (a == "--equity") equity_out = next();
    else if (a == "--log") log_out = next();
    else if (a == "--quiet") E.cfg.quiet = true;
    else if (a == "--set") { std::string kv = next(); auto p = kv.find('='); sets.push_back({kv.substr(0, p), kv.substr(p + 1)}); }
    else { fprintf(stderr, "unknown option %s\n", a.c_str()); return 2; }
  }
  bool found = false;
  for (auto& p : PRESETS) if (E.cfg.symbol == p.name) {
    found = true; E.cfg.base = p.base; E.cfg.quote = p.quote; E.cfg.digits = p.digits; E.cfg.contract = p.contract;
    E.cfg.spread_points = p.spread; E.cfg.commission_rt = p.comm; E.cfg.swap_long = p.swl; E.cfg.swap_short = p.sws;
  }
  if (!found) { fprintf(stderr, "unknown symbol %s\n", E.cfg.symbol.c_str()); return 2; }
  if (spread_set) E.cfg.spread_points = spread;
  if (comm_set) E.cfg.commission_rt = comm;
  if (swap_set) { E.cfg.swap_long = swl; E.cfg.swap_short = sws; }
  for (auto& kv : sets) {
    auto it = InputReg::table().find(kv.first);
    if (it == InputReg::table().end()) { fprintf(stderr, "unknown input %s\n", kv.first.c_str()); return 2; }
    it->second(kv.second);
  }
  if (!log_out.empty()) E.log = fopen(log_out.c_str(), "w");
  E.point = std::pow(10.0, -E.cfg.digits);
  _Symbol = string(E.cfg.symbol); _Point = E.point; _Digits = E.cfg.digits; _Period = PERIOD_M5;
  E.balance = E.cfg.deposit;
  if (!load_state.empty()) {
    std::ifstream sf(load_state); std::string tag;
    if (!sf) { fprintf(stderr, "cannot read state %s\n", load_state.c_str()); return 2; }
    while (sf >> tag) {
      if (tag == "balance") sf >> E.balance;
      else if (tag == "next_ticket") sf >> E.next_ticket;
      else if (tag == "gv") { std::string k; double v; sf >> k >> v; E.gv[k] = v; }
      else if (tag == "pos") {
        EmuPos p; std::string cm; sf >> p.ticket >> p.identifier >> p.type >> p.volume >> p.open >> p.sl >> p.tp >> p.time >> p.time_msc
           >> p.magic >> p.swap >> p.initVolume >> p.initSL >> p.commission >> cm; p.comment = string(cm); E.pos.push_back(p);
      } else if (tag == "deal") {
        EmuDeal d; std::string cm; sf >> d.ticket >> d.order >> d.time >> d.time_msc >> d.type >> d.entry >> d.magic >> d.position_id
           >> d.volume >> d.price >> d.profit >> d.commission >> d.swap >> d.fee >> d.sl >> d.tp >> d.reason >> cm; d.comment = string(cm); E.deals.push_back(d);
      } else if (tag == "realized") { ulong t; double v; sf >> t >> v; g_realized[t] = v; }
      else if (tag == "risk") { ulong t; double v; sf >> t >> v; g_risk[t] = v; }
      else if (tag == "trade") {
        EmuTradeRec r; std::string ex; sf >> r.ticket >> r.type >> r.open_time >> r.close_time >> r.volume >> r.open >> r.close >> r.initSL
           >> r.tp >> r.profit >> r.riskMoney >> ex; r.exit_reason = string(ex); E.trades.push_back(r);
      }
    }
  }

  // news file (live mode): "YYYY-MM-DD HH:MM,CUR,importance,name"
  if (!E.cfg.news_file.empty()) {
    std::ifstream nf(E.cfg.news_file); std::string line;
    while (std::getline(nf, line)) {
      if (line.empty() || line[0] == '#') continue;
      std::stringstream ss(line); std::string t, c, imp, name;
      std::getline(ss, t, ','); std::getline(ss, c, ','); std::getline(ss, imp, ','); std::getline(ss, name);
      E.news.push_back(EmuNews{parse_date(t), string(c), std::stoi(imp), string(name)});
    }
  }

  // load M1 data
  struct M1 { datetime t; double o, h, l, c; };
  std::vector<M1> m1; m1.reserve(2000000);
  { FILE* f = fopen(data.c_str(), "r"); if (!f) { fprintf(stderr, "cannot open %s\n", data.c_str()); return 2; }
    char line[256]; if (!fgets(line, sizeof line, f)) return 2;
    while (fgets(line, sizeof line, f)) { M1 b; long t; if (sscanf(line, "%ld,%lf,%lf,%lf,%lf", &t, &b.o, &b.h, &b.l, &b.c) == 5) { b.t = t; m1.push_back(b); } }
    fclose(f); }
  if (m1.empty()) { fprintf(stderr, "no data\n"); return 2; }
  datetime start = from_s.empty() ? m1.front().t + E.cfg.warmup_days * 86400 : parse_date(from_s);
  datetime end = to_s.empty() ? m1.back().t + 60 : parse_date(to_s);
  datetime stop_at = stop_s.empty() ? 0 : parse_date(stop_s);
  E.cfg.from = start; E.cfg.to = end;

  int init_rc = -1; E.peak_equity = E.cfg.deposit; E.peak_balance = E.cfg.deposit;
  long n_ticks = 0;
  for (size_t bi = 0; bi < m1.size() && !E.stopped; bi++) {
    const M1& b = m1[bi];
    if (b.t >= end) break;
    if (stop_at > 0 && b.t >= stop_at && E.started) { E.stopped = true; break; }
    double p[4]; p[0] = b.o;
    if (std::fabs(b.h - b.o) < std::fabs(b.o - b.l)) { p[1] = b.h; p[2] = b.l; } else { p[1] = b.l; p[2] = b.h; }
    p[3] = b.c;
    for (int k = 0; k < 4; k++) {
      if (k > 0 && p[k] == p[k - 1]) continue;
      E.on_tick_price(b.t + k * 15, p[k], k == 0);
      if (b.t < start) continue;
      if (!E.started) {
        E.started = true;
        std::feclearexcept(FE_ALL_EXCEPT);
        init_rc = OnInit();
        if (init_rc != INIT_SUCCEEDED) { fprintf(stderr, "OnInit failed with code %d\n", init_rc); return 3; }
        E.last_day = b.t - b.t % 86400;
        continue;
      }
      // daily swap at server midnight (triple on the night to Thursday)
      datetime day = b.t - b.t % 86400;
      if (day != E.last_day) {
        MqlDateTime d; TimeToStruct(day, d);
        int mult = d.day_of_week == 4 ? 3 : 1;
        for (auto& ps : E.pos) ps.swap += (ps.type == 0 ? E.cfg.swap_long : E.cfg.swap_short) * ps.volume * mult;
        E.last_day = day;
      }
      E.check_stops();
#ifdef HAS_ONTIMER
      if (E.timer_sec > 0 && E.tick.time >= E.next_timer) { E.next_timer = E.tick.time + E.timer_sec; OnTimer(); }
#endif
      OnTick();
      n_ticks++;
      double eq = E.equity();
      if (eq > E.peak_equity) E.peak_equity = eq;
      double dd = E.peak_equity - eq;
      if (dd > E.max_dd) E.max_dd = dd;
      if (E.peak_equity > 0 && dd / E.peak_equity * 100 > E.max_dd_rel) E.max_dd_rel = dd / E.peak_equity * 100;
      if (E.balance > E.peak_balance) E.peak_balance = E.balance;
      if (E.peak_balance - E.balance > E.max_bdd) { E.max_bdd = E.peak_balance - E.balance; E.max_bdd_rel = E.max_bdd / E.peak_balance * 100; }
      if (E.equity_curve.empty() || E.tick.time - E.equity_curve.back().first >= 3600) E.equity_curve.push_back({E.tick.time, eq});
    }
  }
  if (!E.started) { fprintf(stderr, "test range contains no data\n"); return 3; }
  if (stop_at > 0 && E.stopped) {  // simulated terminal shutdown: keep positions, persist state
    OnDeinit(9);
    std::ofstream sf(save_state);
    sf.precision(10);
    sf << "balance " << E.balance << "\nnext_ticket " << E.next_ticket << "\n";
    for (auto& kv : E.gv) sf << "gv " << kv.first << " " << kv.second << "\n";
    for (auto& p : E.pos) sf << "pos " << p.ticket << " " << p.identifier << " " << p.type << " " << p.volume << " " << p.open << " " << p.sl
       << " " << p.tp << " " << p.time << " " << p.time_msc << " " << p.magic << " " << p.swap << " " << p.initVolume << " " << p.initSL
       << " " << p.commission << " " << (p.comment.s.empty() ? "-" : p.comment.s) << "\n";
    for (auto& d : E.deals) sf << "deal " << d.ticket << " " << d.order << " " << d.time << " " << d.time_msc << " " << d.type << " " << d.entry
       << " " << d.magic << " " << d.position_id << " " << d.volume << " " << d.price << " " << d.profit << " " << d.commission << " " << d.swap
       << " " << d.fee << " " << d.sl << " " << d.tp << " " << d.reason << " " << (d.comment.s.empty() ? "-" : d.comment.s) << "\n";
    for (auto& kv : g_realized) sf << "realized " << kv.first << " " << kv.second << "\n";
    for (auto& kv : g_risk) sf << "risk " << kv.first << " " << kv.second << "\n";
    for (auto& r : E.trades) sf << "trade " << r.ticket << " " << r.type << " " << r.open_time << " " << r.close_time << " " << r.volume << " "
       << r.open << " " << r.close << " " << r.initSL << " " << r.tp << " " << r.profit << " " << r.riskMoney << " " << r.exit_reason.s << "\n";
    printf("state saved at %s with %zu open position(s), balance %.2f\n", fmt_time(E.tick.time).c_str(), E.pos.size(), E.balance);
    return 0;
  }
  // end of test: close remaining positions like the MT5 tester
  while (!E.pos.empty()) E.close_volume(E.pos.size() - 1, E.pos.back().volume, E.pos.back().type == 0 ? E.tick.bid : E.tick.ask, DEAL_REASON_CLIENT, string("end of test"));
  double criterion = 0;
#ifdef HAS_ONTESTER
  criterion = OnTester();
#endif
  OnDeinit(0);
  if (std::fetestexcept(FE_INVALID)) fprintf(stderr, "warning: invalid floating point operation (NaN) occurred during the run\n");

  // ---------------- report
  double gp = 0, gl = 0, sumR = 0; long w = 0, l = 0, nR = 0; double maxR = -1e9, minR = 1e9;
  std::map<int, std::pair<long, double>> by_year; std::map<std::string, long> exits;
  for (auto& t : E.trades) {
    if (t.profit > 0) { gp += t.profit; w++; } else { gl -= t.profit; l++; }
    if (t.riskMoney > 0) { double r = t.profit / t.riskMoney; sumR += r; nR++; maxR = std::max(maxR, r); minR = std::min(minR, r); }
    MqlDateTime d; TimeToStruct(t.open_time, d); by_year[d.year].first++; by_year[d.year].second += t.profit;
    exits[t.exit_reason.s]++;
  }
  long n = (long)E.trades.size();
  printf("==== IABot emulator report: %s  %s -> %s ====\n", E.cfg.symbol.c_str(), fmt_time(start, false).c_str(), fmt_time(E.tick.time, false).c_str());
  printf("ticks processed       : %ld\n", n_ticks);
  printf("initial deposit       : %.2f\n", E.cfg.deposit);
  printf("final balance         : %.2f  (net %+.2f, %+.2f%%)\n", E.balance, E.balance - E.cfg.deposit, (E.balance / E.cfg.deposit - 1) * 100);
  printf("trades                : %ld  (won %ld, lost %ld, win rate %.1f%%)\n", n, w, l, n ? 100.0 * w / n : 0.0);
  printf("profit factor         : %.2f\n", gl > 0 ? gp / gl : 0.0);
  printf("avg trade (R)         : %+.3f   best %+.2fR  worst %+.2fR\n", nR ? sumR / nR : 0.0, nR ? maxR : 0.0, nR ? minR : 0.0);
  printf("max equity drawdown   : %.2f (%.2f%%)\n", E.max_dd, E.max_dd_rel);
  printf("requests / modifies / rejected : %ld / %ld / %ld\n", E.n_requests, E.n_modify, E.n_rejected);
  printf("exit reasons          :"); for (auto& e : exits) printf(" %s=%ld", e.first.c_str(), e.second); printf("\n");
  printf("events                :"); for (auto& e : E.event_counts) printf(" %s=%ld", e.first.c_str(), e.second); printf("\n");
  printf("by year (trades, net) :"); for (auto& y : by_year) printf(" %d:(%ld, %+.0f)", y.first, y.second.first, y.second.second); printf("\n");
  printf("OnTester criterion    : %.4f\n", criterion);
  if (!E.cfg.tester || E.cfg.visual) printf("last chart comment    :\n%s\n", E.last_comment.c_str());
  if (!trades_out.empty()) {
    FILE* f = fopen(trades_out.c_str(), "w");
    fprintf(f, "ticket,type,open_time,close_time,volume,open,close,init_sl,tp,profit,risk_money,R,exit\n");
    for (auto& t : E.trades)
      fprintf(f, "%lu,%s,%s,%s,%.2f,%.5f,%.5f,%.5f,%.5f,%.2f,%.2f,%.3f,%s\n", t.ticket, t.type == 0 ? "BUY" : "SELL",
              fmt_time(t.open_time).c_str(), fmt_time(t.close_time).c_str(), t.volume, t.open, t.close, t.initSL, t.tp,
              t.profit, t.riskMoney, t.riskMoney > 0 ? t.profit / t.riskMoney : 0.0, t.exit_reason.c_str());
    fclose(f);
  }
  if (!equity_out.empty()) {
    FILE* f = fopen(equity_out.c_str(), "w"); fprintf(f, "time,equity\n");
    for (auto& e : E.equity_curve) fprintf(f, "%ld,%.2f\n", e.first, e.second);
    fclose(f);
  }
  if (E.log != stdout) fclose(E.log);
  return 0;
}
