//+------------------------------------------------------------------+
//|                                                     IABot_M5.mq5 |
//|      Expert Advisor M5 : tendance multi-timeframe + repli RSI    |
//|                                                                  |
//|  Logique :                                                       |
//|   1. Tendance sur H1 : cloture > EMA200 et EMA50 > EMA200        |
//|      (inverse pour la vente).                                    |
//|   2. Entree sur M5 : repli court terme = RSI(3) < 10 en tendance |
//|      haussiere (RSI(3) > 90 en tendance baissiere), bougie M5    |
//|      cloturee uniquement (aucun repaint).                        |
//|   3. Stop loss = 3 x ATR(14) H1, take profit = 4 R.              |
//|   4. Break-even a +0.8 R (verrouille +0.1 R), trailing stop a    |
//|      partir de +2 R (distance 1.5 R), cloture partielle option.  |
//|   5. Risque fixe en % du capital, limites journalieres,          |
//|      coupe-circuit drawdown, filtres session / spread / news.    |
//+------------------------------------------------------------------+
#property copyright   "IABot"
#property version     "1.00"
#property description "EA M5 : tendance H1 (EMA 50/200) + repli RSI(3) sur M5."
#property description "SL/TP automatiques (ATR H1), break-even, trailing stop,"
#property description "risque fixe en %, limites journalieres, filtres session/spread/news."

//+------------------------------------------------------------------+
//| Enumerations                                                      |
//+------------------------------------------------------------------+
enum ENUM_RISK_MODE
  {
   RISK_PCT_BALANCE = 0, // % du solde
   RISK_PCT_EQUITY  = 1, // % des fonds propres (equity)
   RISK_FIXED_LOT   = 2  // Lot fixe
  };

enum ENUM_TIME_BASE
  {
   TIME_BASE_SERVER = 0, // Heure du serveur (heure du graphique MT5)
   TIME_BASE_GMT    = 1  // Heure GMT / UTC
  };

//+------------------------------------------------------------------+
//| Parametres                                                        |
//+------------------------------------------------------------------+
input group "=== Général ==="
input ulong           InpMagic            = 26111601;          // Numéro magique (identifiant des trades du robot)
input string          InpTradeComment     = "IABot_M5";        // Commentaire des ordres
input ENUM_TIMEFRAMES InpSignalTF         = PERIOD_M5;         // Unité de temps des signaux (M5)

input group "=== Stratégie : tendance + repli ==="
input ENUM_TIMEFRAMES InpTrendTF          = PERIOD_H1;         // Unité de temps de la tendance
input int             InpTrendFastEMA     = 50;                // EMA rapide de tendance
input int             InpTrendSlowEMA     = 200;               // EMA lente de tendance
input int             InpTrendADXMin      = 0;                 // ADX minimum de la tendance (0 = désactivé)
input int             InpRSIPeriod        = 3;                 // Période du RSI de repli (M5)
input double          InpRSIBuyLevel      = 10.0;              // Achat si RSI M5 < ce niveau
input double          InpRSISellLevel     = 90.0;              // Vente si RSI M5 > ce niveau
input int             InpATRPeriod        = 14;                // Période ATR (unité de tendance)

input group "=== Stop loss / Take profit / Break-even ==="
input double          InpSL_ATR           = 3.0;               // Stop loss = ATR x (définit 1 R)
input double          InpTP_R             = 4.0;               // Take profit = R x
input bool            InpUseBreakEven     = true;              // Activer le break-even
input double          InpBE_TriggerR      = 0.8;               // Break-even déclenché à +R
input double          InpBE_LockR         = 0.1;               // Gain verrouillé au break-even (R)
input bool            InpUseTrailing      = true;              // Activer le trailing stop
input double          InpTrailStartR      = 2.0;               // Trailing actif à partir de +R
input double          InpTrailDistR       = 1.5;               // Distance du trailing (R)
input bool            InpUsePartialClose  = false;             // Clôture partielle
input double          InpPartialAtR       = 1.0;               // Clôture partielle à +R
input double          InpPartialPercent   = 50.0;              // % du volume clôturé
input int             InpMaxHoldHours     = 0;                 // Durée max d'un trade en heures (0 = illimitée)

input group "=== Gestion du risque ==="
input ENUM_RISK_MODE  InpRiskMode         = RISK_PCT_BALANCE;  // Calcul du lot
input double          InpRiskPercent      = 0.5;               // Risque par trade (%)
input double          InpFixedLot         = 0.01;              // Lot fixe (mode lot fixe)
input double          InpMaxLot           = 50.0;              // Lot maximum
input double          InpMinLotMaxRiskPct = 2.0;               // Risque max (%) toléré si le lot minimum est imposé
input double          InpCommissionPerLot = 0.0;               // Commission aller-retour par lot (devise du compte)
input double          InpMaxDailyLossPct  = 3.0;               // Perte journalière max en % (0 = off)
input bool            InpCloseOnDailyLoss = false;             // Fermer les positions si la perte journalière est atteinte
input double          InpMaxDrawdownPct   = 15.0;              // Drawdown max depuis le sommet en % (0 = off)
input bool            InpCloseOnMaxDD     = true;              // Fermer les positions si le drawdown max est atteint
input bool            InpResetProtection  = false;             // Réarmer le robot après un arrêt drawdown
input int             InpMaxTradesPerDay  = 4;                 // Trades max par jour (0 = illimité)
input int             InpMaxConsecLosses  = 3;                 // Pertes consécutives max par jour (0 = off)
input int             InpMaxSpreadPoints  = 0;                 // Spread max en points (0 = automatique)
input double          InpMaxSpreadPctSL   = 10.0;              // Spread max en % de la distance du SL
input int             InpSlippagePoints   = 30;                // Glissement max (points)

input group "=== Horaires ==="
input ENUM_TIME_BASE  InpTimeBase         = TIME_BASE_SERVER;  // Référence horaire de la session
input int             InpSessionStart     = 9;                 // Début de session (heure)
input int             InpSessionEnd       = 20;                // Fin de session (heure, exclue)
input int             InpFridayLastEntry  = 18;                // Vendredi : pas de nouveau trade à partir de (heure serveur, -1 = off)
input int             InpFridayCloseHour  = 22;                // Vendredi : fermeture des positions (heure serveur, -1 = off)
input int             InpTesterGMTOffset  = 2;                 // Testeur : décalage GMT du serveur (hiver)
input bool            InpTesterUSDST      = true;              // Testeur : +1h pendant l'heure d'été US

input group "=== Filtre actualités (calendrier MT5) ==="
input bool            InpUseNewsFilter    = true;              // Activer le filtre des news
input int             InpNewsBeforeMin    = 30;                // Pause avant une news (minutes)
input int             InpNewsAfterMin     = 30;                // Pause après une news (minutes)
input bool            InpNewsHighOnly     = true;              // Uniquement les news à fort impact
input string          InpNewsCurrencies   = "";                // Devises surveillées (vide = devises du symbole)

input group "=== Affichage ==="
input bool            InpShowPanel        = true;              // Afficher le panneau d'information

//+------------------------------------------------------------------+
//| Variables globales                                                |
//+------------------------------------------------------------------+
int      g_hEmaFast        = INVALID_HANDLE;
int      g_hEmaSlow        = INVALID_HANDLE;
int      g_hATR            = INVALID_HANDLE;
int      g_hRSI            = INVALID_HANDLE;
int      g_hADX            = INVALID_HANDLE;

bool     g_isTester        = false;
bool     g_isHedging       = true;
ENUM_ORDER_TYPE_FILLING g_filling = ORDER_FILLING_FOK;

datetime g_lastSignalBar   = 0;
string   g_gvPrefix        = "";

datetime g_dayStart        = 0;
double   g_dayStartBalance = 0.0;
bool     g_dailyHalt       = false;
bool     g_ddHalt          = false;
double   g_peakEquity      = 0.0;
double   g_peakSaved       = 0.0;

int      g_tradesToday     = 0;
int      g_consecLosses    = 0;
double   g_closedPLToday   = 0.0;

string   g_newsCurrencies[];
datetime g_newsTimes[];
string   g_newsNames[];
datetime g_newsLastRefresh = 0;
bool     g_newsAvailable   = true;

ulong    g_failTickets[];
datetime g_failTimes[];

string   g_status          = "Initialisation";
string   g_trendText       = "-";
double   g_lastRSI         = 0.0;
uint     g_lastPanelMs     = 0;

//+------------------------------------------------------------------+
//| Outils : symbole, prix, volumes                                   |
//+------------------------------------------------------------------+
double SymPoint()
  {
   return SymbolInfoDouble(_Symbol, SYMBOL_POINT);
  }

int SymDigits()
  {
   return (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
  }

double TickSize()
  {
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(ts <= 0.0)
      ts = SymPoint();
   return ts;
  }

double NormalizePrice(const double price)
  {
   double ts = TickSize();
   if(ts <= 0.0)
      return NormalizeDouble(price, SymDigits());
   return NormalizeDouble(MathRound(price / ts) * ts, SymDigits());
  }

int VolumeDigits()
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0.0)
      return 2;
   int d = (int)MathCeil(-MathLog10(step) - 1e-9);
   if(d < 0)
      d = 0;
   if(d > 8)
      d = 8;
   return d;
  }

double NormalizeVolume(const double volume)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step <= 0.0)
      step = (vmin > 0.0 ? vmin : 0.01);
   double v = MathFloor(volume / step + 1e-7) * step;
   if(vmax > 0.0 && v > vmax)
      v = vmax;
   return NormalizeDouble(v, VolumeDigits());
  }

// distance minimale (prix) imposée par le courtier entre le prix et SL/TP
double StopsMinDistance()
  {
   long lvl = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   return (double)(lvl + 1) * SymPoint();
  }

double FreezeDistance()
  {
   long lvl = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   return (double)lvl * SymPoint();
  }

string TFToString(const ENUM_TIMEFRAMES tf)
  {
   switch(tf)
     {
      case PERIOD_M1:
         return "M1";
      case PERIOD_M5:
         return "M5";
      case PERIOD_M15:
         return "M15";
      case PERIOD_M30:
         return "M30";
      case PERIOD_H1:
         return "H1";
      case PERIOD_H4:
         return "H4";
      case PERIOD_D1:
         return "D1";
      default:
         break;
     }
   return "TF" + IntegerToString(PeriodSeconds(tf) / 60);
  }

string FmtMoney(const double v)
  {
   return DoubleToString(v, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY);
  }

//+------------------------------------------------------------------+
//| Outils : temps                                                    |
//+------------------------------------------------------------------+
datetime DayStart(const datetime t)
  {
   return t - (t % 86400);
  }

int DowOf(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   return dt.day_of_week;
  }

int HourOf(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   return dt.hour;
  }

// jour (du mois) du n-ième dimanche d'un mois donné
int NthSunday(const int year, const int month, const int n)
  {
   MqlDateTime dt;
   dt.year = year;
   dt.mon = month;
   dt.day = 1;
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;
   dt.day_of_week = 0;
   dt.day_of_year = 0;
   datetime first = StructToTime(dt);
   int dow = DowOf(first);
   int firstSunday = 1 + ((7 - dow) % 7);
   return firstSunday + 7 * (n - 1);
  }

// heure d'été américaine active (2e dimanche de mars -> 1er dimanche de novembre)
bool IsUSDST(const datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   int startDay = NthSunday(dt.year, 3, 2);
   int endDay = NthSunday(dt.year, 11, 1);
   if(dt.mon < 3 || dt.mon > 11)
      return false;
   if(dt.mon > 3 && dt.mon < 11)
      return true;
   if(dt.mon == 3)
      return dt.day >= startDay;
   return dt.day < endDay;
  }

// décalage (secondes) entre l'heure du serveur et GMT
int ServerGMTOffset(const datetime serverTime)
  {
   if(g_isTester)
     {
      int off = InpTesterGMTOffset * 3600;
      if(InpTesterUSDST && IsUSDST(serverTime))
         off += 3600;
      return off;
     }
   long diff = (long)(TimeTradeServer() - TimeGMT());
   return (int)(MathRound((double)diff / 1800.0) * 1800.0);
  }

// heure (0-23) dans la référence choisie pour la session
int SessionHour(const datetime serverTime)
  {
   if(InpTimeBase == TIME_BASE_GMT)
      return HourOf(serverTime - ServerGMTOffset(serverTime));
   return HourOf(serverTime);
  }

bool HourInWindow(const int h, const int startH, const int endH)
  {
   if(startH == endH)
      return true;
   if(startH < endH)
      return (h >= startH && h < endH);
   return (h >= startH || h < endH);
  }

//+------------------------------------------------------------------+
//| Outils : indicateurs                                              |
//+------------------------------------------------------------------+
bool GetIndicatorValue(const int handle, const int buffer, const int shift, double &value)
  {
   value = 0.0;
   if(handle == INVALID_HANDLE)
      return false;
   double buf[];
   ResetLastError();
   if(CopyBuffer(handle, buffer, shift, 1, buf) != 1)
      return false;
   value = buf[0];
   if(!MathIsValidNumber(value) || value == EMPTY_VALUE)
      return false;
   return true;
  }

//+------------------------------------------------------------------+
//| Variables globales du terminal (persistance après redémarrage)    |
//+------------------------------------------------------------------+
string GVName(const string key)
  {
   return g_gvPrefix + key;
  }

double GVGet(const string key, const double def)
  {
   string n = GVName(key);
   if(!GlobalVariableCheck(n))
      return def;
   return GlobalVariableGet(n);
  }

void GVSet(const string key, const double value)
  {
   GlobalVariableSet(GVName(key), value);
  }

void GVDel(const string key)
  {
   string n = GVName(key);
   if(GlobalVariableCheck(n))
      GlobalVariableDel(n);
  }

string TicketKey(const string kind, const ulong ticket)
  {
   return kind + IntegerToString((long)ticket);
  }

bool IsMyPosition(const ulong ticket)
  {
   if(!PositionSelectByTicket(ticket))
      return false;
   if(PositionGetString(POSITION_SYMBOL) != _Symbol)
      return false;
   return ((ulong)PositionGetInteger(POSITION_MAGIC) == InpMagic);
  }

// supprime les données mémorisées de positions qui n'existent plus
void CleanupTicketVariables()
  {
   string pr = g_gvPrefix + "R";
   string pv = g_gvPrefix + "V";
   int prLen = StringLen(pr);
   for(int i = GlobalVariablesTotal() - 1; i >= 0; i--)
     {
      string n = GlobalVariableName(i);
      bool isR = (StringFind(n, pr) == 0);
      bool isV = (StringFind(n, pv) == 0);
      if(!isR && !isV)
         continue;
      string num = StringSubstr(n, prLen);
      ulong ticket = (ulong)StringToInteger(num);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         GlobalVariableDel(n);
     }
  }

//+------------------------------------------------------------------+
//| Compte / historique                                               |
//+------------------------------------------------------------------+
void UpdateDayAnchor()
  {
   datetime today = DayStart(TimeCurrent());
   if(today == g_dayStart)
      return;
   g_dayStart = today;
   g_dailyHalt = false;
   double savedDay = GVGet("day", 0.0);
   double savedBal = GVGet("daybal", 0.0);
   if((datetime)(long)savedDay == today && savedBal > 0.0)
      g_dayStartBalance = savedBal;
   else
     {
      g_dayStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      GVSet("day", (double)today);
      GVSet("daybal", g_dayStartBalance);
     }
  }

void ComputeTodayStats()
  {
   g_tradesToday = 0;
   g_consecLosses = 0;
   g_closedPLToday = 0.0;
   if(!HistorySelect(g_dayStart, TimeCurrent() + 86400))
      return;
   int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong deal = HistoryDealGetTicket(i);
      if(deal == 0)
         continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol)
         continue;
      if((ulong)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic)
         continue;
      ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY);
      double pl = HistoryDealGetDouble(deal, DEAL_PROFIT)
                  + HistoryDealGetDouble(deal, DEAL_COMMISSION)
                  + HistoryDealGetDouble(deal, DEAL_SWAP)
                  + HistoryDealGetDouble(deal, DEAL_FEE);
      g_closedPLToday += pl;
      if(entry == DEAL_ENTRY_IN)
         g_tradesToday++;
      else
         if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY || entry == DEAL_ENTRY_INOUT)
           {
            if(pl < 0.0)
               g_consecLosses++;
            else
               g_consecLosses = 0;
           }
     }
  }

int CountMyPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      count++;
     }
   return count;
  }

int CountSymbolPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol)
         count++;
     }
   return count;
  }

//+------------------------------------------------------------------+
//| Envoi des ordres                                                  |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING DetectFilling()
  {
   long fm = SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((fm & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   if((fm & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
  }

ENUM_ORDER_TYPE_FILLING NextFilling(const ENUM_ORDER_TYPE_FILLING f)
  {
   if(f == ORDER_FILLING_FOK)
      return ORDER_FILLING_IOC;
   if(f == ORDER_FILLING_IOC)
      return ORDER_FILLING_RETURN;
   return ORDER_FILLING_FOK;
  }

bool IsRetryable(const uint rc)
  {
   return (rc == TRADE_RETCODE_REQUOTE || rc == TRADE_RETCODE_PRICE_CHANGED ||
           rc == TRADE_RETCODE_PRICE_OFF || rc == TRADE_RETCODE_TIMEOUT ||
           rc == TRADE_RETCODE_CONNECTION || rc == TRADE_RETCODE_TOO_MANY_REQUESTS ||
           rc == TRADE_RETCODE_LOCKED);
  }

// envoie une requête avec nouvelles tentatives (requote, prix modifié, mode de remplissage...)
bool SendRequest(MqlTradeRequest &req, MqlTradeResult &res, const string what)
  {
   for(int attempt = 0; attempt < 5; attempt++)
     {
      if(attempt > 0 && req.action == TRADE_ACTION_DEAL)
        {
         MqlTick tk;
         if(SymbolInfoTick(_Symbol, tk))
            req.price = (req.type == ORDER_TYPE_BUY) ? tk.ask : tk.bid;
        }
      ZeroMemory(res);
      ResetLastError();
      bool sent = OrderSend(req, res);
      uint rc = res.retcode;
      if(rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_DONE_PARTIAL || rc == TRADE_RETCODE_PLACED)
         return true;
      if(rc == TRADE_RETCODE_NO_CHANGES && req.action == TRADE_ACTION_SLTP)
         return true;
      if(rc == TRADE_RETCODE_INVALID_FILL && req.action == TRADE_ACTION_DEAL)
        {
         req.type_filling = NextFilling(req.type_filling);
         g_filling = req.type_filling;
         continue;
        }
      if(IsRetryable(rc))
        {
         if(!g_isTester)
            Sleep(250 * (attempt + 1));
         continue;
        }
      PrintFormat("IABot: échec %s (envoyé=%s) retcode=%u (%s) erreur=%d",
                  what, (sent ? "oui" : "non"), rc, res.comment, GetLastError());
      return false;
     }
   PrintFormat("IABot: échec %s après plusieurs tentatives, dernier retcode=%u (%s)",
               what, res.retcode, res.comment);
   return false;
  }

bool ModifyStops(const ulong ticket, const double sl, const double tp, const string why)
  {
   if(!PositionSelectByTicket(ticket))
      return false;
   MqlTradeRequest req;
   MqlTradeResult res;
   ZeroMemory(req);
   ZeroMemory(res);
   req.action = TRADE_ACTION_SLTP;
   req.position = ticket;
   req.symbol = _Symbol;
   req.sl = sl;
   req.tp = tp;
   req.magic = InpMagic;
   bool ok = SendRequest(req, res, "modification SL/TP (" + why + ")");
   if(ok)
      PrintFormat("IABot: #%I64u %s -> SL=%s TP=%s", ticket, why,
                  DoubleToString(sl, SymDigits()), DoubleToString(tp, SymDigits()));
   return ok;
  }

bool ClosePosition(const ulong ticket, const double volume, const string why)
  {
   if(!PositionSelectByTicket(ticket))
      return false;
   MqlTick tk;
   if(!SymbolInfoTick(_Symbol, tk))
      return false;
   ENUM_POSITION_TYPE ptype = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double posVol = PositionGetDouble(POSITION_VOLUME);
   double vol = NormalizeVolume(MathMin(volume, posVol));
   if(vol <= 0.0)
      return false;
   MqlTradeRequest req;
   MqlTradeResult res;
   ZeroMemory(req);
   ZeroMemory(res);
   req.action = TRADE_ACTION_DEAL;
   req.position = ticket;
   req.symbol = _Symbol;
   req.volume = vol;
   req.type = (ptype == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   req.price = (ptype == POSITION_TYPE_BUY) ? tk.bid : tk.ask;
   req.deviation = (ulong)InpSlippagePoints;
   req.magic = InpMagic;
   req.type_filling = g_filling;
   req.type_time = ORDER_TIME_GTC;
   req.comment = InpTradeComment;
   bool ok = SendRequest(req, res, "clôture (" + why + ")");
   if(ok)
      PrintFormat("IABot: #%I64u clôturé %s lot(s) - raison : %s", ticket, DoubleToString(vol, VolumeDigits()), why);
   return ok;
  }

void CloseAllMine(const string why)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(!IsMyPosition(ticket))
         continue;
      ClosePosition(ticket, PositionGetDouble(POSITION_VOLUME), why);
     }
  }

//+------------------------------------------------------------------+
//| Calcul du volume                                                  |
//+------------------------------------------------------------------+
// perte (devise du compte) pour 1 lot si le SL est touché, commission incluse
double LossPerLot(const ENUM_ORDER_TYPE type, const double price, const double sl)
  {
   double profit = 0.0;
   double loss = 0.0;
   if(OrderCalcProfit(type, _Symbol, 1.0, price, sl, profit) && profit < 0.0)
      loss = -profit;
   else
     {
      double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
      if(tickValue <= 0.0)
         tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      double ts = TickSize();
      if(tickValue > 0.0 && ts > 0.0)
         loss = MathAbs(price - sl) / ts * tickValue;
     }
   if(loss <= 0.0)
      return 0.0;
   return loss + MathMax(InpCommissionPerLot, 0.0);
  }

double CalcLots(const ENUM_ORDER_TYPE type, const double price, const double sl, string &msg)
  {
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(vmin <= 0.0 || vmax <= 0.0)
     {
      msg = "Volumes du symbole indisponibles";
      return 0.0;
     }
   if(step <= 0.0)
      step = vmin;

   double lossPerLot = LossPerLot(type, price, sl);
   if(lossPerLot <= 0.0)
     {
      msg = "Impossible d'évaluer la perte au SL";
      return 0.0;
     }
   double capital = (InpRiskMode == RISK_PCT_EQUITY) ? AccountInfoDouble(ACCOUNT_EQUITY)
                    : AccountInfoDouble(ACCOUNT_BALANCE);
   if(capital <= 0.0)
     {
      msg = "Capital nul";
      return 0.0;
     }

   double lots = 0.0;
   if(InpRiskMode == RISK_FIXED_LOT)
      lots = InpFixedLot;
   else
      lots = capital * InpRiskPercent / 100.0 / lossPerLot;

   lots = MathMin(lots, InpMaxLot);
   lots = MathMin(lots, vmax);
   lots = MathFloor(lots / step + 1e-7) * step;

   if(lots < vmin - 1e-9)
     {
      double riskAtMin = vmin * lossPerLot / capital * 100.0;
      if(InpRiskMode != RISK_FIXED_LOT && riskAtMin <= InpMinLotMaxRiskPct)
         lots = vmin;
      else
        {
         msg = StringFormat("Lot min %s = risque %.2f%% (> %.2f%%) : capital trop faible pour ce SL",
                            DoubleToString(vmin, VolumeDigits()), riskAtMin, InpMinLotMaxRiskPct);
         return 0.0;
        }
     }

   // limite de volume total du symbole
   double vlimit = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_LIMIT);
   if(vlimit > 0.0 && lots > vlimit)
      lots = MathFloor(vlimit / step + 1e-7) * step;

   // contrôle de la marge disponible
   double margin = 0.0;
   if(OrderCalcMargin(type, _Symbol, lots, price, margin) && margin > 0.0)
     {
      double freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE) * 0.90;
      if(margin > freeMargin)
        {
         lots = MathFloor(lots * (freeMargin / margin) / step + 1e-7) * step;
         if(lots < vmin - 1e-9)
           {
            msg = "Marge libre insuffisante";
            return 0.0;
           }
        }
     }
   return NormalizeVolume(lots);
  }

//+------------------------------------------------------------------+
//| Ouverture d'une position                                          |
//+------------------------------------------------------------------+
ulong FindNewestPosition()
  {
   ulong best = 0;
   long bestTime = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      long t = PositionGetInteger(POSITION_TIME_MSC);
      if(best == 0 || t >= bestTime)
        {
         best = ticket;
         bestTime = t;
        }
     }
   return best;
  }

bool OpenPosition(const int dir, const double slDist, string &msg)
  {
   MqlTick tk;
   if(!SymbolInfoTick(_Symbol, tk) || tk.bid <= 0.0 || tk.ask <= 0.0)
     {
      msg = "Prix indisponible";
      return false;
     }
   ENUM_ORDER_TYPE type = (dir > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double price = (dir > 0) ? tk.ask : tk.bid;
   double sl = NormalizePrice((dir > 0) ? price - slDist : price + slDist);
   double tp = 0.0;
   if(InpTP_R > 0.0)
      tp = NormalizePrice((dir > 0) ? price + slDist * InpTP_R : price - slDist * InpTP_R);

   double minDist = StopsMinDistance();
   if(dir > 0)
     {
      if(tk.bid - sl < minDist || (tp > 0.0 && tp - tk.bid < minDist))
        {
         msg = "SL/TP trop proches du prix (stops level du courtier)";
         return false;
        }
     }
   else
     {
      if(sl - tk.ask < minDist || (tp > 0.0 && tk.ask - tp < minDist))
        {
         msg = "SL/TP trop proches du prix (stops level du courtier)";
         return false;
        }
     }

   double lots = CalcLots(type, price, sl, msg);
   if(lots <= 0.0)
      return false;

   MqlTradeRequest req;
   MqlTradeResult res;
   MqlTradeCheckResult check;
   ZeroMemory(req);
   ZeroMemory(res);
   ZeroMemory(check);
   req.action = TRADE_ACTION_DEAL;
   req.symbol = _Symbol;
   req.volume = lots;
   req.type = type;
   req.price = price;
   req.sl = sl;
   req.tp = tp;
   req.deviation = (ulong)InpSlippagePoints;
   req.magic = InpMagic;
   req.comment = InpTradeComment;
   req.type_filling = g_filling;
   req.type_time = ORDER_TIME_GTC;

   // vérification préalable (marge, stops, mode de remplissage)
   bool checked = false;
   for(int k = 0; k < 3; k++)
     {
      ZeroMemory(check);
      if(OrderCheck(req, check))
        {
         checked = true;
         break;
        }
      if(check.retcode == TRADE_RETCODE_INVALID_FILL)
        {
         req.type_filling = NextFilling(req.type_filling);
         continue;
        }
      break;
     }
   if(!checked)
     {
      msg = StringFormat("Ordre refusé par la vérification : %u (%s)", check.retcode, check.comment);
      return false;
     }
   g_filling = req.type_filling;

   if(!SendRequest(req, res, (dir > 0 ? "ACHAT" : "VENTE")))
     {
      msg = StringFormat("Échec de l'ouverture : retcode %u", res.retcode);
      return false;
     }

   // position créée : mémoriser R et le volume initial
   ulong ticket = 0;
   if(res.order > 0 && PositionSelectByTicket(res.order))
      ticket = res.order;
   else
      ticket = FindNewestPosition();
   if(ticket == 0 || !PositionSelectByTicket(ticket))
     {
      msg = "Position ouverte mais introuvable";
      return true;
     }
   double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
   double posSL = PositionGetDouble(POSITION_SL);
   double posTP = PositionGetDouble(POSITION_TP);
   double posVol = PositionGetDouble(POSITION_VOLUME);
   GVSet(TicketKey("R", ticket), slDist);
   GVSet(TicketKey("V", ticket), posVol);

   // sécurité : le SL et le TP doivent être présents sur la position
   if(posSL == 0.0 || (tp > 0.0 && posTP == 0.0))
     {
      double fixSL = NormalizePrice((dir > 0) ? openPrice - slDist : openPrice + slDist);
      double fixTP = 0.0;
      if(InpTP_R > 0.0)
         fixTP = NormalizePrice((dir > 0) ? openPrice + slDist * InpTP_R : openPrice - slDist * InpTP_R);
      if(!ModifyStops(ticket, fixSL, fixTP, "pose SL/TP"))
        {
         Print("IABot: SL impossible à poser -> fermeture immédiate par sécurité");
         ClosePosition(ticket, posVol, "SL non posé");
         msg = "SL impossible à poser";
         return false;
        }
     }

   PrintFormat("IABot: %s %s lot(s) @ %s  SL=%s  TP=%s  (R=%s, risque %.2f%%)",
               (dir > 0 ? "ACHAT" : "VENTE"), DoubleToString(posVol, VolumeDigits()),
               DoubleToString(openPrice, SymDigits()), DoubleToString(sl, SymDigits()),
               DoubleToString(tp, SymDigits()), DoubleToString(slDist, SymDigits()),
               InpRiskMode == RISK_FIXED_LOT ? 0.0 : InpRiskPercent);
   msg = "Position ouverte";
   return true;
  }

//+------------------------------------------------------------------+
//| Gestion des positions ouvertes (à chaque tick)                    |
//+------------------------------------------------------------------+
// anti-spam : après un refus du serveur, pas de nouvelle modification avant 30 s
bool RecentlyFailed(const ulong ticket, const datetime now)
  {
   for(int i = 0; i < ArraySize(g_failTickets); i++)
      if(g_failTickets[i] == ticket)
         return (now - g_failTimes[i] < 30);
   return false;
  }

void MarkFailed(const ulong ticket, const datetime now)
  {
   int n = ArraySize(g_failTickets);
   for(int i = 0; i < n; i++)
     {
      if(g_failTickets[i] == ticket)
        {
         g_failTimes[i] = now;
         return;
        }
     }
   if(n >= 64)
     {
      ArrayResize(g_failTickets, 0);
      ArrayResize(g_failTimes, 0);
      n = 0;
     }
   ArrayResize(g_failTickets, n + 1);
   ArrayResize(g_failTimes, n + 1);
   g_failTickets[n] = ticket;
   g_failTimes[n] = now;
  }

// R = distance initiale du stop loss
double PositionRisk(const ulong ticket, const double openPrice, const double sl, const double tp)
  {
   double r = GVGet(TicketKey("R", ticket), 0.0);
   if(r > 0.0)
      return r;
   if(tp > 0.0 && InpTP_R > 0.0)
      return MathAbs(tp - openPrice) / InpTP_R;
   if(sl > 0.0)
      return MathAbs(openPrice - sl);
   return 0.0;
  }

bool IsFridayCloseTime(const datetime now)
  {
   if(InpFridayCloseHour < 0)
      return false;
   return (DowOf(now) == 5 && HourOf(now) >= InpFridayCloseHour);
  }

void ManagePositions()
  {
   MqlTick tk;
   if(!SymbolInfoTick(_Symbol, tk) || tk.bid <= 0.0 || tk.ask <= 0.0)
      return;
   datetime now = TimeCurrent();
   double minDist = StopsMinDistance();
   double freeze = FreezeDistance();
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0.0)
      step = vmin;

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;

      ENUM_POSITION_TYPE ptype = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      bool isBuy = (ptype == POSITION_TYPE_BUY);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl = PositionGetDouble(POSITION_SL);
      double tp = PositionGetDouble(POSITION_TP);
      double vol = PositionGetDouble(POSITION_VOLUME);
      datetime openTime = (datetime)PositionGetInteger(POSITION_TIME);
      double R = PositionRisk(ticket, openPrice, sl, tp);
      if(R <= 0.0)
         continue;

      double cur = isBuy ? tk.bid : tk.ask;
      double profitR = isBuy ? (cur - openPrice) / R : (openPrice - cur) / R;

      // 1) sorties temporelles
      if(InpMaxHoldHours > 0 && (long)(now - openTime) >= (long)InpMaxHoldHours * 3600)
        {
         ClosePosition(ticket, vol, "durée max atteinte");
         continue;
        }
      if(IsFridayCloseTime(now))
        {
         ClosePosition(ticket, vol, "fermeture du vendredi");
         continue;
        }

      // 2) clôture partielle (une seule fois)
      if(InpUsePartialClose && profitR >= InpPartialAtR && InpPartialPercent > 0.0)
        {
         double initVol = GVGet(TicketKey("V", ticket), 0.0);
         if(initVol > 0.0 && vol > initVol - step * 0.5)
           {
            double cv = NormalizeVolume(initVol * InpPartialPercent / 100.0);
            if(cv >= vmin && vol - cv >= vmin - 1e-9)
              {
               if(ClosePosition(ticket, cv, "clôture partielle"))
                  continue;
              }
            else
               GVSet(TicketKey("V", ticket), vol * 0.5);   // volume trop faible : on n'essaie plus
           }
        }

      // 3) break-even puis trailing stop
      double newSL = sl;
      if(InpUseBreakEven && profitR >= InpBE_TriggerR)
        {
         double be = isBuy ? openPrice + InpBE_LockR * R : openPrice - InpBE_LockR * R;
         if(isBuy && (newSL == 0.0 || newSL < be))
            newSL = be;
         if(!isBuy && (newSL == 0.0 || newSL > be))
            newSL = be;
        }
      if(InpUseTrailing && profitR >= InpTrailStartR)
        {
         double tr = isBuy ? cur - InpTrailDistR * R : cur + InpTrailDistR * R;
         if(isBuy && (newSL == 0.0 || tr > newSL))
            newSL = tr;
         if(!isBuy && (newSL == 0.0 || tr < newSL))
            newSL = tr;
        }
      if(newSL == sl)
         continue;

      // respect du stops level (le SL doit rester du bon côté du prix)
      if(isBuy && newSL > tk.bid - minDist)
         newSL = tk.bid - minDist;
      if(!isBuy && newSL < tk.ask + minDist)
         newSL = tk.ask + minDist;
      newSL = NormalizePrice(newSL);

      // amélioration minimale pour éviter de spammer le serveur
      double minStep = MathMax(0.05 * R, 2.0 * TickSize());
      bool improves = false;
      if(sl == 0.0)
         improves = true;
      else
         if(isBuy)
            improves = (newSL >= sl + minStep);
         else
            improves = (newSL <= sl - minStep);
      if(!improves)
         continue;

      // le TP existant doit lui aussi respecter le stops level, sinon le serveur refuse la modification
      if(tp > 0.0)
        {
         if(isBuy && tp - tk.bid < minDist)
            continue;
         if(!isBuy && tk.ask - tp < minDist)
            continue;
        }
      // niveau de gel : modification interdite trop près du SL/TP
      if(freeze > 0.0)
        {
         if(sl > 0.0 && MathAbs(cur - sl) <= freeze)
            continue;
         if(tp > 0.0 && MathAbs(tp - cur) <= freeze)
            continue;
        }
      if(RecentlyFailed(ticket, now))
         continue;
      string why = (InpUseTrailing && profitR >= InpTrailStartR) ? "trailing stop" : "break-even";
      if(!ModifyStops(ticket, newSL, tp, why))
         MarkFailed(ticket, now);
     }
  }

//+------------------------------------------------------------------+
//| Filtre des actualités économiques                                 |
//+------------------------------------------------------------------+
void BuildNewsCurrencies()
  {
   ArrayResize(g_newsCurrencies, 0);
   string list = InpNewsCurrencies;
   if(StringLen(list) == 0)
      list = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE) + "," + SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);
   string parts[];
   int n = StringSplit(list, ',', parts);
   for(int i = 0; i < n; i++)
     {
      string c = parts[i];
      StringTrimLeft(c);
      StringTrimRight(c);
      StringToUpper(c);
      if(StringLen(c) != 3)
         continue;
      bool dup = false;
      for(int j = 0; j < ArraySize(g_newsCurrencies); j++)
         if(g_newsCurrencies[j] == c)
            dup = true;
      if(dup)
         continue;
      int sz = ArraySize(g_newsCurrencies);
      ArrayResize(g_newsCurrencies, sz + 1);
      g_newsCurrencies[sz] = c;
     }
  }

void RefreshNews()
  {
   if(g_isTester || !InpUseNewsFilter)
      return;
   datetime now = TimeTradeServer();
   if(g_newsLastRefresh > 0 && now - g_newsLastRefresh < 900)
      return;
   g_newsLastRefresh = now;
   ArrayResize(g_newsTimes, 0);
   ArrayResize(g_newsNames, 0);
   bool anyOk = false;
   for(int c = 0; c < ArraySize(g_newsCurrencies); c++)
     {
      MqlCalendarValue values[];
      ResetLastError();
      if(!CalendarValueHistory(values, now - 6 * 3600, now + 36 * 3600, NULL, g_newsCurrencies[c]))
         continue;
      anyOk = true;
      int n = ArraySize(values);
      for(int k = 0; k < n; k++)
        {
         MqlCalendarEvent ev;
         if(!CalendarEventById(values[k].event_id, ev))
            continue;
         if(ev.time_mode != CALENDAR_TIMEMODE_DATETIME)
            continue;
         bool important = (ev.importance == CALENDAR_IMPORTANCE_HIGH) ||
                          (!InpNewsHighOnly && ev.importance == CALENDAR_IMPORTANCE_MODERATE);
         if(!important)
            continue;
         int sz = ArraySize(g_newsTimes);
         ArrayResize(g_newsTimes, sz + 1);
         ArrayResize(g_newsNames, sz + 1);
         g_newsTimes[sz] = values[k].time;
         g_newsNames[sz] = g_newsCurrencies[c] + " " + ev.name;
        }
     }
   if(!anyOk && ArraySize(g_newsCurrencies) > 0)
     {
      if(g_newsAvailable)
         PrintFormat("IABot: calendrier économique indisponible (erreur %d) - filtre news inactif", GetLastError());
      g_newsAvailable = false;
      g_newsLastRefresh = now - 600;  // nouvel essai dans 5 minutes
     }
   else
      g_newsAvailable = true;
  }

bool IsNewsBlackout(const datetime now, string &info)
  {
   info = "";
   if(g_isTester || !InpUseNewsFilter)
      return false;
   int n = ArraySize(g_newsTimes);
   for(int i = 0; i < n; i++)
     {
      datetime t = g_newsTimes[i];
      if(now >= t - (datetime)(InpNewsBeforeMin * 60) && now <= t + (datetime)(InpNewsAfterMin * 60))
        {
         info = g_newsNames[i] + " à " + TimeToString(t, TIME_MINUTES);
         return true;
        }
     }
   return false;
  }

string NextNewsText(const datetime now)
  {
   if(g_isTester)
      return "inactif dans le testeur";
   if(!InpUseNewsFilter)
      return "désactivé";
   if(!g_newsAvailable)
      return "calendrier indisponible";
   datetime best = 0;
   string name = "";
   for(int i = 0; i < ArraySize(g_newsTimes); i++)
     {
      if(g_newsTimes[i] >= now && (best == 0 || g_newsTimes[i] < best))
        {
         best = g_newsTimes[i];
         name = g_newsNames[i];
        }
     }
   if(best == 0)
      return "aucune news majeure prévue";
   return name + " à " + TimeToString(best, TIME_DATE | TIME_MINUTES);
  }

//+------------------------------------------------------------------+
//| Protections du capital                                            |
//+------------------------------------------------------------------+
void UpdateProtections()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq <= 0.0)
      return;

   // sommet d'equity (persistant)
   if(eq > g_peakEquity)
     {
      g_peakEquity = eq;
      if(g_peakEquity > g_peakSaved * 1.001)
        {
         GVSet("peak", g_peakEquity);
         g_peakSaved = g_peakEquity;
        }
     }

   // coupe-circuit drawdown
   if(InpMaxDrawdownPct > 0.0 && g_peakEquity > 0.0 && !g_ddHalt)
     {
      double dd = (g_peakEquity - eq) / g_peakEquity * 100.0;
      if(dd >= InpMaxDrawdownPct)
        {
         g_ddHalt = true;
         GVSet("halt", 1.0);
         string m = StringFormat("IABot: DRAWDOWN MAX ATTEINT (%.2f%%) - robot arrêté", dd);
         Print(m);
         if(!g_isTester)
            Alert(m);
         if(InpCloseOnMaxDD)
            CloseAllMine("drawdown max");
        }
     }

   // perte journalière
   if(InpMaxDailyLossPct > 0.0 && g_dayStartBalance > 0.0 && !g_dailyHalt)
     {
      double loss = (g_dayStartBalance - eq) / g_dayStartBalance * 100.0;
      if(loss >= InpMaxDailyLossPct)
        {
         g_dailyHalt = true;
         PrintFormat("IABot: perte journalière max atteinte (%.2f%%) - plus de trade aujourd'hui", loss);
         if(InpCloseOnDailyLoss)
            CloseAllMine("perte journalière max");
        }
     }
  }

double CurrentDrawdownPct()
  {
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(g_peakEquity <= 0.0)
      return 0.0;
   return MathMax(0.0, (g_peakEquity - eq) / g_peakEquity * 100.0);
  }

//+------------------------------------------------------------------+
//| Conditions d'ouverture                                            |
//+------------------------------------------------------------------+
bool TradingAllowed(string &why)
  {
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
     {
      why = "Trading automatique désactivé dans le terminal (bouton Algo Trading)";
      return false;
     }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
     {
      why = "Trading non autorisé pour ce robot (cocher 'Autoriser le trading algorithmique')";
      return false;
     }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      why = "Trading interdit sur ce compte";
      return false;
     }
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))
     {
      why = "Robots de trading interdits par le courtier";
      return false;
     }
   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   if(mode == SYMBOL_TRADE_MODE_DISABLED || mode == SYMBOL_TRADE_MODE_CLOSEONLY)
     {
      why = "Symbole non négociable actuellement";
      return false;
     }
   return true;
  }

bool CanOpenNewTrade(const datetime signalBarTime, string &why)
  {
   if(!TradingAllowed(why))
      return false;
   if(g_ddHalt)
     {
      why = "ARRÊT : drawdown max atteint (réarmer avec 'Réarmer le robot')";
      return false;
     }
   if(g_dailyHalt)
     {
      why = "Pause : perte journalière max atteinte";
      return false;
     }
   if(InpMaxTradesPerDay > 0 && g_tradesToday >= InpMaxTradesPerDay)
     {
      why = "Pause : nombre max de trades du jour atteint";
      return false;
     }
   if(InpMaxConsecLosses > 0 && g_consecLosses >= InpMaxConsecLosses)
     {
      why = "Pause : trop de pertes consécutives aujourd'hui";
      return false;
     }
   if(CountMyPositions() > 0)
     {
      why = "Position en cours - gestion active";
      return false;
     }
   if(!g_isHedging && CountSymbolPositions() > 0)
     {
      why = "Compte netting : une autre position existe déjà sur ce symbole";
      return false;
     }
   datetime now = TimeCurrent();
   int dow = DowOf(now);
   if(dow == 0 || dow == 6)
     {
      why = "Week-end";
      return false;
     }
   if(dow == 5 && InpFridayLastEntry >= 0 && HourOf(now) >= InpFridayLastEntry)
     {
      why = "Vendredi soir : pas de nouvelle position";
      return false;
     }
   if(!HourInWindow(SessionHour(signalBarTime), InpSessionStart, InpSessionEnd))
     {
      why = StringFormat("Hors session (%dh-%dh)", InpSessionStart, InpSessionEnd);
      return false;
     }
   string info;
   if(IsNewsBlackout(now, info))
     {
      why = "Pause news : " + info;
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Signal de la stratégie (bougies clôturées uniquement)             |
//+------------------------------------------------------------------+
// dir : +1 achat, -1 vente, 0 rien. slDist : distance du stop loss en prix
bool GetSignal(int &dir, double &slDist, string &why)
  {
   dir = 0;
   slDist = 0.0;
   double emaFast = 0.0, emaSlow = 0.0, atr = 0.0, rsi = 0.0;
   if(!GetIndicatorValue(g_hEmaFast, 0, 1, emaFast) ||
      !GetIndicatorValue(g_hEmaSlow, 0, 1, emaSlow) ||
      !GetIndicatorValue(g_hATR, 0, 1, atr) ||
      !GetIndicatorValue(g_hRSI, 0, 1, rsi))
     {
      why = "Indicateurs en cours de chargement";
      return false;
     }
   if(Bars(_Symbol, InpTrendTF) < InpTrendSlowEMA + 10 || Bars(_Symbol, InpSignalTF) < InpRSIPeriod + 10)
     {
      why = "Historique insuffisant";
      return false;
     }
   double trendClose = iClose(_Symbol, InpTrendTF, 1);
   if(trendClose <= 0.0 || atr <= 0.0)
     {
      why = "Historique insuffisant";
      return false;
     }
   g_lastRSI = rsi;

   bool up = (trendClose > emaSlow && emaFast > emaSlow);
   bool down = (trendClose < emaSlow && emaFast < emaSlow);
   g_trendText = up ? "HAUSSIÈRE" : (down ? "BAISSIÈRE" : "NEUTRE");

   if(InpTrendADXMin > 0)
     {
      double adx = 0.0;
      if(!GetIndicatorValue(g_hADX, 0, 1, adx))
        {
         why = "ADX en cours de chargement";
         return false;
        }
      if(adx < (double)InpTrendADXMin)
        {
         why = StringFormat("Tendance trop faible (ADX %.1f < %d)", adx, InpTrendADXMin);
         return true;
        }
     }

   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   if(up && rsi < InpRSIBuyLevel && mode != SYMBOL_TRADE_MODE_SHORTONLY)
      dir = 1;
   else
      if(down && rsi > InpRSISellLevel && mode != SYMBOL_TRADE_MODE_LONGONLY)
         dir = -1;

   slDist = InpSL_ATR * atr;
   if(dir == 0)
     {
      if(!up && !down)
         why = "Pas de tendance claire sur " + TFToString(InpTrendTF);
      else
         why = StringFormat("Tendance %s - attente d'un repli (RSI %.1f)", g_trendText, rsi);
     }
   else
      why = (dir > 0) ? "Signal ACHAT" : "Signal VENTE";
   return true;
  }

bool SpreadOK(const double slDist, string &why)
  {
   MqlTick tk;
   if(!SymbolInfoTick(_Symbol, tk))
     {
      why = "Prix indisponible";
      return false;
     }
   double spread = tk.ask - tk.bid;
   double pt = SymPoint();
   if(InpMaxSpreadPoints > 0 && pt > 0.0 && spread > InpMaxSpreadPoints * pt + pt * 0.5)
     {
      why = StringFormat("Spread trop élevé (%.0f pts > %d)", spread / pt, InpMaxSpreadPoints);
      return false;
     }
   if(InpMaxSpreadPctSL > 0.0 && slDist > 0.0 && spread > slDist * InpMaxSpreadPctSL / 100.0)
     {
      why = StringFormat("Spread trop élevé (%.1f%% du SL)", spread / slDist * 100.0);
      return false;
     }
   return true;
  }

//+------------------------------------------------------------------+
//| Panneau d'information                                             |
//+------------------------------------------------------------------+
void UpdatePanel(const bool force)
  {
   if(!InpShowPanel || (g_isTester && !MQLInfoInteger(MQL_VISUAL_MODE)))
      return;
   uint nowMs = GetTickCount();
   if(!force && nowMs - g_lastPanelMs < 1000)
      return;
   g_lastPanelMs = nowMs;

   MqlTick tk;
   double spreadPts = 0.0;
   if(SymbolInfoTick(_Symbol, tk) && SymPoint() > 0.0)
      spreadPts = (tk.ask - tk.bid) / SymPoint();
   datetime now = TimeCurrent();
   bool inSession = HourInWindow(SessionHour(now), InpSessionStart, InpSessionEnd);

   string s = "";
   s += "IABot M5  |  " + _Symbol + "  |  compte " + (g_isHedging ? "hedging" : "netting") + "  |  magic " + IntegerToString((long)InpMagic) + "\n";
   s += "Tendance " + TFToString(InpTrendTF) + " : " + g_trendText + "   |   RSI(" + IntegerToString(InpRSIPeriod) + ") " + TFToString(InpSignalTF) + " : " + DoubleToString(g_lastRSI, 1) + "\n";
   s += "Session " + IntegerToString(InpSessionStart) + "h-" + IntegerToString(InpSessionEnd) + "h : " + (inSession ? "OUVERTE" : "fermée") + "   |   Spread : " + DoubleToString(spreadPts, 0) + " pts\n";
   s += "News : " + NextNewsText(now) + "\n";
   s += "Risque/trade : " + (InpRiskMode == RISK_FIXED_LOT ? "lot fixe " + DoubleToString(InpFixedLot, 2) : DoubleToString(InpRiskPercent, 2) + "%");
   s += "   |   Trades du jour : " + IntegerToString(g_tradesToday) + (InpMaxTradesPerDay > 0 ? "/" + IntegerToString(InpMaxTradesPerDay) : "") + "\n";
   s += "Résultat du jour : " + FmtMoney(g_closedPLToday) + "   |   Drawdown : " + DoubleToString(CurrentDrawdownPct(), 2) + "% (max " + DoubleToString(InpMaxDrawdownPct, 1) + "%)\n";

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || (ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      bool isBuy = ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
      double op = PositionGetDouble(POSITION_PRICE_OPEN);
      double psl = PositionGetDouble(POSITION_SL);
      double ptp = PositionGetDouble(POSITION_TP);
      double R = PositionRisk(ticket, op, psl, ptp);
      double cur = PositionGetDouble(POSITION_PRICE_CURRENT);
      double pr = (R > 0.0) ? (isBuy ? (cur - op) / R : (op - cur) / R) : 0.0;
      s += "Position : " + (isBuy ? "ACHAT " : "VENTE ") + DoubleToString(PositionGetDouble(POSITION_VOLUME), VolumeDigits()) +
           " @ " + DoubleToString(op, SymDigits()) + "  SL " + DoubleToString(psl, SymDigits()) +
           "  TP " + DoubleToString(ptp, SymDigits()) + "  (" + DoubleToString(pr, 2) + " R, " +
           FmtMoney(PositionGetDouble(POSITION_PROFIT)) + ")\n";
     }
   s += "Statut : " + g_status;
   Comment(s);
  }

//+------------------------------------------------------------------+
//| Validation des paramètres                                         |
//+------------------------------------------------------------------+
bool ValidateInputs()
  {
   bool ok = true;
   if(InpTrendFastEMA < 1 || InpTrendSlowEMA <= InpTrendFastEMA)
     {
      Print("IABot: EMA rapide/lente invalides (il faut 1 <= rapide < lente)");
      ok = false;
     }
   if(InpRSIPeriod < 2 || InpATRPeriod < 1)
     {
      Print("IABot: périodes RSI/ATR invalides");
      ok = false;
     }
   if(InpRSIBuyLevel <= 0.0 || InpRSISellLevel >= 100.0 || InpRSIBuyLevel >= InpRSISellLevel)
     {
      Print("IABot: niveaux RSI invalides");
      ok = false;
     }
   if(InpSL_ATR <= 0.0 || InpTP_R < 0.0)
     {
      Print("IABot: SL/TP invalides");
      ok = false;
     }
   if(InpRiskMode != RISK_FIXED_LOT && (InpRiskPercent <= 0.0 || InpRiskPercent > 10.0))
     {
      Print("IABot: le risque par trade doit être compris entre 0 et 10 %");
      ok = false;
     }
   if(InpRiskMode == RISK_FIXED_LOT && InpFixedLot <= 0.0)
     {
      Print("IABot: lot fixe invalide");
      ok = false;
     }
   if(InpUseTrailing && InpTrailDistR <= 0.0)
     {
      Print("IABot: distance de trailing invalide");
      ok = false;
     }
   if(InpUsePartialClose && (InpPartialPercent <= 0.0 || InpPartialPercent >= 100.0))
     {
      Print("IABot: pourcentage de clôture partielle invalide (1-99)");
      ok = false;
     }
   if(InpSessionStart < 0 || InpSessionStart > 23 || InpSessionEnd < 0 || InpSessionEnd > 24)
     {
      Print("IABot: heures de session invalides");
      ok = false;
     }
   if(PeriodSeconds(InpTrendTF) <= PeriodSeconds(InpSignalTF))
      Print("IABot: attention, l'unité de tendance devrait être supérieure à celle des signaux");
   return ok;
  }

//+------------------------------------------------------------------+
//| Événements                                                        |
//+------------------------------------------------------------------+
int OnInit()
  {
   if(!ValidateInputs())
      return INIT_PARAMETERS_INCORRECT;

   g_isTester = (MQLInfoInteger(MQL_TESTER) != 0);
   ENUM_ACCOUNT_MARGIN_MODE mm = (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   g_isHedging = (mm == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
   g_filling = DetectFilling();
   g_gvPrefix = "IAB_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + IntegerToString((long)InpMagic) + "_";

   g_hEmaFast = iMA(_Symbol, InpTrendTF, InpTrendFastEMA, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaSlow = iMA(_Symbol, InpTrendTF, InpTrendSlowEMA, 0, MODE_EMA, PRICE_CLOSE);
   g_hATR = iATR(_Symbol, InpTrendTF, InpATRPeriod);
   g_hRSI = iRSI(_Symbol, InpSignalTF, InpRSIPeriod, PRICE_CLOSE);
   if(InpTrendADXMin > 0)
      g_hADX = iADX(_Symbol, InpTrendTF, 14);
   if(g_hEmaFast == INVALID_HANDLE || g_hEmaSlow == INVALID_HANDLE || g_hATR == INVALID_HANDLE ||
      g_hRSI == INVALID_HANDLE || (InpTrendADXMin > 0 && g_hADX == INVALID_HANDLE))
     {
      PrintFormat("IABot: impossible de créer les indicateurs (erreur %d)", GetLastError());
      return INIT_FAILED;
     }

   // protections persistantes
   if(InpResetProtection)
     {
      GVDel("halt");
      GVDel("peak");
      Print("IABot: protection drawdown réarmée");
     }
   g_ddHalt = (GVGet("halt", 0.0) > 0.5);
   g_peakEquity = MathMax(GVGet("peak", 0.0), AccountInfoDouble(ACCOUNT_EQUITY));
   g_peakSaved = g_peakEquity;
   GVSet("peak", g_peakEquity);
   g_dayStart = 0;
   UpdateDayAnchor();
   ComputeTodayStats();

   BuildNewsCurrencies();
   RefreshNews();

   // le premier signal sera évalué à la prochaine bougie (pas d'entrée tardive)
   g_lastSignalBar = iTime(_Symbol, InpSignalTF, 0);

   if(_Period != InpSignalTF)
      PrintFormat("IABot: info - le graphique est en %s, les signaux sont calculés en %s",
                  TFToString(_Period), TFToString(InpSignalTF));
   PrintFormat("IABot: démarré sur %s | compte %s | remplissage %d | risque %.2f%% | SL %.1f ATR | TP %.1f R",
               _Symbol, (g_isHedging ? "hedging" : "netting"), (int)g_filling, InpRiskPercent, InpSL_ATR, InpTP_R);
   if(g_ddHalt)
      Print("IABot: ATTENTION - le robot est à l'arrêt (drawdown max atteint précédemment). Réglez 'Réarmer le robot' sur true pour reprendre.");

   EventSetTimer(30);
   g_status = "En attente de la prochaine bougie " + TFToString(InpSignalTF);
   UpdatePanel(true);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(g_peakEquity > 0.0)
      GVSet("peak", g_peakEquity);
   if(g_hEmaFast != INVALID_HANDLE)
      IndicatorRelease(g_hEmaFast);
   if(g_hEmaSlow != INVALID_HANDLE)
      IndicatorRelease(g_hEmaSlow);
   if(g_hATR != INVALID_HANDLE)
      IndicatorRelease(g_hATR);
   if(g_hRSI != INVALID_HANDLE)
      IndicatorRelease(g_hRSI);
   if(g_hADX != INVALID_HANDLE)
      IndicatorRelease(g_hADX);
   g_hEmaFast = INVALID_HANDLE;
   g_hEmaSlow = INVALID_HANDLE;
   g_hATR = INVALID_HANDLE;
   g_hRSI = INVALID_HANDLE;
   g_hADX = INVALID_HANDLE;
   Comment("");
   PrintFormat("IABot: arrêté (raison %d)", reason);
  }

void OnTimer()
  {
   RefreshNews();
   UpdatePanel(true);
  }

void OnTick()
  {
   UpdateDayAnchor();
   UpdateProtections();
   ManagePositions();

   datetime barTime = iTime(_Symbol, InpSignalTF, 0);
   if(barTime == 0 || barTime == g_lastSignalBar)
     {
      UpdatePanel(false);
      return;
     }
   g_lastSignalBar = barTime;

   // nouvelle bougie : statistiques et nettoyage
   ComputeTodayStats();
   CleanupTicketVariables();
   RefreshNews();

   datetime signalBarTime = iTime(_Symbol, InpSignalTF, 1);
   string why = "";
   int dir = 0;
   double slDist = 0.0;
   bool haveSignal = GetSignal(dir, slDist, why);
   if(!haveSignal)
     {
      // données pas encore synchronisées : nouvel essai au tick suivant (première minute seulement)
      if(TimeCurrent() - barTime < 60)
         g_lastSignalBar = 0;
      g_status = why;
      UpdatePanel(true);
      return;
     }
   if(dir == 0)
     {
      g_status = why;
      UpdatePanel(true);
      return;
     }
   if(!CanOpenNewTrade(signalBarTime, why))
     {
      g_status = "Signal ignoré - " + why;
      UpdatePanel(true);
      return;
     }
   if(!SpreadOK(slDist, why))
     {
      g_status = "Signal ignoré - " + why;
      UpdatePanel(true);
      return;
     }
   string msg = "";
   if(OpenPosition(dir, slDist, msg))
     {
      ComputeTodayStats();
      g_status = msg;
     }
   else
     {
      g_status = "Signal non exécuté - " + msg;
      Print("IABot: " + g_status);
     }
   UpdatePanel(true);
  }

//+------------------------------------------------------------------+
//| Critère personnalisé pour l'optimisation (testeur de stratégie)   |
//+------------------------------------------------------------------+
double OnTester()
  {
   double trades = TesterStatistics(STAT_TRADES);
   double profit = TesterStatistics(STAT_PROFIT);
   double pf = TesterStatistics(STAT_PROFIT_FACTOR);
   double ddPct = TesterStatistics(STAT_EQUITY_DDREL_PERCENT);
   if(trades < 30.0 || profit <= 0.0)
      return 0.0;
   // récompense la régularité : PF, nombre de trades et faible drawdown
   return (pf - 1.0) * MathSqrt(trades) * (100.0 - MathMin(ddPct, 99.0)) / 100.0;
  }
//+------------------------------------------------------------------+
