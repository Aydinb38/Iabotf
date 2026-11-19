// emu_impl.h - implementation of the MQL5 emulator API and trading engine.
#pragma once
#include <cfenv>

Emu E;
string _Symbol;
ENUM_TIMEFRAMES _Period = PERIOD_M5;
double _Point = 0.01;
int _Digits = 2;

static std::string fmt_time(datetime t, bool secs = true) {
  time_t tt = (time_t)t; struct tm g; gmtime_r(&tt, &g);
  char b[40];
  if (secs) snprintf(b, sizeof b, "%04d.%02d.%02d %02d:%02d:%02d", g.tm_year + 1900, g.tm_mon + 1, g.tm_mday, g.tm_hour, g.tm_min, g.tm_sec);
  else snprintf(b, sizeof b, "%04d.%02d.%02d %02d:%02d", g.tm_year + 1900, g.tm_mon + 1, g.tm_mday, g.tm_hour, g.tm_min);
  return b;
}

void emu_print_line(const std::string& s) {
  if (E.cfg.quiet) return;
  std::fprintf(E.log, "%s  %s\n", fmt_time(E.tick.time).c_str(), s.c_str());
}

// ------------------------------------------------------------------ format
std::string emu_format(const std::string& fmt, const std::vector<FmtArg>& args) {
  std::string out; size_t ai = 0;
  auto need = [&](const char* what) -> const FmtArg& {
    if (ai >= args.size()) emu_fatal(std::string("StringFormat: too few arguments for format \"") + fmt + "\" (" + what + ")");
    return args[ai++];
  };
  for (size_t i = 0; i < fmt.size(); i++) {
    char c = fmt[i];
    if (c != '%') { out += c; continue; }
    if (i + 1 < fmt.size() && fmt[i + 1] == '%') { out += '%'; i++; continue; }
    std::string spec = "%"; size_t j = i + 1;
    while (j < fmt.size() && std::strchr("-+ #0", fmt[j])) spec += fmt[j++];
    while (j < fmt.size() && (std::isdigit((uchar)fmt[j]) || fmt[j] == '*')) {
      if (fmt[j] == '*') { const FmtArg& a = need("*"); spec += std::to_string(a.k == 0 ? a.i : (long long)a.u); j++; }
      else spec += fmt[j++];
    }
    if (j < fmt.size() && fmt[j] == '.') {
      spec += fmt[j++];
      while (j < fmt.size() && (std::isdigit((uchar)fmt[j]) || fmt[j] == '*')) {
        if (fmt[j] == '*') { const FmtArg& a = need(".*"); spec += std::to_string(a.k == 0 ? a.i : (long long)a.u); j++; }
        else spec += fmt[j++];
      }
    }
    bool is64 = false;
    if (fmt.compare(j, 3, "I64") == 0) { is64 = true; j += 3; }
    else if (fmt.compare(j, 3, "I32") == 0) { j += 3; }
    else while (j < fmt.size() && std::strchr("hlLqjzt", fmt[j])) { if (fmt[j] == 'l') is64 = true; j++; }
    if (j >= fmt.size()) emu_fatal("StringFormat: truncated format spec in \"" + fmt + "\"");
    char conv = fmt[j]; i = j;
    char b[512];
    const FmtArg& a = need(&conv);
    switch (conv) {
      case 'd': case 'i': {
        if (a.k > 1) emu_fatal("StringFormat: %d used with a non-integer argument in \"" + fmt + "\"");
        long long v = a.k == 0 ? a.i : (long long)a.u;
        if (!is64 && (v > INT_MAX || v < INT_MIN)) emu_fatal("StringFormat: 64-bit value printed with %d (use %I64d) in \"" + fmt + "\"");
        snprintf(b, sizeof b, (spec + "lld").c_str(), v); out += b; break;
      }
      case 'u': case 'x': case 'X': case 'o': case 'c': {
        if (a.k > 1) emu_fatal("StringFormat: %u/%x used with a non-integer argument in \"" + fmt + "\"");
        unsigned long long v = a.k == 1 ? a.u : (unsigned long long)a.i;
        if (conv == 'c') { snprintf(b, sizeof b, (spec + "c").c_str(), (int)v); out += b; break; }
        if (!is64 && v > UINT_MAX) emu_fatal("StringFormat: 64-bit value printed with %u (use %I64u) in \"" + fmt + "\"");
        snprintf(b, sizeof b, (spec + "ll" + conv).c_str(), v); out += b; break;
      }
      case 'f': case 'F': case 'e': case 'E': case 'g': case 'G': case 'a': case 'A': {
        if (a.k != 2) emu_fatal("StringFormat: floating format used with a non-double argument in \"" + fmt + "\"");
        snprintf(b, sizeof b, (spec + conv).c_str(), a.d); out += b; break;
      }
      case 's': {
        if (a.k != 3) emu_fatal("StringFormat: %s used with a non-string argument in \"" + fmt + "\"");
        snprintf(b, sizeof b, (spec + "s").c_str(), a.s.c_str()); out += b; break;
      }
      default: emu_fatal(std::string("StringFormat: unsupported conversion %") + conv);
    }
  }
  if (ai != args.size()) emu_fatal("StringFormat: too many arguments for format \"" + fmt + "\"");
  return out;
}

// ------------------------------------------------------------------ time
bool TimeToStruct(datetime t, MqlDateTime& s) {
  time_t tt = (time_t)t; struct tm g; gmtime_r(&tt, &g);
  s.year = g.tm_year + 1900; s.mon = g.tm_mon + 1; s.day = g.tm_mday; s.hour = g.tm_hour; s.min = g.tm_min;
  s.sec = g.tm_sec; s.day_of_week = g.tm_wday; s.day_of_year = g.tm_yday;
  return true;
}
datetime StructToTime(MqlDateTime& s) {
  struct tm g; std::memset(&g, 0, sizeof g);
  g.tm_year = s.year - 1900; g.tm_mon = s.mon - 1; g.tm_mday = s.day; g.tm_hour = s.hour; g.tm_min = s.min; g.tm_sec = s.sec;
  return (datetime)timegm(&g);
}
string TimeToString(datetime t, int mode) {
  time_t tt = (time_t)t; struct tm g; gmtime_r(&tt, &g); char b[40]; std::string r;
  if (mode & TIME_DATE) { snprintf(b, sizeof b, "%04d.%02d.%02d", g.tm_year + 1900, g.tm_mon + 1, g.tm_mday); r += b; }
  if (mode & (TIME_MINUTES | TIME_SECONDS)) {
    if (!r.empty()) r += " ";
    if (mode & TIME_SECONDS) snprintf(b, sizeof b, "%02d:%02d:%02d", g.tm_hour, g.tm_min, g.tm_sec);
    else snprintf(b, sizeof b, "%02d:%02d", g.tm_hour, g.tm_min);
    r += b;
  }
  return string(r);
}
int PeriodSeconds(ENUM_TIMEFRAMES tf) {
  if (tf == PERIOD_CURRENT) tf = _Period;
  int v = (int)tf;
  if (v < 16384) return v * 60;
  if (v == PERIOD_W1) return 604800;
  if (v == PERIOD_MN1) return 2592000;
  return (v - 16384) * 3600;
}

// ------------------------------------------------------------------ info
static void check_symbol(const string& s) {
  if (s.s != E.cfg.symbol) emu_fatal("symbol '" + s.s + "' is not available in the emulator");
}
bool SymbolSelect(const string& sym, bool) { return sym.s == E.cfg.symbol || E.find_aux(sym.s) != nullptr; }
// number of extra-symbol M1 bars already closed at the current emulated time
static size_t aux_visible(const EmuAux& a) {
  datetime now = E.tick.time;
  size_t lo = 0, hi = a.m1.size();
  while (lo < hi) { size_t mid = (lo + hi) / 2; if (a.m1[mid].t + 60 <= now) lo = mid + 1; else hi = mid; }
  return lo;
}
static std::vector<EmuBar>& aux_tf(EmuAux& a, int tf) {
  if (tf == PERIOD_CURRENT) tf = _Period;
  auto it = a.tf.find(tf);
  if (it != a.tf.end()) return it->second;
  long sec = PeriodSeconds((ENUM_TIMEFRAMES)tf);
  std::vector<EmuBar> bars; std::vector<size_t> first;
  for (size_t i = 0; i < a.m1.size(); i++) {
    const EmuBar& b = a.m1[i];
    datetime st = (sec == 604800) ? ((b.t + 4 * 86400) / 604800) * 604800 - 4 * 86400 : b.t - b.t % sec;
    if (bars.empty() || bars.back().t != st) { bars.push_back(EmuBar{st, b.o, b.h, b.l, b.c, b.tv}); first.push_back(i); }
    else { auto& x = bars.back(); x.h = std::max(x.h, b.h); x.l = std::min(x.l, b.l); x.c = b.c; x.tv += b.tv; }
  }
  a.first_m1[tf] = first;
  return a.tf[tf] = bars;
}
// visible bars of an extra symbol: count, and the bar `shift` (the newest one is built from closed M1 bars only)
static long aux_count(EmuAux& a, int tf) {
  size_t k = aux_visible(a); if (k == 0) return 0;
  auto& bars = aux_tf(a, tf); datetime lt = a.m1[k - 1].t;
  size_t lo = 0, hi = bars.size();
  while (lo < hi) { size_t mid = (lo + hi) / 2; if (bars[mid].t <= lt) lo = mid + 1; else hi = mid; }
  return (long)lo;
}
static const EmuBar* aux_bar(EmuAux& a, int tf, int shift) {
  static EmuBar tmp;
  long n = aux_count(a, tf);
  if (shift < 0 || shift >= n) return nullptr;
  auto& bars = aux_tf(a, tf); size_t j = (size_t)(n - 1 - shift);
  if (shift > 0) return &bars[j];
  size_t k = aux_visible(a); size_t f = a.first_m1[tf == PERIOD_CURRENT ? (int)_Period : tf][j];
  tmp = EmuBar{bars[j].t, a.m1[f].o, a.m1[f].h, a.m1[f].l, a.m1[f].c, 0};
  for (size_t i = f; i < k; i++) { tmp.h = std::max(tmp.h, a.m1[i].h); tmp.l = std::min(tmp.l, a.m1[i].l); tmp.c = a.m1[i].c; tmp.tv += a.m1[i].tv; }
  return &tmp;
}
double SymbolInfoDouble(const string& sym, ENUM_SYMBOL_INFO_DOUBLE p) {
  check_symbol(sym);
  double conv = E.price_conv(E.tick.bid > 0 ? E.tick.bid : 1.0);
  switch (p) {
    case SYMBOL_BID: return E.tick.bid;
    case SYMBOL_ASK: return E.tick.ask;
    case SYMBOL_POINT: return E.point;
    case SYMBOL_TRADE_TICK_SIZE: return E.point;
    case SYMBOL_TRADE_TICK_VALUE: case SYMBOL_TRADE_TICK_VALUE_PROFIT: case SYMBOL_TRADE_TICK_VALUE_LOSS:
      return E.point * E.cfg.contract * conv;
    case SYMBOL_TRADE_CONTRACT_SIZE: return E.cfg.contract;
    case SYMBOL_VOLUME_MIN: return E.cfg.vmin;
    case SYMBOL_VOLUME_MAX: return E.cfg.vmax;
    case SYMBOL_VOLUME_STEP: return E.cfg.vstep;
    case SYMBOL_VOLUME_LIMIT: return E.cfg.vlimit;
    case SYMBOL_SWAP_LONG: return E.cfg.swap_long;
    case SYMBOL_SWAP_SHORT: return E.cfg.swap_short;
    default: return 0;
  }
}
long SymbolInfoInteger(const string& sym, ENUM_SYMBOL_INFO_INTEGER p) {
  check_symbol(sym);
  switch (p) {
    case SYMBOL_DIGITS: return E.cfg.digits;
    case SYMBOL_SPREAD: return (long)std::llround((E.tick.ask - E.tick.bid) / E.point);
    case SYMBOL_SPREAD_FLOAT: return 1;
    case SYMBOL_TRADE_STOPS_LEVEL: return E.cfg.stops_level;
    case SYMBOL_TRADE_FREEZE_LEVEL: return E.cfg.freeze_level;
    case SYMBOL_TRADE_MODE: return E.cfg.trade_mode;
    case SYMBOL_TRADE_EXEMODE: return SYMBOL_TRADE_EXECUTION_MARKET;
    case SYMBOL_FILLING_MODE: return E.cfg.filling_flags;
    case SYMBOL_TIME: return E.tick.time;
    default: return 1;
  }
}
string SymbolInfoString(const string& sym, ENUM_SYMBOL_INFO_STRING p) {
  check_symbol(sym);
  switch (p) {
    case SYMBOL_CURRENCY_BASE: case SYMBOL_CURRENCY_MARGIN: return string(E.cfg.base);
    case SYMBOL_CURRENCY_PROFIT: return string(E.cfg.quote);
    default: return string(E.cfg.symbol);
  }
}
bool SymbolInfoTick(const string& sym, MqlTick& t) { check_symbol(sym); t = E.tick; return E.tick.time > 0; }
double AccountInfoDouble(ENUM_ACCOUNT_INFO_DOUBLE p) {
  switch (p) {
    case ACCOUNT_BALANCE: return E.balance;
    case ACCOUNT_EQUITY: return E.equity();
    case ACCOUNT_PROFIT: return E.floating();
    case ACCOUNT_MARGIN: return E.margin();
    case ACCOUNT_MARGIN_FREE: return E.equity() - E.margin();
    case ACCOUNT_MARGIN_LEVEL: { double m = E.margin(); return m > 0 ? E.equity() / m * 100.0 : 0.0; }
    case ACCOUNT_MARGIN_SO_SO: return 50.0;
    case ACCOUNT_MARGIN_SO_CALL: return 100.0;
    default: return 0;
  }
}
long AccountInfoInteger(ENUM_ACCOUNT_INFO_INTEGER p) {
  switch (p) {
    case ACCOUNT_LOGIN: return 5012345;
    case ACCOUNT_LEVERAGE: return (long)E.cfg.leverage;
    case ACCOUNT_TRADE_ALLOWED: return 1;
    case ACCOUNT_TRADE_EXPERT: return 1;
    case ACCOUNT_MARGIN_MODE: return E.cfg.hedging ? ACCOUNT_MARGIN_MODE_RETAIL_HEDGING : ACCOUNT_MARGIN_MODE_RETAIL_NETTING;
    case ACCOUNT_CURRENCY_DIGITS: return 2;
    default: return 0;
  }
}
string AccountInfoString(ENUM_ACCOUNT_INFO_STRING p) {
  if (p == ACCOUNT_CURRENCY) return string("USD");
  return string("Emulator");
}
int TerminalInfoInteger(ENUM_TERMINAL_INFO_INTEGER p) {
  if (p == TERMINAL_TRADE_ALLOWED) return E.cfg.algo_allowed ? 1 : 0;
  if (p == TERMINAL_CONNECTED) return 1;
  return 0;
}
int MQLInfoInteger(ENUM_MQL_INFO_INTEGER p) {
  switch (p) {
    case MQL_TESTER: return E.cfg.tester ? 1 : 0;
    case MQL_VISUAL_MODE: return E.cfg.visual ? 1 : 0;
    case MQL_TRADE_ALLOWED: return E.cfg.algo_allowed ? 1 : 0;
    default: return 0;
  }
}

// ------------------------------------------------------------------ series
static long tf_seconds(int tf) { return PeriodSeconds((ENUM_TIMEFRAMES)tf); }
static datetime bar_start(datetime t, long sec) {
  if (sec == 604800) { long w = (t + 4 * 86400) / 604800; return w * 604800 - 4 * 86400; }
  return t - t % sec;
}
EmuSeries& Emu::ser(int tf) {
  if (tf == PERIOD_CURRENT) tf = _Period;
  for (auto& s : series) if (s.tf == tf) return s;
  EmuSeries ns; ns.tf = tf; ns.sec = tf_seconds(tf);
  // build from the M1 series (always present, index 0)
  if (!series.empty()) {
    for (auto& b : series[0].bars) {
      datetime st = bar_start(b.t, ns.sec);
      if (ns.bars.empty() || ns.bars.back().t != st) ns.bars.push_back(EmuBar{st, b.o, b.h, b.l, b.c, b.tv});
      else { auto& x = ns.bars.back(); x.h = std::max(x.h, b.h); x.l = std::min(x.l, b.l); x.c = b.c; x.tv += b.tv; }
    }
  }
  series.push_back(ns);
  return series.back();
}
void Emu::on_tick_price(datetime t, double bid, bool bar_open) {
  prev_tick_time = tick.time;
  tick.time = t; tick.bid = bid; tick.ask = NormalizeDouble(bid + cfg.spread_points * point, cfg.digits);
  tick.last = 0; tick.volume = 1; tick.time_msc = t * 1000; tick_is_bar_open = bar_open;
  if (series.empty()) ser(PERIOD_M1);
  for (auto& s : series) {
    datetime st = bar_start(t, s.sec);
    if (s.bars.empty() || st > s.bars.back().t) s.bars.push_back(EmuBar{st, bid, bid, bid, bid, 1});
    else { auto& x = s.bars.back(); x.h = std::max(x.h, bid); x.l = std::min(x.l, bid); x.c = bid; x.tv++; }
  }
}
static EmuSeries& S(const string& sym, ENUM_TIMEFRAMES tf) { check_symbol(sym); return E.ser(tf); }
int Bars(const string& sym, ENUM_TIMEFRAMES tf) {
  if (EmuAux* a = E.find_aux(sym.s)) return (int)aux_count(*a, tf);
  return (int)S(sym, tf).bars.size();
}
static const EmuBar* bar_at(const string& sym, ENUM_TIMEFRAMES tf, int shift) {
  if (EmuAux* a = E.find_aux(sym.s)) return aux_bar(*a, tf, shift);
  auto& s = S(sym, tf); long n = (long)s.bars.size();
  if (shift < 0 || shift >= n) return nullptr;
  return &s.bars[(size_t)(n - 1 - shift)];
}
datetime iTime(const string& sym, ENUM_TIMEFRAMES tf, int shift) { auto b = bar_at(sym, tf, shift); return b ? b->t : 0; }
double iOpen(const string& sym, ENUM_TIMEFRAMES tf, int shift) { auto b = bar_at(sym, tf, shift); return b ? b->o : 0; }
double iHigh(const string& sym, ENUM_TIMEFRAMES tf, int shift) { auto b = bar_at(sym, tf, shift); return b ? b->h : 0; }
double iLow(const string& sym, ENUM_TIMEFRAMES tf, int shift) { auto b = bar_at(sym, tf, shift); return b ? b->l : 0; }
double iClose(const string& sym, ENUM_TIMEFRAMES tf, int shift) { auto b = bar_at(sym, tf, shift); return b ? b->c : 0; }
int iBarShift(const string& sym, ENUM_TIMEFRAMES tf, datetime time, bool exact) {
  long n = Bars(sym, tf); if (n <= 0) return -1;
  long lo = 0, hi = n;  // first shift whose bar starts at or before `time` (shift 0 = newest)
  while (lo < hi) { long mid = (lo + hi) / 2; const EmuBar* b = bar_at(sym, tf, (int)mid); if (b && b->t > time) lo = mid + 1; else hi = mid; }
  if (lo >= n) return -1;
  if (exact && bar_at(sym, tf, (int)lo)->t != time) return -1;
  return (int)lo;
}
int CopyRates(const string& sym, ENUM_TIMEFRAMES tf, int start, int count, MqlArray<MqlRates>& out) {
  auto& s = S(sym, tf); long n = (long)s.bars.size();
  if (start < 0 || count <= 0 || start >= n) { E.last_error = 4401; return -1; }
  long avail = std::min<long>(count, n - start);
  out.v.resize((size_t)avail);
  for (long k = 0; k < avail; k++) {
    const EmuBar& b = s.bars[(size_t)(n - 1 - (start + k))];
    MqlRates r{b.t, b.o, b.h, b.l, b.c, b.tv, (int)std::llround(E.cfg.spread_points), 0};
    out.v[(size_t)(out.series ? k : avail - 1 - k)] = r;
  }
  return (int)avail;
}

// ------------------------------------------------------------------ indicators
static double applied(const EmuBar& b, int ap) {
  switch (ap) {
    case PRICE_OPEN: return b.o; case PRICE_HIGH: return b.h; case PRICE_LOW: return b.l;
    case PRICE_MEDIAN: return (b.h + b.l) / 2; case PRICE_TYPICAL: return (b.h + b.l + b.c) / 3;
    case PRICE_WEIGHTED: return (b.h + b.l + 2 * b.c) / 4; default: return b.c;
  }
}
static int new_handle(EmuInd ind, int nbuf, int naux) {
  ind.buf.assign((size_t)nbuf, {}); ind.aux.assign((size_t)naux, {});
  E.inds.push_back(ind);
  return (int)E.inds.size() - 1;
}
int iMA(const string& sym, ENUM_TIMEFRAMES tf, int period, int shift, ENUM_MA_METHOD method, ENUM_APPLIED_PRICE price) {
  check_symbol(sym); if (period < 1 || shift != 0) { E.last_error = 4002; return INVALID_HANDLE; }
  EmuInd i; i.kind = 1; i.tf = tf == PERIOD_CURRENT ? _Period : tf; i.p1 = period; i.p2 = 0; i.method = method; i.applied = price;
  E.ser(i.tf); return new_handle(i, 1, 0);
}
int iRSI(const string& sym, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_PRICE price) {
  check_symbol(sym); if (period < 1) { E.last_error = 4002; return INVALID_HANDLE; }
  EmuInd i; i.kind = 2; i.tf = tf == PERIOD_CURRENT ? _Period : tf; i.p1 = period; i.p2 = 0; i.method = 0; i.applied = price;
  E.ser(i.tf); return new_handle(i, 1, 2);
}
int iATR(const string& sym, ENUM_TIMEFRAMES tf, int period) {
  check_symbol(sym); if (period < 1) { E.last_error = 4002; return INVALID_HANDLE; }
  EmuInd i; i.kind = 3; i.tf = tf == PERIOD_CURRENT ? _Period : tf; i.p1 = period; i.p2 = 0; i.method = 0; i.applied = PRICE_CLOSE;
  E.ser(i.tf); return new_handle(i, 1, 1);
}
int iADX(const string& sym, ENUM_TIMEFRAMES tf, int period) {
  check_symbol(sym); if (period < 1) { E.last_error = 4002; return INVALID_HANDLE; }
  EmuInd i; i.kind = 4; i.tf = tf == PERIOD_CURRENT ? _Period : tf; i.p1 = period; i.p2 = 0; i.method = 0; i.applied = PRICE_CLOSE;
  E.ser(i.tf); return new_handle(i, 3, 3);
}
// computes values of bar i (needs values of bars < i already stored)
void Emu::ind_step(EmuInd& ind, const std::vector<EmuBar>& b, size_t i, double* out, double* ax) {
  const int n = ind.p1;
  switch (ind.kind) {
    case 1: {  // moving averages (MT5 MovingAverages.mqh semantics)
      double p = applied(b[i], ind.applied);
      if (ind.method == MODE_EMA) {
        double a = 2.0 / (n + 1.0);
        out[0] = i == 0 ? p : p * a + ind.buf[0][i - 1] * (1 - a);
      } else if (ind.method == MODE_SMMA) {
        if ((long)i < n - 1) out[0] = 0;
        else if ((long)i == n - 1) { double s = 0; for (size_t k = 0; k < (size_t)n; k++) s += applied(b[i - k], ind.applied); out[0] = s / n; }
        else out[0] = (ind.buf[0][i - 1] * (n - 1) + p) / n;
      } else {  // SMA / LWMA
        if ((long)i < n - 1) { out[0] = 0; break; }
        double s = 0, w = 0;
        for (size_t k = 0; k < (size_t)n; k++) {
          double wk = ind.method == MODE_LWMA ? (double)(n - (long)k) : 1.0;
          s += applied(b[i - k], ind.applied) * wk; w += wk;
        }
        out[0] = s / w;
      }
      break;
    }
    case 2: {  // RSI (MT5 RSI.mq5)
      if ((long)i < n) { out[0] = 0; ax[0] = 0; ax[1] = 0; break; }
      if ((long)i == n) {
        double sp = 0, sn = 0;
        for (size_t k = 1; k <= (size_t)n; k++) {
          double d = applied(b[k], ind.applied) - applied(b[k - 1], ind.applied);
          sp += d > 0 ? d : 0; sn += d < 0 ? -d : 0;
        }
        ax[0] = sp / n; ax[1] = sn / n;
      } else {
        double d = applied(b[i], ind.applied) - applied(b[i - 1], ind.applied);
        ax[0] = (ind.aux[0][i - 1] * (n - 1) + (d > 0 ? d : 0)) / n;
        ax[1] = (ind.aux[1][i - 1] * (n - 1) + (d < 0 ? -d : 0)) / n;
      }
      if (ax[1] != 0) out[0] = 100.0 - 100.0 / (1.0 + ax[0] / ax[1]);
      else out[0] = ax[0] != 0 ? 100.0 : 50.0;
      break;
    }
    case 3: {  // ATR (MT5 ATR.mq5 : simple average of true range)
      ax[0] = i == 0 ? 0.0 : std::max(b[i].h, b[i - 1].c) - std::min(b[i].l, b[i - 1].c);
      if ((long)i < n) out[0] = 0;
      else if ((long)i == n) { double s = 0; for (size_t k = 1; k <= (size_t)n; k++) s += (k == i ? ax[0] : ind.aux[0][k]); out[0] = s / n; }
      else out[0] = ind.buf[0][i - 1] + (ax[0] - ind.aux[0][i - (size_t)n]) / n;
      break;
    }
    case 4: {  // ADX (MT5 ADX.mq5)
      if (i == 0) { out[0] = out[1] = out[2] = 0; ax[0] = ax[1] = ax[2] = 0; break; }
      double hp = b[i].h - b[i - 1].h, np = b[i - 1].l - b[i].l;
      if (hp < 0) hp = 0;
      if (np < 0) np = 0;
      if (hp > np) np = 0; else if (hp < np) hp = 0; else { hp = 0; np = 0; }
      double tr = std::max(std::max(std::fabs(b[i].h - b[i].l), std::fabs(b[i].h - b[i - 1].c)), std::fabs(b[i].l - b[i - 1].c));
      ax[0] = tr != 0 ? 100.0 * hp / tr : 0; ax[1] = tr != 0 ? 100.0 * np / tr : 0;
      double pr = 2.0 / (n + 1.0);
      out[1] = ax[0] * pr + ind.buf[1][i - 1] * (1 - pr);
      out[2] = ax[1] * pr + ind.buf[2][i - 1] * (1 - pr);
      double s = out[1] + out[2];
      ax[2] = s != 0 ? 100.0 * std::fabs((out[1] - out[2]) / s) : 0;
      out[0] = ax[2] * pr + ind.buf[0][i - 1] * (1 - pr);
      break;
    }
  }
}
void Emu::calc_ind(EmuInd& ind, size_t last) {
  auto& b = ser(ind.tf).bars;
  if (b.empty()) return;
  for (auto& v : ind.buf) if (v.size() < b.size()) v.resize(b.size(), 0.0);
  for (auto& v : ind.aux) if (v.size() < b.size()) v.resize(b.size(), 0.0);
  double out[4], ax[4];
  size_t closed_end = b.size() - 1;  // bars [0, closed_end) are closed
  for (size_t i = ind.done; i <= last && i < b.size(); i++) {
    ind_step(ind, b, i, out, ax);
    for (size_t k = 0; k < ind.buf.size(); k++) ind.buf[k][i] = out[k];
    for (size_t k = 0; k < ind.aux.size(); k++) ind.aux[k][i] = ax[k];
    if (i < closed_end) ind.done = i + 1;
  }
}
int CopyBuffer(int handle, int buffer, int start, int count, MqlArray<double>& out) {
  if (handle < 0 || handle >= (int)E.inds.size() || E.inds[(size_t)handle].released) { E.last_error = 4807; return -1; }
  EmuInd& ind = E.inds[(size_t)handle];
  if (buffer < 0 || buffer >= (int)ind.buf.size()) { E.last_error = 4806; return -1; }
  auto& b = E.ser(ind.tf).bars; long n = (long)b.size();
  if (start < 0 || count <= 0 || start >= n) { E.last_error = 4806; return -1; }
  E.calc_ind(ind, (size_t)(n - 1));
  long avail = std::min<long>(count, n - start);
  out.v.resize((size_t)avail);
  for (long k = 0; k < avail; k++) {
    double v = ind.buf[(size_t)buffer][(size_t)(n - 1 - (start + k))];
    out.v[(size_t)(out.series ? k : avail - 1 - k)] = v;
  }
  return (int)avail;
}
int BarsCalculated(int handle) {
  if (handle < 0 || handle >= (int)E.inds.size()) return -1;
  return (int)E.ser(E.inds[(size_t)handle].tf).bars.size();
}
bool IndicatorRelease(int handle) {
  if (handle < 0 || handle >= (int)E.inds.size()) return false;
  E.inds[(size_t)handle].released = true; return true;
}

// ------------------------------------------------------------------ trading engine
static bool vol_ok(double v) {
  if (v < E.cfg.vmin - 1e-9 || v > E.cfg.vmax + 1e-9) return false;
  double k = v / E.cfg.vstep;
  return std::fabs(k - std::round(k)) < 1e-6;
}
static bool price_normalized(double p) {
  if (p == 0) return true;
  double k = p / E.point;
  return std::fabs(k - std::round(k)) < 1e-6;
}
static bool filling_ok(ENUM_ORDER_TYPE_FILLING f) {
  if (f == ORDER_FILLING_FOK) return (E.cfg.filling_flags & SYMBOL_FILLING_FOK) != 0;
  if (f == ORDER_FILLING_IOC) return (E.cfg.filling_flags & SYMBOL_FILLING_IOC) != 0;
  if (f == ORDER_FILLING_RETURN) return E.cfg.allow_return;
  return false;
}
// type: 0 buy position, 1 sell position
static bool stops_ok(int type, double sl, double tp) {
  double lvl = (double)E.cfg.stops_level * E.point, eps = E.point * 0.5;
  if (!price_normalized(sl) || !price_normalized(tp)) return false;
  if (type == 0) {
    if (sl > 0 && !(E.tick.bid - sl >= lvl - eps && E.tick.bid - sl > eps)) return false;
    if (tp > 0 && !(tp - E.tick.bid >= lvl - eps && tp - E.tick.bid > eps)) return false;
  } else {
    if (sl > 0 && !(sl - E.tick.ask >= lvl - eps && sl - E.tick.ask > eps)) return false;
    if (tp > 0 && !(E.tick.ask - tp >= lvl - eps && E.tick.ask - tp > eps)) return false;
  }
  return true;
}
static long find_pos(ulong ticket) {
  for (size_t i = 0; i < E.pos.size(); i++) if (E.pos[i].ticket == ticket) return (long)i;
  return -1;
}
static ulong add_deal(int type, int entry, const EmuPos& p, double vol, double price, double profit, double comm, double swap,
                      int reason, const string& comment) {
  EmuDeal d; d.ticket = E.next_ticket++; d.order = d.ticket; d.time = E.tick.time; d.time_msc = E.tick.time_msc;
  d.type = type; d.entry = entry; d.magic = p.magic; d.position_id = p.identifier; d.volume = vol; d.price = price;
  d.profit = profit; d.commission = comm; d.swap = swap; d.fee = 0; d.sl = p.sl; d.tp = p.tp; d.reason = reason; d.comment = comment;
  E.deals.push_back(d);
  return d.ticket;
}
static std::map<ulong, double> g_realized;  // position -> realized net result so far
static std::map<ulong, double> g_risk;      // position -> money at risk at entry
void Emu::close_volume(size_t idx, double vol, double price, int reason, const string& comment) {
  EmuPos& p = pos[idx];
  if (vol > p.volume) vol = p.volume;
  double diff = p.type == 0 ? price - p.open : p.open - price;
  double profit = diff * vol * cfg.contract * price_conv(price);
  double comm = -cfg.commission_rt / 2.0 * vol;
  double swp = p.volume > 0 ? p.swap * vol / p.volume : 0;
  balance += profit + comm + swp;
  add_deal(p.type == 0 ? DEAL_TYPE_SELL : DEAL_TYPE_BUY, DEAL_ENTRY_OUT, p, vol, price, profit, comm, swp, reason, comment);
  g_realized[p.ticket] += profit + comm + swp;
  p.volume = NormalizeDouble(p.volume - vol, 8); p.swap -= swp;
  const char* rs = reason == DEAL_REASON_SL ? "SL" : reason == DEAL_REASON_TP ? "TP" : reason == DEAL_REASON_SO ? "STOPOUT" : "EA";
  log_event(std::string("close_") + rs);
  if (p.volume <= 1e-9) {
    EmuTradeRec r; r.ticket = p.ticket; r.type = p.type; r.open_time = p.time; r.close_time = tick.time; r.volume = p.initVolume;
    r.open = p.open; r.close = price; r.initSL = p.initSL; r.tp = p.tp; r.profit = g_realized[p.ticket];
    r.riskMoney = g_risk[p.ticket]; r.exit_reason = rs;
    if (rs == std::string("SL") && p.initSL != 0 && std::fabs(p.sl - p.initSL) > point * 0.5) r.exit_reason = "SL(moved)";
    trades.push_back(r);
    pos.erase(pos.begin() + (long)idx);
  }
}
void Emu::check_stops() {
  for (long i = (long)pos.size() - 1; i >= 0; i--) {
    EmuPos& p = pos[(size_t)i];
    if (p.type == 0) {
      if (p.sl > 0 && tick.bid <= p.sl) { close_volume((size_t)i, p.volume, tick_is_bar_open ? tick.bid : p.sl, DEAL_REASON_SL, string("[sl]")); continue; }
      if (p.tp > 0 && tick.bid >= p.tp) { close_volume((size_t)i, p.volume, tick_is_bar_open ? tick.bid : p.tp, DEAL_REASON_TP, string("[tp]")); continue; }
    } else {
      if (p.sl > 0 && tick.ask >= p.sl) { close_volume((size_t)i, p.volume, tick_is_bar_open ? tick.ask : p.sl, DEAL_REASON_SL, string("[sl]")); continue; }
      if (p.tp > 0 && tick.ask <= p.tp) { close_volume((size_t)i, p.volume, tick_is_bar_open ? tick.ask : p.tp, DEAL_REASON_TP, string("[tp]")); continue; }
    }
  }
  double m = margin();
  if (m > 0 && equity() / m * 100.0 < 50.0) {
    emu_print_line("STOP OUT: margin level below 50%");
    while (!pos.empty()) close_volume(pos.size() - 1, pos.back().volume, pos.back().type == 0 ? tick.bid : tick.ask, DEAL_REASON_SO, string("[so]"));
  }
}

static bool fail(MqlTradeResult& res, uint rc, const char* c) {
  res.retcode = rc; res.comment = string(c); res.bid = E.tick.bid; res.ask = E.tick.ask;
  E.n_rejected++; E.last_error = 4756; E.log_event(std::string("reject_") + std::to_string(rc));
  return false;
}
static bool open_new(MqlTradeRequest& req, MqlTradeResult& res, int ptype, double vol, double px, bool check_only) {
  double sl = E.cfg.ignore_sltp_on_open ? 0.0 : req.sl, tp = E.cfg.ignore_sltp_on_open ? 0.0 : req.tp;
  if (!stops_ok(ptype, req.sl, req.tp)) return fail(res, TRADE_RETCODE_INVALID_STOPS, "Invalid stops");
  double need = vol * E.cfg.contract * E.margin_rate(px) / E.cfg.leverage;
  if (need > E.equity() - E.margin()) return fail(res, TRADE_RETCODE_NO_MONEY, "No money");
  if (check_only) return true;
  EmuPos p; p.ticket = E.next_ticket++; p.identifier = p.ticket; p.type = ptype; p.volume = vol; p.open = px;
  p.sl = sl; p.tp = tp; p.time = E.tick.time; p.time_msc = E.tick.time_msc; p.magic = req.magic; p.comment = req.comment;
  p.swap = 0; p.initVolume = vol; p.initSL = sl; p.commission = -E.cfg.commission_rt / 2.0 * vol;
  E.balance += p.commission;
  E.pos.push_back(p);
  g_realized[p.ticket] = p.commission;
  g_risk[p.ticket] = sl > 0 ? std::fabs(px - sl) * vol * E.cfg.contract * E.price_conv(px) + E.cfg.commission_rt * vol : 0.0;
  ulong d = add_deal(ptype == 0 ? DEAL_TYPE_BUY : DEAL_TYPE_SELL, DEAL_ENTRY_IN, p, vol, px, 0, p.commission, 0, DEAL_REASON_EXPERT, req.comment);
  res.retcode = TRADE_RETCODE_DONE; res.deal = d; res.order = p.ticket; res.volume = vol; res.price = px;
  res.bid = E.tick.bid; res.ask = E.tick.ask; res.comment = string("Request executed");
  E.log_event("open");
  return true;
}
static bool do_trade(MqlTradeRequest& req, MqlTradeResult& res, bool check_only) {
  res = MqlTradeResult();
  if (req.symbol.s != E.cfg.symbol) return fail(res, TRADE_RETCODE_INVALID, "Invalid symbol");
  if (!E.cfg.algo_allowed) return fail(res, TRADE_RETCODE_CLIENT_DISABLES_AT, "AutoTrading disabled");
  if (req.action == TRADE_ACTION_DEAL) {
    if (req.type != ORDER_TYPE_BUY && req.type != ORDER_TYPE_SELL) return fail(res, TRADE_RETCODE_INVALID, "Invalid type");
    if (!vol_ok(req.volume)) return fail(res, TRADE_RETCODE_INVALID_VOLUME, "Invalid volume");
    if (!filling_ok(req.type_filling)) return fail(res, TRADE_RETCODE_INVALID_FILL, "Unsupported filling mode");
    if (E.cfg.trade_mode == SYMBOL_TRADE_MODE_DISABLED) return fail(res, TRADE_RETCODE_TRADE_DISABLED, "Trade disabled");
    if (!check_only && E.cfg.requote_prob > 0) {
      std::uniform_real_distribution<double> u(0, 1);
      if (u(E.rng) < E.cfg.requote_prob) return fail(res, TRADE_RETCODE_REQUOTE, "Requote");
    }
    double px = req.type == ORDER_TYPE_BUY ? E.tick.ask : E.tick.bid;
    int dir = req.type == ORDER_TYPE_BUY ? 0 : 1;
    long idx = -1;
    if (req.position != 0) {
      idx = find_pos(req.position);
      if (idx < 0) return fail(res, TRADE_RETCODE_POSITION_CLOSED, "Position not found");
    } else if (!E.cfg.hedging) {
      for (size_t i = 0; i < E.pos.size(); i++) idx = (long)i;
    }
    if (idx >= 0) {
      EmuPos& p = E.pos[(size_t)idx];
      if (p.type == dir) {  // netting: increase
        if (E.cfg.hedging) return fail(res, TRADE_RETCODE_INVALID, "Wrong close direction");
        if (check_only) return true;
        double nv = p.volume + req.volume; p.open = (p.open * p.volume + px * req.volume) / nv; p.volume = nv;
        ulong d = add_deal(dir == 0 ? DEAL_TYPE_BUY : DEAL_TYPE_SELL, DEAL_ENTRY_IN, p, req.volume, px, 0, -E.cfg.commission_rt / 2 * req.volume, 0, DEAL_REASON_EXPERT, req.comment);
        E.balance += -E.cfg.commission_rt / 2 * req.volume;
        res.retcode = TRADE_RETCODE_DONE; res.deal = d; res.order = p.ticket; res.volume = req.volume; res.price = px; return true;
      }
      double cv = std::min(req.volume, p.volume);
      if (req.volume > p.volume + 1e-9 && E.cfg.hedging) return fail(res, TRADE_RETCODE_INVALID_VOLUME, "Close volume exceeds position");
      if (check_only) return true;
      double rest = req.volume - cv;
      E.close_volume((size_t)idx, cv, px, DEAL_REASON_EXPERT, req.comment);
      res.retcode = TRADE_RETCODE_DONE; res.deal = E.deals.back().ticket; res.order = res.deal; res.volume = cv; res.price = px;
      res.bid = E.tick.bid; res.ask = E.tick.ask;
      if (rest > 1e-9) return open_new(req, res, dir, NormalizeDouble(rest, 8), px, false);
      return true;
    }
    return open_new(req, res, dir, req.volume, px, check_only);
  }
  if (req.action == TRADE_ACTION_SLTP) {
    long idx = -1;
    if (req.position != 0) idx = find_pos(req.position);
    else if (!E.cfg.hedging && !E.pos.empty()) idx = 0;
    if (idx < 0) return fail(res, TRADE_RETCODE_POSITION_CLOSED, "Position not found");
    EmuPos& p = E.pos[(size_t)idx];
    if (E.cfg.reject_sltp) return fail(res, TRADE_RETCODE_REJECT, "Rejected by dealer");
    if (!stops_ok(p.type, req.sl, req.tp)) return fail(res, TRADE_RETCODE_INVALID_STOPS, "Invalid stops");
    double fz = (double)E.cfg.freeze_level * E.point;
    double cur = p.type == 0 ? E.tick.bid : E.tick.ask;
    if (fz > 0 && ((p.sl > 0 && std::fabs(cur - p.sl) <= fz) || (p.tp > 0 && std::fabs(cur - p.tp) <= fz)))
      return fail(res, TRADE_RETCODE_FROZEN, "Frozen");
    if (std::fabs(req.sl - p.sl) < E.point * 0.1 && std::fabs(req.tp - p.tp) < E.point * 0.1)
      return fail(res, TRADE_RETCODE_NO_CHANGES, "No changes");
    if (check_only) return true;
    if (p.initSL == 0 && req.sl > 0) {
      p.initSL = req.sl;
      g_risk[p.ticket] = std::fabs(p.open - req.sl) * p.volume * E.cfg.contract * E.price_conv(p.open) + E.cfg.commission_rt * p.volume;
    }
    p.sl = req.sl; p.tp = req.tp;
    E.n_modify++; E.log_event("modify");
    res.retcode = TRADE_RETCODE_DONE; res.order = p.ticket; res.bid = E.tick.bid; res.ask = E.tick.ask;
    return true;
  }
  return fail(res, TRADE_RETCODE_INVALID, "Unsupported action");
}
bool OrderSend(MqlTradeRequest& req, MqlTradeResult& res) { E.n_requests++; return do_trade(req, res, false); }
bool OrderCheck(MqlTradeRequest& req, MqlTradeCheckResult& chk) {
  MqlTradeResult r; bool ok = do_trade(req, r, true);
  chk = MqlTradeCheckResult(); chk.retcode = ok ? 0 : r.retcode; chk.comment = r.comment;
  chk.balance = E.balance; chk.equity = E.equity(); chk.margin = E.margin(); chk.margin_free = E.equity() - E.margin();
  return ok;
}
bool OrderCalcProfit(ENUM_ORDER_TYPE type, const string& sym, double vol, double open, double close, double& profit) {
  check_symbol(sym);
  double diff = type == ORDER_TYPE_BUY ? close - open : open - close;
  profit = diff * vol * E.cfg.contract * E.price_conv(close);
  return true;
}
bool OrderCalcMargin(ENUM_ORDER_TYPE, const string& sym, double vol, double price, double& margin) {
  check_symbol(sym); margin = vol * E.cfg.contract * E.margin_rate(price) / E.cfg.leverage; return true;
}
int PositionsTotal() { return (int)E.pos.size(); }
ulong PositionGetTicket(int index) {
  if (index < 0 || index >= (int)E.pos.size()) { E.selected_pos = -1; return 0; }
  E.selected_pos = (long)E.pos[(size_t)index].ticket; return E.pos[(size_t)index].ticket;
}
bool PositionSelectByTicket(ulong t) {
  if (find_pos(t) < 0) { E.selected_pos = -1; return false; }
  E.selected_pos = (long)t; return true;
}
bool PositionSelect(const string& sym) {
  for (auto& p : E.pos) if (sym.s == E.cfg.symbol) { E.selected_pos = (long)p.ticket; return true; }
  return false;
}
static const EmuPos* sel_pos() {
  long i = E.selected_pos < 0 ? -1 : find_pos((ulong)E.selected_pos);
  if (i < 0) { E.last_error = 4753; return nullptr; }
  return &E.pos[(size_t)i];
}
double PositionGetDouble(ENUM_POSITION_PROPERTY_DOUBLE p) {
  const EmuPos* x = sel_pos(); if (!x) return 0;
  switch (p) {
    case POSITION_VOLUME: return x->volume; case POSITION_PRICE_OPEN: return x->open; case POSITION_SL: return x->sl;
    case POSITION_TP: return x->tp; case POSITION_PRICE_CURRENT: return x->type == 0 ? E.tick.bid : E.tick.ask;
    case POSITION_SWAP: return x->swap; case POSITION_PROFIT: return E.pos_profit(*x);
  }
  return 0;
}
long PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER p) {
  const EmuPos* x = sel_pos(); if (!x) return 0;
  switch (p) {
    case POSITION_TICKET: return (long)x->ticket; case POSITION_TIME: return x->time; case POSITION_TIME_MSC: return x->time_msc;
    case POSITION_TIME_UPDATE: return x->time; case POSITION_TYPE: return x->type; case POSITION_MAGIC: return (long)x->magic;
    case POSITION_IDENTIFIER: return (long)x->identifier; case POSITION_REASON: return 3;
  }
  return 0;
}
string PositionGetString(ENUM_POSITION_PROPERTY_STRING p) {
  const EmuPos* x = sel_pos(); if (!x) return string();
  if (p == POSITION_SYMBOL) return string(E.cfg.symbol);
  if (p == POSITION_COMMENT) return x->comment;
  return string();
}
bool HistorySelect(datetime from, datetime to) {
  E.hist_sel.clear();
  for (size_t i = 0; i < E.deals.size(); i++) if (E.deals[i].time >= from && E.deals[i].time <= to) E.hist_sel.push_back(i);
  return true;
}
bool HistorySelectByPosition(long position_id) {
  E.hist_sel.clear();
  for (size_t i = 0; i < E.deals.size(); i++) if ((long)E.deals[i].position_id == position_id) E.hist_sel.push_back(i);
  return true;
}
int HistoryDealsTotal() { return (int)E.hist_sel.size(); }
ulong HistoryDealGetTicket(int index) {
  if (index < 0 || index >= (int)E.hist_sel.size()) return 0;
  return E.deals[E.hist_sel[(size_t)index]].ticket;
}
static const EmuDeal* deal_by(ulong t) {
  for (size_t i : E.hist_sel) if (E.deals[i].ticket == t) return &E.deals[i];
  E.last_error = 4755; return nullptr;
}
double HistoryDealGetDouble(ulong t, ENUM_DEAL_PROPERTY_DOUBLE p) {
  const EmuDeal* d = deal_by(t); if (!d) return 0;
  switch (p) {
    case DEAL_VOLUME: return d->volume; case DEAL_PRICE: return d->price; case DEAL_COMMISSION: return d->commission;
    case DEAL_SWAP: return d->swap; case DEAL_PROFIT: return d->profit; case DEAL_FEE: return d->fee;
    case DEAL_SL: return d->sl; case DEAL_TP: return d->tp;
  }
  return 0;
}
long HistoryDealGetInteger(ulong t, ENUM_DEAL_PROPERTY_INTEGER p) {
  const EmuDeal* d = deal_by(t); if (!d) return 0;
  switch (p) {
    case DEAL_TICKET: return (long)d->ticket; case DEAL_ORDER: return (long)d->order; case DEAL_TIME: return d->time;
    case DEAL_TIME_MSC: return d->time_msc; case DEAL_TYPE: return d->type; case DEAL_ENTRY: return d->entry;
    case DEAL_MAGIC: return (long)d->magic; case DEAL_REASON: return d->reason; case DEAL_POSITION_ID: return (long)d->position_id;
  }
  return 0;
}
string HistoryDealGetString(ulong t, ENUM_DEAL_PROPERTY_STRING p) {
  const EmuDeal* d = deal_by(t); if (!d) return string();
  if (p == DEAL_SYMBOL) return string(E.cfg.symbol);
  if (p == DEAL_COMMENT) return d->comment;
  return string();
}

// ------------------------------------------------------------------ global variables
bool GlobalVariableCheck(const string& n) { return E.gv.count(n.s) > 0; }
double GlobalVariableGet(const string& n) { auto it = E.gv.find(n.s); if (it == E.gv.end()) { E.last_error = 4501; return 0; } return it->second; }
datetime GlobalVariableSet(const string& n, double v) {
  if (n.s.size() > 63) emu_fatal("global variable name longer than 63 characters: " + n.s);
  E.gv[n.s] = v; return E.tick.time;
}
bool GlobalVariableDel(const string& n) { return E.gv.erase(n.s) > 0; }
int GlobalVariablesTotal() { return (int)E.gv.size(); }
string GlobalVariableName(int index) {
  if (index < 0 || index >= (int)E.gv.size()) return string();
  auto it = E.gv.begin(); std::advance(it, index); return string(it->first);
}

// ------------------------------------------------------------------ calendar (only in --live mode)
bool CalendarValueHistory(MqlArray<MqlCalendarValue>& values, datetime from, datetime to, const string& country, const string& currency) {
  (void)country;
  values.v.clear();
  if (E.cfg.tester) { E.last_error = 5401; return false; }
  for (size_t i = 0; i < E.news.size(); i++) {
    const EmuNews& n = E.news[i];
    if (n.t < from || (to > 0 && n.t > to)) continue;
    if (!currency.s.empty() && n.currency.s != currency.s) continue;
    MqlCalendarValue v{}; v.id = i + 1; v.event_id = i + 1; v.time = n.t; values.v.push_back(v);
  }
  return true;
}
bool CalendarEventById(ulong id, MqlCalendarEvent& ev) {
  if (id == 0 || id > E.news.size()) return false;
  const EmuNews& n = E.news[id - 1];
  ev = MqlCalendarEvent(); ev.id = id; ev.time_mode = CALENDAR_TIMEMODE_DATETIME;
  ev.importance = (ENUM_CALENDAR_EVENT_IMPORTANCE)n.importance; ev.name = n.name;
  return true;
}

// ------------------------------------------------------------------ statistics
double TesterStatistics(ENUM_STATISTICS s) {
  double gp = 0, gl = 0; long nt = 0, np = 0, nl = 0;
  for (auto& t : E.trades) { nt++; if (t.profit > 0) { gp += t.profit; np++; } else { gl += -t.profit; nl++; } }
  double profit = E.balance - E.cfg.deposit;
  switch (s) {
    case STAT_INITIAL_DEPOSIT: return E.cfg.deposit;
    case STAT_PROFIT: return profit;
    case STAT_GROSS_PROFIT: return gp;
    case STAT_GROSS_LOSS: return -gl;
    case STAT_PROFIT_FACTOR: return gl > 0 ? gp / gl : 0;
    case STAT_TRADES: return (double)nt;
    case STAT_PROFIT_TRADES: return (double)np;
    case STAT_LOSS_TRADES: return (double)nl;
    case STAT_EXPECTED_PAYOFF: return nt ? profit / (double)nt : 0;
    case STAT_EQUITY_DD: return E.max_dd;
    case STAT_EQUITY_DDREL_PERCENT: return E.max_dd_rel;
    case STAT_BALANCE_DD: return E.max_bdd;
    case STAT_BALANCE_DDREL_PERCENT: return E.max_bdd_rel;
    case STAT_RECOVERY_FACTOR: return E.max_dd > 0 ? profit / E.max_dd : 0;
    case STAT_DEALS: return (double)E.deals.size();
    default: return 0;
  }
}
