# IABot EURUSD : robot de trading autonome spécialisé EURUSD (MetaTrader 5, M5)

Expert Advisor **entièrement automatique**, spécialisé sur une seule paire : **EURUSD**. Une fois lancé,
il fait tout seul :

- il analyse le marché et prend **plusieurs trades par jour** (environ 2,2 en moyenne) ;
- il pose **immédiatement le Stop Loss et le Take Profit** de chaque trade ;
- il déplace le stop au **break-even** et ferme les positions au bon moment ;
- il **adapte son risque** à ses propres résultats récents, et sa mémoire survit aux redémarrages ;
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

### Résultats (10 000 $ au départ, risque 0,4 % par trade)

| Période | Trades | Trades/jour | % gagnants | Profit factor | Résultat | Drawdown max |
|---|---:|---:|---:|---:|---:|---:|
| **2005 → 2018** (14 ans) | 7 860 | 2,2 | 53,9 % | 1,16 | **+158 %** (10 000 $ → 25 848 $) | 13,9 % |
| **2026** (avr. → sept.) | 243 | 2,2 | 51,0 % | 1,06 | **+1,1 %** | 4,7 % |

- **13 années positives sur 14** (seule 2013 est négative : -4 %).
- Environ **+7 % par an** en moyenne (composé), avec une baisse maximale de 14 %.
- Le détail année par année est dans
  [`results/backtest_results_eurusd.csv`](results/backtest_results_eurusd.csv).

| Année | 2005 | 2006 | 2007 | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018* | 2026* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Résultat ($) | +1 670 | +1 532 | +42 | +717 | +114 | +1 648 | +38 | +1 962 | -406 | +3 725 | +2 334 | +345 | +435 | +1 692 | +106 |

\* 2018 : janvier-août ; 2026 : avril-septembre.

---

## 1. Comment le robot a été construit

### Ce que nous avons testé

1. **Une vraie IA d'apprentissage automatique.**
   - Le modèle (gradient boosting et régression logistique) utilise 26 informations : heure, jour,
     rendements sur 5 min à 24 h, RSI, tendances, volatilité, position dans la journée, range
     asiatique, veille, semaine.
   - Il est **réentraîné chaque mois** sur les 3 années précédentes, puis testé sur la période
     suivante qu'il n'a jamais vue, de 2008 à 2018.
   - **Résultat** : il prédit la direction d'EURUSD un peu mieux que le hasard, chaque année (AUC
     0,54, soit environ 58 % de bonnes directions sur ses prédictions les plus confiantes). Mais
     l'avantage ne vaut que **0,5 à 1 pip**, et **les frais l'annulent** : en trading réel simulé, il
     perd 0,3 à 0,7 pip par trade.
   - Une variante restreinte gagne 8 années sur 11, mais elle change de résultat selon la durée
     d'entraînement : elle n'est pas assez fiable pour votre argent.
   - **Elle n'est donc pas utilisée pour trader.** Un « filtre IA » qui ne prédit rien de rentable
     n'apporterait que l'illusion de l'intelligence.
2. **Les 24 heures de la journée**, sur 18 paires (2 106 créneaux). Seule la séance européenne
   montre un avantage qui résiste aux frais et au temps. La nuit, le spread rend tout effet
   inexploitable.
3. **8 familles de stratégies classiques** (repli dans la tendance, retour à la moyenne, cassures,
   scalping, etc.). Aucune ne bat les frais de façon fiable en M5.

### Ce que le robot sait

- **L'euro baisse face au dollar pendant la séance européenne.** C'est un effet documenté par la
  recherche académique (Ranaldo 2009 ; Breedon & Ranaldo 2013) : une devise tend à se déprécier
  pendant les heures de bureau de sa propre place financière. Nous l'avons vérifié sur **14 ans**,
  et les années 2005-2013 n'avaient jamais servi à le régler.
- **Les meilleures entrées sont les rebonds courts en M5**, quand le RSI(3) dépasse 70 : le robot vend
  plus haut.
- **Plusieurs entrées espacées d'une heure** font mieux qu'une seule : sur 14 ans, le gain annuel
  moyen double, et la pire année est moins mauvaise.
- **Couper le risque de moitié quand les 60 derniers trades sont globalement perdants** fait passer
  le drawdown maximal de 18,2 % à 13,9 %. En contrepartie, le gain passe de +203 % à +158 % sur
  14 ans. Le robot détecte ainsi lui-même les périodes où l'effet faiblit. Vous pouvez désactiver
  cette adaptation pour viser plus de rendement, avec plus de risque.

## 2. Règles de trading

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Sens | **Vente** d'EURUSD (euro faible en séance européenne). |
| Fenêtre d'entrée | **10 h - 13 h, heure serveur GMT+2/+3**, du lundi au vendredi. |
| Signal | Rebond court terme M5 : **RSI(3) > 70**. |
| Plusieurs trades | Jusqu'à **3 positions par jour**, simultanées, avec **au moins 1 h** entre deux entrées. |
| Stop Loss | **3 × ATR(14) H1**, soit environ 20 à 40 pips, adapté à la volatilité. Cette distance définit « 1 R ». |
| Take Profit | **3 R**, posé à l'ouverture. |
| Break-even | Profil *rendement* (défaut) : à **+1 R**. Profil *taux de réussite* : à **+0,5 R**. Le stop passe à l'entrée + 0,1 R. |
| Sortie forcée | À **15 h**, avant les statistiques américaines (15 h 30). Aucune position la nuit, donc aucun swap. |
| Risque | **0,4 %** du capital par trade, réduit à **0,2 %** quand le bilan des 60 derniers trades est négatif. |

Hors de la fenêtre, le robot reste actif : il gère les positions, surveille les protections et affiche
l'heure de la prochaine fenêtre de trading.

### Taux de réussite ou rendement ?

| Profil (2005-2018) | % gagnants | Résultat | DD max | Années positives | 2026 |
|---|---:|---:|---:|---:|---:|
| **Rendement** (défaut) | 53,9 % | **+158 %** | 13,9 % | **13/14** | +1,1 % |
| Taux de réussite | **58,3 %** | +123 % | 14,3 % | 11/14 | +0,2 % |

Le profil « taux de réussite » gagne plus souvent, mais **rapporte moins**. Le profil « rendement »
fait mieux sur tous les critères d'argent : c'est pourquoi il est réglé par défaut. On peut pousser le
taux de réussite au-delà de 60 % avec un TP très proche, mais les tests montrent qu'alors le compte
**perd** de l'argent.

## 3. Protections du capital

- **Risque fixe et adaptatif par trade**. Le lot est calculé à partir de la vraie perte au SL
  (`OrderCalcProfit`), puis vérifié contre la marge libre et les limites du courtier.
- **Perte journalière max** (3 %) : plus aucun trade jusqu'au lendemain.
- **Coupe-circuit drawdown** (20 % depuis le plus haut) : le robot ferme ses positions et s'arrête
  **définitivement**. Pour le relancer, passez « Réarmer le robot » à `true`.
- **Choc de volatilité** : aucun trade si l'ATR dépasse 3 fois sa moyenne (Brexit, décision surprise
  d'une banque centrale…).
- **Filtre news** : pause de 30 min avant et après chaque annonce à fort impact sur l'EUR ou l'USD,
  via le calendrier économique de MT5. Il fonctionne en réel ; MT5 ne fournit pas le calendrier dans le
  testeur.
- **Filtre de spread** : maximum 2 pips, et au plus 10 % du stop.
- **Sécurité SL** : si le courtier ignore le SL/TP, le robot les pose aussitôt. S'il ne peut pas, il
  **ferme la position**. Jamais de position sans stop.
- **Compatibilité courtiers** :
  - modes de remplissage FOK/IOC/RETURN détectés automatiquement ;
  - nouvelles tentatives après un requote ;
  - stops level et freeze level respectés ;
  - en compte **netting**, une seule position à la fois, car ce type de compte n'en permet pas
    plusieurs.
- **Redémarrage sans risque** : la gestion des positions et la mémoire des 60 derniers trades sont
  sauvegardées dans les variables globales du terminal.
- **Panneau d'information** sur le graphique :
  - fenêtre ouverte ou fermée, et prochaine fenêtre de trading ;
  - RSI, spread, prochaine news ;
  - mémoire et risque adaptatif ;
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

> **Heure du serveur.** La fenêtre 10 h-13 h suppose un courtier en GMT+2 l'hiver et GMT+3 l'été, ce
> qui est le cas de la grande majorité des courtiers MT5. Vérifiez : la bougie de minuit doit
> correspondre à la clôture de New York (23 h à Paris). Sinon, réglez **« Référence horaire » = Heure
> GMT**, la fenêtre sur **8 h-11 h** et la sortie à **13 h**.

- **Compte** : ECN à bas coûts (spread + commission ≤ 1 pip sur EURUSD). C'est indispensable, car
  l'avantage du robot se compte en fractions de pip.
- **Capital** : environ 1 000 $ minimum pour respecter exactement 0,4 % de risque avec des lots de
  0,01.

## 5. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Profil de sortie | Rendement maximal | Ou « Taux de réussite élevé », ou « Personnalisé ». |
| Risque par trade (%) | 0,4 | Jusqu'à 1 % pour les plus agressifs. Le drawdown augmente en proportion. |
| Risque adaptatif | oui (60 trades, × 0,5) | Réduit le risque après une mauvaise série. Désactivé : +203 % au lieu de +158 % sur 14 ans, mais DD 18 % au lieu de 14 %. |
| Positions simultanées max / trades max par jour | 3 / 3 | Fréquence. |
| Minutes entre deux entrées | 60 | Espacement. |
| Fenêtre d'entrée / sortie | 10 h - 13 h / 15 h | Heure serveur. |
| Vente si RSI > | 70 | Niveau du rebond M5. |
| Stop loss = ATR x / TP = R x | 3,0 / 3,0 | SL et TP. |
| Perte journalière / drawdown max | 3 % / 20 % | Coupe-circuits. |
| Commission par lot | 0 | Indiquez votre commission aller-retour (ex. 7) pour un calcul du lot exact. |

## 6. Vérification du robot

MetaTrader ne fonctionne pas sous Linux. Nous avons donc construit un **émulateur MQL5**
(`tools/mql5emu/`) qui compile et exécute **le fichier `.mq5` lui-même** :

1. **Compilation stricte**, tout avertissement étant traité comme une erreur. Elle vérifie la
   compatibilité MQL5, les signatures de l'API, les conversions avec perte, les variables masquées et
   les formats. Le contrôleur a été testé en injectant 10 erreurs typiques : toutes ont été détectées.
2. **Moteur de backtest tick par tick** fidèle à MT5 :
   - indicateurs calculés avec les formules de MetaQuotes ;
   - stops level, marge, swaps ;
   - historique, variables globales, calendrier.
3. **19 scénarios automatiques** (rapport :
   [`tools/verify/last_report_eurusd.md`](tools/verify/last_report_eurusd.md)) :
   - SL et TP sur 100 % des trades ;
   - break-even exact, risque ≤ 0,4 % ;
   - fenêtre horaire et sortie à 15 h respectées ;
   - 3 positions max, espacées d'au moins 1 h ;
   - requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
   - compte netting et petit capital ;
   - perte journalière, coupe-circuit et filtre news ;
   - redémarrage en pleine position ;
   - **risque adaptatif** : bascule, retour à la normale et risque exact à chaque entrée ;
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

## 7. Limites connues

- Avantage **réel mais modeste** : environ +0,04 R par trade. Des mois et des années faibles arrivent
  (2007, 2009, 2011 proches de zéro ; 2013 à -4 %).
- Très **sensible aux frais** du courtier.
- Un effet de marché peut s'affaiblir avec le temps. Le risque adaptatif amortit ces périodes, mais
  surveillez les résultats.
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.

## 8. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_EURUSD.mq5  ← LE robot EURUSD (version recommandée)
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← version précédente (EURUSD + GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD)
results/                             ← résultats détaillés
tools/mql5emu/                       ← émulateur MQL5 (traducteur, API, moteur de backtest)
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (IA walk-forward, scan 24 h, stratégies)
tools/data/                          ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé
de perte en capital.*
