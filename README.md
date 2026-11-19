# IABot EURUSD v10 : robot de trading autonome 100 % EURUSD (MetaTrader 5, M5)

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
- il pose **immédiatement le Stop Loss et le Take Profit**, passe au **break-even**, puis **encaisse 70 % du gain dès
  +1 R** ;
- il **sort en gain chaque fois que c'est possible** : environ **73 % de trades gagnants** ;
- il ne prend pas de position autour des **annonces économiques** (calendrier MT5 en direct) ;
- il affiche le **gain du mois en cours et du mois précédent** ;
- il protège le capital : perte journalière max, coupe-circuit, filtres de spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging** recommandé.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Les chiffres ci-dessous viennent du **vrai code du robot**, exécuté sur **19 ans de données MT5 réelles (EURUSD 2007-2025)**,
avec l'heure serveur exacte et le spread réel de chaque minute, puis sur 2026. Commencez **sur un compte démo**.

## 1. Ce qui a changé (v9.1 → v10) : moins de pertes, plus de gain chaque mois

Point de départ : votre backtest MT5 de la v9.1.

| Votre rapport MT5 (v9.1) | Valeur |
|---|---:|
| Profit net (50 000 $ au départ) | +405 443 $ |
| Positions gagnantes | 74,6 % |
| Ratio de Sharpe | 3,97 |
| Drawdown | 11,5 % |
| Gain moyen par trade gagnant | +299 $ |
| Perte moyenne par trade perdant | -660 $ |

Les pertes étaient en moyenne **2 fois plus grosses que les gains**. Votre graphique MFE montrait aussi beaucoup de
trades d'abord gagnants qui finissaient en perte. Ces points ont été attaqués un par un, directement dans le vrai code
du robot (émulateur, 19 ans de données) :

| Essai | Résultat |
|---|---|
| **Encaisser 70 % de la position dès +1 R** | **Retenu.** Même gain, mais drawdown -10 %. Les trades déjà bien gagnants ne peuvent plus finir en perte. |
| Stop 3,5 ATR + break-even dès 0,5 R | 76 % de positions gagnantes, mais 2 fois moins de bénéfice : rejeté. |
| Supprimer les entrées de 14 h | Légèrement moins bon sur 19 ans (elles pèsent déjà 0,2) : gardées. |
| Fermer les positions en perte à 16 h au lieu de 17 h | Identique : 17 h est gardé. |
| Encaisser plus tôt (0,5 ou 0,7 R) ou moins (30 %) | Moins bon que 70 % à +1 R. |

Comme la clôture partielle réduit le drawdown, le robot peut **miser un peu plus pour le même risque** que la v9.1.
Le profil Équilibré passe de 0,35 % à 0,39 %.

**Même risque, plus de gain :**

| Drawdown max ≈ 13,5 % | v9.1 | **v10** |
|---|---:|---:|
| 19 ans (2007-2025, 10 000 $) | +7 358 % | **+11 853 %** |
| Votre période 2019-2025 (50 000 $) | +177 327 $ | **+224 833 $** |
| Gain mensuel moyen (2019-2025) | +2 111 $ | **+2 677 $** |
| 2026 (avr. → sept.) | +4,0 % | +3,3 % |

**Taux de réussite dans votre rapport MT5.** MT5 compte chaque fermeture comme un « trade ». Chaque encaissement de
70 % est un trade gagnant de plus, donc le pourcentage affiché par MT5 devrait monter vers **77-78 %**. Compté par
position, il reste d'environ 73-74 %.

## 1 bis. Recherche : tout ce qui a été essayé pour gagner plus (et pourquoi c'est rejeté)

Toutes ces idées ont été testées sur 19 ans, avec des réglages choisis sur 2007-2018 et jugés sur 2019-2025 et 2026 :

| Idée | Résultat |
|---|---|
| Ne plus ajouter de vente si les positions ouvertes perdent | **Moins bon.** Revendre plus haut quand le marché monte reste rentable : le retour à la moyenne finit par jouer. |
| Plus de positions par jour (15, 20), entrées plus rapprochées | Plus de trades, mais moins de gain à drawdown égal : les positions d'une même journée sont liées. |
| Vendre plus haut avec un ordre limite (+0,05 à +0,5 ATR) | **Moins bon.** Le robot rate les meilleurs trades, ceux qui repartent tout de suite à la baisse. |
| Prendre tout le gain plus tôt (TP 0,5 R à 1 R) | Jusqu'à 80 % de gagnants, mais 2 à 8 fois moins de bénéfice. |
| Cassure de la nuit asiatique, à l'achat ou à la vente | **Perdant** sur 19 ans (2 à 10 années positives sur 19 seulement). |
| Suivi de tendance journalier (Donchian 20/10) | **Perdant** depuis 2013 : l'EURUSD revient vers sa moyenne bien plus qu'il ne suit les tendances. |
| Filtres de régime (tendance journalière, hebdomadaire…) | Aucun ne se comporte de la même façon sur 2007-2018 et sur 2019-2025 : ce serait du hasard. |
| Filtres « nuit asiatique » et volatilité 0,9 (v8) | Sans effet sur 2007-2018 : retirés en v9. |
| Couper un trade qui perd plus de 0,3 à 0,7 R après 1 à 4 h | Perte moyenne plus petite (-0,6 R au lieu de -0,9 R), mais moins de trades gagnants (59 à 69 %) et moins de bénéfice : ces trades se rattrapent souvent. |
| Attendre une bougie de confirmation avant de vendre | Même taux de réussite, 30 à 80 % de trades en moins, nettement moins de bénéfice, négatif en 2026. |
| Petit compte : refuser le lot minimum quand il dépasse 1,5 fois la mise prévue | Légèrement moins bon (2 000 $ : +372 % au lieu de +377 %) : ces trades restent rentables. |
| Moduler la mise selon le jour, l'amplitude de la veille, le RSI ou les positions ouvertes | Les effets s'inversent entre 2007-2018 et 2019-2025 : ce serait du hasard. |
| Volatilité ≤ 0,9 au lieu de 1,0 | Drawdown 19 ans plus profond (16,4 % au lieu de 13,5 %) pour le même gain. |
| Deuxième trade l'après-midi (achat après une forte baisse du matin, vente après une forte hausse), 72 variantes | **Aucune** n'est positive sur les 3 périodes : rejeté. |
| Garder les positions en perte jusqu'au lendemain | 74,3 % de positions gagnantes au lieu de 72,8 %, mais même bénéfice, drawdown un peu plus profond, plus les frais de nuit et le risque d'écart de prix à la réouverture. |

**Les 4 profils v10** (votre période 2019-2025, 50 000 $ au départ, gains composés) :

| Profil (paramètre « Profil de risque ») | Mise de base | Gain mensuel moyen | Gain total 2019-2025 | Pire mois | Drawdown max |
|---|---:|---:|---:|---:|---:|
| Prudent | 0,33 % | +1 951 $ | +163 844 $ | -6 940 $ | 11,6 % |
| **Équilibré (défaut)** | 0,39 % | **+2 677 $** | **+224 833 $** | -10 301 $ | 13,5 % |
| Dynamique | 0,44 % | +3 358 $ | +282 073 $ | -13 756 $ | 15,3 % |
| Maximum | 0,50 % | +4 338 $ | +364 409 $ | -19 515 $ | 17,5 % |

- **Régularité.** Pour tous les profils, 7 mois sur 10 sont positifs. Le gain mensuel médian du profil Équilibré
  est de +3 156 $.
- **Pas de profil plus agressif.** Au-delà de 0,50 %, le drawdown approche le coupe-circuit de 20 %.

## 2. Résultats v10 (réglages par défaut : profil Équilibré)

| Données | Trades | **% gagnants** (par position) | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **MT5 réel 2007 → 2025** (19 ans, 10 000 $) | 11 873 | **72,9 %** | 1,36 | **+11 853 %** | 13,5 % |
| **Votre période 2019 → 2025** (50 000 $) | 4 995 | **73,7 %** | 1,34 | **+224 833 $** | 13,5 % |
| **2026** (avr. → sept., jamais utilisé pour régler le robot) | 245 | **73,1 %** | 1,15 | +3,3 % | 7,1 % |

**Les 19 années sont positives.** Sur votre période (50 000 $) :

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gain | +20 214 $ | +22 694 $ | +29 168 $ | +31 704 $ | +49 589 $ | +13 792 $ | +57 672 $ |

**Frais.** Avec 0,3 pip de frais en plus sur chaque trade, le résultat sur 19 ans reste positif : +4 471 %, PF 1,31,
drawdown 15 %.

Le détail est dans [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

## 2 ter. Votre backtest MT5 de la v10 (50 000 $)

| | v9.1 | **v10** |
|---|---:|---:|
| Profit net | +405 443 $ | **+414 137 $** |
| Drawdown maximal des fonds | 11,5 % | **9,4 %** |
| Positions gagnantes (MT5) | 74,6 % | **78,5 %** |
| Ratio de Sharpe | 3,97 | 3,83 |

**Choix du profil chez votre courtier.** Votre rapport indique un « drawdown relatif des fonds » de **16,8 %** en
profil Équilibré : c'est le pire recul mesuré par rapport au sommet du moment. Le profil Maximum (mise ×1,28)
dépasserait le coupe-circuit de 20 % et arrêterait le robot. Chez ce courtier :
- restez en **Équilibré**, ou au plus en **Dynamique** ;
- n'utilisez le profil Maximum qu'en remontant le paramètre « Drawdown max » à 25 %, en connaissance de cause.

## 2 bis. Le levier le plus concret : les frais du courtier

Le robot fait environ 650 trades par an, donc chaque dixième de pip compte. Résultats sur votre période (2019-2025,
50 000 $, profil Équilibré) selon le coût par trade (spread + commission) :

| Coût moyen par trade | Gain 2019-2025 | Profit factor | Drawdown max |
|---|---:|---:|---:|
| 0,3 pip (compte ECN très bon marché) | **+427 070 $** | 1,47 | 11,5 % |
| 0,6 pip (compte ECN courant) | **+335 291 $** | 1,41 | 11,2 % |
| 1,1 pip (spread réel des données de test) | +224 833 $ | 1,34 | 13,5 % |
| 1,2 pip | +205 309 $ | 1,32 | 14,0 % |
| 1,3 pip | +185 697 $ | 1,31 | 14,2 % |

**Choisir un compte ECN / « raw spread » à bas coût peut presque doubler le gain**, sans rien changer au robot.
Indiquez votre commission aller-retour par lot dans le paramètre « Commission par lot » pour que la taille des
positions tienne compte des frais.

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
| Take Profit | **2 R**, posé à l'ouverture. **70 % de la position sont encaissés à +1 R.** |
| Break-even | À **+0,7 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | À **15 h** pour les positions en gain. Les positions en perte sont gardées et fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. |
| Mise | **0,39 %** de base par trade (profil Équilibré) × **1,5 à 8 h**, 1 à 9 h, 0,9 à 10 h, 1 à 11 h, 0,6 à 12 h, 0,4 à 13 h, **0,2 à 14 h**. |

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
Mémoire : 60 trades, bilan 6.5 R  ->  risque normal
Risque/trade : 0.35% (base 0.39% x0.9 selon l'heure)   |   Trades du jour : 2/10
Ce mois-ci : 0.00 USD (2 trades)   |   Mois précédent : 148.35 USD
Résultat du jour : 0.00 USD   |   Drawdown : 0.74% (max 20.0%)
Position : VENTE 0.12 @ 1.09040  SL 1.09358  TP 1.08403  (0.20 R, 7.68 USD)
Position : VENTE 0.17 @ 1.09018  SL 1.09352  TP 1.08350  (0.13 R, 7.14 USD)
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

- **Profils prêts à l'emploi** : copiez les fichiers de [`MQL5/Presets/`](MQL5/Presets) dans le dossier `MQL5/Presets`
  de MetaTrader. Dans la fenêtre des paramètres du robot (ou du testeur), cliquez sur **Charger** et choisissez
  `IABot_EURUSD_Prudent`, `_Equilibre`, `_Dynamique` ou `_Maximum`.
- **Testeur MT5** : utilisez **EURUSD, M5**, avec « Chaque tick basé sur les ticks réels ».
- **Capital conseillé : 5 000 $ ou plus.** Le lot minimum est de 0,01. Avec moins, les mises ne peuvent pas suivre
  exactement la pondération horaire ni l'encaissement de 70 %. Sur 2019-2025, le gain passe de +450 % (50 000 $) à
  +377 % (2 000 $) et +319 % (1 000 $).
- **Lire le rapport MT5.**
  - MT5 compte chaque fermeture comme un trade, et chaque encaissement de 70 % est un petit trade gagnant. Le « gain
    moyen » affiché paraît donc bien plus petit que la « perte moyenne » : c'est normal. Le profit factor et la
    courbe de capital sont les bons repères.
  - Les entrées de 14 h ne misent que 0,2 fois la mise normale : leur résultat pèse très peu.
- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). Le robot fait environ 650 trades par an.

**Si quelque chose ne fonctionne pas**, envoyez-moi :
- le message de l'onglet **Erreurs** de MetaEditor (compilation) ;
- ou les dernières lignes de l'onglet **Journal** du testeur ou du terminal.

## 8. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Profil de risque | Équilibré (0,39 %) | Prudent 0,33 / Équilibré 0,39 / Dynamique 0,44 / Maximum 0,50 (voir tableau 1 bis). |
| Clôture partielle | oui, 70 % à +1 R | Encaisse la plus grande partie du gain. |
| Risque personnalisé (%) | 0 | Si > 0, remplace le profil. |
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
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot (v10, 100 % EURUSD)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancien robot, non maintenu
MQL5/Experts/IABot/IABot_M5.mq5      ← ancien robot (or), non maintenu
MQL5/Presets/IABot_EURUSD_*.set     ← réglages des 4 profils de risque (à charger dans MT5)
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (v9_*.py, v10_*.py : dernières études)
tools/data/                          ← téléchargement, nettoyage et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé de perte en
capital.*
