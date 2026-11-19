# IABot EURUSD v8 : robot de trading autonome 100 % EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, qui travaille **uniquement sur EURUSD**. Il ne lit **aucune autre paire** :
un seul graphique et rien d'autre à configurer. Une fois lancé, il fait tout seul :

- il **analyse le marché en temps réel** :
  - tendances M5/H1/H4/D1, ADX, MACD, Bollinger, RSI, points pivots ;
  - volatilité, calendrier économique, prévision par heure ;
- il trade de **8 h à 15 h** (heure serveur), avec jusqu'à **10 positions par jour** ;
- **avant chaque trade, il vérifie 10 conditions** et les affiche à l'écran :
  - fenêtre horaire et calendrier (lundi, décision de la Fed, fin de mois) ;
  - amplitude de la veille et de la nuit asiatique, volatilité ;
  - annonces économiques et spread ;
  - rebond étiré : RSI(3) > 65 **et** prix à plus de 1,5 écart-type au-dessus de sa moyenne (Bollinger) ;
  - nombre de positions déjà ouvertes ;
- il **met plus de risque le matin** (de 8 h à 11 h, les meilleures heures) et moins l'après-midi ;
- il pose **immédiatement le Stop Loss et le Take Profit**, puis passe au **break-even** ;
- il **sort en gain chaque fois que c'est possible** : environ **77 % de trades gagnants** ;
- il ne prend pas de position autour des **annonces économiques** (calendrier MT5 en direct) ;
- il protège le capital : perte journalière max, coupe-circuit, filtres de spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging** recommandé.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Les chiffres ci-dessous viennent du **vrai code du robot**, exécuté sur **19 ans de données MT5 réelles (EURUSD 2007-2025)**,
avec l'heure serveur exacte et le spread réel de chaque minute, puis sur 2026. Commencez **sur un compte démo**.

## 1. Ce qui a changé (v7 → v8)

Objectif : plus de trades gagnants, plus de régularité, sans perdre en gain. Chaque changement a été vérifié sur
2007-2012, 2013-2018 et 2019-2025, puis sur 2026.

- **Sortie retravaillée.** Après le test de 324 combinaisons, le robot pose un stop à **3,5 ATR** au lieu de 3, et le
  break-even passe à **+0,5 R** au lieu de +0,7. Les trades qui finissent au stop complet passent de 22,8 % à
  18,2 %.
- **Nuit asiatique.** Le robot ne vend pas quand la nuit asiatique (1 h-8 h) a été trop calme, soit moins de
  1,4 × l'ATR. Ces jours-là, la vente européenne ne rapporte presque rien, et c'est vrai sur les 3 périodes.
- **Volatilité.** Le seuil passe de 1,0 à 0,9 : le robot ne trade que quand le marché est calme. Les trades les
  plus agités ne rapportaient presque rien.
- **10 contrôles visibles avant chaque trade.** Le panneau affiche par exemple « Contrôles avant trade (9/10) :
  fenêtre OK | calendrier OK | veille 11.0 OK | nuit Asie 1.9 OK | volatilité 0.59 OK | news OK | spread OK |
  RSI 66 OK | Bollinger -0.6 NON | positions OK ».

| Votre période (2019-2025, 50 000 $, mêmes données) | v5 | v6 | v7 | **v8** |
|---|---:|---:|---:|---:|
| Gain net | +32 695 $ | +81 082 $ | +142 847 $ | **+163 062 $ (+326 %)** |
| % gagnants | 73,7 % | 74,0 % | 73,7 % | **77,4 %** |
| Profit factor | 1,22 | 1,35 | 1,33 | **1,49** |
| Drawdown max | 10,6 % | 13,2 % | 12,6 % | 12,7 % |
| Années positives | 5/7 | 7/7 | 7/7 | **7/7** |

**Régularité (19 ans) :**

| Périodes positives | v7 | **v8** |
|---|---:|---:|
| Jours tradés | 67 % | **73 %** |
| Semaines | 65 % | **69 %** |
| Mois | 68 % | 68 % |
| Trimestres | 82 % | 78 % |
| Trades perdus au stop complet | 22,8 % | **18,2 %** |

## 2. Résultats v8 (réglages par défaut : risque de base 0,3 %)

| Données | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans, 10 000 $) | 9 085 | **76,7 %** | 1,50 | **+3 379 %** | 13,3 % |
| **Votre période 2019 → 2025** (50 000 $) | 4 009 | **77,4 %** | 1,49 | **+326 %** | 12,7 % |
| **2026** (avr. → sept., jamais utilisé pour régler le robot) | 196 | **75,5 %** | 1,26 | +3,6 % | 4,9 % |

**Les 19 années sont positives** :

| Année | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Trades | 324 | 398 | 442 | 418 | 433 | 429 | 461 | 429 | 476 | 433 | 379 | 454 | 448 | 578 | 603 | 590 | 646 | 607 | 537 |
| % gagnants | 67 | 75 | 79 | 76 | 74 | 75 | 72 | 83 | 75 | 78 | 76 | 79 | 73 | 77 | 80 | 78 | 78 | 76 | 80 |
| Résultat (R) | +8 | +22 | +58 | +56 | +56 | +86 | +24 | +86 | +46 | +32 | +30 | +76 | +33 | +46 | +54 | +79 | +68 | +57 | +55 |

**Selon le risque choisi :**

| Risque de base par trade | Résultat 19 ans | Drawdown max | Votre période (50 000 $) |
|---|---:|---:|---:|
| 0,25 % (prudent) | +1 840 % | 11,1 % | +118 802 $ (DD 10,9 %) |
| **0,30 % (défaut)** | **+3 379 %** | **13,3 %** | **+163 062 $** (DD 12,7 %) |
| 0,35 % (agressif) | +6 068 % | 15,5 % | +212 663 $ (DD 14,8 %) |

- **Frais.** Avec 0,3 pip de frais en plus sur chaque trade, le résultat sur 19 ans reste positif : +1 918 %, PF 1,45,
  drawdown 13,5 %.
- **Comparaison avec la v7.** Sur 19 ans, la v8 gagne un peu moins que la v7 (+3 379 % contre +4 220 %), car elle
  trade moins. Mais elle gagne plus sur 2019-2025 et sur 2026, et résiste mieux aux frais.

Le détail est dans [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

## 3. Pourquoi le robot ne trade pas 24 h/24

Toutes les heures ont été testées dans les deux sens sur 19 ans de données MT5. La v8 a refait ce test avec les filtres
actuels (rebond étiré, volatilité, veille) :

- **8 h-15 h, vente** : positif sur toutes les périodes. C'est la fenêtre du robot.
- **Nuit et rollover (20 h-1 h)** : perdant dans les deux sens. Les spreads s'écartent et les prix « sautent ».
- **Asie, après-midi américain, achats** : des effets instables, qui changent de signe d'une période à l'autre.
- **Jours écartés** (lundi, Fed, fin de mois) : ni la vente ni l'achat n'y sont rentables.
- **Annonces économiques** (historique 2007-2025) :
  - les entrées autour d'une annonce restent rentables ;
  - fermer avant une annonce une position en perte coûtait 0,1 R par trade ;
  - le robot ne prend donc simplement pas de position 30 min avant ou après une annonce majeure.
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
| Filtre du jour | Amplitude de la veille ≥ **6 × ATR(14) H1**. **Nuit asiatique (1 h-8 h) ≥ 1,4 × ATR**. Pas de trade le **lundi**, le jour d'une **décision de la Fed** ni le **dernier jour ouvré du mois**. |
| Filtre de volatilité | ATR(14) H1 ≤ **0,9 ×** sa moyenne sur 240 heures. |
| Fenêtre d'entrée | **8 h - 15 h, heure serveur GMT+2/+3**, du mardi au vendredi. |
| Signal | Rebond M5 étiré : **RSI(3) > 65** et clôture à plus de **1,5 écart-type** au-dessus de la moyenne 20 (Bollinger). |
| Fréquence | **10 positions par jour** au maximum, avec au moins **15 min** entre deux entrées. |
| Stop Loss | **3,5 × ATR(14) H1**. Cette distance définit « 1 R ». |
| Take Profit | **2 R**, posé à l'ouverture. |
| Break-even | À **+0,5 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | À **15 h** pour les positions en gain. Les positions en perte sont gardées et fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. |
| Risque | **0,3 %** de base par trade : **×1,5 de 8 h à 11 h**, ×1 de 11 h à 13 h, **×0,5 de 13 h à 15 h**. |

## 5. Ce que le robot affiche en temps réel

```
IABot EURUSD  |  EURUSD  |  compte hedging  |  magic 26111603
Biais : VENTE (euro faible en séance européenne)   |   RSI(3) M5 : 66.1
Fenêtre d'entrée 8h-15h : OUVERTE   |   Sortie 15h (si perte : jusqu'à 17h)   |   Spread : 11 pts
Tendances : M5 baisse | H1 hausse | H4 hausse | D1 hausse   |   séance : Europe
Volatilité : calme (x0.59, seuil 0.90 : OK)   |   prix à 30% du range du jour
Indicateurs : ADX H1 34 (tendance) | RSI14 M5 45 | MACD H1 +0.51 ATR (baisse) | Bollinger M5 -0.6 ET (seuil 1.5) | Pivot 1.08973 R1 1.09684 S1 1.08476
Filtre du jour : FAVORABLE - amplitude de la veille 11.0 x ATR (seuil 6.0)
Prévision : vente favorable - sur 19 ans, les entrées de 10h ont gagné 75% du temps (+0.091 R/trade)
Contrôles avant trade (9/10) : fenêtre OK | calendrier OK | veille 11.0 OK | nuit Asie 1.9 OK | volatilité 0.59 OK | news OK | spread OK | RSI 66 OK | Bollinger -0.6 NON | positions OK
News : USD US CPI m/m à 2025.03.12 15:30
Mémoire : 52 trades, bilan 0.3 R  ->  risque normal
Risque/trade : 0.45% (base 0.30% x1.5 selon l'heure)   |   Trades du jour : 2/10
Résultat du jour : 0.00 USD   |   Drawdown : 0.22% (max 20.0%)
Position : VENTE 0.12 @ 1.09040  SL 1.09411  TP 1.08297  (0.17 R, 7.68 USD)
Position : VENTE 0.11 @ 1.09018  SL 1.09408  TP 1.08238  (0.11 R, 4.62 USD)
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
- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot fait environ 500 à 600 trades par an.

**Si quelque chose ne fonctionne pas**, envoyez-moi :
- le message de l'onglet **Erreurs** de MetaEditor (compilation) ;
- ou les dernières lignes de l'onglet **Journal** du testeur ou du terminal.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Risque de base par trade (%) | 0,3 | 0,35 = plus agressif : +425 % au lieu de +326 % sur 2019-2025, drawdown 15 %. |
| Risque pondéré selon l'heure | oui | ×1,5 de 8 h à 11 h, ×0,5 après 13 h. |
| Positions simultanées / trades par jour | 10 / 10 | |
| Minutes entre deux entrées | 15 | |
| Fenêtre / sortie / maintien si perte | 8-15 h / 15 h / 17 h | Heure serveur. |
| Vente si RSI(3) > | 65 | |
| Seuil Bollinger (écarts-types) | 1,5 | 0 = désactivé. Plus haut = moins de trades, mais meilleurs. |
| Nuit asiatique minimale (x ATR) | 1,4 | 0 = désactivé. |
| Lundi / Fed / fin de mois | écartés | Chacun peut être réactivé. |
| Filtre du jour (amplitude veille ≥ x ATR) | 6,0 | 0 = désactivé. |
| Filtre de volatilité (ATR ≤ x moyenne) | 0,9 | 0 = désactivé. |
| SL / TP / break-even | 3,5 ATR / 2 R / 0,5 R | Profil « taux de réussite max ». |
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

La recherche se trouve dans `tools/research/v7_*.py` et `v8_*.py`, avec la bibliothèque `v6lib.py`. La préparation des
données est dans `tools/data/` : `clean_m1.py` (nettoyage des artefacts du flux) et `convert_calendar.py`.

```bash
tools/data/fetch_data.sh        # télécharge et prépare les données (EURUSD MT5 2007-2025, calendrier 2007-2025)
tools/verify/verify_all.sh      # compile le robot dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_MT5c.csv --symbol EURUSD --commission 0
```

## 10. Limites connues

- Avantage **réel mais modeste** : environ +0,11 R par trade. Il dépend des frais du courtier.
- **2026 est plus faible** (+3,6 % sur 6 mois) : une période défavorable peut durer plusieurs mois.
- **Jours sans trade.** Le robot ne trade qu'environ 1 jour sur 2 : les autres jours ne réunissent pas les 10 conditions.
- Le taux de réussite élevé vient de la sortie « dès que la position repasse en gain ». Les gains sont souvent petits
  et les pertes plus grosses : c'est l'ensemble qui est positif.
- Les positions d'une même journée sont corrélées : une mauvaise journée touche plusieurs positions à la fois.
- Le filtre news ne fonctionne pas dans le testeur MT5, mais les jours de Fed sont écartés grâce à la table intégrée.

## 11. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot (v8, 100 % EURUSD)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancien robot, non maintenu
MQL5/Experts/IABot/IABot_M5.mq5      ← ancien robot (or), non maintenu
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (v8_*.py : étude v8)
tools/data/                          ← téléchargement, nettoyage et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé de perte en
capital.*
