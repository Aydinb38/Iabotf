# IABot EURUSD v5 : robot de trading autonome spécialisé EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, spécialisé sur **EURUSD**. Une fois lancé, il fait tout seul :

- il **analyse le marché en temps réel** : tendances M5/H1/H4/D1, volatilité, séance, position du
  prix, calendrier économique, et prévision statistique de l'heure en cours ;
- il juge **chaque jour** si les conditions sont favorables (filtres d'amplitude et de volatilité) ;
- il trade **de 11 h à 14 h** (heure serveur), avec jusqu'à **2 positions par jour** ;
- il pose **immédiatement le Stop Loss et le Take Profit**, puis passe au **break-even** ;
- il **sort en gain chaque fois que c'est possible** : environ **72 à 80 % de trades gagnants** ;
- il **ne trade pas pendant les annonces économiques**, et ferme une position gardée en perte juste
  avant une annonce ;
- il protège le capital : perte journalière max, coupe-circuit, filtres de spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging** recommandé.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Les chiffres ci-dessous viennent du **vrai code du robot**, exécuté sur **19 ans de données MT5
réelles (EURUSD 2007-2025)**, avec l'heure serveur exacte et le **spread réel de chaque minute**, puis
sur 2026. Commencez **sur un compte démo**.

## 1. Ce qu'a changé votre backtest MT5 (v4 → v5)

Votre backtest de la v4 (50 000 $, ticks réels) a confirmé le comportement du robot :
- **72,4 % de trades gagnants**, PF 1,15, +82,8 %, Sharpe 2,13 ;
- mais un **drawdown de 18,2 %**, tout près du coupe-circuit de 20 %, et 10 pertes consécutives.

En le reproduisant, nous avons trouvé et corrigé trois problèmes.

1. **Décalage horaire des anciennes données.** Les données HistData utilisées jusqu'ici étaient
   **décalées d'une heure en été** par rapport à l'heure serveur réelle d'un courtier MT5. Nous l'avons
   vérifié minute par minute : l'écart est de 0,2 pip avec un décalage d'une heure, contre 4,7 pips
   sans. Toute la recherche a donc été **refaite sur 19 ans de vraies données MT5**.
2. **Fenêtre mal calée.** À la bonne heure, les entrées de 10 h sont les plus faibles en période
   récente. La fenêtre devient **11 h-14 h**.
3. **Positions trop corrélées.** Les 3 positions d'une même séance parient sur le même mouvement :
   elles gagnent ensemble et perdent ensemble, ce qui gonfle le drawdown. Le robot en prend désormais
   **2 au maximum**. Il a aussi un **filtre de volatilité** : pas de trade si l'ATR horaire dépasse
   1,1 fois sa moyenne sur 10 jours. Sur 19 ans, cet indicateur est favorable 16 années sur 19.

| Sur votre période (2019-2025, 50 000 $, données MT5) | v4 | **v5** |
|---|---:|---:|
| Gain | +49,8 % | **+51,8 %** |
| Profit factor | 1,10 | **1,18** |
| % gagnants | 70,4 % | **73,3 %** |
| **Drawdown max** | **19,7 %** | **10,7 %** |
| Avec 0,3 pip de frais en plus | perdant | +37,6 % (DD 10,6 %) |

Sur 19 ans de données MT5, la v4 touchait le coupe-circuit de 20 % dès 2008. La v5 ne descend jamais
au-delà de 14,6 %.

## 2. Résultats v5 (10 000 $, risque 0,5 % par trade, réglages par défaut)

| Données | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans) | 4 510 | **72,2 %** | 1,20 | **+159 %** | 14,6 % |
| **2026** (avr. → sept.) | 118 | **79,7 %** | 1,84 | **+8,1 %** | 2,7 % |
| HistData 2005 → 2018 (contrôle) | 3 515 | 74,2 % | 1,24 | +156 % | 12,3 % |

**15 années positives sur 19.** Les années négatives sont 2007 (-885 $), 2018 (-443 $),
2019 (-543 $) et 2024 (-877 $). Le détail est dans
[`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

| Année | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| % gagnants | 58 | 67 | 76 | 73 | 72 | 70 | 69 | 79 | 80 | 75 | 81 | 67 | 68 | 69 | 77 | 78 | 76 | 69 | 77 | 80 |
| Résultat ($) | -885 | +357 | +984 | +571 | +1024 | +1357 | +1277 | +262 | +762 | +699 | +1178 | -443 | -543 | +44 | +1627 | +4127 | +1654 | -877 | +2705 | +811 |

## 3. Pourquoi le robot ne trade pas 24 h/24

Nous avons testé **864 861 trades candidats** sur les 19 ans de données MT5 : à toutes les heures,
dans les deux sens, avec les mêmes techniques que la stratégie principale.

- **Séance européenne (11 h-14 h), vente** : le seul créneau positif sur les trois périodes
  (2007-2012, 2013-2018 et 2019-2025) et en 2026.
- **Nuit (20 h-1 h)** : fortement **perdante dans les deux sens** (jusqu'à -0,2 R par trade). Au
  rollover, les spreads s'écartent et les prix « sautent », ce qui déclenche les stops, à l'achat comme
  à la vente.
- **Asie et après-midi américain** : de petits effets positifs sur certaines périodes, mais fortement
  perdants en 2026 (PF 0,45 à 0,55).
- **Plus de positions par jour** : plus de trades, mais pas plus d'avantage, car ce sont des paris
  sur le même mouvement. Le drawdown, lui, double.

Trader 24 h/24 ferait plus de trades **et ferait perdre de l'argent**. Le robot reste allumé 24 h/24
du lundi au vendredi : il surveille le marché et les annonces, gère ses positions et affiche l'heure de
la prochaine fenêtre.

**Intelligence artificielle.** Des modèles d'apprentissage automatique (gradient boosting et
régression logistique sur 26 indicateurs, réentraînés en continu) ont été testés pour prédire les
trades gagnants. Leur pouvoir prédictif est trop faible et trop instable (AUC 0,52 à 0,54) : ils ne
sont pas utilisés. Les règles du robot sont celles qui ont tenu sur 19 ans.

## 4. Règles de trading

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Sens | **Vente** d'EURUSD (l'euro faiblit pendant la séance européenne : Ranaldo 2009, Breedon & Ranaldo 2013). |
| Filtre du jour | Amplitude de la veille ≥ **6 × ATR(14) H1**. |
| Filtre de volatilité | ATR(14) H1 ≤ **1,1 ×** sa moyenne sur 240 heures (environ 10 jours). |
| Fenêtre d'entrée | **11 h - 14 h, heure serveur GMT+2/+3**, du lundi au vendredi. |
| Signal | Rebond court terme M5 : **RSI(3) > 65**. |
| Fréquence | **2 positions par jour** au maximum, avec au moins **1 h** entre les deux. |
| Stop Loss | **3 × ATR(14) H1**, soit environ 20 à 40 pips. Cette distance définit « 1 R ». |
| Take Profit | **3 R**, posé à l'ouverture. |
| Break-even | À **+1 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | À **15 h** pour les positions en gain. Les positions en perte sont gardées et fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. Elles sont fermées 10 min avant une annonce importante. |
| Risque | **0,5 %** du capital par trade. |

## 5. Ce que le robot affiche en temps réel

```
IABot EURUSD  |  EURUSD  |  compte hedging  |  magic 26111603
Biais : VENTE (euro faible en séance européenne)   |   RSI(3) M5 : 76.7
Fenêtre d'entrée 11h-14h : OUVERTE   |   Sortie 15h (si perte : jusqu'à 17h)   |   Spread : 3 pts
Tendances : M5 hausse | H1 hausse | H4 baisse | D1 baisse   |   séance : Europe
Volatilité : normale (x0.80, seuil 1.10 : OK)   |   prix à 76% du range du jour
Filtre du jour : FAVORABLE - amplitude de la veille 6.3 x ATR (seuil 6.0)
Prévision : vente favorable - sur 19 ans, les entrées de 11h ont gagné 71% du temps (+0.049 R/trade)
News : USD US CPI à 2026.06.10 15:30
Risque/trade : 0.50%   |   Trades du jour : 1/2
Position : VENTE 0.20 @ 1.16884  SL 1.17129  TP 1.16149  (0.02 R, 0.80 USD)
Statut : Position ouverte
```

En dehors de la fenêtre, le panneau affiche la prochaine fenêtre de trading. Pendant une annonce, il
affiche la pause.

## 6. Protections du capital

- **Lot calculé sur la vraie perte au SL** (`OrderCalcProfit`), vérifié contre la marge libre.
- **Perte journalière max** (3 %) et **coupe-circuit drawdown** (20 % depuis le plus haut). Après un
  arrêt, passez « Réarmer le robot » à `true` pour relancer.
- **Annonces économiques** (calendrier MT5, en réel) : pas d'entrée 30 min avant et après une annonce à
  fort impact sur l'EUR ou l'USD.
- **Filtre de spread** : maximum 2 pips, et au plus 10 % du stop.
- **Sécurité SL** : un SL est toujours posé ; si c'est impossible, la position est fermée.
- **Compatibilité courtiers** :
  - modes de remplissage FOK/IOC/RETURN détectés automatiquement ;
  - nouvelles tentatives après un requote ;
  - stops level et freeze level respectés ;
  - en compte netting, une seule position à la fois.
- **Redémarrage sans risque** : l'état des positions est sauvegardé dans les variables globales du
  terminal.

## 7. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**, puis copiez `IABot_EURUSD.mq5`
   dans `MQL5/Experts/IABot/`.
2. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
3. Ouvrez un graphique **EURUSD M5** et glissez **IABot_EURUSD** dessus.
4. Cochez **« Autoriser le trading algorithmique »**, puis activez le bouton **Algo Trading**.
5. Laissez le terminal allumé du lundi au vendredi : un **VPS** est fortement conseillé.

> **Heure du serveur.** Les horaires supposent un courtier en GMT+2 l'hiver et GMT+3 l'été, ce qui est
> le cas de la plupart des courtiers MT5. Vérifiez : la bougie de minuit doit correspondre à la clôture
> de New York (23 h à Paris). Sinon, réglez **« Référence horaire » = Heure GMT**, la fenêtre sur
> **9 h-12 h**, la sortie à **13 h** et le maintien jusqu'à **15 h**.

- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot est sensible aux
  frais.
- **Testeur MT5** : utilisez « Chaque tick basé sur les ticks réels ». Le calendrier économique n'y
  est pas disponible.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Profil de sortie | Taux de réussite max | Ou « Rendement maximal » (sortie à 15 h dans tous les cas, environ 55 % de gagnants). |
| Risque par trade (%) | 0,5 | Le drawdown évolue en proportion (14,6 % sur 19 ans à 0,5 %). |
| Positions simultanées / trades par jour | 2 / 2 | 3 ou plus : plus de trades, mais le drawdown double. |
| Fenêtre / sortie / maintien si perte | 11-14 h / 15 h / 17 h | Heure serveur. |
| Filtre du jour (amplitude veille ≥ x ATR) | 6,0 | 0 = désactivé. |
| Filtre de volatilité (ATR ≤ x moyenne) | 1,1 | 0 = désactivé. |
| Vente si RSI > | 65 | Niveau du rebond M5. |
| Perte journalière / drawdown max | 3 % / 20 % | Coupe-circuits. |
| Commission par lot | 0 | Indiquez votre commission aller-retour pour un calcul du lot exact. |

## 9. Vérification

Un **émulateur MQL5** (`tools/mql5emu/`) compile et exécute le fichier `.mq5` lui-même :
- compilation stricte, tout avertissement étant traité comme une erreur ;
- backtest tick par tick avec le spread réel de chaque minute.

Il reproduit votre backtest MT5 :

| 2019-2025 | Votre MT5 | Émulateur |
|---|---:|---:|
| Trades | 3 223 | 3 357 |
| % gagnants | 72,4 % | 70,4 % |
| Drawdown | 18,2 % | 19,7 % |

Les **19 scénarios automatiques** sont décrits dans
[`tools/verify/last_report_eurusd.md`](tools/verify/last_report_eurusd.md) :
- SL et TP sur 100 % des trades, break-even exact, risque ≤ 0,5 % ;
- entrées de 11 h à 14 h, fermeture au plus tard à 17 h, 2 positions max ;
- requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
- compte netting et petit capital ;
- perte journalière, coupe-circuit, filtre news, fermeture avant annonce ;
- redémarrage en pleine position ;
- AddressSanitizer et UBSan.

```bash
tools/data/fetch_data.sh        # télécharge les données (dont EURUSD MT5 2007-2025)
tools/verify/verify_all.sh      # compile les robots dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_MT5.csv --symbol EURUSD --commission 0 --trades trades.csv
```

## 10. Limites connues

- Avantage **réel mais modeste** : environ +0,045 R par trade. Des années négatives arrivent
  (4 sur 19), et la période récente (2019-2025) est plus difficile que 2009-2017.
- Très **sensible aux frais** du courtier.
- Le taux de réussite élevé vient de la sortie « dès que la position repasse en gain ». Les gains sont
  souvent petits, et les pertes plus grosses. C'est l'ensemble qui est positif.
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.

## 11. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot EURUSD (v5, version recommandée)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancienne version (EURUSD + GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD)
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (mt5_*.py : étude v5 sur données MT5)
tools/data/                          ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé
de perte en capital.*
