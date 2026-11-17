# IABot EURUSD v3 : robot de trading autonome spécialisé EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, spécialisé sur une seule paire : **EURUSD**. Une fois lancé,
il fait tout seul :

- il juge **chaque jour** si les conditions sont favorables ;
- il prend **jusqu'à 3 trades par jour** et pose **immédiatement le Stop Loss et le Take Profit** ;
- il déplace le stop au **break-even** ;
- il sort **en gain chaque fois que c'est possible** (taux de réussite d'environ **72 %**) ;
- il protège le capital avec des limites journalières, un coupe-circuit et des filtres de news, de
  spread et de volatilité.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_EURUSD.mq5`](MQL5/Experts/IABot/IABot_EURUSD.mq5)
> Graphique : **EURUSD, M5**. Compte **hedging** recommandé.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Tous les chiffres ci-dessous viennent du **vrai code du robot**, exécuté minute par minute sur
**14 ans de données réelles d'EURUSD (2005-2018)** puis sur 2026, avec spread, commission et swaps.
Les performances passées ne préjugent pas des performances futures. Commencez **sur un compte démo**.

### Résultats v3 (10 000 $ au départ, risque 0,5 % par trade, réglages par défaut)

| Période | Trades | **% gagnants** | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|
| **2005 → 2018** (14 ans) | 4 745 | **71,6 %** | 1,20 | **+296 %** (10 000 $ → 39 588 $) | 13,7 % |
| **2026** (avr. → sept.) | 169 | **74,0 %** | 1,41 | **+7,8 %** | 4,9 % |

Sur 2005-2018, cela fait environ **+10,6 % par an** en moyenne (composé). **13 années positives sur 14** :
seule 2016 est à -85 $, soit -0,3 %. Le détail année par année est dans
[`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

| Année | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018* | 2026* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| % gagnants | 79 | 78 | 72 | 71 | 78 | 68 | 71 | 68 | 67 | 75 | 70 | 68 | 73 | 67 | 74 |
| Résultat ($) | +1 877 | +1 877 | +1 540 | +1 672 | +1 877 | +648 | +1 927 | +3 437 | +378 | +7 874 | +2 786 | -85 | +2 565 | +1 215 | +776 |

\* 2018 : janvier-août ; 2026 : avril-septembre. Les gains en dollars augmentent avec les années, car
le capital grossit et le robot risque toujours 0,5 % du solde.

### Progression entre versions (même période 2005-2018)

| Version | % gagnants | Résultat 14 ans | DD max | Années + | 2026 |
|---|---:|---:|---:|---:|---:|
| v2 | 53,9 % | +158 % | 13,9 % | 13/14 | +1,1 % |
| **v3 « taux de réussite »** (défaut) | **71,6 %** | **+296 %** | 13,7 % | 13/14 | **+7,8 %** |
| v3 « rendement » | 55,0 % | +273 % | **11,6 %** | **14/14** | **+9,1 %** |

---

## 1. Ce que le robot a appris d'EURUSD

### L'effet exploité

**L'euro baisse face au dollar pendant la séance européenne.** C'est un effet documenté par la
recherche académique (Ranaldo 2009 ; Breedon & Ranaldo 2013) : une devise tend à se déprécier pendant
les heures de bureau de sa propre place financière. Nous l'avons vérifié sur 14 ans.

### Les trois améliorations de la v3

Elles ont été trouvées en analysant **47 322 trades candidats** sur 14 ans :

1. **Filtre de qualité journalier.** Le robot ne trade que si **l'amplitude de la veille dépasse
   6 fois l'ATR horaire actuel**. Explication : la baisse de l'euro pendant la séance est
   proportionnelle à l'agitation habituelle du marché sur une journée. Quand le stop (basé sur
   l'ATR horaire) est petit par rapport à ce mouvement attendu, le trade a nettement plus de chances
   d'aboutir.
   - Sur les 26 indicateurs testés, c'est le plus net : le résultat moyen par trade passe de
     -0,003 R à +0,091 R du quintile le plus bas au plus haut, et l'écart est dans le bon sens
     12 années sur 14.
   - Il améliore séparément 2005-2011 **et** 2012-2018, ainsi que 2026, qui n'avait jamais servi au
     réglage.
2. **Sortie « taux de réussite ».** À 15 h, le robot ferme les positions en gain. Une position
   encore en perte est gardée : stop, break-even et TP restent actifs, et elle est fermée **dès
   qu'elle repasse en gain**, au plus tard à 17 h. Le taux de réussite passe de 55 % à **72 %**, en
   ne sacrifiant qu'une petite part du gain.
3. **Signal un peu plus large** : RSI(3) > 65 au lieu de 70, donc plus d'occasions de qualité égale.

### Ce qui a été testé et écarté

- **Plusieurs IA d'apprentissage automatique** (gradient boosting et régression logistique,
  26 indicateurs) :
  - un modèle qui prédit la direction, réentraîné chaque mois sur 14 ans ;
  - un modèle qui sélectionne les trades, entraîné chaque année sur le seul passé.

  Elles trouvent un léger signal (AUC 0,52 à 0,54, alors que le hasard vaut 0,50), mais trop faible et
  trop instable pour améliorer les résultats après les frais. **Elles ne sont pas utilisées** : une
  « IA » qui n'améliore rien donnerait seulement l'illusion de l'intelligence.
- **Le risque adaptatif** (risque divisé par 2 après une mauvaise série) était utile en v2. Avec le
  filtre de qualité, il ne réduit plus le drawdown et coupe le gain (+135 % au lieu de +200 % à 0,4 %
  de risque). Il est donc **désactivé par défaut**, mais reste disponible.
- **Viser plus de 72 % de trades gagnants** : c'est possible avec un TP minuscule, mais le compte
  perd alors de l'argent.
- **Trader les autres heures et les autres paires** : rien n'y résiste aux frais (2 106 créneaux
  horaires et 18 paires testés).

## 2. Règles de trading

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Sens | **Vente** d'EURUSD (euro faible en séance européenne). |
| Filtre du jour | **Amplitude de la veille ≥ 6 × ATR(14) H1**. Sinon, pas de trade ce jour-là (environ 4 jours sur 10). |
| Fenêtre d'entrée | **10 h - 13 h, heure serveur GMT+2/+3**, du lundi au vendredi. |
| Signal | Rebond court terme M5 : **RSI(3) > 65**. |
| Fréquence | Jusqu'à **3 positions par jour**, simultanées, avec **au moins 1 h** entre deux entrées. En moyenne 2,3 trades les jours où il trade. |
| Stop Loss | **3 × ATR(14) H1**, soit environ 20 à 40 pips, adapté à la volatilité. Cette distance définit « 1 R ». |
| Take Profit | **3 R**, posé à l'ouverture. |
| Break-even | À **+1 R**, le stop passe à l'entrée + 0,1 R. |
| Sortie | **15 h** pour les positions en gain. Celles en perte sont fermées dès qu'elles atteignent +0,05 R, au plus tard à **17 h**. Profil « rendement » : fermeture à 15 h dans tous les cas. |
| Risque | **0,5 %** du capital par trade. |

## 3. Protections du capital

- **Lot calculé sur la vraie perte au SL** (`OrderCalcProfit`), vérifié contre la marge libre et les
  limites du courtier.
- **Perte journalière max** (3 %) et **coupe-circuit drawdown** (20 % depuis le plus haut). Le
  coupe-circuit ferme les positions et arrête le robot ; pour le relancer, passez « Réarmer le
  robot » à `true`.
- **Choc de volatilité** : aucun trade si l'ATR dépasse 3 fois sa moyenne.
- **Filtre news** : pause de 30 min avant et après chaque annonce à fort impact sur l'EUR ou l'USD
  (calendrier MT5, en réel). Une position **gardée en perte après 15 h** est aussi fermée
  **10 minutes avant** une annonce importante. Sur 14 ans, les rares pertes supérieures au stop
  (8 trades sur 4 745, au pire -1,67 R) venaient de glissements sur ces annonces.
- **Filtre de spread** : maximum 2 pips, et au plus 10 % du stop.
- **Sécurité SL** : un SL est toujours posé ; si c'est impossible, la position est fermée.
- **Compatibilité courtiers** :
  - modes de remplissage FOK/IOC/RETURN détectés automatiquement ;
  - nouvelles tentatives après un requote ;
  - stops level et freeze level respectés ;
  - en compte netting, une seule position à la fois.
- **Redémarrage sans risque** : la gestion des positions est sauvegardée dans les variables globales du
  terminal.
- **Panneau d'information** :
  - fenêtre ouverte ou fermée, et prochaine fenêtre ;
  - filtre du jour (amplitude de la veille), RSI, spread, prochaine news ;
  - trades et résultat du jour, drawdown ;
  - positions en cours en R, et ce que fait le robot.

## 4. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**.
2. Copiez `IABot_EURUSD.mq5` dans `MQL5/Experts/IABot/`.
3. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
   Le résultat attendu est `0 errors, 0 warnings`.
4. Ouvrez un graphique **EURUSD en M5** et glissez **IABot_EURUSD** dessus.
5. Dans l'onglet *Commun*, cochez **« Autoriser le trading algorithmique »**, puis activez le bouton
   **Algo Trading**. Le panneau apparaît en haut à gauche.
6. Laissez le terminal allumé du lundi au vendredi : un **VPS** est fortement conseillé.

> **Heure du serveur.** Les horaires supposent un courtier en GMT+2 l'hiver et GMT+3 l'été, ce qui est
> le cas de la grande majorité des courtiers MT5. Vérifiez : la bougie de minuit doit correspondre à la
> clôture de New York (23 h à Paris). Sinon, réglez **« Référence horaire » = Heure GMT**, la fenêtre
> sur **8 h-11 h**, la sortie à **13 h** et le maintien jusqu'à **15 h**.

- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). C'est indispensable.
- **Capital** : environ 800 $ minimum pour respecter exactement 0,5 % de risque avec des lots de 0,01.

## 5. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Profil de sortie | Taux de réussite max | Ou « Rendement maximal » (14/14 années positives, 55 % de gagnants), ou « Personnalisé ». |
| Risque par trade (%) | 0,5 | Le drawdown évolue en proportion (13,7 % sur 14 ans à 0,5 %). |
| Filtre : amplitude de la veille ≥ x ATR H1 | 6,0 | 0 = désactivé (plus de trades, moins bons). |
| Vente si RSI > | 65 | Niveau du rebond M5. |
| Fenêtre / sortie / maintien si perte | 10-13 h / 15 h / 17 h | Heure serveur. |
| Positions simultanées / trades par jour / minutes entre entrées | 3 / 3 / 60 | Fréquence. |
| Stop loss = ATR x / TP = R x / break-even | 3,0 / 3,0 / 1 R | Gestion du trade. |
| Risque adaptatif | non | Option : risque divisé par 2 si les 60 derniers trades sont perdants. |
| Perte journalière / drawdown max | 3 % / 20 % | Coupe-circuits. |
| Commission par lot | 0 | Indiquez votre commission aller-retour (ex. 7) pour un calcul du lot exact. |

## 6. Vérification

MetaTrader ne fonctionne pas sous Linux. Nous avons donc construit un **émulateur MQL5**
(`tools/mql5emu/`) qui compile et exécute **le fichier `.mq5` lui-même** :

- **Compilation stricte**, tout avertissement étant traité comme une erreur.
- **Moteur de backtest tick par tick** fidèle à MT5.
- **19 scénarios automatiques** (rapport :
  [`tools/verify/last_report_eurusd.md`](tools/verify/last_report_eurusd.md)) :
  - SL et TP sur 100 % des trades, break-even exact, risque ≤ 0,5 % ;
  - entrées de 10 h à 13 h, fermeture au plus tard à 17 h ;
  - 3 positions max, espacées d'au moins 1 h ;
  - requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
  - compte netting et petit capital ;
  - perte journalière, coupe-circuit et filtre news ;
  - fermeture d'une position gardée en perte **avant une annonce de 15 h 30** (33 fermetures sur
    20 jours testés, aucune après l'annonce) ;
  - redémarrage en pleine position, risque adaptatif ;
  - AddressSanitizer et UBSan sur toutes les données.

**Ce qui reste à faire de votre côté.** Compilez dans MetaEditor (F7), seule vérification impossible
ici. Faites un test dans le **Testeur de stratégie MT5** (EURUSD, M5, « Chaque tick basé sur les ticks
réels ») avec les données de votre courtier. Puis faites tourner le robot **au moins un mois sur un
compte démo**.

```bash
tools/data/fetch_data.sh        # télécharge les données minute publiques (dont EURUSD 2005-2018)
tools/verify/verify_all.sh      # compile les robots dans l'émulateur + scénarios
build/eurusd/emu --data data/m1/EURUSD_ALL.csv --symbol EURUSD --trades trades.csv   # backtest 14 ans
```

La recherche complète se trouve dans `tools/research/`, avec un fichier par étude :
- `eu_cand.py` : les 47 322 trades candidats ;
- `eu_filters.py` : l'analyse des 26 indicateurs ;
- `eu_validate.py` : la validation par période ;
- `eu_exit2.py` : les règles de sortie ;
- `eu_ai_select.py` et `eurusd_wf*.py` : les IA.

## 7. Limites connues

- Avantage **réel mais modeste** : environ +0,06 R par trade. Des années faibles arrivent (2010,
  2013, 2016).
- Le taux de réussite élevé vient en partie de la sortie « dès que la position repasse en gain ». Les
  gains sont donc souvent petits, et les pertes (stop touché) plus grosses. C'est l'ensemble qui est
  positif.
- Très **sensible aux frais** du courtier.
- Le filtre de qualité a été trouvé sur l'historique 2005-2018. Il est validé sur deux périodes
  séparées et sur 2026, mais un effet de marché peut s'affaiblir avec le temps : surveillez les
  résultats.
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.

## 8. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot EURUSD (v3, version recommandée)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← ancienne version (EURUSD + GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD)
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5 (traducteur, API, moteur de backtest)
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche
tools/data/                          ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé
de perte en capital.*
