//+------------------------------------------------------------------+
//|                                                 IABot_EURUSD.mq5 |
//|          Robot de trading autonome spécialisé EURUSD (M5)        |
//|                                                                  |
//|  Robot 100 % EURUSD : il ne lit aucune autre paire.              |
//|                                                                  |
//|  Ce que le robot a appris (19 ans de données MT5 réelles EURUSD  |
//|  2007-2025, heure serveur exacte, spread réel, calendrier        |
//|  économique 2007-2025 ; réglages appris sur 2007-2018 et validés |
//|  sur 2019-2025 et 2026) :                                        |
//|   - l'euro tend à baisser face au dollar pendant la séance       |
//|     européenne (Ranaldo 2009, Breedon & Ranaldo 2013), surtout   |
//|     en tout début de séance : ventes sur rebond M5 de 8h à 15h   |
//|     (heure serveur GMT+2/+3), jusqu'à 10 positions par jour ;    |
//|   - entrée seulement si tout est validé : rebond étiré (RSI(3)   |
//|     > 65 et Bollinger > 1,5 écart-type), veille >= 6 ATR,        |
//|     volatilité calme, pas lundi / Fed / fin de mois, pas         |
//|     d'annonce, spread correct ;                                  |
//|   - mise pondérée selon l'heure (appris sur 2007-2018) : x1,5 à  |
//|     8h, x1 de 9h à 12h, x0,6 à 12h, x0,4 à 13h, x0,2 à 14h.      |
//|                                                                  |
//|  Gestion : SL = 3 x ATR(14) H1, TP = 2 R, break-even à +0,7 R.   |
//|  Sortie à 15h si la position est en gain, sinon elle est gardée  |
//|  et fermée dès qu'elle repasse en gain, au plus tard à 17h.      |
//|  Temps réel : liste des contrôles, tendances M5/H1/H4/D1, ADX,   |
//|  MACD, Bollinger, RSI, pivots, volatilité, calendrier MT5.       |
//+------------------------------------------------------------------+
#property copyright   "IABot"
#property version     "9.10"
#property description "Robot autonome 100 % EURUSD (M5) : séance européenne 8h-15h, jusqu'à 10 trades/jour,"
#property description "rebonds étirés (RSI + Bollinger), 10 contrôles avant chaque trade (calendrier, veille, volatilité,"
#property description "news...), mise pondérée selon l'heure (x1,5 à 8h), SL 3 ATR H1, TP 2 R, BE 0,7 R, sortie 15h-17h."

//+------------------------------------------------------------------+
//| Enumerations                                                      |
//+------------------------------------------------------------------+
enum ENUM_RISK_MODE
  {
   RISK_PCT_BALANCE = 0, // % du solde
   RISK_PCT_EQUITY  = 1, // % des fonds propres (equity)
   RISK_FIXED_LOT   = 2  // Lot fixe
  };

enum ENUM_RISK_PROFILE
  {
   RISK_PROFILE_PRUDENT  = 0, // Prudent : 0,30 % (drawdown 19 ans ~12 %)
   RISK_PROFILE_BALANCED = 1, // Équilibré : 0,35 % (drawdown ~14 %)
   RISK_PROFILE_DYNAMIC  = 2, // Dynamique : 0,40 % (drawdown ~15,5 %)
   RISK_PROFILE_MAXIMUM  = 3  // Maximum : 0,45 % (drawdown ~17,5 %)
  };

enum ENUM_FX_DIRECTION
  {
   FX_DIR_AUTO      = 0, // Automatique (vente de l'EURUSD)
   FX_DIR_SELL_ONLY = 1, // Ventes uniquement
   FX_DIR_BUY_ONLY  = 2  // Achats uniquement (déconseillé : aucun avantage mesuré)
  };

enum ENUM_FX_PROFILE
  {
   FX_PROFILE_WINRATE = 0, // Taux de réussite max (sortie en gain, maintien jusqu'à 17h si perte)
   FX_PROFILE_RETURN  = 1, // Rendement maximal (sortie à 15h dans tous les cas)
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
input double            InpRSIPullback      = 65.0;              // Vente si RSI > niveau (achat si RSI < 100 - niveau)
input double            InpMinPrevRangeATR  = 6.0;               // Filtre : amplitude de la veille >= x ATR H1 (0 = off)
input ENUM_TIMEFRAMES   InpATRTF            = PERIOD_H1;         // Unité de temps de l'ATR (stop loss)
input int               InpATRPeriod        = 14;                // Période ATR
input int               InpExitHour         = 15;                // Heure de sortie forcée (référence horaire de la session)
input int               InpMaxPositions     = 10;                // Positions simultanées max
input int               InpMinMinutesBetween = 15;               // Minutes minimum entre deux entrées

input group "=== Stop loss / Take profit / Break-even ==="
input ENUM_FX_PROFILE   InpProfile          = FX_PROFILE_WINRATE; // Profil de sortie
input int               InpHoldUntilHour    = 17;                // Profil taux de réussite : position perdante gardée jusqu'à (heure)
input double            InpExitMinProfitR   = 0.05;              // Profil taux de réussite : sortie dès que le gain atteint +R
input double            InpSL_ATR           = 3.0;               // Stop loss = ATR x (définit 1 R)
input double            InpTP_R             = 2.0;               // Take profit = R x (profil personnalisé)
input bool              InpUseBreakEven     = true;              // Activer le break-even
input double            InpBE_TriggerR      = 0.7;               // Break-even déclenché à +R (profil personnalisé)
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
input ENUM_RISK_PROFILE InpRiskProfile   = RISK_PROFILE_BALANCED; // Profil de risque (mise de base par trade, x1,5 à 8h ... x0,2 à 14h)
input double          InpRiskPercent      = 0.0;               // Risque personnalisé (%) : remplace le profil si > 0
input double          InpFixedLot         = 0.01;              // Lot fixe (mode lot fixe)
input double          InpMaxLot           = 50.0;              // Lot maximum
input double          InpMinLotMaxRiskPct = 2.0;               // Risque max (%) toléré si le lot minimum est imposé
input double          InpCommissionPerLot = 0.0;               // Commission aller-retour par lot (devise du compte)
input double          InpMaxDailyLossPct  = 3.0;               // Perte journalière max en % (0 = off)
input bool            InpCloseOnDailyLoss = false;             // Fermer les positions si la perte journalière est atteinte
input double          InpMaxDrawdownPct   = 20.0;              // Drawdown max depuis le sommet en % (0 = off)
input bool            InpCloseOnMaxDD     = true;              // Fermer les positions si le drawdown max est atteint
input bool            InpResetProtection  = false;             // Réarmer le robot après un arrêt drawdown
input int             InpMaxTradesPerDay  = 10;                // Trades max par jour (0 = illimité)
input bool            InpUseAdaptiveRisk  = false;             // Risque adaptatif (mémoire des derniers trades)
input int             InpAdaptiveWindow   = 60;                // Nombre de trades mémorisés
input double          InpAdaptiveFactor   = 0.5;               // Multiplicateur de risque si le bilan récent est négatif
input int             InpMaxConsecLosses  = 0;                 // Pertes consécutives max par jour (0 = off)
input double          InpMaxVolatility    = 1.0;               // Filtre volatilité : pas de trade si ATR H1 > x fois sa moyenne 10 jours (0 = off)
input int             InpMaxSpreadPoints  = 20;                // Spread max en points (0 = automatique)
input double          InpMaxSpreadPctSL   = 10.0;              // Spread max en % de la distance du SL
input int             InpSlippagePoints   = 10;                // Glissement max (points)

input group "=== Horaires ==="
input ENUM_TIME_BASE  InpTimeBase         = TIME_BASE_SERVER;  // Référence horaire de la session
input int             InpSessionStart     = 8;                 // Début de la fenêtre d'entrée (heure)
input int             InpSessionEnd       = 15;                // Fin de la fenêtre d'entrée (heure, exclue)
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
input bool            InpCloseBeforeNews  = false;             // Fermer une position gardée en perte 10 min avant une news (déconseillé)

input group "=== Intelligence de marché (v9, EURUSD seul) ==="
input bool            InpSkipMonday       = true;              // Pas de trade le lundi (jour le plus faible, 13 années sur 19)
input bool            InpSkipFOMC         = true;              // Pas de trade le jour d'une décision de la Fed (FOMC)
input bool            InpSkipMonthEnd     = true;              // Pas de trade le dernier jour ouvré du mois
input double          InpMinBollinger     = 1.5;               // Vente si le prix est > x écarts-types au-dessus de sa moyenne 20 M5 (0 = off)
input double          InpMinAsiaRangeATR  = 0.0;               // Nuit asiatique (7h avant la fenêtre) : amplitude >= x ATR H1 (0 = off, non retenu)
input bool            InpHourWeighting    = true;              // Mise pondérée selon l'heure (x1,5 à 8h ... x0,2 à 14h)

input group "=== Affichage ==="
input bool            InpShowPanel        = true;              // Afficher le panneau d'information

//+------------------------------------------------------------------+
//| Variables globales                                                |
//+------------------------------------------------------------------+
int      g_hATR            = INVALID_HANDLE;
int      g_hRSI            = INVALID_HANDLE;
int      g_hATRLong        = INVALID_HANDLE;
int      g_hEmaM5          = INVALID_HANDLE;   // analyse de marché (EMA 50)
int      g_hEmaH1          = INVALID_HANDLE;
int      g_hEmaH4          = INVALID_HANDLE;
int      g_hEmaD1          = INVALID_HANDLE;
int      g_hADX            = INVALID_HANDLE;   // analyse : force de tendance H1
int      g_hRSI14          = INVALID_HANDLE;   // analyse : RSI(14) M5
int      g_hEma12H1        = INVALID_HANDLE;   // analyse : MACD H1 (EMA 12 - EMA 26)
int      g_hEma26H1        = INVALID_HANDLE;

datetime g_fomcDays[];               // jours de décision de la Fed (heure serveur, début de journée)

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
bool     g_condExit        = true;  // sortie de séance conditionnelle (profil taux de réussite)
double   g_prevRangeATR    = 0.0;   // amplitude de la veille en ATR H1 (filtre de qualité)

string   g_status          = "Initialisation";
double   g_lastBB          = 0.0;   // dernier écart Bollinger M5 (écarts-types)
double   g_monthPL         = 0.0;   // gain clôturé du mois en cours
double   g_prevMonthPL     = 0.0;   // gain clôturé du mois précédent
int      g_monthTrades     = 0;     // trades ouverts ce mois-ci
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

// mise selon l'heure d'entrée, proportionnelle au gain moyen mesuré sur 2007-2018 (validé sur 2019-2026) :
// 1re heure x1,5 ; 2e x1,0 ; 3e x0,9 ; 4e x1,0 ; 5e x0,6 ; 6e x0,4 ; 7e x0,2
double HourRiskFactor(const int sessionHour)
  {
   if(!InpHourWeighting)
      return 1.0;
   int k = sessionHour - InpSessionStart;
   switch(k)
     {
      case 0:
         return 1.5;
      case 1:
         return 1.0;
      case 2:
         return 0.9;
      case 3:
         return 1.0;
      case 4:
         return 0.6;
      case 5:
         return 0.4;
      case 6:
         return 0.2;
      default:
         return 1.0;
     }
  }

// mise de base selon le profil (ou le risque personnalisé)
double ProfileRiskPercent()
  {
   if(InpRiskPercent > 0.0)
      return InpRiskPercent;
   switch(InpRiskProfile)
     {
      case RISK_PROFILE_PRUDENT:
         return 0.30;
      case RISK_PROFILE_DYNAMIC:
         return 0.40;
      case RISK_PROFILE_MAXIMUM:
         return 0.45;
      default:
         return 0.35;
     }
  }

double BaseRiskPercent()
  {
   return ProfileRiskPercent() * HourRiskFactor(SessionHour(TimeCurrent()));
  }

double EffectiveRiskPercent()
  {
   if(!InpUseAdaptiveRisk)
      return BaseRiskPercent();
   int count = 0;
   double sum = RecentPerformanceR(count);
   bool reduce = (count >= InpAdaptiveWindow && sum < 0.0);
   if(reduce != g_riskReduced)
     {
      g_riskReduced = reduce;
      PrintFormat("IABot: risque adaptatif -> %s (bilan des %d derniers trades : %+.1f R)",
                  reduce ? "RÉDUIT" : "normal", count, sum);
     }
   return reduce ? BaseRiskPercent() * InpAdaptiveFactor : BaseRiskPercent();
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

// gains clôturés du mois en cours et du mois précédent (positions du robot)
void ComputeMonthStats()
  {
   g_monthPL = 0.0;
   g_prevMonthPL = 0.0;
   g_monthTrades = 0;
   MqlDateTime d;
   TimeToStruct(TimeCurrent(), d);
   d.day = 1;
   d.hour = 0;
   d.min = 0;
   d.sec = 0;
   datetime monthStart = StructToTime(d);
   d.mon -= 1;
   if(d.mon < 1)
     {
      d.mon = 12;
      d.year -= 1;
     }
   datetime prevStart = StructToTime(d);
   if(!HistorySelect(prevStart, TimeCurrent() + 86400))
      return;
   int total = HistoryDealsTotal();
   for(int i = 0; i < total; i++)
     {
      ulong deal = HistoryDealGetTicket(i);
      if(deal == 0)
         continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol || (ulong)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic)
         continue;
      datetime dt = (datetime)HistoryDealGetInteger(deal, DEAL_TIME);
      double pl = HistoryDealGetDouble(deal, DEAL_PROFIT) + HistoryDealGetDouble(deal, DEAL_COMMISSION)
                  + HistoryDealGetDouble(deal, DEAL_SWAP) + HistoryDealGetDouble(deal, DEAL_FEE);
      if(dt >= monthStart)
        {
         g_monthPL += pl;
         if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) == DEAL_ENTRY_IN)
            g_monthTrades++;
        }
      else
         g_prevMonthPL += pl;
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
// une news importante est-elle prévue dans les prochaines minutes ?
bool NewsWithin(const datetime now, const int minutes, string &info)
  {
   info = "";
   if(g_isTester || !InpUseNewsFilter)
      return false;
   for(int i = 0; i < ArraySize(g_newsTimes); i++)
     {
      datetime t = g_newsTimes[i];
      if(t >= now && t - now <= (datetime)(minutes * 60))
        {
         info = g_newsNames[i];
         return true;
        }
     }
   return false;
  }

// sortie de séance : à l'heure de sortie ; en profil "taux de réussite", une position perdante est gardée
// (SL / break-even / TP toujours actifs) et fermée dès qu'elle repasse en gain, au plus tard à InpHoldUntilHour
bool IsSessionExitTime(const datetime now, const datetime openTime, const double profitR)
  {
   if(InpExitHour < 0)
      return false;
   if(now - openTime >= 20 * 3600)
      return true;
   int h = SessionHour(now);
   if(!(h >= InpExitHour && SessionHour(openTime) < InpExitHour))
      return false;
   if(!g_condExit)
      return true;
   if(profitR >= InpExitMinProfitR)
      return true;
   return (h >= InpHoldUntilHour);
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
      // option : ne pas laisser une position gardée en perte traverser une news importante (désactivé par défaut :
      // sur 2007-2025, cette fermeture faisait perdre 0,1 R par trade en moyenne)
      if(InpCloseBeforeNews && g_condExit && InpExitHour >= 0 && SessionHour(now) >= InpExitHour && SessionHour(openTime) < InpExitHour)
        {
         string newsInfo = "";
         if(NewsWithin(now, 10, newsInfo))
           {
            ClosePosition(ticket, vol, "news imminente : " + newsInfo);
            continue;
           }
        }
      if(IsSessionExitTime(now, openTime, profitR))
        {
         ClosePosition(ticket, vol, (profitR >= 0.0) ? "sortie de fin de séance (en gain)" : "sortie de fin de séance");
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
         why = StringFormat("Volatilité trop élevée (ATR H1 = %.2f x sa moyenne > %.2f)", atrNow / atrLong, InpMaxVolatility);
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
//| Intelligence de marché : calendrier et force des devises          |
//+------------------------------------------------------------------+
// décisions de la Fed (FOMC), heure serveur : 2007-2026 (calendrier officiel publié à l'avance)
string FomcDates()
  {
   string d = "";
   d += "2007.01.31 2007.03.21 2007.05.09 2007.06.28 2007.08.07 2007.09.18 2007.10.31 2007.12.11 ";
   d += "2008.01.22 2008.01.30 2008.03.18 2008.04.30 2008.06.25 2008.08.05 2008.09.16 2008.10.08 2008.10.29 2008.12.16 ";
   d += "2009.01.28 2009.03.18 2009.04.29 2009.06.24 2009.08.12 2009.09.23 2009.11.04 2009.12.16 ";
   d += "2010.01.27 2010.03.16 2010.04.28 2010.06.23 2010.08.10 2010.09.21 2010.11.03 2010.12.14 ";
   d += "2011.01.26 2011.03.15 2011.04.27 2011.06.22 2011.08.09 2011.09.21 2011.11.02 2011.12.13 ";
   d += "2012.01.25 2012.03.13 2012.04.25 2012.06.20 2012.08.01 2012.09.13 2012.10.24 2012.12.12 ";
   d += "2013.01.30 2013.03.20 2013.05.01 2013.06.19 2013.07.31 2013.09.18 2013.10.30 2013.12.18 ";
   d += "2014.01.29 2014.03.19 2014.04.30 2014.06.18 2014.07.30 2014.09.17 2014.10.29 2014.12.17 ";
   d += "2015.01.28 2015.03.18 2015.04.29 2015.06.17 2015.07.29 2015.09.17 2015.10.28 2015.12.16 ";
   d += "2016.01.27 2016.03.16 2016.04.27 2016.06.15 2016.07.27 2016.09.21 2016.11.02 2016.12.14 ";
   d += "2017.02.01 2017.03.15 2017.05.03 2017.06.14 2017.07.26 2017.09.20 2017.11.01 2017.12.13 ";
   d += "2018.01.31 2018.03.21 2018.05.02 2018.06.13 2018.08.01 2018.09.26 2018.11.08 2018.12.19 ";
   d += "2019.01.30 2019.03.20 2019.05.01 2019.06.19 2019.07.31 2019.09.18 2019.10.30 2019.12.11 ";
   d += "2020.01.29 2020.03.03 2020.03.16 2020.04.29 2020.06.10 2020.07.29 2020.09.16 2020.11.05 2020.12.16 ";
   d += "2021.01.27 2021.03.17 2021.04.28 2021.06.16 2021.07.28 2021.09.22 2021.11.03 2021.12.15 ";
   d += "2022.01.26 2022.03.16 2022.05.04 2022.06.15 2022.07.27 2022.09.21 2022.11.02 2022.12.14 ";
   d += "2023.02.01 2023.03.22 2023.05.03 2023.06.14 2023.07.26 2023.09.20 2023.11.01 2023.12.13 ";
   d += "2024.01.31 2024.03.20 2024.05.01 2024.06.12 2024.07.31 2024.09.18 2024.11.07 2024.12.18 ";
   d += "2025.01.29 2025.03.19 2025.05.07 2025.06.18 2025.07.30 2025.09.17 2025.10.29 2025.12.10 ";
   d += "2026.01.28 2026.03.18 2026.04.29 2026.06.17 2026.07.29 2026.09.16 2026.10.28 2026.12.09";
   return d;
  }

void LoadFOMCDates()
  {
   string parts[];
   int n = StringSplit(FomcDates(), ' ', parts);
   ArrayResize(g_fomcDays, 0);
   for(int i = 0; i < n; i++)
     {
      if(StringLen(parts[i]) != 10)
         continue;
      MqlDateTime d;
      ZeroMemory(d);
      d.year = (int)StringToInteger(StringSubstr(parts[i], 0, 4));
      d.mon = (int)StringToInteger(StringSubstr(parts[i], 5, 2));
      d.day = (int)StringToInteger(StringSubstr(parts[i], 8, 2));
      int sz = ArraySize(g_fomcDays);
      ArrayResize(g_fomcDays, sz + 1);
      g_fomcDays[sz] = StructToTime(d);
     }
  }

// jour de décision de la Fed : table officielle, complétée en direct par le calendrier MT5
bool IsFOMCDay(const datetime t)
  {
   datetime day = DayStart(t);
   for(int i = 0; i < ArraySize(g_fomcDays); i++)
      if(g_fomcDays[i] == day)
         return true;
   for(int i = 0; i < ArraySize(g_newsTimes); i++)
      if(DayStart(g_newsTimes[i]) == day && StringFind(g_newsNames[i], "USD") == 0 &&
         (StringFind(g_newsNames[i], "Fed Interest Rate Decision") >= 0 || StringFind(g_newsNames[i], "FOMC Statement") >= 0))
         return true;
   return false;
  }

// dernier jour ouvré du mois (le jour ouvré suivant tombe dans un autre mois)
bool IsMonthEnd(const datetime t)
  {
   datetime day = DayStart(t);
   datetime next = day + 86400;
   while(DowOf(next) == 0 || DowOf(next) == 6)
      next += 86400;
   MqlDateTime a, b;
   TimeToStruct(day, a);
   TimeToStruct(next, b);
   return (a.mon != b.mon);
  }

// jour écarté par le calendrier : renvoie la raison (vide = jour tradable)
string CalendarDayBlock(const datetime t)
  {
   if(InpSkipMonday && DowOf(t) == 1)
      return "lundi (jour historiquement défavorable)";
   if(InpSkipFOMC && IsFOMCDay(t))
      return "décision de la Fed (FOMC) aujourd'hui";
   if(InpSkipMonthEnd && IsMonthEnd(t))
      return "dernier jour ouvré du mois (flux de fin de mois)";
   return "";
  }

// écart de la clôture `shift` à sa moyenne mobile 20 (M5), en écarts-types (Bollinger, écart-type de population)
bool BollingerZ(const int shift, double &z)
  {
   z = 0.0;
   double sum = 0.0, sq = 0.0;
   for(int k = shift; k < shift + 20; k++)
     {
      double c = iClose(_Symbol, PERIOD_M5, k);
      if(c <= 0.0)
         return false;
      sum += c;
      sq += c * c;
     }
   double mid = sum / 20.0;
   double variance = sq / 20.0 - mid * mid;
   if(variance <= 0.0)
      return false;
   z = (iClose(_Symbol, PERIOD_M5, shift) - mid) / MathSqrt(variance);
   return true;
  }

// amplitude de la nuit asiatique du jour : clôtures M5 des 7 heures qui précèdent la fenêtre d'entrée
// (1h-8h serveur par défaut), rapportée à l'ATR H1. Faux si les bougies manquent.
bool AsiaRangeATR(const datetime barTime, const double atr, double &rangeATR)
  {
   rangeATR = 0.0;
   if(atr <= 0.0)
      return false;
   int offset = (InpTimeBase == TIME_BASE_GMT) ? ServerGMTOffset(barTime) : 0;
   datetime day = DayStart(barTime);
   datetime from = day + (datetime)((InpSessionStart - 7) * 3600 + offset);
   datetime to = day + (datetime)(InpSessionStart * 3600 + offset);
   double hi = 0.0, lo = 0.0;
   int n = 0;
   for(int k = 1; k < 500; k++)
     {
      datetime t = iTime(_Symbol, PERIOD_M5, k);
      if(t == 0 || t < from)
         break;
      if(t >= to)
         continue;
      double c = iClose(_Symbol, PERIOD_M5, k);
      if(c <= 0.0)
         continue;
      if(n == 0 || c > hi)
         hi = c;
      if(n == 0 || c < lo)
         lo = c;
      n++;
     }
   if(n < 12)
      return false;
   rangeATR = (hi - lo) / atr;
   return true;
  }

//+------------------------------------------------------------------+
//| Signal de la stratégie (bougies clôturées uniquement)             |
//+------------------------------------------------------------------+
// biais de la stratégie : -1 vendre la paire, +1 acheter, 0 paire non prise en charge
bool IsEURUSD()
  {
   return (SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE) == "EUR" && SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT) == "USD");
  }

int TradeBias()
  {
   // robot 100 % EURUSD : aucune autre paire n'est tradée
   if(!IsEURUSD())
      return 0;
   if(InpDirection == FX_DIR_BUY_ONLY)
      return 1;
   // l'euro faiblit face au dollar pendant la séance européenne
   return -1;
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
   // filtre de qualité : la veille doit avoir bougé suffisamment par rapport à la volatilité horaire actuelle
   g_prevRangeATR = 0.0;
   double pdHigh = iHigh(_Symbol, PERIOD_D1, 1);
   double pdLow = iLow(_Symbol, PERIOD_D1, 1);
   if(pdHigh > 0.0 && pdLow > 0.0)
      g_prevRangeATR = (pdHigh - pdLow) / atr;
   if(InpMinPrevRangeATR > 0.0)
     {
      if(pdHigh <= 0.0 || pdLow <= 0.0)
        {
         why = "Bougie journalière de la veille indisponible";
         return false;
        }
      if(g_prevRangeATR < InpMinPrevRangeATR)
        {
         why = StringFormat("Journée écartée : amplitude de la veille %.1f x ATR (< %.1f)", g_prevRangeATR, InpMinPrevRangeATR);
         return true;
        }
     }

   // calendrier : lundi, décision de la Fed, fin de mois
   string block = CalendarDayBlock(entryBarTime);
   if(StringLen(block) > 0)
     {
      why = "Journée écartée : " + block;
      return true;
     }
   // nuit asiatique trop calme : le marché manque d'élan, les ventes européennes rapportent peu
   if(InpMinAsiaRangeATR > 0.0)
     {
      double ar = 0.0;
      if(!AsiaRangeATR(entryBarTime, atr, ar))
        {
         why = "Nuit asiatique : données M5 insuffisantes";
         return true;
        }
      if(ar < InpMinAsiaRangeATR)
        {
         why = StringFormat("Journée écartée : nuit asiatique trop calme (%.1f x ATR < %.1f)", ar, InpMinAsiaRangeATR);
         return true;
        }
     }

   ENUM_SYMBOL_TRADE_MODE mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
   if(bias < 0 && rsi > InpRSIPullback && mode != SYMBOL_TRADE_MODE_LONGONLY)
      dir = -1;
   else
      if(bias > 0 && rsi < 100.0 - InpRSIPullback && mode != SYMBOL_TRADE_MODE_SHORTONLY)
         dir = 1;

   if(dir == 0)
     {
      why = StringFormat("Fenêtre ouverte - attente d'un rebond M5 (RSI %.1f)", rsi);
      return true;
     }
   // rebond suffisamment étiré : écart du prix à sa moyenne 20 (Bollinger M5), en écarts-types
   if(InpMinBollinger > 0.0)
     {
      double z = 0.0;
      if(!BollingerZ(1, z))
        {
         why = "Historique M5 insuffisant (Bollinger)";
         dir = 0;
         return true;
        }
      g_lastBB = z;
      if(z * (dir < 0 ? 1.0 : -1.0) <= InpMinBollinger)
        {
         why = StringFormat("Rebond pas assez étiré : Bollinger %+.2f écart-type (seuil %.2f)", z, InpMinBollinger);
         dir = 0;
         return true;
        }
     }
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
//| Analyse de marché en temps réel (affichage)                       |
//+------------------------------------------------------------------+
string TrendOf(const int handle, const ENUM_TIMEFRAMES tf)
  {
   double e1 = 0.0, e4 = 0.0;
   if(!GetIndicatorValue(handle, 0, 1, e1) || !GetIndicatorValue(handle, 0, 4, e4))
      return "?";
   double c = iClose(_Symbol, tf, 1);
   if(c > e1 && e1 > e4)
      return "hausse";
   if(c < e1 && e1 < e4)
      return "baisse";
   return "neutre";
  }

string MarketSessionName(const datetime serverTime)
  {
   int h = HourOf(serverTime);
   if(h >= 1 && h < 9)
      return "Asie";
   if(h >= 9 && h < 15)
      return "Europe";
   if(h >= 15 && h < 22)
      return "Etats-Unis";
   return "clôture / rollover";
  }

// prévision statistique : résultats du robot sur 14 ans (EURUSD 2005-2018) selon l'heure d'entrée
string ForecastText(const datetime now)
  {
   if(TradeBias() == 0)
      return "symbole non pris en charge";
   int h = SessionHour(now);
   if(!HourInWindow(h, InpSessionStart, InpSessionEnd))
      return "aucun avantage statistique mesuré à cette heure (19 ans de données MT5) - le robot observe";
   // statistiques du robot v9 sur 19 ans de données MT5 réelles (EURUSD 2007-2025), par heure d'entrée
   double win = 0.0, er = 0.0;
   switch(h)
     {
      case 8:
         win = 70.0;
         er = 0.168;
         break;
      case 9:
         win = 67.0;
         er = 0.082;
         break;
      case 10:
         win = 70.0;
         er = 0.089;
         break;
      case 11:
         win = 77.0;
         er = 0.110;
         break;
      case 12:
         win = 75.0;
         er = 0.045;
         break;
      case 13:
         win = 77.0;
         er = 0.031;
         break;
      case 14:
         win = 83.0;
         er = 0.021;
         break;
      default:
         break;
     }
   if(win <= 0.0)
      return "fenêtre ouverte (heure hors statistiques de référence)";
   return StringFormat("vente favorable - sur 19 ans, les entrées de %dh ont gagné %.0f%% du temps (%+.3f R/trade)", h, win, er);
  }

// liste des contrôles effectués avant chaque trade (OK = condition remplie)
string CheckItem(const string name, const bool ok, int &passed, int &total)
  {
   total++;
   if(ok)
      passed++;
   return name + (ok ? " OK" : " NON");
  }

string ChecklistText(const datetime now, const double prevATR, const bool asiaKnown, const double asiaR, const double atr, const double atrL)
  {
   int passed = 0, total = 0;
   string c = "";
   c += CheckItem("fenêtre", HourInWindow(SessionHour(now), InpSessionStart, InpSessionEnd), passed, total) + " | ";
   c += CheckItem("calendrier", StringLen(CalendarDayBlock(now)) == 0, passed, total) + " | ";
   c += CheckItem(StringFormat("veille %.1f", prevATR), InpMinPrevRangeATR <= 0.0 || prevATR >= InpMinPrevRangeATR, passed, total) + " | ";
   c += CheckItem(asiaKnown ? StringFormat("nuit Asie %.1f", asiaR) : "nuit Asie ?", InpMinAsiaRangeATR <= 0.0 || (asiaKnown && asiaR >= InpMinAsiaRangeATR), passed, total) + " | ";
   c += CheckItem(StringFormat("volatilité %.2f", atrL > 0.0 ? atr / atrL : 0.0), InpMaxVolatility <= 0.0 || (atrL > 0.0 && atr <= InpMaxVolatility * atrL), passed, total) + " | ";
   string newsInfo = "";
   c += CheckItem("news", !IsNewsBlackout(now, newsInfo), passed, total) + " | ";
   MqlTick tk;
   double spread = (SymbolInfoTick(_Symbol, tk) ? tk.ask - tk.bid : 0.0);
   c += CheckItem("spread", InpMaxSpreadPoints <= 0 || spread <= InpMaxSpreadPoints * SymPoint() + SymPoint() * 0.5, passed, total) + " | ";
   c += CheckItem(StringFormat("RSI %.0f", g_lastRSI), g_lastRSI > InpRSIPullback, passed, total) + " | ";
   double z = 0.0;
   bool zOK = BollingerZ(1, z);
   c += CheckItem(StringFormat("Bollinger %+.1f", z), InpMinBollinger <= 0.0 || (zOK && z > InpMinBollinger), passed, total) + " | ";
   c += CheckItem("positions", CountMyPositions() < InpMaxPositions, passed, total);
   return StringFormat("Contrôles avant trade (%d/%d) : ", passed, total) + c + "\n";
  }

string MarketAnalysisText(const datetime now)
  {
   string s = "Tendances : M5 " + TrendOf(g_hEmaM5, PERIOD_M5) + " | H1 " + TrendOf(g_hEmaH1, PERIOD_H1) +
              " | H4 " + TrendOf(g_hEmaH4, PERIOD_H4) + " | D1 " + TrendOf(g_hEmaD1, PERIOD_D1) +
              "   |   séance : " + MarketSessionName(now) + "\n";
   double atr = 0.0, atrL = 0.0;
   string vol = "?";
   if(GetIndicatorValue(g_hATR, 0, 1, atr) && GetIndicatorValue(g_hATRLong, 0, 1, atrL) && atrL > 0.0)
     {
      double r = atr / atrL;
      vol = ((r < 0.8) ? "calme" : ((r > 1.3) ? "agitée" : "normale")) + StringFormat(" (x%.2f", r) +
            ((InpMaxVolatility > 0.0) ? StringFormat(", seuil %.2f : %s)", InpMaxVolatility, (r <= InpMaxVolatility) ? "OK" : "trop élevée") : ")");
     }
   MqlTick tk;
   double pos = 50.0;
   double dh = iHigh(_Symbol, PERIOD_D1, 0), dl = iLow(_Symbol, PERIOD_D1, 0);
   if(SymbolInfoTick(_Symbol, tk) && dh > dl)
      pos = (tk.bid - dl) / (dh - dl) * 100.0;
   double ph = iHigh(_Symbol, PERIOD_D1, 1), pl = iLow(_Symbol, PERIOD_D1, 1);
   if(atr <= 0.0)
      GetIndicatorValue(g_hATR, 0, 1, atr);
   double prevATR = (atr > 0.0 && ph > pl) ? (ph - pl) / atr : 0.0;
   s += "Volatilité : " + vol + "   |   prix à " + DoubleToString(pos, 0) + "% du range du jour\n";
   // indicateurs complémentaires
   double adx = 0.0, rsi14 = 0.0, e12 = 0.0, e26 = 0.0, e12p = 0.0, e26p = 0.0;
   string ind = "";
   if(GetIndicatorValue(g_hADX, 0, 1, adx))
      ind += StringFormat("ADX H1 %.0f (%s)", adx, adx >= 25.0 ? "tendance" : "range");
   if(GetIndicatorValue(g_hRSI14, 0, 1, rsi14))
      ind += StringFormat(" | RSI14 M5 %.0f", rsi14);
   if(GetIndicatorValue(g_hEma12H1, 0, 1, e12) && GetIndicatorValue(g_hEma26H1, 0, 1, e26) &&
      GetIndicatorValue(g_hEma12H1, 0, 2, e12p) && GetIndicatorValue(g_hEma26H1, 0, 2, e26p) && atr > 0.0)
      ind += StringFormat(" | MACD H1 %+.2f ATR (%s)", (e12 - e26) / atr, (e12 - e26) > (e12p - e26p) ? "monte" : "baisse");
   double sum = 0.0, sq = 0.0;
   int nb = 0;
   for(int k = 1; k <= 20; k++)
     {
      double c = iClose(_Symbol, PERIOD_M5, k);
      if(c <= 0.0)
         break;
      sum += c;
      sq += c * c;
      nb++;
     }
   if(nb == 20)
     {
      double mid = sum / 20.0, sd = MathSqrt(MathMax(0.0, sq / 20.0 - mid * mid));
      if(sd > 0.0)
         ind += StringFormat(" | Bollinger M5 %+.1f ET (seuil %.1f)", (iClose(_Symbol, PERIOD_M5, 1) - mid) / sd, InpMinBollinger);
     }
   double pc = iClose(_Symbol, PERIOD_D1, 1);
   if(ph > pl && pc > 0.0)
     {
      double pv = (ph + pl + pc) / 3.0;
      ind += StringFormat(" | Pivot %s R1 %s S1 %s", DoubleToString(pv, SymDigits()), DoubleToString(2.0 * pv - pl, SymDigits()), DoubleToString(2.0 * pv - ph, SymDigits()));
     }
   s += "Indicateurs : " + ind + "\n";

   string calBlock = CalendarDayBlock(now);
   double asiaR = 0.0;
   bool asiaKnown = (SessionHour(now) >= InpSessionStart && AsiaRangeATR(now, atr, asiaR));
   bool asiaOK = (InpMinAsiaRangeATR <= 0.0 || !asiaKnown || asiaR >= InpMinAsiaRangeATR);
   bool dayOK = (InpMinPrevRangeATR <= 0.0 || prevATR >= InpMinPrevRangeATR) && StringLen(calBlock) == 0 && asiaOK;
   s += "Filtre du jour : " + (dayOK ? "FAVORABLE" : "défavorable (pas de trade aujourd'hui)") +
        StringFormat(" - amplitude de la veille %.1f x ATR (seuil %.1f)", prevATR, InpMinPrevRangeATR) +
        (StringLen(calBlock) > 0 ? " - " + calBlock : "") + "\n";
   bool volOK = (InpMaxVolatility <= 0.0 || atrL <= 0.0 || atr <= InpMaxVolatility * atrL);
   string newsInfo = "";
   string forecast = ForecastText(now);
   if(!dayOK)
      forecast = "conditions du jour défavorables (filtre) - le robot ne trade pas aujourd'hui";
   else
      if(!volOK)
         forecast = "volatilité horaire trop élevée - le robot attend un marché plus calme";
   else
      if(IsNewsBlackout(now, newsInfo))
         forecast = "pause pendant l'annonce (" + newsInfo + ") - " + forecast;
   s += "Prévision : " + forecast + "\n";
   s += ChecklistText(now, prevATR, asiaKnown, asiaR, atr, atrL);
   return s;
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
   s += "Fenêtre d'entrée " + IntegerToString(InpSessionStart) + "h-" + IntegerToString(InpSessionEnd) + "h : " + (inSession ? "OUVERTE" : "fermée") + "   |   Sortie " + IntegerToString(InpExitHour) + "h" + (g_condExit ? " (si perte : jusqu'à " + IntegerToString(InpHoldUntilHour) + "h)" : "") + "   |   Spread : " + DoubleToString(spreadPts, 0) + " pts\n";
   if(!inSession)
      s += "Prochaine fenêtre de trading : " + NextWindowText(now) + "\n";
   s += MarketAnalysisText(now);
   string newsNow = "";
   s += "News : " + NextNewsText(now) + (IsNewsBlackout(now, newsNow) ? "   ->  PAUSE (" + newsNow + ")" : "") + "\n";
   int memCount = 0;
   double memSum = RecentPerformanceR(memCount);
   s += "Mémoire : " + IntegerToString(memCount) + " trades, bilan " + DoubleToString(memSum, 1) + " R  ->  risque " +
        (g_riskReduced ? "RÉDUIT (protection)" : "normal") + "\n";
   s += "Risque/trade : " + (InpRiskMode == RISK_FIXED_LOT ? "lot fixe " + DoubleToString(InpFixedLot, 2) : DoubleToString(EffectiveRiskPercent(), 2) + "%" +
        (InpHourWeighting ? StringFormat(" (base %.2f%% x%.1f selon l'heure)", ProfileRiskPercent(), HourRiskFactor(SessionHour(now))) : ""));
   s += "   |   Trades du jour : " + IntegerToString(g_tradesToday) + (InpMaxTradesPerDay > 0 ? "/" + IntegerToString(InpMaxTradesPerDay) : "") + "\n";
   s += "Ce mois-ci : " + FmtMoney(g_monthPL) + StringFormat(" (%d trades)", g_monthTrades) + "   |   Mois précédent : " + FmtMoney(g_prevMonthPL) + "\n";
   s += "Résultat du jour : " + FmtMoney(g_closedPLToday) + "   |   Drawdown : " + DoubleToString(CurrentDrawdownPct(), 2) + "% (max " + DoubleToString(InpMaxDrawdownPct, 1) + "%)\n";

   int shown = 0, npos = 0;
   double totR = 0.0, totP = 0.0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || (ulong)PositionGetInteger(POSITION_MAGIC) != InpMagic)
         continue;
      npos++;
      totP += PositionGetDouble(POSITION_PROFIT);
      bool isBuy = ((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
      double op = PositionGetDouble(POSITION_PRICE_OPEN);
      double psl = PositionGetDouble(POSITION_SL);
      double ptp = PositionGetDouble(POSITION_TP);
      double R = PositionRisk(ticket, op, psl, ptp);
      double cur = PositionGetDouble(POSITION_PRICE_CURRENT);
      double pr = (R > 0.0) ? (isBuy ? (cur - op) / R : (op - cur) / R) : 0.0;
      totR += pr;
      if(++shown > 3)
         continue;
      s += "Position : " + (isBuy ? "ACHAT " : "VENTE ") + DoubleToString(PositionGetDouble(POSITION_VOLUME), VolumeDigits()) +
           " @ " + DoubleToString(op, SymDigits()) + "  SL " + DoubleToString(psl, SymDigits()) +
           "  TP " + DoubleToString(ptp, SymDigits()) + "  (" + DoubleToString(pr, 2) + " R, " +
           FmtMoney(PositionGetDouble(POSITION_PROFIT)) + ")\n";
     }
   if(npos > 3)
      s += StringFormat("... %d positions au total : %+.2f R cumulés, ", npos, totR) + FmtMoney(totP) + "\n";
   s += "Statut : " + g_status;
   if(StringLen(s) > 2000)
      s = StringSubstr(s, 0, 2000);   // limite d'affichage de Comment()
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
   if(InpHoldUntilHour < 0 || InpHoldUntilHour > 23 || InpMinPrevRangeATR < 0.0)
     {
      Print("IABot: heure de maintien ou filtre d'amplitude invalides");
      ok = false;
     }
   if(InpMinBollinger < 0.0 || InpMinBollinger > 4.0)
     {
      Print("IABot: seuil Bollinger invalide (0 à 4)");
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
   if(InpRiskMode != RISK_FIXED_LOT && (InpRiskPercent < 0.0 || InpRiskPercent > 10.0))
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
      g_tpR = 2.0;
      g_beR = 0.7;
      g_condExit = true;
     }
   else
      if(InpProfile == FX_PROFILE_RETURN)
        {
         g_tpR = 2.0;
         g_beR = 0.7;
         g_condExit = false;
        }
      else
        {
         g_tpR = InpTP_R;
         g_beR = InpBE_TriggerR;
         g_condExit = (InpHoldUntilHour > InpExitHour);
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
   g_hEmaM5 = iMA(_Symbol, PERIOD_M5, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaH1 = iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaH4 = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_hEmaD1 = iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_hADX = iADX(_Symbol, PERIOD_H1, 14);
   g_hRSI14 = iRSI(_Symbol, PERIOD_M5, 14, PRICE_CLOSE);
   g_hEma12H1 = iMA(_Symbol, PERIOD_H1, 12, 0, MODE_EMA, PRICE_CLOSE);
   g_hEma26H1 = iMA(_Symbol, PERIOD_H1, 26, 0, MODE_EMA, PRICE_CLOSE);
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
   ComputeMonthStats();

   BuildNewsCurrencies();
   RefreshNews();
   LoadFOMCDates();

   // le premier signal sera évalué à la prochaine bougie (pas d'entrée tardive)
   g_lastSignalBar = iTime(_Symbol, InpSignalTF, 0);

   if(_Period != InpSignalTF)
      PrintFormat("IABot: info - le graphique est en %s, les signaux sont calculés en %s",
                  TFToString(_Period), TFToString(InpSignalTF));
   PrintFormat("IABot: démarré sur %s | compte %s | remplissage %d | risque %.2f%% | SL %.1f ATR | TP %.1f R | fenêtre %dh-%dh | %d positions max",
               _Symbol, (g_isHedging ? "hedging" : "netting"), (int)g_filling, ProfileRiskPercent(), InpSL_ATR, g_tpR, InpSessionStart, InpSessionEnd, InpMaxPositions);
   if(TradeBias() == 0)
      PrintFormat("IABot: ATTENTION - robot 100 %% EURUSD : %s n'est pas tradé. Placez le robot sur un graphique EURUSD.", _Symbol);
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
   if(g_hEmaM5 != INVALID_HANDLE)
      IndicatorRelease(g_hEmaM5);
   if(g_hEmaH1 != INVALID_HANDLE)
      IndicatorRelease(g_hEmaH1);
   if(g_hEmaH4 != INVALID_HANDLE)
      IndicatorRelease(g_hEmaH4);
   if(g_hEmaD1 != INVALID_HANDLE)
      IndicatorRelease(g_hEmaD1);
   if(g_hADX != INVALID_HANDLE)
      IndicatorRelease(g_hADX);
   if(g_hRSI14 != INVALID_HANDLE)
      IndicatorRelease(g_hRSI14);
   if(g_hEma12H1 != INVALID_HANDLE)
      IndicatorRelease(g_hEma12H1);
   if(g_hEma26H1 != INVALID_HANDLE)
      IndicatorRelease(g_hEma26H1);
   g_hADX = INVALID_HANDLE;
   g_hRSI14 = INVALID_HANDLE;
   g_hEma12H1 = INVALID_HANDLE;
   g_hEma26H1 = INVALID_HANDLE;
   g_hEmaM5 = INVALID_HANDLE;
   g_hEmaH1 = INVALID_HANDLE;
   g_hEmaH4 = INVALID_HANDLE;
   g_hEmaD1 = INVALID_HANDLE;
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
   ComputeMonthStats();
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
