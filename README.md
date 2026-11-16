# IABot : robots de trading M5 pour MetaTrader 5

Deux Expert Advisors **entièrement automatiques** pour MetaTrader 5, en unité de temps **M5**. Chacun
analyse le marché, ouvre les positions, pose **immédiatement le Stop Loss et le Take Profit**, gère le
**break-even** et applique un ensemble complet de protections du capital.

| Robot | Marché | Fichier à installer |
|---|---|---|
| **IABot FX** | **Forex : EURUSD et GBPUSD** | [`MQL5/Experts/IABot/IABot_FX_M5.mq5`](MQL5/Experts/IABot/IABot_FX_M5.mq5) |
| **IABot Or** | Or : XAUUSD | [`MQL5/Experts/IABot/IABot_M5.mq5`](MQL5/Experts/IABot/IABot_M5.mq5) |

Les deux robots partagent le même moteur : calcul du lot, protections, exécution des ordres et
panneau d'information. Seule la stratégie d'entrée change.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Ceux-ci ne font pas exception.
Chaque chiffre de ce document vient d'un test réel sur des données historiques minute, **avec spread,
commission et swaps**, y compris les périodes perdantes. Les performances passées ne préjugent pas des
performances futures. Commencez **sur un compte démo**, puis en réel avec un petit risque
(0,5 % par trade maximum).

| Résumé des tests (10 000 $, risque 0,5 %/trade) | 2014-2017 (conception) | 2018 (jan-oct, jamais vue) | 2026 (avr-sep, jamais vue) |
|---|---|---|---|
| **IABot FX** sur EURUSD | **+31,1 %** · PF 1,19 · DD 6,0 % | **+7,2 %** · PF 1,25 · DD 4,3 % | **+1,9 %** · PF 1,14 · DD 3,3 % |
| **IABot FX** sur GBPUSD | **+21,0 %** · PF 1,11 · DD 10,9 % | **+7,6 %** · PF 1,22 · DD 4,2 % | **+1,6 %** · PF 1,13 · DD 3,4 % |
| **IABot FX** EURUSD + GBPUSD ensemble | **+52,1 %** · PF 1,15 · DD 9,2 % | **+14,7 %** · PF 1,24 · DD 6,7 % | **+3,4 %** · PF 1,13 · DD 5,6 % |
| **IABot Or** sur XAUUSD | **+48,5 %** · PF 1,30 · DD 7,2 % | **-12,1 %** · PF 0,64 · DD 13,2 % | **+6,2 %** · PF 1,41 · DD 4,7 % |

(PF = profit factor, c'est-à-dire gains bruts ÷ pertes brutes ; DD = baisse maximale du capital.)

---

## 1. IABot FX : le robot Forex

### Comment la stratégie a été trouvée

Nous avons testé **19 paires Forex** (majeures et croisées) sur 4 ans de données minute, avec des frais
réalistes qui augmentent la nuit. Les familles de stratégies testées :

- repli dans la tendance, retour à la moyenne (Bollinger, RSI), cassure du range asiatique ;
- cassure des plus hauts et plus bas de la veille, bougies d'impulsion ;
- tendance H4 et journalière, canaux de Donchian ;
- retour à la moyenne de nuit (« night scalping »).

**Aucune n'a d'avantage fiable une fois les frais payés.** En M5, les objectifs (2 à 5 pips) sont trop
petits face au spread et à la commission (1 à 3 pips).

Nous avons ensuite analysé **1 782 fenêtres horaires** sur toutes les paires. Un seul effet ressort,
stable chaque année et confirmé hors échantillon : **l'euro et la livre baissent face au dollar pendant
la séance européenne.** Ce phénomène est documenté dans la recherche académique (Ranaldo 2009 ;
Breedon & Ranaldo 2013) : une devise tend à se déprécier pendant les heures de bureau de sa propre place
financière. Le robot exploite cet effet, en entrant au meilleur moment grâce au M5.

### Règles

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Paires | **EURUSD** et **GBPUSD** en **vente uniquement** (mode automatique). |
| Fenêtre d'entrée | Entre **10 h et 13 h (heure serveur GMT+2/+3)**, c'est-à-dire en pleine séance européenne. |
| Entrée (M5) | Sur un **rebond court terme** : RSI(3) > 70, pour vendre plus haut. |
| Stop Loss | **3 × ATR(14) H1**, soit environ 20 à 40 pips selon la volatilité. Cette distance définit « 1 R ». |
| Take Profit | **3 R**, posé en même temps que le SL. |
| Break-even | À **+1 R**, le SL passe à l'entrée + 0,1 R. |
| Sortie forcée | À **15 h** si ni le SL ni le TP n'ont été touchés, juste avant les statistiques américaines (15 h 30). |
| Fréquence | **1 trade par jour et par paire** au maximum. Durée médiane : environ 4 h 30. Aucun swap à payer. |

### Résultats détaillés

| Paire | Période | Trades | % gagnants | PF | R moyen | Résultat | DD max |
|---|---|---:|---:|---:|---:|---:|---:|
| **EURUSD** | 2014-2017 | 1 005 | 53,0 % | 1,19 | +0,056 | **+31,1 %** | 6,0 % |
| **EURUSD** | 2018 | 192 | 56,2 % | 1,25 | +0,073 | **+7,2 %** | 4,3 % |
| **EURUSD** | 2026 | 109 | 52,3 % | 1,14 | +0,034 | **+1,9 %** | 3,3 % |
| **GBPUSD** | 2014-2017 | 1 004 | 53,1 % | 1,11 | +0,042 | **+21,0 %** | 10,9 % |
| **GBPUSD** | 2018 | 190 | 51,1 % | 1,22 | +0,079 | **+7,6 %** | 4,2 % |
| **GBPUSD** | 2026 | 108 | 53,7 % | 1,13 | +0,032 | **+1,6 %** | 3,4 % |

EURUSD est positif chaque année de 2014 à 2017 (+1 255 $, +1 076 $, +355 $, +425 $). Le même robot,
forcé sur d'autres paires, ne gagne pas : il est neutre ou perdant sur EURJPY, EURCAD, EURGBP, USDJPY,
USDCAD, AUDUSD et NZDUSD. C'est pourquoi le mode automatique ne trade **que EURUSD et GBPUSD**.
Toutes les lignes figurent dans [`results/backtest_results_fx.csv`](results/backtest_results_fx.csv).

**Lecture honnête.** C'est un avantage **petit mais régulier** : environ +0,05 R par trade et
53 % de trades gagnants, autour de 21 trades par mois et par paire. La plupart des trades sont fermés
par la sortie de 15 h (78 %). Le TP à 3 R est posé sur chaque trade mais rarement atteint (1 %). Le
résultat dépend fortement des frais. Avec 1,3 pip de frais au lieu de 1,0 sur EURUSD, le PF tombe
à 1,15 sur 2014-2017 et à 1,01 sur 2026. **Un compte ECN à bas coûts est indispensable.**

### Capital minimum

Un SL de 20 à 40 pips sur EURUSD vaut 2 à 4 $ pour 0,01 lot. Avec 0,5 % de risque, **environ 800 $
suffisent** pour un calcul de lot exact.

---

## 2. IABot Or : le robot XAUUSD

| Étape | Règle |
|---|---|
| Tendance (H1) | Achat seulement si clôture H1 > EMA 200 **et** EMA 50 > EMA 200. Vente : l'inverse. |
| Entrée (M5) | Repli court terme : **RSI(3) < 10** en tendance haussière (**> 90** en baissière). |
| Session | Entrées entre **9 h et 20 h (heure serveur)**. |
| Stop Loss / Take Profit | **3 × ATR(14) H1** / **4 R**. |
| Break-even / trailing | À **+0,8 R**, le SL passe à l'entrée + 0,1 R. À partir de **+2 R**, le SL suit le prix à 1,5 R de distance. |
| Week-end | Plus d'entrée le vendredi après 18 h, fermeture des positions le vendredi à 22 h. |

L'or gagne en marché directionnel (2014-2017, 2026) et **perd en range** (2018 : -12 %). Aux prix de
2026, 0,01 lot risque déjà 40 à 70 $ : il faut environ **12 000 $** pour risquer exactement 0,5 %, et au
moins 3 000 $ pour que le robot puisse trader. Détail dans
[`results/backtest_results.csv`](results/backtest_results.csv).

---

## 3. Protections communes aux deux robots

- **Risque fixe par trade** (0,5 % du solde par défaut). Le lot est calculé à partir de la vraie perte
  au SL (`OrderCalcProfit`), puis vérifié contre la marge libre et les limites de volume du courtier.
- **Perte journalière max** (3 %) : plus aucun trade jusqu'au lendemain.
- **Coupe-circuit drawdown** (15 % depuis le plus haut) : le robot ferme ses positions et s'arrête
  **définitivement**. Pour le relancer, passez le paramètre « Réarmer le robot » à `true`.
- **Choc de volatilité** : aucun trade si l'ATR actuel dépasse 3 fois sa moyenne (Brexit, décision
  surprise d'une banque centrale…).
- **Filtre news** : pause de 30 min avant et après chaque annonce à fort impact sur les devises du
  symbole, via le calendrier économique intégré à MT5. Il fonctionne en réel ; MT5 ne fournit pas le
  calendrier dans le testeur.
- **Filtre de spread** : le spread doit rester sous 10 % du SL, et sous 2 pips pour le Forex.
- **Sécurité SL** : si le courtier ignore le SL/TP à l'ouverture, le robot les pose aussitôt. S'il ne
  peut pas les poser, il **ferme la position**. Il ne laisse jamais une position sans stop.
- **Compatibilité courtiers** : comptes hedging et netting. Le mode de remplissage
  (FOK/IOC/RETURN) est détecté automatiquement. Le robot réessaie après un requote, respecte le stops
  level et le freeze level, et attend 30 s après un refus du serveur pour ne pas l'inonder de requêtes.
- **Redémarrage sans risque** : l'état de chaque position est sauvegardé dans les variables globales
  du terminal. Après un redémarrage du PC ou du VPS, le robot reprend la gestion de la position.
- **Panneau d'information** sur le graphique : biais ou tendance, RSI, fenêtre horaire, prochaine
  news, spread, résultat du jour, drawdown, position en cours en R, et ce que fait le robot.

## 4. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**.
2. Copiez `IABot_FX_M5.mq5` (et/ou `IABot_M5.mq5`) dans `MQL5/Experts/IABot/`.
3. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
   Le résultat attendu est `0 errors, 0 warnings`.
4. **Forex** : ouvrez un graphique **EURUSD M5**, glissez **IABot_FX_M5** dessus, puis faites de même
   sur un graphique **GBPUSD M5**. **Or** : un graphique **XAUUSD M5** avec **IABot_M5**.
   Chaque robot a son propre numéro magique, les deux peuvent donc tourner sur le même compte.
5. Dans l'onglet *Commun*, cochez **« Autoriser le trading algorithmique »**, puis activez le bouton
   **Algo Trading** dans la barre d'outils. Le panneau apparaît en haut à gauche.
6. Le terminal doit rester allumé : un **VPS** est fortement conseillé.

> **Heure du serveur.** Les horaires par défaut supposent un courtier en GMT+2 l'hiver et GMT+3
> l'été, ce qui est le cas de la grande majorité des courtiers MT5. Vérifiez sur votre graphique :
> la bougie de minuit doit correspondre à la clôture de New York (23 h à Paris). Si votre courtier est
> différent, réglez **« Référence horaire » = Heure GMT** avec, pour IABot FX, une fenêtre de 8 h à 11 h
> et une sortie à 13 h.

## 5. Paramètres principaux d'IABot FX

| Paramètre | Défaut | Rôle |
|---|---|---|
| Sens des trades | Automatique | Ventes sur EURUSD/GBPUSD. « Ventes uniquement » ou « Achats uniquement » forcent le sens sur d'autres paires, sans validation. |
| Risque par trade (%) | 0,5 | Perte maximale si le SL est touché. 1 % au grand maximum. |
| Fenêtre d'entrée | 10 h - 13 h | Heure serveur. |
| Heure de sortie forcée | 15 h | Avant les statistiques américaines. |
| Vente si RSI > | 70 | Niveau du rebond M5. |
| Stop loss = ATR x / Take profit = R x | 3,0 / 3,0 | SL et TP. |
| Break-even à +R / gain verrouillé | 1,0 / 0,1 | Sécurisation du trade. |
| Trades max par jour | 1 | Par paire. |
| Spread max | 20 points (2 pips) | Pas de trade si le spread est trop large. |
| Commission par lot | 0 | Indiquez la commission aller-retour de votre compte ECN (ex. 7) pour un calcul du lot exact. |

Le critère d'optimisation personnalisé (`OnTester`) récompense le profit factor, le nombre de trades
et un faible drawdown. Si vous optimisez, vérifiez toujours le résultat sur une autre période.

## 6. Comment les robots ont été vérifiés

MetaTrader ne fonctionne pas sous Linux. Nous avons donc construit un **émulateur MQL5**
(`tools/mql5emu/`) qui compile et exécute **les fichiers `.mq5` eux-mêmes**, et non une copie de la
stratégie :

1. **Contrôle de compatibilité MQL5** : il signale toute construction C++ invalide en MQL5, les
   structures passées par valeur, les initialisations de membres et les variables référence.
2. **Compilation stricte**, tout avertissement étant traité comme une erreur. Elle vérifie les
   signatures exactes de l'API MQL5, les conversions avec perte, les variables masquées, les
   comparaisons signé/non signé, la concaténation chaîne + nombre et l'écriture dans un paramètre
   d'entrée. Le contrôleur a lui-même été testé en injectant 10 erreurs typiques : toutes ont été
   détectées (8 à la compilation, 2 à l'exécution).
3. **Moteur de backtest tick par tick** qui reproduit MT5 :
   - indicateurs calculés avec les formules de MetaQuotes ;
   - stops level, freeze level, marge, swaps ;
   - historique des transactions, variables globales, calendrier.

   Il vérifie aussi à l'exécution les formats de `PrintFormat` et les accès hors tableau.
4. **18 scénarios automatiques par robot**, tous réussis (rapports :
   [`tools/verify/last_report_fx.md`](tools/verify/last_report_fx.md) et
   [`tools/verify/last_report.md`](tools/verify/last_report.md)) :
   - SL et TP sur 100 % des trades, avec un TP exact ;
   - break-even vérifié sur chaque déplacement ;
   - risque réel ≤ 0,5 %, horaires respectés, sortie de 15 h ;
   - requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
   - compte netting et petit capital ;
   - perte journalière, coupe-circuit drawdown et filtre news ;
   - redémarrage avec une position ouverte ;
   - exécution sous AddressSanitizer et UBSan sur toutes les données.
5. **Validation croisée** : le moteur de recherche (Python) et l'EA réel dans l'émulateur donnent les
   mêmes chiffres (EURUSD 2014-2017 : PF 1,19 dans les deux cas).

Défauts trouvés et corrigés grâce à ces tests :
- avec un stops level élevé, le robot envoyait des modifications refusées à chaque tick ;
- une durée maximale de trade coupait des trades gagnants sur l'or ;
- le jour du Brexit, le robot Forex (testé sur EURJPY) prenait position avec un SL de 633 pips :
  d'où l'ajout du filtre de choc de volatilité.

**Ce qui reste à faire de votre côté.** La compilation dans MetaEditor (F7) est la vérification
finale, impossible ici. Le code n'utilise que l'API standard MQL5, sans bibliothèque externe.
Lancez ensuite un test dans le **Testeur de stratégie MT5** avec les données de votre courtier
(EURUSD, M5, mode « Chaque tick basé sur les ticks réels »). Puis faites tourner le robot **au moins un
mois sur un compte démo** avant de passer en réel.

### Relancer la vérification soi-même (Linux, Python 3, g++)

```bash
tools/data/fetch_data.sh        # télécharge les données minute publiques dans data/m1
tools/verify/verify_all.sh      # compile les deux EA dans l'émulateur + 2 × 18 scénarios
build/fx/emu --data data/m1/EURUSD_IS.csv --symbol EURUSD --trades trades.csv   # backtest libre
build/fx/emu ... --set InpRiskPercent=1.0 --set InpExitHour=16                  # changer un paramètre
```

## 7. Limites connues

- **IABot FX** : avantage petit (environ +0,05 R par trade), très sensible aux frais. Un mois négatif
  est normal ; plusieurs mois négatifs de suite sont possibles.
- **IABot Or** : gagne seulement en marché directionnel, il faut s'attendre à des périodes perdantes
  de plusieurs mois (2018).
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.
- Les jours fériés où le marché ferme avant 22 h le vendredi, le robot Or peut garder une position
  pendant le week-end : 3 cas en 4 ans.

## 8. Structure du dépôt

```
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← robot Forex (EURUSD, GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD)
results/                             ← résultats détaillés par symbole et par période
tools/mql5emu/                       ← émulateur MQL5 (traducteur, API, moteur de backtest)
tools/verify/                        ← scénarios de vérification + derniers rapports
tools/research/                      ← recherche de stratégies (toutes les idées testées)
tools/data/                          ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque
élevé de perte en capital.*
