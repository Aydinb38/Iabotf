//+------------------------------------------------------------------+
//|                                                 IABot_EURUSD.mq5 |
//|          Robot de trading autonome spécialisé EURUSD (M5)        |
//|                                                                  |
//|  Ce que le robot a appris sur 14 ans d'EURUSD (2005-2018) :      |
//|   - l'euro tend à baisser face au dollar pendant la séance       |
//|     européenne (effet documenté : Ranaldo 2009, Breedon &        |
//|     Ranaldo 2013), 12 années positives sur 14 ;                  |
//|   - les meilleures entrées sont les rebonds courts M5 (RSI(3)    |
//|     > 70) entre 10h et 13h (heure serveur GMT+2/+3) ;            |
//|   - plusieurs entrées espacées d'1h améliorent le résultat.      |
//|                                                                  |
//|  Gestion : jusqu'à 3 positions/jour, SL = 3 x ATR(14) H1,        |
//|  TP = 3 R, break-even à +1 R (profil rendement, par défaut) ou   |
//|  +0,5 R (profil taux de réussite), sortie forcée à 15h.          |
//|  Adaptation : volatilité (ATR), heure d'été, news, choc de       |
//|  volatilité, et risque adaptatif : le robot mémorise le résultat |
//|  de ses 60 derniers trades et réduit son risque de moitié quand  |
//|  ce bilan devient négatif.                                       |
//+------------------------------------------------------------------+
#property copyright   "IABot"
#property version     "2.00"
#property description "Robot autonome spécialisé EURUSD (M5) : séance européenne, jusqu'à 3 trades/jour,"
#property description "SL 3 ATR H1, TP 3 R, break-even, sortie 15h, risque adaptatif à mémoire persistante,"
#property description "limites journalières, coupe-circuit, filtres spread / news / volatilité."

//+------------------------------------------------------------------+
//| Enumerations                                                      |
//+------------------------------------------------------------------+
enum ENUM_RISK_MODE
  {
   RISK_PCT_BALANCE = 0, // % du solde
   RISK_PCT_EQUITY  = 1, // % des fonds propres (equity)
   RISK_FIXED_LOT   = 2  // Lot fixe
  };

enum ENUM_FX_DIRECTION
  {
   FX_DIR_AUTO      = 0, // Automatique (vente de l'EURUSD)
   FX_DIR_SELL_ONLY = 1, // Ventes uniquement
   FX_DIR_BUY_ONLY  = 2  // Achats uniquement
  };

enum ENUM_FX_PROFILE
  {
   FX_PROFILE_WINRATE = 0, // Taux de réussite élevé (TP 3 R, break-even 0,5 R)
   FX_PROFILE_RETURN  = 1, // Rendement maximal (TP 3 R, break-even 1 R)
   FX_PROFILE_CUSTOM  = 2  // Personnalisé (paramètres TP / break-even ci-dessous)
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
input ulong             InpMagic            = 26111603;          // Numéro magique (identifiant des trades du robot)
input string            InpTradeComment     = "IABot_EURUSD";        // Commentaire des ordres
input ENUM_TIMEFRAMES   InpSignalTF         = PERIOD_M5;         // Unité de temps des signaux (M5)

input group "=== Stratégie EURUSD : séance européenne ==="
input ENUM_FX_DIRECTION InpDirection        = FX_DIR_AUTO;       // Sens des trades
input int               InpRSIPeriod        = 3;                 // Période du RSI de rebond (M5)
input double            InpRSIPullback      = 70.0;              // Vente si RSI > niveau (achat si RSI < 100 - niveau)
input ENUM_TIMEFRAMES   InpATRTF            = PERIOD_H1;         // Unité de temps de l'ATR (stop loss)
input int               InpATRPeriod        = 14;                // Période ATR
input int               InpExitHour         = 15;                // Heure de sortie forcée (référence horaire de la session)
input int               InpMaxPositions     = 3;                 // Positions simultanées max
input int               InpMinMinutesBetween = 60;               // Minutes minimum entre deux entrées

input group "=== Stop loss / Take profit / Break-even ==="
input ENUM_FX_PROFILE   InpProfile          = FX_PROFILE_RETURN; // Profil de sortie
input double            InpSL_ATR           = 3.0;               // Stop loss = ATR x (définit 1 R)
input double            InpTP_R             = 3.0;               // Take profit = R x (profil personnalisé)
input bool              InpUseBreakEven     = true;              // Activer le break-even
input double            InpBE_TriggerR      = 0.5;               // Break-even déclenché à +R (profil personnalisé)
input double            InpBE_LockR         = 0.1;               // Gain verrouillé au break-even (R)
input bool              InpUseTrailing      = false;             // Activer le trailing stop
input double            InpTrailStartR      = 2.0;               // Trailing actif à partir de +R
input double            InpTrailDistR       = 1.5;               // Distance du trailing (R)
input bool              InpUsePartialClose  = false;             // Clôture partielle
input double            InpPartialAtR       = 0.5;               // Clôture partielle à +R (doit être inférieur au TP)
input double            InpPartialPercent   = 50.0;              // % du volume clôturé
input int               InpMaxHoldHours     = 0;                 // Durée max d'un trade en heures (0 = illimitée)

input group "=== Gestion du risque ==="
input ENUM_RISK_MODE  InpRiskMode         = RISK_PCT_BALANCE;  // Calcul du lot
input double          InpRiskPercent      = 0.4;               // Risque par trade (%)
input double          InpFixedLot         = 0.01;              // Lot fixe (mode lot fixe)
input double          InpMaxLot           = 50.0;              // Lot maximum
input double          InpMinLotMaxRiskPct = 2.0;               // Risque max (%) toléré si le lot minimum est imposé
input double          InpCommissionPerLot = 0.0;               // Commission aller-retour par lot (devise du compte)
input double          InpMaxDailyLossPct  = 3.0;               // Perte journalière max en % (0 = off)
input bool            InpCloseOnDailyLoss = false;             // Fermer les positions si la perte journalière est atteinte
input double          InpMaxDrawdownPct   = 20.0;              // Drawdown max depuis le sommet en % (0 = off)
input bool            InpCloseOnMaxDD     = true;              // Fermer les positions si le drawdown max est atteint
input bool            InpResetProtection  = false;             // Réarmer le robot après un arrêt drawdown
input int             InpMaxTradesPerDay  = 3;                 // Trades max par jour (0 = illimité)
input bool            InpUseAdaptiveRisk  = true;              // Risque adaptatif (mémoire des derniers trades)
input int             InpAdaptiveWindow   = 60;                // Nombre de trades mémorisés
input double          InpAdaptiveFactor   = 0.5;               // Multiplicateur de risque si le bilan récent est négatif
input int             InpMaxConsecLosses  = 3;                 // Pertes consécutives max par jour (0 = off)
input double          InpMaxVolatility    = 3.0;               // Pas de trade si ATR actuel > x fois l'ATR moyen (choc de volatilité, 0 = off)
input int             InpMaxSpreadPoints  = 20;                // Spread max en points (0 = automatique)
input double          InpMaxSpreadPctSL   = 10.0;              // Spread max en % de la distance du SL
input int             InpSlippagePoints   = 10;                // Glissement max (points)

input group "=== Horaires ==="
input ENUM_TIME_BASE  InpTimeBase         = TIME_BASE_SERVER;  // Référence horaire de la session
input int             InpSessionStart     = 10;                // Début de la fenêtre d'entrée (heure)
input int             InpSessionEnd       = 13;                // Fin de la fenêtre d'entrée (heure, exclue)
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
int      g_hATR            = INVALID_HANDLE;
int      g_hRSI            = INVALID_HANDLE;
int      g_hATRLong        = INVALID_HANDLE;

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

double   g_tpR             = 3.0;   // take profit effectif (R) selon le profil
datetime g_lastEntryTime   = 0;     // dernière entrée du jour
bool     g_riskReduced     = false; // risque adaptatif réduit
double   g_beR             = 1.0;   // déclenchement effectif du break-even (R)

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

//+------------------------------------------------------------------+
//| Mémoire des résultats : base du risque adaptatif                  |
//+------------------------------------------------------------------+
// ajoute le résultat (en R) d'un trade clôturé dans une mémoire circulaire persistante
void PushTradeResult(const double r)
  {
   int window = MathMax(InpAdaptiveWindow, 1);
   int n = (int)GVGet("Hn", 0.0);
   int idx = (int)GVGet("Hi", 0.0);
   if(idx < 0 || idx >= window)
      idx = 0;
   GVSet("H" + IntegerToString(idx), r);
   idx = (idx + 1) % window;
   if(n < window)
      n++;
   GVSet("Hi", (double)idx);
   GVSet("Hn", (double)n);
  }

// bilan (somme des R) des derniers trades mémorisés
double RecentPerformanceR(int &count)
  {
   int window = MathMax(InpAdaptiveWindow, 1);
   count = MathMin((int)GVGet("Hn", 0.0), window);
   double sum = 0.0;
   for(int i = 0; i < count; i++)
      sum += GVGet("H" + IntegerToString(i), 0.0);
   return sum;
  }

double EffectiveRiskPercent()
  {
   if(!InpUseAdaptiveRisk)
      return InpRiskPercent;
   int count = 0;
   double sum = RecentPerformanceR(count);
   bool reduce = (count >= InpAdaptiveWindow && sum < 0.0);
   if(reduce != g_riskReduced)
     {
      g_riskReduced = reduce;
      PrintFormat("IABot: risque adaptatif -> %s (bilan des %d derniers trades : %+.1f R)",
                  reduce ? "RÉDUIT" : "normal", count, sum);
     }
   return reduce ? InpRiskPercent * InpAdaptiveFactor : InpRiskPercent;
  }

// résultat net (devise du compte) d'une position clôturée, d'après l'historique
bool ClosedPositionProfit(const long positionId, double &profit)
  {
   profit = 0.0;
   if(!HistorySelectByPosition(positionId))
      return false;
   bool closed = false;
   int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong deal = HistoryDealGetTicket(i);
      if(deal == 0)
         continue;
      ENUM_DEAL_ENTRY entry = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY);
      if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_OUT_BY || entry == DEAL_ENTRY_INOUT)
         closed = true;
      profit += HistoryDealGetDouble(deal, DEAL_PROFIT) + HistoryDealGetDouble(deal, DEAL_COMMISSION)
                + HistoryDealGetDouble(deal, DEAL_SWAP) + HistoryDealGetDouble(deal, DEAL_FEE);
     }
   return closed;
  }

// positions disparues : enregistre leur résultat en R puis supprime leurs données
void CleanupTicketVariables()
  {
   string pr = g_gvPrefix + "R";
   string pv = g_gvPrefix + "V";
   string pm = g_gvPrefix + "M";
   string pp = g_gvPrefix + "P";
   int prLen = StringLen(pr);
   string names[];
   ArrayResize(names, 0);
   int total = GlobalVariablesTotal();
   for(int i = 0; i < total; i++)
     {
      string n = GlobalVariableName(i);
      if(StringFind(n, pr) == 0 || StringFind(n, pv) == 0 || StringFind(n, pm) == 0 || StringFind(n, pp) == 0)
        {
         ulong t = (ulong)StringToInteger(StringSubstr(n, prLen));
         if(t == 0 || PositionSelectByTicket(t))
            continue;
         int sz = ArraySize(names);
         ArrayResize(names, sz + 1);
         names[sz] = n;
        }
     }
   // 1) résultats des positions clôturées -> mémoire du risque adaptatif
   for(int k = 0; k < ArraySize(names); k++)
     {
      if(StringFind(names[k], pm) != 0)
         continue;
      ulong ticket = (ulong)StringToInteger(StringSubstr(names[k], prLen));
      double riskMoney = GlobalVariableGet(names[k]);
      double idv = GVGet(TicketKey("P", ticket), (double)ticket);
      double profit = 0.0;
      if(riskMoney > 0.0 && ClosedPositionProfit((long)idv, profit))
         PushTradeResult(profit / riskMoney);
     }
   // 2) suppression des données devenues inutiles
   for(int k = 0; k < ArraySize(names); k++)
      GlobalVariableDel(names[k]);
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
   g_lastEntryTime = 0;
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
        {
         g_tradesToday++;
         datetime dt = (datetime)HistoryDealGetInteger(deal, DEAL_TIME);
         if(dt > g_lastEntryTime)
            g_lastEntryTime = dt;
        }
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
      lots = capital * EffectiveRiskPercent() / 100.0 / lossPerLot;

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
   if(g_tpR > 0.0)
      tp = NormalizePrice((dir > 0) ? price + slDist * g_tpR : price - slDist * g_tpR);

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
   double lossLot = LossPerLot(type, openPrice, NormalizePrice((dir > 0) ? openPrice - slDist : openPrice + slDist));
   if(lossLot > 0.0)
      GVSet(TicketKey("M", ticket), lossLot * posVol);
   GVSet(TicketKey("P", ticket), (double)PositionGetInteger(POSITION_IDENTIFIER));

   // sécurité : le SL et le TP doivent être présents sur la position
   if(posSL == 0.0 || (tp > 0.0 && posTP == 0.0))
     {
      double fixSL = NormalizePrice((dir > 0) ? openPrice - slDist : openPrice + slDist);
      double fixTP = 0.0;
      if(g_tpR > 0.0)
         fixTP = NormalizePrice((dir > 0) ? openPrice + slDist * g_tpR : openPrice - slDist * g_tpR);
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
               InpRiskMode == RISK_FIXED_LOT ? 0.0 : EffectiveRiskPercent());
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
   if(tp > 0.0 && g_tpR > 0.0)
      return MathAbs(tp - openPrice) / g_tpR;
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

// sortie forcée : heure de sortie atteinte, ou position restée ouverte plus de 20 h
bool IsSessionExitTime(const datetime now, const datetime openTime)
  {
   if(InpExitHour < 0)
      return false;
   if(now - openTime >= 20 * 3600)
      return true;
   return (SessionHour(now) >= InpExitHour && SessionHour(openTime) < InpExitHour);
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
      if(IsSessionExitTime(now, openTime))
        {
         ClosePosition(ticket, vol, "sortie de fin de séance");
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
      if(InpUseBreakEven && profitR >= g_beR)
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

bool CanOpenNewTrade(const datetime entryBarTime, string &why)
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
   int openCount = CountMyPositions();
   if(openCount >= InpMaxPositions)
     {
      why = StringFormat("%d position(s) en cours - gestion active", openCount);
      return false;
     }
   if(g_lastEntryTime > 0 && TimeCurrent() - g_lastEntryTime < (datetime)(InpMinMinutesBetween * 60))
     {
      why = StringFormat("Espacement : prochaine entrée possible %d min après la précédente", InpMinMinutesBetween);
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
   if(!HourInWindow(SessionHour(entryBarTime), InpSessionStart, InpSessionEnd))
     {
      why = StringFormat("Hors fenêtre d'entrée (%dh-%dh)", InpSessionStart, InpSessionEnd);
      return false;
     }
   if(InpMaxVolatility > 0.0)
     {
      double atrNow = 0.0, atrLong = 0.0;
      if(GetIndicatorValue(g_hATR, 0, 1, atrNow) && GetIndicatorValue(g_hATRLong, 0, 1, atrLong) && atrLong > 0.0 &&
         atrNow > InpMaxVolatility * atrLong)
        {
         why = StringFormat("Choc de volatilité (ATR x%.1f la normale)", atrNow / atrLong);
         return false;
        }
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
// biais de la stratégie : -1 vendre la paire, +1 acheter, 0 paire non prise en charge
int TradeBias()
  {
   if(InpDirection == FX_DIR_SELL_ONLY)
      return -1;
   if(InpDirection == FX_DIR_BUY_ONLY)
      return 1;
   string base = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE);
   string quote = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);
   // robot spécialisé : l'euro faiblit face au dollar pendant la séance européenne
   if(base == "EUR" && quote == "USD")
      return -1;
   return 0;
  }

// dir : +1 achat, -1 vente, 0 rien. slDist : distance du stop loss en prix
bool GetSignal(const datetime entryBarTime, int &dir, double &slDist, string &why)
  {
   dir = 0;
   slDist = 0.0;
   double atr = 0.0, rsi = 0.0;
   if(!GetIndicatorValue(g_hATR, 0, 1, atr) ||
      !GetIndicatorValue(g_hRSI, 0, 1, rsi))
     {
      why = "Indicateurs en cours de chargement";
      return false;
     }
   if(Bars(_Symbol, InpATRTF) < InpATRPeriod + 10 || Bars(_Symbol, InpSignalTF) < InpRSIPeriod + 10 || atr <= 0.0)
     {
      why = "Historique insuffisant";
      return false;
     }
   g_lastRSI = rsi;

   int bias = TradeBias();
   g_trendText = (bias < 0) ? "VENTE (euro faible en séance européenne)" : ((bias > 0) ? "ACHAT (sens forcé)" : "aucun");
   if(bias == 0)
     {
      why = "Robot spécialisé EURUSD : placez-le sur un graphique EURUSD";
      return true;
     }
   slDist = InpSL_ATR * atr;
   if(!HourInWindow(SessionHour(entryBarTime), InpSessionStart, InpSessionEnd))
     {
      why = StringFormat("Hors fenêtre d'entrée (%dh-%dh)", InpSessionStart, InpSessionEnd);
      return true;
     }

   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   if(bias < 0 && rsi > InpRSIPullback && mode != SYMBOL_TRADE_MODE_LONGONLY)
      dir = -1;
   else
      if(bias > 0 && rsi < 100.0 - InpRSIPullback && mode != SYMBOL_TRADE_MODE_SHORTONLY)
         dir = 1;

   if(dir == 0)
      why = StringFormat("Fenêtre ouverte - attente d'un rebond M5 (RSI %.1f)", rsi);
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
// prochaine ouverture de la fenêtre d'entrée (jours ouvrés), en heure serveur
string NextWindowText(const datetime now)
  {
   int offset = (InpTimeBase == TIME_BASE_GMT) ? ServerGMTOffset(now) : 0;
   datetime day = DayStart(now);
   for(int k = 0; k < 8; k++)
     {
      datetime start = day + (datetime)(k * 86400) + (datetime)(InpSessionStart * 3600) + (datetime)offset;
      int dow = DowOf(start);
      if(dow == 0 || dow == 6 || start <= now)
         continue;
      long mins = (long)(start - now) / 60;
      return TimeToString(start, TIME_DATE | TIME_MINUTES) + StringFormat(" (dans %I64dh%02I64d)", mins / 60, mins % 60);
     }
   return "-";
  }

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
   s += "IABot EURUSD  |  " + _Symbol + "  |  compte " + (g_isHedging ? "hedging" : "netting") + "  |  magic " + IntegerToString((long)InpMagic) + "\n";
   s += "Biais : " + g_trendText + "   |   RSI(" + IntegerToString(InpRSIPeriod) + ") " + TFToString(InpSignalTF) + " : " + DoubleToString(g_lastRSI, 1) + "\n";
   s += "Fenêtre d'entrée " + IntegerToString(InpSessionStart) + "h-" + IntegerToString(InpSessionEnd) + "h : " + (inSession ? "OUVERTE" : "fermée") + "   |   Sortie " + IntegerToString(InpExitHour) + "h   |   Spread : " + DoubleToString(spreadPts, 0) + " pts\n";
   if(!inSession)
      s += "Prochaine fenêtre de trading : " + NextWindowText(now) + "\n";
   s += "News : " + NextNewsText(now) + "\n";
   int memCount = 0;
   double memSum = RecentPerformanceR(memCount);
   s += "Mémoire : " + IntegerToString(memCount) + " trades, bilan " + DoubleToString(memSum, 1) + " R  ->  risque " +
        (g_riskReduced ? "RÉDUIT (protection)" : "normal") + "\n";
   s += "Risque/trade : " + (InpRiskMode == RISK_FIXED_LOT ? "lot fixe " + DoubleToString(InpFixedLot, 2) : DoubleToString(EffectiveRiskPercent(), 2) + "%");
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
   if(InpRSIPeriod < 2 || InpATRPeriod < 1)
     {
      Print("IABot: périodes RSI/ATR invalides");
      ok = false;
     }
   if(InpMaxPositions < 1 || InpMinMinutesBetween < 0 || InpAdaptiveWindow < 1 || InpAdaptiveFactor <= 0.0 || InpAdaptiveFactor > 1.0)
     {
      Print("IABot: paramètres de positions / risque adaptatif invalides");
      ok = false;
     }
   if(InpRSIPullback <= 50.0 || InpRSIPullback >= 100.0)
     {
      Print("IABot: niveau de rebond RSI invalide (entre 50 et 100)");
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
   if(InpSessionStart < 0 || InpSessionStart > 23 || InpSessionEnd < 0 || InpSessionEnd > 24 || InpSessionStart >= InpSessionEnd)
     {
      Print("IABot: fenêtre d'entrée invalide");
      ok = false;
     }
   if(InpExitHour >= 0 && (InpExitHour > 23 || InpExitHour < InpSessionEnd))
     {
      Print("IABot: l'heure de sortie doit être après la fin de la fenêtre d'entrée");
      ok = false;
     }
   return ok;
  }

//+------------------------------------------------------------------+
//| Événements                                                        |
//+------------------------------------------------------------------+
int OnInit()
  {
   if(!ValidateInputs())
      return INIT_PARAMETERS_INCORRECT;
   if(InpProfile == FX_PROFILE_WINRATE)
     {
      g_tpR = 3.0;
      g_beR = 0.5;
     }
   else
      if(InpProfile == FX_PROFILE_RETURN)
        {
         g_tpR = 3.0;
         g_beR = 1.0;
        }
      else
        {
         g_tpR = InpTP_R;
         g_beR = InpBE_TriggerR;
        }
   if(InpUsePartialClose && g_tpR > 0.0 && InpPartialAtR >= g_tpR)
      PrintFormat("IABot: attention - clôture partielle à %.2f R >= take profit (%.2f R) : elle ne se déclenchera jamais",
                  InpPartialAtR, g_tpR);

   g_isTester = (MQLInfoInteger(MQL_TESTER) != 0);
   ENUM_ACCOUNT_MARGIN_MODE mm = (ENUM_ACCOUNT_MARGIN_MODE)AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   g_isHedging = (mm == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
   g_filling = DetectFilling();
   g_gvPrefix = "IAB_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + IntegerToString((long)InpMagic) + "_";

   g_hATR = iATR(_Symbol, InpATRTF, InpATRPeriod);
   g_hRSI = iRSI(_Symbol, InpSignalTF, InpRSIPeriod, PRICE_CLOSE);
   g_hATRLong = iATR(_Symbol, InpATRTF, 240);
   if(g_hATR == INVALID_HANDLE || g_hRSI == INVALID_HANDLE)
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
               _Symbol, (g_isHedging ? "hedging" : "netting"), (int)g_filling, InpRiskPercent, InpSL_ATR, g_tpR);
   if(TradeBias() == 0)
      PrintFormat("IABot: ATTENTION - robot spécialisé EURUSD, %s n'est pas pris en charge", _Symbol);
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
   if(g_hATR != INVALID_HANDLE)
      IndicatorRelease(g_hATR);
   if(g_hRSI != INVALID_HANDLE)
      IndicatorRelease(g_hRSI);
   if(g_hATRLong != INVALID_HANDLE)
      IndicatorRelease(g_hATRLong);
   g_hATRLong = INVALID_HANDLE;
   g_hATR = INVALID_HANDLE;
   g_hRSI = INVALID_HANDLE;
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

   string why = "";
   int dir = 0;
   double slDist = 0.0;
   bool haveSignal = GetSignal(barTime, dir, slDist, why);
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
   if(!CanOpenNewTrade(barTime, why))
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
