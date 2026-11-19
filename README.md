# IABot EURUSD v9 : robot de trading autonome 100 % EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, qui travaille **uniquement sur EURUSD**. Il ne lit **aucune autre paire** :
un seul graphique et rien d'autre à configurer. Une fois lancé, il fait tout seul :

- il **analyse le marché en temps réel** :
  - tendances M5/H1/H4/D1, ADX, MACD, Bollinger, RSI, points pivots ;
  - volatilité, calendrier économique, prévision par heure ;
- il trade de **8 h à 15 h** (heure serveur), avec jusqu'à **10 positions par jour** ;
- **avant chaque trade, il vérifie 10 conditions** et les affiche à l'écran :
  - fenêtre horaire et calendrier (lundi, décision de la Fed, fin de mois) ;
  - amplitude de la veille, volatilité, annonces économiques, spread ;
  - rebond étiré : RSI(3) > 65 **et** prix à plus de 1,5 écart-type au-dessus de sa moyenne (Bollinger) ;
  - nombre de positions déjà ouvertes ;
- il **mise plus quand ses chances sont les meilleures** : ×1,5 à 8 h (l'heure la plus rentable), puis de moins en
  moins jusqu'à ×0,2 à 14 h ;
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

## 1. Ce qui a changé (v8 → v9) : le plus rentable des neuf

La v8 rapportait moins que la v7. Pour comprendre pourquoi, chaque réglage a été revérifié avec une méthode plus
stricte : il est appris sur **2007-2018 uniquement**, puis jugé sur **2019-2025 et 2026**, des données qu'il n'a
jamais vues.

- **Retiré.** Deux filtres de la v8 ne tenaient pas sur 2007-2018 : la « nuit asiatique » et le seuil de volatilité
  à 0,9. Ils marchaient par hasard sur la période récente. La v9 revient au cœur de la v7, plus robuste : stop à
  3 ATR, break-even à 0,7 R, volatilité ≤ 1,0.
- **Ajouté : la mise selon l'heure, apprise sur 2007-2018.** Sur 2007-2018, une entrée à 8 h rapportait 2 fois plus
  qu'à 9 h-11 h, et 5 fois plus qu'à 14 h. Le robot mise donc ×1,5 à 8 h, ×1 à 9 h, ×0,9 à 10 h, ×1 à 11 h, ×0,6 à
  12 h, ×0,4 à 13 h et ×0,2 à 14 h. Testé sur 2019-2025 et 2026, cela améliore le résultat.
- **Gardé de la v8.** Les **10 contrôles visibles avant chaque trade**.
- **Testé et rejeté.**
  - Plus de positions par jour (12 à 15), départ à 7 h, mise réduite après une série de pertes : à risque égal,
    tout cela rapporte moins.
  - Prendre aussi les signaux « moyens » avec une petite mise : sur données jamais vues, cela rapporte moins que de
    ne garder que les meilleurs.

**Comparaison des versions avec les réglages par défaut** (émulateur, mêmes données propres) :

| | v7 | v8 | **v9** |
|---|---:|---:|---:|
| 19 ans (2007-2025, 10 000 $) | +4 220 % | +3 379 % | **+7 358 %** |
| Votre période 2019-2025 (50 000 $) | +142 847 $ | +163 062 $ | **+177 327 $ (+355 %)** |
| 2026 (avr. → sept., jamais vu) | +2,2 % | +3,6 % | **+4,0 %** |
| % gagnants (19 ans) | 72,9 % | 76,7 % | 72,9 % |
| Drawdown max (19 ans) | 13,0 % | 13,3 % | 13,7 % |

Le drawdown reste au même niveau, donc la v9 ne prend pas plus de risque : elle gagne plus parce qu'elle mise au bon
moment. Elle est **1,7 fois plus rentable que la v7 sur 19 ans**, et meilleure que la v7 et la v8 sur chacune des trois
périodes.

## 2. Résultats v9 (réglages par défaut : risque de base 0,35 %)

| Données | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans, 10 000 $) | 11 895 | **72,9 %** | 1,37 | **+7 358 %** | 13,7 % |
| **Votre période 2019 → 2025** (50 000 $) | 5 012 | **73,7 %** | 1,35 | **+177 327 $** | 13,7 % |
| **2026** (avr. → sept., jamais utilisé pour régler le robot) | 245 | **73,1 %** | 1,21 | +4,0 % | 6,3 % |

**Les 19 années sont positives** (19 ans, départ 10 000 $, gains composés) :

| Année | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trades | 441 | 511 | 565 | 546 | 533 | 564 | 604 | 637 | 656 | 577 | 549 | 701 | 638 | 759 | 702 | 706 | 781 | 790 | 635 |
| % gagnants | 67 | 72 | 79 | 74 | 72 | 71 | 67 | 73 | 72 | 74 | 74 | 74 | 72 | 73 | 77 | 74 | 74 | 71 | 75 |

**Votre période (50 000 $) année par année :**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gain | +16 800 $ | +16 877 $ | +20 591 $ | +26 100 $ | +37 740 $ | +14 748 $ | +44 469 $ |

En moyenne, le robot gagne **+2 111 $ par mois** sur cette période. Environ **7 mois sur 10** sont positifs, et
**8 trimestres sur 10**.

**Selon le risque choisi** (19 ans, 10 000 $ au départ) :

| Risque de base par trade | Résultat 19 ans | Drawdown max |
|---|---:|---:|
| 0,30 % (prudent) | +3 940 % | 11,8 % |
| **0,35 % (défaut)** | **+7 358 %** | **13,7 %** |
| 0,40 % (agressif) | +13 459 % | 15,5 % |

- **Risque plus élevé.** Au-delà de 0,40 %, le drawdown approche du coupe-circuit de 20 %.
- **Frais.** Avec 0,3 pip de frais en plus sur chaque trade, le résultat sur 19 ans reste positif : +3 178 %, PF 1,32,
  drawdown 14,7 %.

Le détail est dans [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

## 3. Pourquoi pas plus d'heures ou plus de trades

Toutes les heures ont été testées dans les deux sens sur 19 ans de données MT5, à chaque version et avec les filtres
du moment :

- **8 h-15 h, vente** : positif sur toutes les périodes. C'est la fenêtre du robot.
- **Nuit et rollover (20 h-1 h)** : perdant dans les deux sens. Les spreads s'écartent et les prix « sautent ».
- **Asie, après-midi américain, achats** : des effets instables, qui changent de signe d'une période à l'autre.
- **Jours écartés** (lundi, Fed, fin de mois) : ni la vente ni l'achat n'y sont rentables.
- **Fixings BCE / Londres** : un effet documenté (Krohn et al.), mais perdant après le spread sur l'EURUSD.
- **Plus de positions par jour** : plus de trades, mais pas plus de gain à risque égal. Les positions d'une même
  journée sont liées : elles gagnent et perdent ensemble.

Ajouter ces heures ou ces trades ferait **perdre** de l'argent ou augmenterait le risque plus que le gain. Le robot
reste allumé 24 h/24 du lundi au vendredi : il surveille le marché et les annonces, gère ses positions et affiche la
prochaine fenêtre.

**Pour gagner plus**, le seul levier honnête est le **risque par trade** (tableau ci-dessus) : plus de gain veut
aussi dire plus de drawdown.

**Intelligence artificielle.** Des modèles d'apprentissage automatique (gradient boosting et régression logistique sur
26 indicateurs) ont été testés : leur pouvoir prédictif est trop faible (AUC 0,52 à 0,54). L'« intelligence » du robot
repose sur des règles apprises sur 2007-2018 et confirmées sur des données jamais vues.

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
| Mise | **0,35 %** de base par trade × **1,5 à 8 h**, 1 à 9 h, 0,9 à 10 h, 1 à 11 h, 0,6 à 12 h, 0,4 à 13 h, **0,2 à 14 h**. |

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
Contrôles avant trade (9/10) : fenêtre OK | calendrier OK | veille 11.0 OK | nuit Asie 1.9 OK | volatilité 0.59 OK | news OK | spread OK | RSI 66 OK | Bollinger -0.6 NON | positions OK
News : USD US CPI m/m à 2025.03.12 15:30
Mémoire : 60 trades, bilan 6.9 R  ->  risque normal
Risque/trade : 0.32% (base 0.35% x0.9 selon l'heure)   |   Trades du jour : 2/10
Résultat du jour : 0.00 USD   |   Drawdown : 0.65% (max 20.0%)
Position : VENTE 0.11 @ 1.09040  SL 1.09358  TP 1.08403  (0.20 R, 7.04 USD)
Position : VENTE 0.15 @ 1.09018  SL 1.09352  TP 1.08350  (0.13 R, 6.30 USD)
Statut : Rebond pas assez étiré : Bollinger -0.59 écart-type (seuil 1.50)
```
*(panneau réel produit par l'émulateur le 12/03/2025 à 10h40, compte de 10 000 $ ; la « nuit Asie » est affichée
pour information, ce n'est plus un filtre)*

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

- **Testeur MT5** : utilisez **EURUSD, M5**, avec « Chaque tick basé sur les ticks réels ».
- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot fait environ 650 trades par an.

**Si quelque chose ne fonctionne pas**, envoyez-moi :
- le message de l'onglet **Erreurs** de MetaEditor (compilation) ;
- ou les dernières lignes de l'onglet **Journal** du testeur ou du terminal.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Risque de base par trade (%) | 0,35 | 0,30 = prudent (drawdown 12 %) ; 0,40 = agressif (drawdown 15,5 %). |
| Mise pondérée selon l'heure | oui | ×1,5 à 8 h … ×0,2 à 14 h. |
| Positions simultanées / trades par jour | 10 / 10 | |
| Minutes entre deux entrées | 15 | |
| Fenêtre / sortie / maintien si perte | 8-15 h / 15 h / 17 h | Heure serveur. |
| Vente si RSI(3) > | 65 | |
| Seuil Bollinger (écarts-types) | 1,5 | 0 = désactivé. |
| Lundi / Fed / fin de mois | écartés | Chacun peut être réactivé. |
| Filtre du jour (amplitude veille ≥ x ATR) | 6,0 | 0 = désactivé. |
| Filtre de volatilité (ATR ≤ x moyenne) | 1,0 | 0 = désactivé. |
| Nuit asiatique minimale | 0 (désactivé) | Non retenu en v9 : sans effet sur 2007-2018. |
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

La recherche v9 se trouve dans `tools/research/v9_*.py`, avec la bibliothèque `v9lib.py` :
- poids appris sur 2007-2018 puis testés sur 2019-2026 ;
- mise modulée selon la qualité du signal (rejetée) ;
- autres pistes rejetées : RSI, take profit 3 R, risque adaptatif, nombre de positions, départ à 7 h.

```bash
tools/data/fetch_data.sh        # télécharge et prépare les données (EURUSD MT5 2007-2025, calendrier 2007-2025)
tools/verify/verify_all.sh      # compile le robot dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_MT5c.csv --symbol EURUSD --commission 0
```

## 10. Limites connues

- Avantage **réel mais modeste** : environ +0,10 R par trade. Il dépend des frais du courtier.
- **Pas tous les mois.** Environ 3 mois sur 10 sont négatifs. Une période défavorable de plusieurs mois reste
  possible : 2026 est plus faible que la moyenne.
- Le taux de réussite élevé vient de la sortie « dès que la position repasse en gain ». Les gains sont souvent petits
  et les pertes plus grosses : c'est l'ensemble qui est positif.
- Les positions d'une même journée sont liées : une mauvaise journée touche plusieurs positions à la fois.
- Le filtre news ne fonctionne pas dans le testeur MT5, mais les jours de Fed sont écartés grâce à la table intégrée.

## 11. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot (v9, 100 % EURUSD)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancien robot, non maintenu
MQL5/Experts/IABot/IABot_M5.mq5      ← ancien robot (or), non maintenu
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (v9_*.py : étude v9)
tools/data/                          ← téléchargement, nettoyage et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé de perte en
capital.*
