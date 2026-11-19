# IABot EURUSD v7 : robot de trading autonome 100 % EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, qui travaille **uniquement sur EURUSD**. Il ne lit **aucune autre paire** :
un seul graphique et rien d'autre à configurer. Une fois lancé, il fait tout seul :

- il **analyse le marché en temps réel** :
  - tendances M5/H1/H4/D1, ADX, MACD, Bollinger, RSI, points pivots ;
  - volatilité, calendrier économique, prévision par heure ;
- il trade de **8 h à 15 h** (heure serveur), avec jusqu'à **10 positions par jour** ;
- il ne prend que les **meilleurs rebonds** : RSI(3) > 65 **et** prix à plus de 1,5 écart-type au-dessus de sa
  moyenne (Bollinger) ;
- il **écarte les jours défavorables** : lundi, décision de la Fed, dernier jour du mois, veille trop calme,
  volatilité excessive ;
- il **met plus de risque le matin** (de 8 h à 11 h, les meilleures heures) et moins l'après-midi ;
- il pose **immédiatement le Stop Loss et le Take Profit**, puis passe au **break-even** ;
- il **sort en gain chaque fois que c'est possible** : environ **73 % de trades gagnants** ;
- il ne prend pas de position autour des **annonces économiques** (calendrier MT5 en direct) ;
- il protège le capital : perte journalière max, coupe-circuit, filtres de spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging** recommandé.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Les chiffres ci-dessous viennent du **vrai code du robot**, exécuté sur **19 ans de données MT5 réelles (EURUSD 2007-2025)**,
avec l'heure serveur exacte et le spread réel de chaque minute, puis sur 2026. Commencez **sur un compte démo**.

## 1. Ce qui a changé (v6 → v7)

- **Le « bug » de la v6.** La v6 lisait aussi GBPUSD, USDJPY et USDCHF pour mesurer la force des devises. Dans le
  testeur MT5, les cours de ces autres paires sont souvent « indisponibles » tant que leur historique n'est pas
  chargé. La v6 ignorait alors ses signaux : elle pouvait ne prendre presque aucun trade. **La v7 ne lit que
  l'EURUSD** : ce problème ne peut plus arriver.
- **Remplacement 100 % EURUSD.** Le meilleur substitut mesuré sur 19 ans est l'**étirement du rebond** (Bollinger).
  Plus le prix est monté au-dessus de sa moyenne 20, meilleure est la vente, et c'est vrai sur 2007-2012, 2013-2018
  et 2019-2025.
- **Risque pondéré par heure.** En moyenne, les entrées de 8 h rapportent +0,17 R, celles de 14 h +0,02 R. Le risque
  passe donc à ×1,5 de 8 h à 11 h et à ×0,5 après 13 h.
- **Stop à 3 ATR au lieu de 4.** Pour un même drawdown, cela donne environ 28 % de gain en plus.
- **Code simplifié.** Les fonctions multi-paires ont été retirées. Les seules nouveautés restent des fonctions MQL5
  standards.

| Votre période (2019-2025, 50 000 $, mêmes données) | v5 | v6 | **v7** |
|---|---:|---:|---:|
| Gain net | +32 695 $ | +81 082 $ | **+142 847 $ (+286 %)** |
| Trades | 2 118 | 7 044 | **5 017** |
| % gagnants | 73,7 % | 74,0 % | **73,7 %** |
| Profit factor | 1,22 | 1,35 | **1,33** |
| Drawdown max | 10,6 % | 13,2 % | **12,6 %** |
| Années positives | 5/7 | 7/7 | **7/7** |

À titre de repère, la v5 sur ces mêmes données donne +32 700 $, contre environ 35 000 $ dans votre testeur MT5 :
l'émulateur reproduit bien votre courtier.

## 2. Résultats v7 (réglages par défaut : risque de base 0,25 %)

| Données | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans, 10 000 $) | 11 904 | **72,9 %** | 1,35 | **+4 220 %** | 13,0 % |
| **Votre période 2019 → 2025** (50 000 $) | 5 017 | **73,7 %** | 1,33 | **+286 %** | 12,6 % |
| **2026** (avr. → sept., jamais utilisé pour régler le robot) | 247 | **73,3 %** | 1,12 | +2,2 % | 6,0 % |

**Les 19 années sont positives**, sans exception :

| Année | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trades | 441 | 512 | 565 | 546 | 533 | 564 | 604 | 637 | 656 | 577 | 550 | 702 | 638 | 759 | 702 | 709 | 782 | 792 | 635 |
| % gagnants | 67 | 72 | 79 | 74 | 72 | 71 | 67 | 73 | 72 | 74 | 74 | 74 | 72 | 73 | 77 | 74 | 74 | 71 | 75 |
| Résultat (R) | +17 | +47 | +92 | +76 | +79 | +95 | +49 | +66 | +64 | +30 | +61 | +112 | +75 | +53 | +72 | +76 | +76 | +40 | +56 |

**Selon le risque choisi** (19 ans, 10 000 $ au départ) :

| Risque de base par trade | Résultat 19 ans | Drawdown max | Votre période (50 000 $) |
|---|---:|---:|---:|
| 0,20 % (prudent) | +1 883 % | 10,4 % | - |
| **0,25 % (défaut)** | **+4 220 %** | **13,0 %** | **+142 847 $** (DD 12,6 %) |
| 0,30 % (agressif) | +8 720 % | 15,7 % | +195 586 $ (DD 15,0 %) |

- **Frais.** Avec 0,3 pip de frais en plus sur chaque trade, le résultat sur 19 ans reste positif : +1 970 %, PF 1,31,
  drawdown 13,3 %.
- **2026 plus faible.** L'avantage est plus faible en 2026 : +2,2 % sur 6 mois. Une période défavorable de plusieurs
  mois reste possible.

Le détail est dans [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

## 3. Pourquoi le robot ne trade pas 24 h/24

Toutes les heures ont été testées dans les deux sens sur 19 ans de données MT5, avec plus de 800 000 trades
candidats :

- **8 h-15 h, vente** : positif sur toutes les périodes. C'est la fenêtre du robot.
- **Nuit et rollover (20 h-1 h)** : perdant dans les deux sens. Les spreads s'écartent et les prix « sautent ».
- **Asie, après-midi américain, achats** : des effets instables, qui changent de signe d'une période à l'autre.
- **Effet des « fixings »** : un effet documenté (Krohn et al.), où le dollar monte avant les fixings de la BCE et
  de Londres puis se retourne. Testé à toutes les heures, il est **perdant après le spread** sur l'EURUSD : il n'est
  pas utilisé.

Le robot reste allumé 24 h/24 du lundi au vendredi : il surveille le marché et les annonces, gère ses positions et
affiche la prochaine fenêtre.

**Intelligence artificielle.** Des modèles d'apprentissage automatique (gradient boosting et régression logistique sur
26 indicateurs) ont été testés : leur pouvoir prédictif est trop faible (AUC 0,52 à 0,54). L'« intelligence » du robot
repose sur des indicateurs vérifiés période par période :
- étirement du rebond ;
- heure ;
- calendrier de la Fed ;
- fin de mois ;
- jour de la semaine ;
- volatilité.

## 4. Règles de trading

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Sens | **Vente** d'EURUSD (l'euro faiblit pendant la séance européenne : Ranaldo 2009, Breedon & Ranaldo 2013). |
| Filtre du jour | Amplitude de la veille ≥ **6 × ATR(14) H1**. Pas de trade le **lundi**, le jour d'une **décision de la Fed** ni le **dernier jour ouvré du mois**. |
| Filtre de volatilité | ATR(14) H1 ≤ sa moyenne sur 240 heures. |
| Fenêtre d'entrée | **8 h - 15 h, heure serveur GMT+2/+3**, du mardi au vendredi. |
| Signal | Rebond M5 étiré : **RSI(3) > 65** et clôture à plus de **1,5 écart-type** au-dessus de la moyenne 20 (Bollinger). |
| Fréquence | **10 positions par jour** au maximum, avec au moins **15 min** entre deux entrées. |
| Stop Loss | **3 × ATR(14) H1**. Cette distance définit « 1 R ». |
| Take Profit | **2 R**, posé à l'ouverture. |
| Break-even | À **+0,7 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | À **15 h** pour les positions en gain. Les positions en perte sont gardées et fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. |
| Risque | **0,25 %** de base par trade : **×1,5 de 8 h à 11 h**, ×1 de 11 h à 13 h, **×0,5 de 13 h à 15 h**. |

## 5. Ce que le robot affiche en temps réel

```
IABot EURUSD  |  EURUSD  |  compte hedging  |  magic 26111603
Biais : VENTE (euro faible en séance européenne)   |   RSI(3) M5 : 66.1
Fenêtre d'entrée 8h-15h : OUVERTE   |   Sortie 15h (si perte : jusqu'à 17h)   |   Spread : 11 pts
Tendances : M5 baisse | H1 hausse | H4 hausse | D1 hausse   |   séance : Europe
Volatilité : calme (x0.59, seuil 1.00 : OK)   |   prix à 30% du range du jour
Indicateurs : ADX H1 34 (tendance) | RSI14 M5 45 | MACD H1 +0.51 ATR (baisse) | Bollinger M5 -0.6 ET (seuil 1.5) | Pivot 1.08973 R1 1.09684 S1 1.08476
Filtre du jour : FAVORABLE - amplitude de la veille 11.0 x ATR (seuil 6.0)
Prévision : vente favorable - sur 19 ans, les entrées de 10h ont gagné 70% du temps (+0.089 R/trade)
News : USD US CPI m/m à 2025.03.12 15:30
Mémoire : 60 trades, bilan 6.9 R  ->  risque normal
Risque/trade : 0.38% (base 0.25% x1.5 selon l'heure)   |   Trades du jour : 2/10
Résultat du jour : 0.00 USD   |   Drawdown : 0.21% (max 20.0%)
Position : VENTE 0.11 @ 1.09040  SL 1.09358  TP 1.08403  (0.20 R, 7.04 USD)
Position : VENTE 0.11 @ 1.09018  SL 1.09352  TP 1.08350  (0.13 R, 4.62 USD)
Statut : Rebond pas assez étiré : Bollinger -0.59 écart-type (seuil 1.50)
```
*(panneau réel produit par l'émulateur le 12/03/2025 à 10h40, compte de 10 000 $)*

## 6. Protections du capital

- **Lot calculé sur la vraie perte au SL** (`OrderCalcProfit`), vérifié contre la marge libre.
- **Perte journalière max** (3 %) et **coupe-circuit drawdown** (20 % depuis le plus haut). Pour relancer le robot
  après un arrêt, passez « Réarmer le robot » à `true`.
- **Annonces économiques** (calendrier MT5, en réel) : pas d'entrée 30 min avant ou après une annonce à fort impact
  sur l'EUR ou l'USD. Les jours de décision de la Fed (2007-2026) sont intégrés au robot, donc ils sont aussi écartés
  dans le testeur.
- **Filtre de spread** : maximum 2 pips, et au plus 10 % du stop.
- **Sécurité SL** : un SL est toujours posé ; si c'est impossible, la position est fermée.
- **Compatibilité courtiers** :
  - modes de remplissage FOK/IOC/RETURN détectés automatiquement ;
  - nouvelles tentatives après un requote ;
  - stops level et freeze level respectés ;
  - en compte netting, une seule position à la fois.
- **Autre paire que l'EURUSD** : aucun trade, avec un message clair dans le journal.
- **Redémarrage sans risque** : l'état est sauvegardé dans les variables globales du terminal.

## 7. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**, puis copiez `IABot_EURUSD.mq5` dans
   `MQL5/Experts/IABot/`.
2. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7). Le résultat doit être
   « 0 errors ».
3. Ouvrez un graphique **EURUSD M5** et glissez **IABot_EURUSD** dessus.
4. Cochez **« Autoriser le trading algorithmique »**, puis activez le bouton **Algo Trading**.
5. Laissez le terminal allumé du lundi au vendredi : un **VPS** est fortement conseillé.

> **Heure du serveur.** Les horaires supposent un courtier en GMT+2 l'hiver et GMT+3 l'été, comme la plupart des
> courtiers MT5. Vérifiez : la bougie de minuit doit correspondre à la clôture de New York (23 h à Paris). Sinon, réglez :
> - « Référence horaire » = Heure GMT ;
> - fenêtre de **6 h à 13 h** ;
> - sortie à **13 h** ;
> - maintien jusqu'à **15 h**.

- **Testeur MT5** : utilisez **EURUSD, M5**, avec « Chaque tick basé sur les ticks réels ». Au démarrage, le journal
  affiche « IABot: démarré sur EURUSD … fenêtre 8h-15h | 10 positions max ».
- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot fait environ 650 trades par an.

**Si quelque chose ne fonctionne pas**, envoyez-moi :
- le message de l'onglet **Erreurs** de MetaEditor (compilation) ;
- ou les dernières lignes de l'onglet **Journal** du testeur ou du terminal.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Risque de base par trade (%) | 0,25 | 0,3 = plus agressif : +391 % au lieu de +286 % sur 2019-2025, drawdown 15 %. |
| Risque pondéré selon l'heure | oui | ×1,5 de 8 h à 11 h, ×0,5 après 13 h. |
| Positions simultanées / trades par jour | 10 / 10 | |
| Minutes entre deux entrées | 15 | |
| Fenêtre / sortie / maintien si perte | 8-15 h / 15 h / 17 h | Heure serveur. |
| Vente si RSI(3) > | 65 | |
| Seuil Bollinger (écarts-types) | 1,5 | 0 = désactivé. Plus haut = moins de trades, mais meilleurs. |
| Lundi / Fed / fin de mois | écartés | Chacun peut être réactivé. |
| Filtre du jour (amplitude veille ≥ x ATR) | 6,0 | 0 = désactivé. |
| Filtre de volatilité (ATR ≤ x moyenne) | 1,0 | 0 = désactivé. |
| SL / TP / break-even | 3 ATR / 2 R / 0,7 R | Profil « taux de réussite max ». |
| Fermer avant une news une position en perte | non | Coûtait 0,1 R par trade sur 2007-2025. |
| Perte journalière / drawdown max | 3 % / 20 % | Coupe-circuits. |

## 9. Vérification

Un **émulateur MQL5** (`tools/mql5emu/`) compile et exécute le fichier `.mq5` lui-même :
- compilation stricte, tout avertissement étant traité comme une erreur ;
- backtest tick par tick avec le spread réel de chaque minute.

Les **19 scénarios automatiques** sont décrits dans
[`tools/verify/last_report_eurusd.md`](tools/verify/last_report_eurusd.md) :
- SL et TP sur 100 % des trades, break-even exact, risque conforme ;
- entrées de 8 h à 15 h, 10 positions max, 15 min d'écart ;
- aucun trade sur une autre paire ;
- requotes, courtier IOC ou RETURN seulement, SL refusé, stops level élevé ;
- compte netting et petit capital ;
- perte journalière, coupe-circuit, filtre news ;
- redémarrage en pleine position ;
- AddressSanitizer et UBSan.

La recherche v7 se trouve dans `tools/research/v7_*.py`, avec la bibliothèque `v6lib.py`. La préparation des
données est dans `tools/data/` : `clean_m1.py` (nettoyage des artefacts du flux) et `convert_calendar.py`.

```bash
tools/data/fetch_data.sh        # télécharge et prépare les données (EURUSD MT5 2007-2025, calendrier 2007-2025)
tools/verify/verify_all.sh      # compile le robot dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_MT5c.csv --symbol EURUSD --commission 0
```

## 10. Limites connues

- Avantage **réel mais modeste** : environ +0,10 R par trade. Il dépend des frais du courtier.
- **2026 est plus faible** (+2 % sur 6 mois) : une période défavorable peut durer plusieurs mois.
- Le taux de réussite élevé vient de la sortie « dès que la position repasse en gain ». Les gains sont souvent petits
  et les pertes plus grosses : c'est l'ensemble qui est positif.
- Les positions d'une même journée sont corrélées : une mauvaise journée touche plusieurs positions à la fois.
- Le filtre news ne fonctionne pas dans le testeur MT5, mais les jours de Fed sont écartés grâce à la table intégrée.

## 11. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot (v7, 100 % EURUSD)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancien robot, non maintenu
MQL5/Experts/IABot/IABot_M5.mq5      ← ancien robot (or), non maintenu
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (v7_*.py : étude v7)
tools/data/                          ← téléchargement, nettoyage et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé de perte en
capital.*
