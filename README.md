# IABot EURUSD v6 : robot de trading autonome spécialisé EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, spécialisé sur **EURUSD**. Une fois lancé, il fait tout seul :

- il **analyse le marché en temps réel** :
  - tendances M5/H1/H4/D1, ADX, MACD, Bollinger, RSI, points pivots, volatilité ;
  - **force des 5 grandes devises** (EUR, USD, GBP, JPY, CHF), calendrier économique, prévision par heure ;
- il trade de **8 h à 15 h** (heure serveur), avec jusqu'à **10 positions par jour** ;
- il **écarte les jours défavorables** : lundi, jour de décision de la Fed, dernier jour du mois, veille trop calme,
  volatilité excessive, euro déjà trop faible ;
- il pose **immédiatement le Stop Loss et le Take Profit**, puis passe au **break-even** ;
- il **sort en gain chaque fois que c'est possible** : environ **74 % de trades gagnants** ;
- il **ne prend pas de position autour des annonces économiques** (calendrier MT5 en direct) ;
- il protège le capital : perte journalière max, coupe-circuit, filtres de spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging**. Les paires **GBPUSD, USDJPY et USDCHF** doivent exister chez le
> courtier (le robot les lit seul, aucun graphique à ouvrir).

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Les chiffres ci-dessous viennent du **vrai code du robot**, exécuté sur **19 ans de données MT5 réelles (EURUSD 2007-2025)**,
avec l'heure serveur exacte et le spread réel de chaque minute, puis sur 2026. Commencez **sur un compte démo**.

## 1. Ce qui a changé depuis votre backtest de la v5 (v5 → v6)

Votre backtest MT5 de la v5 rapportait environ 35 000 $ net, contre 41 000 $ pour la v4. Voici les 5 causes trouvées
et corrigées.

1. **Données corrompues.** La bougie de 15 h 00 des données 2018-2019 contenait souvent un pic de prix aberrant avec
   5 pips de spread. Ces pics gonflaient aussi l'ATR horaire. La v5 avait été réglée sur ces données : elle tradait
   trop peu. Après nettoyage, la v5 donne +65 % sur votre période dans l'émulateur, à comparer aux ≈ +70 % de votre
   testeur MT5. L'émulateur reproduit donc bien votre courtier.
2. **Fenêtre trop étroite.** Les entrées de 8 h à 11 h sont les **meilleures** (+0,08 à +0,11 R par trade). La fenêtre
   passe de 11 h-14 h à **8 h-15 h**.
3. **Trop peu de positions.** Avec des données propres, plus d'entrées par jour (jusqu'à **10**, espacées de 15 min)
   donnent plus de gain pour un même drawdown.
4. **Nouveaux filtres**, chacun vérifié sur les 3 périodes 2007-2012, 2013-2018 et 2019-2025 :
   - **lundi** : jour perdant 13 années sur 19 ;
   - **décision de la Fed (FOMC)** : le dollar faiblit avant l'annonce, ce qui pénalise la vente d'EURUSD ;
   - **dernier jour du mois** : flux de fin de mois ;
   - **force des devises** : on ne vend pas un euro qui a déjà nettement baissé dans la journée. Ce filtre est mesuré
     contre un panier EUR, USD, GBP, JPY et CHF.
5. **Défaut corrigé.** En réel, la v5 fermait une position gardée en perte 10 min avant une annonce. Avec l'historique
   du calendrier économique 2007-2025, cette règle faisait **perdre 0,1 R par trade** et faisait tomber le taux de
   réussite de 74 % à 66 %. Elle est désactivée. Le testeur MT5 n'ayant pas de calendrier, votre backtest ne le
   montrait pas, mais vos résultats en réel en auraient souffert.

Comparaison sur votre période, avec les mêmes données propres :

| Votre période (2019-2025, 50 000 $) | v4 | v5 | **v6** |
|---|---:|---:|---:|
| Gain net | coupe-circuit 20 % atteint | +32 695 $ (+65 %) | **+81 082 $ (+162 %)** |
| Trades | 981 (arrêt) | 2 118 | **7 044** |
| % gagnants | 67,9 % | 73,7 % | **74,0 %** |
| Profit factor | 0,99 | 1,22 | **1,35** |
| Drawdown max | 20,0 % | 10,6 % | 13,2 % |
| Années positives | - | 5/7 | **7/7** |

Avec un risque de 0,25 % par trade au lieu de 0,2 %, la v6 fait **+115 443 $ (+231 %)** sur la même période, avec un
drawdown de 16,4 %.

## 2. Résultats v6 (réglages par défaut, risque 0,2 % par trade)

| Données | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans, 10 000 $) | 16 908 | **73,8 %** | 1,39 | **+1 638 %** | 13,6 % |
| **Votre période 2019 → 2025** (50 000 $) | 7 044 | **74,0 %** | 1,35 | **+162 %** | 13,2 % |
| **2026** (avr. → sept., jamais utilisé pour régler le robot) | 380 | 69,5 % | 1,07 | +1,1 % | 6,8 % |

- **18 années positives sur 19.** Seule 2007 est négative (-313 $).
- **Frais.** Avec 0,3 pip de frais en plus sur chaque trade, le résultat sur 19 ans reste positif : PF 1,33, drawdown
  18,7 % à 0,25 % de risque.
- **Sans GBPUSD / USDJPY / USDCHF chez le courtier**, le robot divise automatiquement son risque par deux. Sur votre
  période, il fait alors +63 %, avec un drawdown de 9 %.

| Année | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trades | 594 | 710 | 821 | 745 | 744 | 838 | 899 | 909 | 895 | 877 | 820 | 1012 | 898 | 1098 | 981 | 1054 | 1083 | 1026 | 904 |
| % gagnants | 64 | 72 | 78 | 75 | 78 | 67 | 72 | 76 | 75 | 75 | 77 | 72 | 72 | 72 | 77 | 74 | 79 | 72 | 72 |
| Résultat (R) | -16 | +66 | +97 | +90 | +142 | +37 | +100 | +168 | +106 | +61 | +99 | +108 | +64 | +36 | +48 | +97 | +131 | +84 | +47 |

**2026 est plus faible.** Sur les 6 premiers mois, le robot n'a que légèrement gagné. Sur 19 ans, 7 % des périodes de
6 mois ont été aussi mauvaises ou pires : c'est donc dans la variation normale. Mais cela rappelle que l'avantage
n'est pas garanti. Le détail est dans [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

## 3. Pourquoi le robot ne trade pas 24 h/24

Toutes les heures ont été testées dans les deux sens sur 19 ans de données MT5 (plus de 800 000 trades candidats) :

- **8 h-15 h, vente** : positif sur les 3 périodes. C'est la fenêtre du robot, élargie de 3 h à 7 h dans la v6.
- **Nuit et rollover (20 h-1 h)** : perdant dans les deux sens. Les spreads s'écartent et les prix « sautent ».
- **Asie, après-midi américain, achats** : de petits effets instables, qui changent de signe d'une période à l'autre.

Le robot reste allumé 24 h/24 du lundi au vendredi : il surveille le marché et les annonces, gère ses positions et
affiche la prochaine fenêtre.

**Intelligence artificielle.** Des modèles d'apprentissage automatique (gradient boosting et régression logistique sur
26 indicateurs) ont été testés : leur pouvoir prédictif est trop faible (AUC 0,52 à 0,54). L'« intelligence » de la v6
repose sur des indicateurs vérifiés période par période :
- force des devises ;
- calendrier de la Fed ;
- fin de mois ;
- jour de la semaine ;
- volatilité.

## 4. Règles de trading

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Sens | **Vente** d'EURUSD (l'euro faiblit pendant la séance européenne : Ranaldo 2009, Breedon & Ranaldo 2013). |
| Filtre du jour | Amplitude de la veille ≥ **6 × ATR(14) H1**. Pas de trade le **lundi**, le jour d'une **décision de la Fed** ni le **dernier jour ouvré du mois**. |
| Filtre de volatilité | ATR(14) H1 ≤ **1,1 ×** sa moyenne sur 240 heures. |
| Fenêtre d'entrée | **8 h - 15 h, heure serveur GMT+2/+3**, du mardi au vendredi. |
| Signal | Rebond court terme M5 : **RSI(3) > 65**. |
| Force des devises | Pas de vente si la force de l'euro du jour est **< -0,5 ATR**. Elle est calculée sur GBPUSD, USDJPY et USDCHF. |
| Fréquence | **10 positions par jour** au maximum, avec au moins **15 min** entre deux entrées. |
| Stop Loss | **4 × ATR(14) H1**. Cette distance définit « 1 R ». |
| Take Profit | **2 R**, posé à l'ouverture. |
| Break-even | À **+0,7 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | À **15 h** pour les positions en gain. Les positions en perte sont gardées et fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. |
| Risque | **0,2 %** du capital par trade. Avec 10 positions au maximum, l'exposition maximale est de 2 %. |

## 5. Ce que le robot affiche en temps réel

```
IABot EURUSD  |  EURUSD  |  compte hedging  |  magic 26111603
Biais : VENTE (euro faible en séance européenne)   |   RSI(3) M5 : 70.0
Fenêtre d'entrée 8h-15h : OUVERTE   |   Sortie 15h (si perte : jusqu'à 17h)   |   Spread : 12 pts
Tendances : M5 hausse | H1 hausse | H4 hausse | D1 hausse   |   séance : Europe
Volatilité : calme (x0.61, seuil 1.10 : OK)   |   prix à 68% du range du jour
Indicateurs : ADX H1 34 (tendance) | RSI14 M5 59 | MACD H1 +0.44 ATR (baisse) | Bollinger M5 +1.7 σ | Pivot 1.08973 R1 1.09684 S1 1.08476
Force des devises (jour) : CHF +2.8 > USD +1.0 > EUR -0.2 > GBP -0.3 > JPY -3.3  (euro OK pour vendre)
Filtre du jour : FAVORABLE - amplitude de la veille 10.6 x ATR (seuil 6.0)
Prévision : vente favorable - sur 19 ans, les entrées de 11h ont gagné 76% du temps (+0.061 R/trade)
News : USD US CPI m/m à 2025.03.12 15:30
Mémoire : 60 trades, bilan 13.9 R  ->  risque normal
Risque/trade : 0.20%   |   Trades du jour : 6/10
Résultat du jour : 0.00 USD   |   Drawdown : 1.37% (max 20.0%)
Position : VENTE 0.04 @ 1.09045  SL 1.09499  TP 1.08138  (-0.11 R, -2.00 USD)
Position : VENTE 0.04 @ 1.09011  SL 1.09465  TP 1.08104  (-0.19 R, -3.36 USD)
Position : VENTE 0.04 @ 1.08993  SL 1.09433  TP 1.08113  (-0.23 R, -4.08 USD)
... 6 positions au total : -0.94 R cumulés, -16.72 USD
Statut : Position ouverte
```
*(panneau réel produit par l'émulateur le 12/03/2025 à 11h20, compte de 10 000 $)*

## 6. Protections du capital

- **Lot calculé sur la vraie perte au SL** (`OrderCalcProfit`), vérifié contre la marge libre.
- **Perte journalière max** (3 %) et **coupe-circuit drawdown** (20 % depuis le plus haut). Pour relancer le robot
  après un arrêt, passez « Réarmer le robot » à `true`.
- **Annonces économiques** (calendrier MT5, en réel) : pas d'entrée 30 min avant ou après une annonce à fort impact
  sur l'EUR ou l'USD. Les jours de décision de la Fed sont connus à l'avance (2007-2026), donc ils sont aussi écartés
  dans le testeur.
- **Données manquantes** :
  - si GBPUSD, USDJPY ou USDCHF manquent chez le courtier, le risque est divisé par deux et le panneau l'indique ;
  - si leurs prix sont momentanément indisponibles, le trade est ignoré.
- **Filtre de spread** : maximum 2 pips, et au plus 7,5 % du stop.
- **Sécurité SL** : un SL est toujours posé ; si c'est impossible, la position est fermée.
- **Compatibilité courtiers** :
  - modes de remplissage FOK/IOC/RETURN détectés automatiquement ;
  - nouvelles tentatives après un requote ;
  - stops level et freeze level respectés ;
  - suffixes de symboles gérés (par exemple EURUSD.m utilise GBPUSD.m) ;
  - en compte netting, une seule position à la fois.
- **Redémarrage sans risque** : l'état est sauvegardé dans les variables globales du terminal.

## 7. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**, puis copiez `IABot_EURUSD.mq5` dans
   `MQL5/Experts/IABot/`.
2. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
3. Ouvrez un graphique **EURUSD M5** et glissez **IABot_EURUSD** dessus.
4. Cochez **« Autoriser le trading algorithmique »**, puis activez le bouton **Algo Trading**.
5. Laissez le terminal allumé du lundi au vendredi : un **VPS** est fortement conseillé.

> **Heure du serveur.** Les horaires supposent un courtier en GMT+2 l'hiver et GMT+3 l'été, comme la plupart des
> courtiers MT5. Vérifiez : la bougie de minuit doit correspondre à la clôture de New York (23 h à Paris). Sinon, réglez :
> - « Référence horaire » = Heure GMT ;
> - fenêtre de **6 h à 13 h** ;
> - sortie à **13 h** ;
> - maintien jusqu'à **15 h**.

- **Testeur MT5** : utilisez « Chaque tick basé sur les ticks réels », sur EURUSD M5. MT5 charge automatiquement
  l'historique de GBPUSD, USDJPY et USDCHF. Au démarrage, le journal doit afficher « force des devises calculée avec
  GBPUSD, USDJPY, USDCHF ».
- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot fait environ 900 trades par an, il
  est donc sensible aux frais.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Risque par trade (%) | 0,2 | 0,25 = plus agressif : +231 % au lieu de +162 % sur 2019-2025, drawdown 16 % au lieu de 13 %. |
| Positions simultanées / trades par jour | 10 / 10 | Moins de positions = moins de trades. |
| Minutes entre deux entrées | 15 | |
| Fenêtre / sortie / maintien si perte | 8-15 h / 15 h / 17 h | Heure serveur. |
| Lundi / Fed / fin de mois | écartés | Chacun peut être réactivé. |
| Filtre de force des devises | activé, -0,5 ATR | Le filtre qui réduit le plus le drawdown. |
| Filtre du jour (amplitude veille ≥ x ATR) | 6,0 | 0 = désactivé. |
| Filtre de volatilité (ATR ≤ x moyenne) | 1,1 | 0 = désactivé. |
| SL / TP / break-even | 4 ATR / 2 R / 0,7 R | Profil « taux de réussite max ». |
| Fermer avant une news une position en perte | non | Coûtait 0,1 R par trade sur 2007-2025. |
| Perte journalière / drawdown max | 3 % / 20 % | Coupe-circuits. |

## 9. Vérification

Un **émulateur MQL5** (`tools/mql5emu/`) compile et exécute le fichier `.mq5` lui-même :
- compilation stricte, tout avertissement étant traité comme une erreur ;
- backtest tick par tick avec le spread réel de chaque minute ;
- lecture des autres paires (GBPUSD, USDJPY, USDCHF) sans voir le futur.

Les **19 scénarios automatiques** sont décrits dans
[`tools/verify/last_report_eurusd.md`](tools/verify/last_report_eurusd.md) :
- SL et TP sur 100 % des trades, break-even exact, risque ≤ 0,2 % ;
- entrées de 8 h à 15 h, 10 positions max, 15 min d'écart ;
- requotes, courtier IOC ou RETURN seulement, SL refusé, stops level élevé ;
- compte netting et petit capital ;
- perte journalière, coupe-circuit, filtre news ;
- redémarrage en pleine position ;
- AddressSanitizer et UBSan.

La recherche v6 se trouve dans `tools/research/v6_*.py`, avec la bibliothèque `v6lib.py`. Les données sont dans
`tools/data/` : `clean_m1.py` (nettoyage), `convert_calendar.py` (calendrier en heure serveur) et `build_majors.py`.

```bash
tools/data/fetch_data.sh        # télécharge et prépare les données (EURUSD + croisements MT5, calendrier 2007-2025)
tools/verify/verify_all.sh      # compile les robots dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_MT5c.csv --symbol EURUSD --commission 0 \
  --aux GBPUSD=data/m1/GBPUSD_MT5c.csv --aux USDJPY=data/m1/USDJPY_MT5c.csv --aux USDCHF=data/m1/USDCHF_MT5c.csv
```

## 10. Limites connues

- Avantage **réel mais modeste** : environ +0,09 R par trade. Il dépend des frais (environ 900 trades par an).
- **2026 est plus faible** (+1 % sur 6 mois) : une période défavorable peut durer plusieurs mois.
- Le taux de réussite élevé vient de la sortie « dès que la position repasse en gain ». Les gains sont souvent petits
  et les pertes plus grosses : c'est l'ensemble qui est positif.
- Les positions d'une même journée sont corrélées : une mauvaise journée touche plusieurs positions à la fois. C'est
  pourquoi le risque est de 0,2 % par trade.
- Le filtre news ne fonctionne pas dans le testeur MT5, mais les jours de Fed sont écartés grâce à la table intégrée.

## 11. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot EURUSD (v6, version recommandée)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancienne version (EURUSD + GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD)
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5 (multi-symboles)
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (v6_*.py : étude v6)
tools/data/                          ← téléchargement, nettoyage et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé de perte en
capital.*
