// mql5.h - minimal MQL5 runtime emulator (types, API and a tick-level
// trading engine) used to compile and back-test MQL5 Expert Advisors on Linux.
//
// The API signatures follow the official MQL5 documentation so that a clean
// C++ build of the translated EA is a strong indication that the MQL5 source
// uses the platform functions correctly.  Behaviour is modelled on the
// MetaTrader 5 strategy tester ("1 minute OHLC" tick model).
#pragma once
#pragma GCC system_header

#include <algorithm>
#include <cfloat>
#include <climits>
#include <cmath>
#include <csignal>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <functional>
#include <initializer_list>
#include <map>
#include <random>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

// ------------------------------------------------------------------ types
typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;
typedef unsigned long ulong;
typedef long datetime;
typedef unsigned int color;

[[noreturn]] inline void emu_fatal(const std::string& msg);

class string {
 public:
  std::string s;
  string() {}
  string(const char* p) : s(p ? p : "") {}
  string(const std::string& x) : s(x) {}
  string(const string&) = default;
  string& operator=(const string&) = default;
  // MQL5 converts numbers to strings implicitly (with a warning); we forbid it
  template <class T, typename std::enable_if<std::is_arithmetic<T>::value, int>::type = 0>
  string(T) = delete;
  string& operator+=(const string& o) { s += o.s; return *this; }
  template <class T, typename std::enable_if<std::is_arithmetic<T>::value, int>::type = 0>
  string& operator+=(T) = delete;
  const char* c_str() const { return s.c_str(); }
};
inline string operator+(const string& a, const string& b) { return string(a.s + b.s); }
template <class T, typename std::enable_if<std::is_arithmetic<T>::value, int>::type = 0>
string operator+(const string&, T) = delete;
template <class T, typename std::enable_if<std::is_arithmetic<T>::value, int>::type = 0>
string operator+(T, const string&) = delete;
inline bool operator==(const string& a, const string& b) { return a.s == b.s; }
inline bool operator!=(const string& a, const string& b) { return a.s != b.s; }
inline bool operator<(const string& a, const string& b) { return a.s < b.s; }
inline bool operator>(const string& a, const string& b) { return a.s > b.s; }
inline string S_(const char* p) { return string(p); }

struct MqlNull {
  operator string() const { return string(); }
  operator long() const { return 0; }
};
#undef NULL
#define NULL MqlNull()

template <class T>
class MqlArray {
 public:
  std::vector<T> v;
  bool series = false;
  MqlArray() {}
  MqlArray(std::initializer_list<T> il) : v(il) {}
  template <class I>
  T& operator[](I idx) { return v[map((long)idx)]; }
  template <class I>
  const T& operator[](I idx) const { return v[map((long)idx)]; }
  size_t map(long i) const {
    long n = (long)v.size();
    if (i < 0 || i >= n) {
      char b[160];
      snprintf(b, sizeof b, "array out of range (index %ld, size %ld)", i, n);
      emu_fatal(b);
    }
    return (size_t)(series ? n - 1 - i : i);
  }
};

// ------------------------------------------------------------------ enums & constants
enum ENUM_TIMEFRAMES {
  PERIOD_CURRENT = 0, PERIOD_M1 = 1, PERIOD_M2 = 2, PERIOD_M3 = 3, PERIOD_M4 = 4, PERIOD_M5 = 5,
  PERIOD_M6 = 6, PERIOD_M10 = 10, PERIOD_M12 = 12, PERIOD_M15 = 15, PERIOD_M20 = 20, PERIOD_M30 = 30,
  PERIOD_H1 = 16385, PERIOD_H2 = 16386, PERIOD_H3 = 16387, PERIOD_H4 = 16388, PERIOD_H6 = 16390,
  PERIOD_H8 = 16392, PERIOD_H12 = 16396, PERIOD_D1 = 16408, PERIOD_W1 = 32769, PERIOD_MN1 = 49153
};
enum ENUM_MA_METHOD { MODE_SMA = 0, MODE_EMA = 1, MODE_SMMA = 2, MODE_LWMA = 3 };
enum ENUM_APPLIED_PRICE { PRICE_CLOSE = 1, PRICE_OPEN, PRICE_HIGH, PRICE_LOW, PRICE_MEDIAN, PRICE_TYPICAL, PRICE_WEIGHTED };
enum ENUM_ORDER_TYPE { ORDER_TYPE_BUY = 0, ORDER_TYPE_SELL, ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT, ORDER_TYPE_BUY_STOP,
                       ORDER_TYPE_SELL_STOP, ORDER_TYPE_BUY_STOP_LIMIT, ORDER_TYPE_SELL_STOP_LIMIT, ORDER_TYPE_CLOSE_BY };
enum ENUM_ORDER_TYPE_FILLING { ORDER_FILLING_FOK = 0, ORDER_FILLING_IOC = 1, ORDER_FILLING_RETURN = 2, ORDER_FILLING_BOC = 3 };
enum ENUM_ORDER_TYPE_TIME { ORDER_TIME_GTC = 0, ORDER_TIME_DAY, ORDER_TIME_SPECIFIED, ORDER_TIME_SPECIFIED_DAY };
enum ENUM_TRADE_REQUEST_ACTIONS { TRADE_ACTION_DEAL = 1, TRADE_ACTION_PENDING = 5, TRADE_ACTION_SLTP = 6,
                                  TRADE_ACTION_MODIFY = 7, TRADE_ACTION_REMOVE = 8, TRADE_ACTION_CLOSE_BY = 10 };
enum ENUM_POSITION_TYPE { POSITION_TYPE_BUY = 0, POSITION_TYPE_SELL = 1 };
enum ENUM_DEAL_TYPE { DEAL_TYPE_BUY = 0, DEAL_TYPE_SELL, DEAL_TYPE_BALANCE };
enum ENUM_DEAL_ENTRY { DEAL_ENTRY_IN = 0, DEAL_ENTRY_OUT, DEAL_ENTRY_INOUT, DEAL_ENTRY_OUT_BY };
enum ENUM_DEAL_REASON { DEAL_REASON_CLIENT = 0, DEAL_REASON_MOBILE, DEAL_REASON_WEB, DEAL_REASON_EXPERT, DEAL_REASON_SL,
                        DEAL_REASON_TP, DEAL_REASON_SO };
enum ENUM_ACCOUNT_MARGIN_MODE { ACCOUNT_MARGIN_MODE_RETAIL_NETTING = 0, ACCOUNT_MARGIN_MODE_EXCHANGE, ACCOUNT_MARGIN_MODE_RETAIL_HEDGING };
enum ENUM_SYMBOL_TRADE_MODE { SYMBOL_TRADE_MODE_DISABLED = 0, SYMBOL_TRADE_MODE_LONGONLY, SYMBOL_TRADE_MODE_SHORTONLY,
                              SYMBOL_TRADE_MODE_CLOSEONLY, SYMBOL_TRADE_MODE_FULL };
enum ENUM_SYMBOL_TRADE_EXECUTION { SYMBOL_TRADE_EXECUTION_REQUEST = 0, SYMBOL_TRADE_EXECUTION_INSTANT,
                                   SYMBOL_TRADE_EXECUTION_MARKET, SYMBOL_TRADE_EXECUTION_EXCHANGE };
const int SYMBOL_FILLING_FOK = 1;
const int SYMBOL_FILLING_IOC = 2;
const int SYMBOL_FILLING_BOC = 4;

enum ENUM_SYMBOL_INFO_DOUBLE {
  SYMBOL_BID, SYMBOL_ASK, SYMBOL_POINT, SYMBOL_TRADE_TICK_VALUE, SYMBOL_TRADE_TICK_VALUE_PROFIT,
  SYMBOL_TRADE_TICK_VALUE_LOSS, SYMBOL_TRADE_TICK_SIZE, SYMBOL_TRADE_CONTRACT_SIZE, SYMBOL_VOLUME_MIN,
  SYMBOL_VOLUME_MAX, SYMBOL_VOLUME_STEP, SYMBOL_VOLUME_LIMIT, SYMBOL_SWAP_LONG, SYMBOL_SWAP_SHORT, SYMBOL_MARGIN_INITIAL
};
enum ENUM_SYMBOL_INFO_INTEGER {
  SYMBOL_DIGITS, SYMBOL_SPREAD, SYMBOL_SPREAD_FLOAT, SYMBOL_TRADE_STOPS_LEVEL, SYMBOL_TRADE_FREEZE_LEVEL,
  SYMBOL_TRADE_MODE, SYMBOL_TRADE_EXEMODE, SYMBOL_FILLING_MODE, SYMBOL_EXPIRATION_MODE, SYMBOL_TIME, SYMBOL_SELECT, SYMBOL_VISIBLE
};
enum ENUM_SYMBOL_INFO_STRING { SYMBOL_CURRENCY_BASE, SYMBOL_CURRENCY_PROFIT, SYMBOL_CURRENCY_MARGIN, SYMBOL_DESCRIPTION, SYMBOL_PATH };
enum ENUM_ACCOUNT_INFO_DOUBLE { ACCOUNT_BALANCE, ACCOUNT_CREDIT, ACCOUNT_PROFIT, ACCOUNT_EQUITY, ACCOUNT_MARGIN,
                                ACCOUNT_MARGIN_FREE, ACCOUNT_MARGIN_LEVEL, ACCOUNT_MARGIN_SO_CALL, ACCOUNT_MARGIN_SO_SO };
enum ENUM_ACCOUNT_INFO_INTEGER { ACCOUNT_LOGIN, ACCOUNT_TRADE_MODE, ACCOUNT_LEVERAGE, ACCOUNT_LIMIT_ORDERS, ACCOUNT_MARGIN_SO_MODE,
                                 ACCOUNT_TRADE_ALLOWED, ACCOUNT_TRADE_EXPERT, ACCOUNT_MARGIN_MODE, ACCOUNT_CURRENCY_DIGITS };
enum ENUM_ACCOUNT_INFO_STRING { ACCOUNT_NAME, ACCOUNT_SERVER, ACCOUNT_CURRENCY, ACCOUNT_COMPANY };
enum ENUM_TERMINAL_INFO_INTEGER { TERMINAL_CONNECTED, TERMINAL_TRADE_ALLOWED, TERMINAL_DLLS_ALLOWED, TERMINAL_PING_LAST };
enum ENUM_MQL_INFO_INTEGER { MQL_TESTER, MQL_OPTIMIZATION, MQL_VISUAL_MODE, MQL_TRADE_ALLOWED, MQL_DEBUG, MQL_PROFILER };
enum ENUM_POSITION_PROPERTY_DOUBLE { POSITION_VOLUME, POSITION_PRICE_OPEN, POSITION_SL, POSITION_TP, POSITION_PRICE_CURRENT,
                                     POSITION_SWAP, POSITION_PROFIT };
enum ENUM_POSITION_PROPERTY_INTEGER { POSITION_TICKET, POSITION_TIME, POSITION_TIME_MSC, POSITION_TIME_UPDATE, POSITION_TYPE,
                                      POSITION_MAGIC, POSITION_IDENTIFIER, POSITION_REASON };
enum ENUM_POSITION_PROPERTY_STRING { POSITION_SYMBOL, POSITION_COMMENT, POSITION_EXTERNAL_ID };
enum ENUM_DEAL_PROPERTY_DOUBLE { DEAL_VOLUME, DEAL_PRICE, DEAL_COMMISSION, DEAL_SWAP, DEAL_PROFIT, DEAL_FEE, DEAL_SL, DEAL_TP };
enum ENUM_DEAL_PROPERTY_INTEGER { DEAL_TICKET, DEAL_ORDER, DEAL_TIME, DEAL_TIME_MSC, DEAL_TYPE, DEAL_ENTRY, DEAL_MAGIC,
                                  DEAL_REASON, DEAL_POSITION_ID };
enum ENUM_DEAL_PROPERTY_STRING { DEAL_SYMBOL, DEAL_COMMENT, DEAL_EXTERNAL_ID };
enum ENUM_STATISTICS { STAT_INITIAL_DEPOSIT, STAT_WITHDRAWAL, STAT_PROFIT, STAT_GROSS_PROFIT, STAT_GROSS_LOSS,
                       STAT_MAX_PROFITTRADE, STAT_MAX_LOSSTRADE, STAT_BALANCE_DD, STAT_BALANCE_DDREL_PERCENT,
                       STAT_EQUITY_DD, STAT_EQUITY_DDREL_PERCENT, STAT_EXPECTED_PAYOFF, STAT_PROFIT_FACTOR,
                       STAT_RECOVERY_FACTOR, STAT_SHARPE_RATIO, STAT_TRADES, STAT_PROFIT_TRADES, STAT_LOSS_TRADES,
                       STAT_DEALS };
enum ENUM_CALENDAR_EVENT_IMPORTANCE { CALENDAR_IMPORTANCE_NONE = 0, CALENDAR_IMPORTANCE_LOW, CALENDAR_IMPORTANCE_MODERATE,
                                      CALENDAR_IMPORTANCE_HIGH };
enum ENUM_CALENDAR_EVENT_TIMEMODE { CALENDAR_TIMEMODE_DATETIME = 0, CALENDAR_TIMEMODE_DATE, CALENDAR_TIMEMODE_NOTIME,
                                    CALENDAR_TIMEMODE_TENTATIVE };
enum ENUM_CALENDAR_EVENT_TYPE { CALENDAR_TYPE_EVENT = 0, CALENDAR_TYPE_INDICATOR, CALENDAR_TYPE_HOLIDAY };
enum ENUM_CALENDAR_EVENT_SECTOR { CALENDAR_SECTOR_NONE = 0 };
enum ENUM_CALENDAR_EVENT_FREQUENCY { CALENDAR_FREQUENCY_NONE = 0 };
enum ENUM_CALENDAR_EVENT_UNIT { CALENDAR_UNIT_NONE = 0 };
enum ENUM_CALENDAR_EVENT_MULTIPLIER { CALENDAR_MULTIPLIER_NONE = 0 };
enum ENUM_CALENDAR_EVENT_IMPACT { CALENDAR_IMPACT_NA = 0, CALENDAR_IMPACT_POSITIVE, CALENDAR_IMPACT_NEGATIVE };

const int INIT_SUCCEEDED = 0;
const int INIT_FAILED = 1;
const int INIT_PARAMETERS_INCORRECT = 2;
const int INVALID_HANDLE = -1;
const double EMPTY_VALUE = DBL_MAX;
const int WRONG_VALUE = -1;
const int TIME_DATE = 1;
const int TIME_MINUTES = 2;
const int TIME_SECONDS = 4;

const uint TRADE_RETCODE_REQUOTE = 10004, TRADE_RETCODE_REJECT = 10006, TRADE_RETCODE_CANCEL = 10007,
           TRADE_RETCODE_PLACED = 10008, TRADE_RETCODE_DONE = 10009, TRADE_RETCODE_DONE_PARTIAL = 10010,
           TRADE_RETCODE_ERROR = 10011, TRADE_RETCODE_TIMEOUT = 10012, TRADE_RETCODE_INVALID = 10013,
           TRADE_RETCODE_INVALID_VOLUME = 10014, TRADE_RETCODE_INVALID_PRICE = 10015, TRADE_RETCODE_INVALID_STOPS = 10016,
           TRADE_RETCODE_TRADE_DISABLED = 10017, TRADE_RETCODE_MARKET_CLOSED = 10018, TRADE_RETCODE_NO_MONEY = 10019,
           TRADE_RETCODE_PRICE_CHANGED = 10020, TRADE_RETCODE_PRICE_OFF = 10021, TRADE_RETCODE_INVALID_EXPIRATION = 10022,
           TRADE_RETCODE_ORDER_CHANGED = 10023, TRADE_RETCODE_TOO_MANY_REQUESTS = 10024, TRADE_RETCODE_NO_CHANGES = 10025,
           TRADE_RETCODE_SERVER_DISABLES_AT = 10026, TRADE_RETCODE_CLIENT_DISABLES_AT = 10027, TRADE_RETCODE_LOCKED = 10028,
           TRADE_RETCODE_FROZEN = 10029, TRADE_RETCODE_INVALID_FILL = 10030, TRADE_RETCODE_CONNECTION = 10031,
           TRADE_RETCODE_ONLY_REAL = 10032, TRADE_RETCODE_LIMIT_ORDERS = 10033, TRADE_RETCODE_LIMIT_VOLUME = 10034,
           TRADE_RETCODE_INVALID_ORDER = 10035, TRADE_RETCODE_POSITION_CLOSED = 10036;

// ------------------------------------------------------------------ structures
struct MqlDateTime { int year, mon, day, hour, min, sec, day_of_week, day_of_year; };
struct MqlTick { datetime time; double bid, ask, last; ulong volume; long time_msc; uint flags; double volume_real; };
struct MqlRates { datetime time; double open, high, low, close; long tick_volume; int spread; long real_volume; };
struct MqlTradeRequest {
  ENUM_TRADE_REQUEST_ACTIONS action; ulong magic; ulong order; string symbol; double volume; double price;
  double stoplimit; double sl; double tp; ulong deviation; ENUM_ORDER_TYPE type; ENUM_ORDER_TYPE_FILLING type_filling;
  ENUM_ORDER_TYPE_TIME type_time; datetime expiration; string comment; ulong position; ulong position_by;
};
struct MqlTradeResult { uint retcode; ulong deal; ulong order; double volume; double price; double bid; double ask;
                        string comment; uint request_id; int retcode_external; };
struct MqlTradeCheckResult { uint retcode; double balance; double equity; double profit; double margin;
                             double margin_free; double margin_level; string comment; };
struct MqlCalendarValue { ulong id; ulong event_id; datetime time; datetime period; int revision; long actual_value;
                          long prev_value; long revised_prev_value; long forecast_value; ENUM_CALENDAR_EVENT_IMPACT impact_type; };
struct MqlCalendarEvent { ulong id; ENUM_CALENDAR_EVENT_TYPE type; ENUM_CALENDAR_EVENT_SECTOR sector;
                          ENUM_CALENDAR_EVENT_FREQUENCY frequency; ENUM_CALENDAR_EVENT_TIMEMODE time_mode; ulong country_id;
                          ENUM_CALENDAR_EVENT_UNIT unit; ENUM_CALENDAR_EVENT_IMPORTANCE importance;
                          ENUM_CALENDAR_EVENT_MULTIPLIER multiplier; uint digits; string source_url; string event_code; string name; };

template <class T>
void ZeroMemory(T& x) { x = T(); }

// ------------------------------------------------------------------ formatting helpers
struct FmtArg {
  int k;  // 0 signed, 1 unsigned, 2 double, 3 string
  long long i = 0; unsigned long long u = 0; double d = 0; std::string s;
};
template <class T>
FmtArg fmt_arg(const T& v) {
  FmtArg a;
  if constexpr (std::is_same<T, string>::value) { a.k = 3; a.s = v.s; }
  else if constexpr (std::is_same<T, bool>::value) { a.k = 0; a.i = v ? 1 : 0; }
  else if constexpr (std::is_enum<T>::value) { a.k = 0; a.i = (long long)v; }
  else if constexpr (std::is_floating_point<T>::value) { a.k = 2; a.d = (double)v; }
  else if constexpr (std::is_integral<T>::value && std::is_signed<T>::value) { a.k = 0; a.i = (long long)v; }
  else if constexpr (std::is_integral<T>::value) { a.k = 1; a.u = (unsigned long long)v; }
  else if constexpr (std::is_convertible<T, const char*>::value) { a.k = 3; a.s = (const char*)v; }
  else static_assert(sizeof(T) == 0, "unsupported StringFormat argument type");
  return a;
}
std::string emu_format(const std::string& fmt, const std::vector<FmtArg>& args);

// ------------------------------------------------------------------ engine
struct EmuBar { datetime t; double o, h, l, c; long tv; };
struct EmuSeries { int tf; long sec; std::vector<EmuBar> bars; };
struct EmuInd {
  int kind;  // 1 MA, 2 RSI, 3 ATR, 4 ADX
  int tf; int p1, p2; int method; int applied; bool released = false;
  std::vector<std::vector<double>> buf;  // output buffers
  std::vector<std::vector<double>> aux;  // internal buffers
  size_t done = 0;                       // closed bars computed
};
struct EmuPos {
  ulong ticket, identifier; int type; double volume, open, sl, tp; datetime time; long time_msc; ulong magic;
  string comment; double swap; double initVolume, initSL, commission; double mfeR = 0;
};
struct EmuDeal {
  ulong ticket, order; datetime time; long time_msc; int type; int entry; ulong magic; ulong position_id;
  double volume, price, profit, commission, swap, fee, sl, tp; int reason; string comment;
};
struct EmuNews { datetime t; string currency; int importance; string name; };
// read-only extra symbol (multi-currency analysis): M1 history, served without look-ahead
struct EmuAux {
  std::string sym; int digits = 5; std::vector<EmuBar> m1;
  std::map<int, std::vector<EmuBar>> tf;          // resampled bars (complete history)
  std::map<int, std::vector<size_t>> first_m1;    // index of the first M1 bar of each resampled bar
};
struct EmuTradeRec {  // closed round trip (per position) for reports
  ulong ticket; int type; datetime open_time, close_time; double volume, open, close, initSL, tp, profit, riskMoney; string exit_reason;
};

struct EmuConfig {
  std::string symbol = "XAUUSD", base = "XAU", quote = "USD";
  int digits = 2; double contract = 100; double vmin = 0.01, vmax = 100, vstep = 0.01, vlimit = 0;
  double spread_points = 25; double commission_rt = 7.0; double swap_long = 0, swap_short = 0;
  long stops_level = 0, freeze_level = 0; int filling_flags = SYMBOL_FILLING_FOK | SYMBOL_FILLING_IOC; bool allow_return = false;
  int trade_mode = SYMBOL_TRADE_MODE_FULL;
  double deposit = 10000, leverage = 100; bool hedging = true; bool tester = true; int gmt_offset_live = 2; bool live_dst = true;
  double requote_prob = 0; bool ignore_sltp_on_open = false; bool reject_sltp = false; bool algo_allowed = true;
  long warmup_days = 30; datetime from = 0, to = 0; bool quiet = false; bool visual = false;
  std::string news_file; double quote_usd = 1.0;
};

struct Emu {
  EmuConfig cfg;
  double point = 0.01;
  std::vector<EmuSeries> series;
  std::vector<EmuInd> inds;
  MqlTick tick{}; datetime prev_tick_time = 0; bool tick_is_bar_open = false;
  bool started = false; bool stopped = false;
  double balance = 0;
  std::vector<EmuPos> pos; std::vector<EmuDeal> deals; std::vector<EmuTradeRec> trades;
  std::vector<size_t> hist_sel; long selected_pos = -1;
  ulong next_ticket = 1000;
  std::map<std::string, double> gv;
  int last_error = 0; int timer_sec = 0; datetime next_timer = 0;
  std::string last_comment; std::FILE* log = stdout;
  std::mt19937 rng{12345};
  std::vector<EmuNews> news;
  std::vector<EmuAux> aux;
  EmuAux* find_aux(const std::string& s) { for (auto& a : aux) if (a.sym == s) return &a; return nullptr; }
  datetime last_day = 0;
  // statistics
  double peak_equity = 0, max_dd = 0, max_dd_rel = 0, peak_balance = 0, max_bdd = 0, max_bdd_rel = 0;
  long n_requests = 0, n_modify = 0, n_rejected = 0;
  std::vector<std::pair<datetime, double>> equity_curve;
  std::map<std::string, long> event_counts;

  double price_conv(double price_now) const {  // profit currency -> account currency (USD)
    if (cfg.quote == "USD") return 1.0;
    if (cfg.base == "USD") return price_now > 0 ? 1.0 / price_now : 0.0;
    return cfg.quote_usd;                        // crosses: fixed approximate conversion rate
  }
  double margin_rate(double price_now) const {
    if (cfg.base == "USD") return 1.0;
    if (cfg.quote == "USD") return price_now;
    return price_now * cfg.quote_usd;
  }
  double pos_profit(const EmuPos& p) const {
    double px = p.type == 0 ? tick.bid : tick.ask;
    double diff = p.type == 0 ? px - p.open : p.open - px;
    return diff * p.volume * cfg.contract * price_conv(px);
  }
  double floating() const { double f = 0; for (auto& p : pos) f += pos_profit(p) + p.swap; return f; }
  double equity() const { return balance + floating(); }
  double margin() const {
    double m = 0;
    for (auto& p : pos) m += p.volume * cfg.contract * margin_rate(p.open) / cfg.leverage;
    return m;
  }
  EmuSeries& ser(int tf);
  void on_tick_price(datetime t, double bid, bool bar_open);
  void check_stops();
  void close_volume(size_t idx, double vol, double price, int reason, const string& comment);
  void calc_ind(EmuInd& ind, size_t upto_inclusive);
  void ind_step(EmuInd& ind, const std::vector<EmuBar>& b, size_t i, double* out, double* aux_out);
  void log_event(const std::string& kind) { event_counts[kind]++; }
};
extern Emu E;

// ------------------------------------------------------------------ predefined variables
extern string _Symbol;
extern ENUM_TIMEFRAMES _Period;
extern double _Point;
extern int _Digits;

[[noreturn]] inline void emu_fatal(const std::string& msg) {
  std::fprintf(stderr, "\n*** MQL5 RUNTIME ERROR (critical, EA would be stopped): %s at %s\n", msg.c_str(),
               "sim-time");
  std::fflush(stderr);
  std::abort();
}

// ------------------------------------------------------------------ math & conversion
template <class A, class B>
typename std::common_type<A, B>::type MathMax(A a, B b) { return a > b ? a : b; }
template <class A, class B>
typename std::common_type<A, B>::type MathMin(A a, B b) { return a < b ? a : b; }
inline double MathAbs(double v) { return std::fabs(v); }
inline long MathAbs(long v) { return v < 0 ? -v : v; }
inline int MathAbs(int v) { return v < 0 ? -v : v; }
inline double MathRound(double v) { return std::round(v); }
inline double MathFloor(double v) { return std::floor(v); }
inline double MathCeil(double v) { return std::ceil(v); }
inline double MathSqrt(double v) { return std::sqrt(v); }
inline double MathPow(double b, double e) { return std::pow(b, e); }
inline double MathLog(double v) { return std::log(v); }
inline double MathLog10(double v) { return std::log10(v); }
inline double MathExp(double v) { return std::exp(v); }
inline bool MathIsValidNumber(double v) { return std::isfinite(v); }
inline double NormalizeDouble(double v, int digits) {
  if (digits < 0) digits = 0;
  if (digits > 8) digits = 8;
  double p = std::pow(10.0, digits);
  return std::round(v * p) / p;
}
inline string DoubleToString(double v, int digits = 8) {
  char b[64];
  if (digits < 0 || digits > 16) digits = 8;
  snprintf(b, sizeof b, "%.*f", digits, v);
  return string(b);
}
inline string IntegerToString(long v, int len = 0, ushort fill = ' ') {
  std::string s = std::to_string(v);
  while ((int)s.size() < len) s.insert(s.begin(), (char)fill);
  return string(s);
}
inline long StringToInteger(const string& s) { return std::strtol(s.s.c_str(), nullptr, 10); }
inline double StringToDouble(const string& s) { return std::strtod(s.s.c_str(), nullptr); }
inline int StringLen(const string& s) { return (int)s.s.size(); }
inline int StringFind(const string& s, const string& m, int start = 0) {
  size_t p = s.s.find(m.s, (size_t)std::max(0, start));
  return p == std::string::npos ? -1 : (int)p;
}
inline string StringSubstr(const string& s, int start, int length = -1) {
  if (start < 0 || (size_t)start >= s.s.size()) return string();
  return string(length < 0 ? s.s.substr((size_t)start) : s.s.substr((size_t)start, (size_t)length));
}
inline int StringSplit(const string& s, ushort sep, MqlArray<string>& out) {
  out.v.clear();
  if (s.s.empty()) return 0;
  std::string cur;
  for (char c : s.s) {
    if ((ushort)(uchar)c == sep) { out.v.push_back(string(cur)); cur.clear(); }
    else cur += c;
  }
  out.v.push_back(string(cur));
  return (int)out.v.size();
}
inline int StringTrimLeft(string& s) {
  size_t i = 0; while (i < s.s.size() && std::isspace((uchar)s.s[i])) i++;
  s.s.erase(0, i); return (int)i;
}
inline int StringTrimRight(string& s) {
  size_t n = 0; while (!s.s.empty() && std::isspace((uchar)s.s.back())) { s.s.pop_back(); n++; }
  return (int)n;
}
inline bool StringToUpper(string& s) { for (auto& c : s.s) c = (char)std::toupper((uchar)c); return true; }
inline bool StringToLower(string& s) { for (auto& c : s.s) c = (char)std::tolower((uchar)c); return true; }
inline int StringReplace(string& s, const string& f, const string& r) {
  if (f.s.empty()) return 0;
  int n = 0; size_t p = 0;
  while ((p = s.s.find(f.s, p)) != std::string::npos) { s.s.replace(p, f.s.size(), r.s); p += r.s.size(); n++; }
  return n;
}
template <class... A>
string StringFormat(const string& fmt, const A&... a) {
  std::vector<FmtArg> v{fmt_arg(a)...};
  return string(emu_format(fmt.s, v));
}

// ------------------------------------------------------------------ arrays
template <class T> int ArraySize(const MqlArray<T>& a) { return (int)a.v.size(); }
template <class T> int ArrayResize(MqlArray<T>& a, int n, int reserve = 0) {
  (void)reserve;
  if (n < 0) return -1;
  a.v.resize((size_t)n);
  return n;
}
template <class T> bool ArraySetAsSeries(MqlArray<T>& a, bool s) { a.series = s; return true; }
template <class T> bool ArrayGetAsSeries(const MqlArray<T>& a) { return a.series; }
template <class T> void ArrayFree(MqlArray<T>& a) { a.v.clear(); }
template <class T, class V> int ArrayInitialize(MqlArray<T>& a, V val) { for (auto& x : a.v) x = (T)val; return (int)a.v.size(); }

// ------------------------------------------------------------------ time
bool TimeToStruct(datetime t, MqlDateTime& s);
datetime StructToTime(MqlDateTime& s);
string TimeToString(datetime t, int mode = TIME_DATE | TIME_MINUTES);
inline datetime TimeCurrent() { return E.tick.time; }
inline datetime TimeTradeServer() { return E.tick.time; }
inline datetime TimeGMT() {
  if (E.cfg.tester) return E.tick.time;  // like MT5's tester
  MqlDateTime d; TimeToStruct(E.tick.time, d);
  long off = E.cfg.gmt_offset_live * 3600L;
  // US DST approximation for the simulated broker clock
  if (E.cfg.live_dst && d.mon > 3 && d.mon < 11) off += 3600;
  return E.tick.time - off;
}
inline datetime TimeLocal() { return TimeGMT(); }
inline uint GetTickCount() { return (uint)((ulong)E.tick.time * 1000UL); }
inline ulong GetMicrosecondCount() { return (ulong)E.tick.time * 1000000UL; }
inline void Sleep(int) {}
inline bool IsStopped() { return E.stopped; }
inline int GetLastError() { return E.last_error; }
inline void ResetLastError() { E.last_error = 0; }
inline bool EventSetTimer(int s) { E.timer_sec = s; E.next_timer = E.tick.time + s; return true; }
inline void EventKillTimer() { E.timer_sec = 0; }
int PeriodSeconds(ENUM_TIMEFRAMES tf = PERIOD_CURRENT);

// ------------------------------------------------------------------ output
inline std::string emu_to_text(const string& s) { return s.s; }
inline std::string emu_to_text(const char* s) { return s; }
template <class T>
std::string emu_to_text(const T& v) {
  if constexpr (std::is_floating_point<T>::value) { char b[64]; snprintf(b, sizeof b, "%.8g", (double)v); return b; }
  else return std::to_string((long long)v);
}
void emu_print_line(const std::string& s);
template <class... A> void Print(const A&... a) { std::string s; ((s += emu_to_text(a)), ...); emu_print_line(s); }
template <class... A> void Alert(const A&... a) { std::string s = "ALERT: "; ((s += emu_to_text(a)), ...); emu_print_line(s); }
template <class... A> void Comment(const A&... a) { std::string s; ((s += emu_to_text(a)), ...); if (!s.empty()) E.last_comment = s; }
template <class... A> void PrintFormat(const string& fmt, const A&... a) {
  std::vector<FmtArg> v{fmt_arg(a)...};
  emu_print_line(emu_format(fmt.s, v));
}

// ------------------------------------------------------------------ info functions
double SymbolInfoDouble(const string& sym, ENUM_SYMBOL_INFO_DOUBLE p);
long SymbolInfoInteger(const string& sym, ENUM_SYMBOL_INFO_INTEGER p);
string SymbolInfoString(const string& sym, ENUM_SYMBOL_INFO_STRING p);
bool SymbolInfoTick(const string& sym, MqlTick& t);
double AccountInfoDouble(ENUM_ACCOUNT_INFO_DOUBLE p);
long AccountInfoInteger(ENUM_ACCOUNT_INFO_INTEGER p);
string AccountInfoString(ENUM_ACCOUNT_INFO_STRING p);
int TerminalInfoInteger(ENUM_TERMINAL_INFO_INTEGER p);
int MQLInfoInteger(ENUM_MQL_INFO_INTEGER p);

// ------------------------------------------------------------------ series & indicators
int Bars(const string& sym, ENUM_TIMEFRAMES tf);
datetime iTime(const string& sym, ENUM_TIMEFRAMES tf, int shift);
double iOpen(const string& sym, ENUM_TIMEFRAMES tf, int shift);
double iHigh(const string& sym, ENUM_TIMEFRAMES tf, int shift);
double iLow(const string& sym, ENUM_TIMEFRAMES tf, int shift);
double iClose(const string& sym, ENUM_TIMEFRAMES tf, int shift);
int iBarShift(const string& sym, ENUM_TIMEFRAMES tf, datetime time, bool exact = false);
bool SymbolSelect(const string& sym, bool select);
int CopyRates(const string& sym, ENUM_TIMEFRAMES tf, int start, int count, MqlArray<MqlRates>& out);
int iMA(const string& sym, ENUM_TIMEFRAMES tf, int period, int shift, ENUM_MA_METHOD method, ENUM_APPLIED_PRICE price);
int iRSI(const string& sym, ENUM_TIMEFRAMES tf, int period, ENUM_APPLIED_PRICE price);
int iATR(const string& sym, ENUM_TIMEFRAMES tf, int period);
int iADX(const string& sym, ENUM_TIMEFRAMES tf, int period);
int CopyBuffer(int handle, int buffer, int start, int count, MqlArray<double>& out);
int BarsCalculated(int handle);
bool IndicatorRelease(int handle);

// ------------------------------------------------------------------ trading
bool OrderSend(MqlTradeRequest& req, MqlTradeResult& res);
bool OrderCheck(MqlTradeRequest& req, MqlTradeCheckResult& res);
bool OrderCalcProfit(ENUM_ORDER_TYPE type, const string& sym, double vol, double open, double close, double& profit);
bool OrderCalcMargin(ENUM_ORDER_TYPE type, const string& sym, double vol, double price, double& margin);
int PositionsTotal();
ulong PositionGetTicket(int index);
bool PositionSelectByTicket(ulong ticket);
bool PositionSelect(const string& sym);
double PositionGetDouble(ENUM_POSITION_PROPERTY_DOUBLE p);
long PositionGetInteger(ENUM_POSITION_PROPERTY_INTEGER p);
string PositionGetString(ENUM_POSITION_PROPERTY_STRING p);
inline int OrdersTotal() { return 0; }
bool HistorySelect(datetime from, datetime to);
bool HistorySelectByPosition(long position_id);
int HistoryDealsTotal();
ulong HistoryDealGetTicket(int index);
double HistoryDealGetDouble(ulong ticket, ENUM_DEAL_PROPERTY_DOUBLE p);
long HistoryDealGetInteger(ulong ticket, ENUM_DEAL_PROPERTY_INTEGER p);
string HistoryDealGetString(ulong ticket, ENUM_DEAL_PROPERTY_STRING p);

// ------------------------------------------------------------------ global variables
bool GlobalVariableCheck(const string& name);
double GlobalVariableGet(const string& name);
datetime GlobalVariableSet(const string& name, double value);
bool GlobalVariableDel(const string& name);
int GlobalVariablesTotal();
string GlobalVariableName(int index);

// ------------------------------------------------------------------ calendar
bool CalendarValueHistory(MqlArray<MqlCalendarValue>& values, datetime from, datetime to = 0,
                          const string& country_code = NULL, const string& currency = NULL);
bool CalendarEventById(ulong event_id, MqlCalendarEvent& event);

// ------------------------------------------------------------------ tester
double TesterStatistics(ENUM_STATISTICS s);

// ------------------------------------------------------------------ input registration
struct InputReg {
  static std::map<std::string, std::function<void(const std::string&)>>& table() {
    static std::map<std::string, std::function<void(const std::string&)>> t; return t;
  }
  template <class T>
  InputReg(const char* name, T* ptr) {
    table()[name] = [ptr](const std::string& v) {
      if constexpr (std::is_same<T, string>::value) *ptr = string(v);
      else if constexpr (std::is_same<T, bool>::value) *ptr = (v == "true" || v == "1");
      else if constexpr (std::is_enum<T>::value) *ptr = (T)std::stol(v);
      else if constexpr (std::is_floating_point<T>::value) *ptr = (T)std::stod(v);
      else *ptr = (T)std::stoll(v);
    };
  }
};
#define REG_INPUT(NAME) static InputReg NAME##_reg_(#NAME, &NAME);
