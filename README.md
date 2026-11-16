# IABot M5 : Expert Advisor pour MetaTrader 5

Robot de trading **entièrement automatique** pour MetaTrader 5, en unité de temps **M5**.
Il analyse le marché, ouvre les positions et pose **immédiatement le Stop Loss et le Take Profit**.
Il gère ensuite le **break-even**, le **trailing stop** et une clôture partielle optionnelle. Il applique
aussi un ensemble complet de protections du capital.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_M5.mq5`](MQL5/Experts/IABot/IABot_M5.mq5)
> Instrument recommandé : **XAUUSD (or)**, graphique **M5**.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Nous avons fait le choix de l'honnêteté : chaque chiffre de ce document vient d'un test réel sur des
données historiques, **avec spread, commission et swaps**, y compris les périodes où le robot perd.

- Sur l'**or (XAUUSD)**, la stratégie gagne en marché en tendance : **+47,9 % sur 2014-2017**
  (772 trades, 56,7 % de trades gagnants, drawdown max 7,2 %) et **+6,2 % sur avril-septembre 2026**
  (60,3 % de gagnants, DD 4,7 %).
- En marché sans tendance, elle **perd** : **-12,1 % sur janvier-octobre 2018** (DD 13,2 %).
- Sur les **paires Forex** (EURUSD, GBPUSD, AUDUSD, USDJPY), les tests ne montrent **aucun avantage
  fiable** après les frais. Ne l'utilisez pas sur ces paires sans l'avoir testé vous-même.
- Les performances passées ne préjugent pas des performances futures. Commencez **sur un compte démo**,
  puis en réel avec un petit risque (0,5 % par trade maximum).

---

## 1. La stratégie

Avant d'écrire le robot, nous avons testé 8 familles de stratégies M5 sur 4 ans de
données minute réelles et 5 instruments : repli sur moyenne mobile, cassure du range asiatique,
cassure des plus hauts et plus bas de la veille, retour à la moyenne sur les bandes de Bollinger,
bougies d'impulsion, etc. **Aucune n'a d'avantage fiable sur le Forex une fois les frais payés.** Une seule idée montre un
avantage positif chaque année : **suivre la tendance H1 de l'or et acheter les replis courts en M5**.

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Tendance (H1) | Achat seulement si clôture H1 > EMA 200 **et** EMA 50 > EMA 200. Vente : l'inverse. |
| Entrée (M5) | Repli court terme : **RSI(3) < 10** en tendance haussière (**> 90** en baissière). |
| Session | Entrées entre **9 h et 20 h (heure serveur)**, soit environ 7 h-18 h GMT : Londres puis New York. |
| Stop Loss | **3 × ATR(14) H1**. Cette distance définit « 1 R ». |
| Take Profit | **4 R**, posé en même temps que le SL. |
| Break-even | À **+0,8 R**, le SL passe à l'entrée + 0,1 R : le trade ne peut plus perdre. |
| Trailing stop | À partir de **+2 R**, le SL suit le prix à 1,5 R de distance. |
| Week-end | Plus d'entrée le vendredi après 18 h, fermeture des positions le vendredi à 22 h. |

## 2. Protections intégrées

- **Risque fixe par trade** (0,5 % du solde par défaut). Le lot est calculé à partir de la vraie perte
  au SL (`OrderCalcProfit`), et il est vérifié contre la marge libre et les limites de volume du courtier.
- **Perte journalière max** (3 %) : plus aucun trade jusqu'au lendemain.
- **Coupe-circuit drawdown** (15 % depuis le plus haut) : le robot ferme ses positions et s'arrête
  **définitivement**. Pour le relancer, passez le paramètre « Réarmer le robot » à `true`.
- **4 trades max par jour**, **pause après 3 pertes consécutives** dans la journée, **une seule
  position à la fois** par symbole.
- **Filtre news** : pause de 30 min avant et après chaque annonce à fort impact sur les devises du
  symbole, via le calendrier économique intégré à MT5. Il fonctionne en réel ; MT5 ne fournit pas le
  calendrier dans le testeur.
- **Filtre de spread** : le spread doit rester sous 10 % de la distance du SL, avec un maximum en
  points optionnel.
- **Sécurité SL** : si le courtier ignore le SL/TP à l'ouverture, le robot les pose aussitôt.
  S'il ne peut pas les poser, il **ferme la position**. Il ne laisse jamais une position sans stop.
- **Compatibilité courtiers** : comptes hedging et netting. Le mode de remplissage
  (FOK/IOC/RETURN) est détecté automatiquement. Le robot réessaie après un requote, respecte le stops
  level et le freeze level, et attend 30 s après un refus du serveur pour ne pas l'inonder de requêtes.
- **Redémarrage sans risque** : les données de chaque position sont sauvegardées dans les variables
  globales du terminal. Après un redémarrage du PC ou du VPS, le robot reprend la gestion
  (break-even, trailing) là où il s'était arrêté.
- **Panneau d'information** sur le graphique : tendance, RSI, session, prochaine news, spread,
  résultat du jour, drawdown, position en cours en R, et ce que fait le robot.

## 3. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**.
2. Copiez `IABot_M5.mq5` dans `MQL5/Experts/` (par exemple `MQL5/Experts/IABot/`).
3. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
   Le résultat attendu est `0 errors, 0 warnings`.
4. Dans MT5, ouvrez un graphique **XAUUSD en M5**.
5. Glissez **IABot_M5** depuis le Navigateur (section Experts) sur le graphique. Dans l'onglet
   *Commun*, cochez **« Autoriser le trading algorithmique »**.
6. Activez le bouton **Algo Trading** dans la barre d'outils. Le panneau apparaît en haut à gauche.
7. Pour que le robot fonctionne 24 h/24, le terminal doit rester allumé : un **VPS** est fortement
   conseillé.

> **Heure du serveur.** Les heures de session par défaut (9 h-20 h) supposent un courtier en
> GMT+2 l'hiver et GMT+3 l'été, ce qui est le cas de la grande majorité des courtiers MT5. Si le
> vôtre est différent, réglez **« Référence horaire » = Heure GMT** et la session sur **7 h-18 h**.
> Le décalage est alors détecté automatiquement en réel.

## 4. Capital minimum (important pour l'or)

Aux prix de 2026 (environ 4 000-4 600 $ l'once), un SL vaut en général **40 à 70 $ par 0,01 lot**.
Le lot minimum étant de 0,01 :

| Capital | Comportement |
|---|---|
| ≥ 12 000 $ | Risque exact de 0,5 % par trade (réglage par défaut). |
| 3 000 à 12 000 $ | Le robot prend 0,01 lot si le risque réel reste ≤ 2 % (paramètre « Risque max toléré si le lot minimum est imposé »). |
| < 3 000 $ | Beaucoup de trades sont ignorés : le panneau affiche « capital trop faible pour ce SL ». Utilisez un compte **cent** ou un capital plus important. Ne montez pas le risque. |

## 5. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Risque par trade (%) | 0,5 | Perte maximale si le SL est touché. 1 % au grand maximum. |
| Stop loss = ATR x | 3,0 | Distance du SL (1 R). |
| Take profit = R x | 4,0 | Objectif. |
| Break-even à +R / gain verrouillé | 0,8 / 0,1 | Sécurisation rapide du trade. |
| Trailing à partir de +R / distance | 2,0 / 1,5 | Laisse courir les gagnants. |
| Clôture partielle | non | Option : ferme 50 % à +1 R. Les tests montrent un léger coût sur le rendement. |
| Perte journalière / drawdown max | 3 % / 15 % | Coupe-circuits. |
| Session | 9 h-20 h serveur | Londres et New York. |
| Filtre news | oui, ±30 min, fort impact | Calendrier MT5, en réel seulement. |
| Commission par lot | 0 | Indiquez la commission aller-retour de votre compte ECN (ex. 7) pour un calcul du lot exact. |

Le critère d'optimisation personnalisé (`OnTester`) récompense le profit factor, le nombre de trades
et un drawdown faible. Si vous optimisez, vérifiez toujours le résultat sur une période différente
(test « forward »).

## 6. Résultats des tests

Conditions : capital 10 000 $, risque 0,5 %, données minute réelles, simulation « 1 minute OHLC »
(4 ticks par minute), spread 0,25 $ + commission 7 $/lot sur l'or, spread 0,3 à 0,7 pip + 7 $/lot sur
le Forex, swaps négatifs (prudents) facturés chaque nuit et triplés le mercredi.
Les réglages ont été choisis **uniquement sur 2014-2017**. 2018 et 2026 sont des données jamais
utilisées pour les choisir.

| Symbole | Période | Type | Trades | % gagnants | Profit factor | Résultat | DD max |
|---|---|---|---:|---:|---:|---:|---:|
| **XAUUSD** | 2014-2017 | conception | 772 | 56,7 % | 1,29 | **+47,9 %** | 7,2 % |
| **XAUUSD** | 2018 (jan-oct) | hors-échantillon | 150 | 45,3 % | 0,64 | **-12,1 %** | 13,2 % |
| **XAUUSD** | 2026 (avr-sep) | hors-échantillon | 78 | 60,3 % | 1,41 | **+6,2 %** | 4,7 % |
| EURUSD | 2014-2017 | conception | 638 | 52,8 % | 1,00 | -0,4 % | 15,0 %* |
| EURUSD | 2018 | hors-échantillon | 166 | 52,4 % | 0,68 | -10,9 % | 13,0 % |
| GBPUSD | 2014-2017 | conception | 514 | 52,5 % | 0,90 | -10,8 % | 15,0 %* |
| USDJPY | 2014-2017 | conception | 686 | 54,5 % | 1,07 | +9,5 % | 14,0 % |
| USDJPY | 2026 | hors-échantillon | 73 | 46,6 % | 0,73 | -4,2 % | 6,4 % |
| AUDUSD | 2014-2017 | conception | 147 | 40,8 % | 0,58 | -14,2 % | 15,1 %* |

\* Le coupe-circuit de 15 % a stoppé le robot. Toutes les lignes figurent dans
[`results/backtest_results.csv`](results/backtest_results.csv).

**Lecture honnête.** Sur l'or, le robot gagne environ 0,1 R par trade en moyenne et fait environ
16 trades par mois, d'une durée médiane de 13 à 22 heures. Il gagne en tendance et perd en range,
comme 2018. Le taux de réussite tourne autour de **55 à 60 %**. On peut le monter en rapprochant le
TP et le break-even, mais les tests montrent que cela **réduit le gain total**. Un taux de réussite
élevé n'est pas un objectif en soi : ce qui compte, c'est le gain moyen par trade.

## 7. Comment le robot a été vérifié

MetaTrader ne fonctionne pas sous Linux. Nous avons donc construit un **émulateur MQL5** complet
(`tools/mql5emu/`) qui compile et exécute **le fichier `.mq5` lui-même**, et non une copie de la
stratégie :

1. **Contrôle de compatibilité MQL5** (`translate.py`) : il signale toute construction C++ invalide
   en MQL5, les structures passées par valeur, les initialisations de membres et les variables
   référence.
2. **Compilation stricte**, tout avertissement étant traité comme une erreur. Elle vérifie les
   signatures exactes de l'API MQL5, les conversions avec perte, les variables masquées, les
   comparaisons signé/non signé, la concaténation chaîne + nombre et l'écriture dans un paramètre
   d'entrée. Le contrôleur a lui-même été testé en injectant 10 erreurs typiques : toutes ont été détectées (8 à la compilation, 2 à l'exécution).
3. **Moteur de backtest tick par tick** qui reproduit le comportement de MT5 : indicateurs EMA, RSI,
   ATR et ADX calculés avec les formules de MetaQuotes, contrôle du stops level et du freeze level,
   marge, swaps, historique des transactions, variables globales et calendrier. Il vérifie aussi à
   l'exécution les formats de `PrintFormat` et les accès hors tableau.
4. **18 scénarios automatiques**, tous réussis (rapport :
   [`tools/verify/last_report.md`](tools/verify/last_report.md)) :
   - SL et TP présents dès l'ouverture sur 100 % des trades, avec un TP exactement à 4 R ;
   - break-even à +0,1 R vérifié sur chaque déplacement ;
   - trailing toujours au-dessus de +0,5 R ;
   - risque réel ≤ 0,5 % par trade, sessions et règles du vendredi respectées ;
   - requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
   - compte netting et petit capital ;
   - perte journalière, coupe-circuit drawdown et filtre news ;
   - redémarrage du terminal avec une position ouverte ;
   - exécution sous AddressSanitizer et UBSan (division par zéro) sur toutes les données.
5. **Validation croisée** : un moteur de recherche indépendant écrit en Python et l'EA réel exécuté
   dans l'émulateur donnent les mêmes chiffres (environ 900 trades, 56 % de gagnants, PF environ 1,25
   sur l'or 2014-2017).

Deux défauts ont été trouvés et corrigés grâce à ces tests. Le premier : avec un stops level élevé,
le robot envoyait des modifications refusées à chaque tick quand le prix approchait du TP. Le second :
une durée maximale de trade de 48 h coupait des trades gagnants.

**Ce qui reste à faire de votre côté.** La compilation dans MetaEditor (F7) est la vérification
finale, impossible ici. Le code n'utilise que l'API standard MQL5, sans aucune bibliothèque externe.
Ensuite, lancez un test dans le **Testeur de stratégie MT5** avec les données de votre courtier :
XAUUSD, M5, mode « Chaque tick basé sur les ticks réels », dépôt 10 000 $. Puis faites tourner le
robot **au moins un mois sur un compte démo** avant de passer en réel.

### Relancer la vérification soi-même (Linux, Python 3, g++)

```bash
tools/data/fetch_data.sh        # télécharge les données minute publiques (≈ 150 Mo) dans data/m1
tools/verify/verify_all.sh      # compile l'EA dans l'émulateur + 18 scénarios
build/emu --data data/m1/XAUUSD_IS.csv --symbol XAUUSD --trades trades.csv   # backtest libre
build/emu ... --set InpRiskPercent=1.0 --set InpTP_R=3                        # changer un paramètre
```

## 8. Limites connues

- Avantage démontré **uniquement sur l'or** et **seulement en marché directionnel**. Il faut
  s'attendre à des périodes perdantes de plusieurs mois, comme en 2018.
- Les jours fériés où le marché ferme avant 22 h le vendredi (Vendredi saint, 4 juillet,
  Black Friday), une position peut rester ouverte pendant le week-end : 3 cas en 4 ans.
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.
- Les résultats dépendent du spread, de la commission et des swaps de votre courtier. Un compte
  ECN à bas coûts est fortement recommandé.

## 9. Structure du dépôt

```
MQL5/Experts/IABot/IABot_M5.mq5   ← le robot (le seul fichier à installer)
results/backtest_results.csv      ← résultats détaillés par symbole et par période
tools/mql5emu/                    ← émulateur MQL5 (traducteur, API, moteur de backtest)
tools/verify/                     ← 18 scénarios de vérification + dernier rapport
tools/research/                   ← recherche de stratégies (toutes les idées testées)
tools/data/                       ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque
élevé de perte en capital.*
