# IABot FX : robot de trading Forex M5 pour MetaTrader 5

Expert Advisor **entièrement automatique** pour le Forex, en unité de temps **M5**, sur **EURUSD et
GBPUSD**. Une fois lancé, il :

- surveille le marché du lundi au vendredi ;
- prend **plusieurs trades par jour** ;
- pose **immédiatement le Stop Loss et le Take Profit** de chaque trade ;
- déplace le stop au **break-even** quand le trade est en gain ;
- ferme les positions au bon moment ;
- protège le capital avec des limites journalières et un coupe-circuit.

> Fichier à installer : [`MQL5/Experts/IABot/IABot_FX_M5.mq5`](MQL5/Experts/IABot/IABot_FX_M5.mq5)
> À lancer sur **deux graphiques : EURUSD M5 et GBPUSD M5**.

---

## ⚠️ À lire avant tout

Aucun robot ne peut garantir des gains, et aucun ne rend milliardaire. Celui-ci ne fait pas exception.
Chaque chiffre ci-dessous vient d'un test sur des **données minute réelles**, avec spread, commission et
swaps, et sur des périodes **jamais utilisées** pour régler le robot. Les performances passées ne
préjugent pas des performances futures. Commencez **sur un compte démo**, puis en réel avec un petit
risque.

### Résultats (EURUSD + GBPUSD ensemble, 10 000 $, 0,5 % de risque par trade)

| Profil | 2014-2017 (conception) | 2018 jan-oct (jamais vue) | 2026 avr-sep (jamais vue) |
|---|---|---|---|
| **Taux de réussite élevé** (défaut) | **60,8 %** de trades gagnants · PF 1,08 · **+30,9 %** · DD 10,1 % | **63,4 %** · PF 1,19 · **+12,7 %** · DD 4,9 % | **60,2 %** · PF 1,22 · **+6,1 %** · DD 5,3 % |
| **Rendement maximal** | 52,8 % · PF 1,12 · **+50,6 %** · DD 12,4 % | 55,3 % · PF 1,29 · **+20,2 %** · DD 5,1 % | 53,4 % · PF 1,16 · **+4,4 %** · DD 5,8 % |

Fréquence : environ **2,5 à 3 trades par jour** (1,2 à 1,5 par paire). PF (profit factor) = gains bruts
÷ pertes brutes ; DD = baisse maximale du capital. Détail par paire :
[`results/backtest_results_fx.csv`](results/backtest_results_fx.csv).

---

## 1. Ce que nous avons cherché, et ce qui marche vraiment

**24 heures sur 24, 18 paires.** Nous avons mesuré le mouvement moyen de 18 paires Forex sur
**2 106 créneaux horaires** couvrant toute la journée, sur 4 ans de données minute. Les frais sont
réalistes et augmentent la nuit, quand les spreads s'élargissent.
- Seuls 13 créneaux restent positifs chaque année **et** hors échantillon après les frais.
- Presque tous concernent la **séance européenne**.
- La nuit, aucun effet n'est exploitable : le seul effet fort (AUDNZD) se produit juste après minuit,
  quand le spread est le plus large.
- En séance américaine, aucun effet ne résiste hors échantillon.

**Stratégies classiques.** Repli dans la tendance, retour à la moyenne, cassures de range,
scalping de nuit, Donchian et tendance H4 ou journalière : **aucune ne bat les frais** de façon fiable
en M5. Les objectifs (2 à 5 pips) sont trop petits face au spread et à la commission (1 à 3 pips).

**Intelligence artificielle.** Nous avons entraîné des modèles (régression logistique et gradient
boosting) pour prédire si un trade allait gagner. Ils utilisaient 12 indicateurs : RSI, tendances H1 et
journalière, volatilité, mouvement de la séance, position dans le range asiatique, heure, jour…
Résultat : **aucun pouvoir prédictif**. L'AUC est d'environ 0,50, c'est-à-dire le niveau d'un tirage à
pile ou face, aussi bien en validation croisée qu'en 2018 et 2026. Nous ne l'avons donc **pas** ajouté :
un « filtre IA » qui ne prédit rien donnerait l'illusion de l'intelligence sans rien apporter.

**L'effet retenu.** L'**euro et la livre baissent face au dollar pendant la séance européenne**. Ce
phénomène est documenté dans la recherche académique (Ranaldo 2009 ; Breedon & Ranaldo 2013) : une
devise tend à se déprécier pendant les heures de bureau de sa propre place financière. Il est positif
chaque année de 2014 à 2017, puis en 2018 et en 2026. Il est **absent** des paires croisées (EURJPY,
EURCAD, EURGBP, GBPJPY…), où les frais sont plus élevés.

> **Pourquoi pas de trades la nuit ?** Le robot est actif 24 h/24 du lundi au vendredi : il surveille,
> gère et protège en continu. Mais il **n'ouvre des positions que pendant la fenêtre où un avantage a
> été mesuré**. Trader aux autres heures ferait plus de trades, mais perdrait de l'argent. Le panneau
> affiche à tout moment l'heure de la prochaine fenêtre.

## 2. Règles du robot

| Étape | Règle (bougies clôturées uniquement, aucun repaint) |
|---|---|
| Paires | **EURUSD** et **GBPUSD**, en **vente** (mode automatique). |
| Fenêtre d'entrée | **10 h - 13 h, heure serveur GMT+2/+3** (en pleine séance européenne), du lundi au vendredi. |
| Entrée (M5) | Sur un **rebond court terme** : RSI(3) > 70, pour vendre plus haut. |
| Plusieurs trades | Jusqu'à **3 trades par jour et par paire**, une position à la fois. Un nouveau trade peut partir dès que le précédent est clôturé. |
| Stop Loss | **3 × ATR(14) H1**, soit environ 20 à 40 pips selon la volatilité. Cette distance définit « 1 R ». |
| Take Profit | Profil *taux de réussite* : **1 R**. Profil *rendement* : **3 R**. Toujours posé à l'ouverture. |
| Break-even | Profil *taux de réussite* : à **+0,5 R**. Profil *rendement* : à **+1 R**. Le stop passe à l'entrée + 0,1 R. |
| Sortie forcée | À **15 h**, juste avant les statistiques américaines (15 h 30). Aucune position la nuit, donc aucun swap à payer. |

### Pourquoi environ 60 % de trades gagnants, et pas 80 % ?

Le taux de réussite se règle facilement : il suffit de rapprocher le Take Profit. Avec un TP à 0,3 R,
on dépasse 70 % de trades gagnants, mais **le compte perd de l'argent**, parce que les petits gains ne
couvrent plus les pertes. Nous avons testé 36 combinaisons stop / TP / break-even. Le profil par
défaut est le réglage qui maximise le taux de réussite **tout en restant positif sur les trois
périodes**.

## 3. Protections du capital

- **Risque fixe par trade** (0,5 % du solde). Le lot est calculé à partir de la vraie perte au SL
  (`OrderCalcProfit`), puis vérifié contre la marge libre et les limites de volume du courtier.
- **Perte journalière max** (3 %) : plus aucun trade jusqu'au lendemain.
- **Coupe-circuit drawdown** (15 % depuis le plus haut) : le robot ferme ses positions et s'arrête
  **définitivement**. Pour le relancer, passez « Réarmer le robot » à `true`.
- **Choc de volatilité** : aucun trade si l'ATR dépasse 3 fois sa moyenne (Brexit, décision surprise
  d'une banque centrale…).
- **Filtre news** : pause de 30 min avant et après chaque annonce à fort impact (EUR, GBP, USD), via le
  calendrier économique intégré à MT5. Il fonctionne en réel ; MT5 ne fournit pas le calendrier dans le
  testeur.
- **Filtre de spread** : maximum 2 pips, et au plus 10 % du stop.
- **Sécurité SL** : si le courtier ignore le SL/TP à l'ouverture, le robot les pose aussitôt. S'il ne
  peut pas les poser, il **ferme la position**. Il ne laisse jamais une position sans stop.
- **Compatibilité courtiers** : comptes hedging et netting. Le mode de remplissage (FOK/IOC/RETURN) est
  détecté automatiquement. Le robot réessaie après un requote, respecte le stops level et le freeze
  level, et attend 30 s après un refus du serveur.
- **Redémarrage sans risque** : l'état de chaque position est sauvegardé dans les variables globales du
  terminal. Après un redémarrage du PC ou du VPS, le robot reprend la gestion de la position.
- **Panneau d'information** sur le graphique :
  - biais, RSI, fenêtre ouverte ou fermée et **prochaine fenêtre de trading** ;
  - prochaine news, spread ;
  - trades du jour, résultat du jour, drawdown ;
  - position en cours en R, et ce que fait le robot.

## 4. Installation (5 minutes)

1. Dans MetaTrader 5 : **Fichier → Ouvrir le dossier des données**.
2. Copiez `IABot_FX_M5.mq5` dans `MQL5/Experts/IABot/`.
3. Ouvrez **MetaEditor** (touche F4), ouvrez le fichier et cliquez sur **Compiler** (F7).
   Le résultat attendu est `0 errors, 0 warnings`.
4. Ouvrez un graphique **EURUSD en M5** et glissez **IABot_FX_M5** dessus. Faites de même sur un
   graphique **GBPUSD en M5**. Une seule instance par paire.
5. Dans l'onglet *Commun*, cochez **« Autoriser le trading algorithmique »**, puis activez le bouton
   **Algo Trading** dans la barre d'outils. Le panneau apparaît en haut à gauche.
6. Le terminal doit rester allumé du lundi au vendredi : un **VPS** est fortement conseillé.

> **Heure du serveur.** La fenêtre 10 h-13 h suppose un courtier en GMT+2 l'hiver et GMT+3 l'été, ce
> qui est le cas de la grande majorité des courtiers MT5. Vérifiez : la bougie de minuit de votre
> graphique doit correspondre à la clôture de New York (23 h à Paris). Sinon, réglez
> **« Référence horaire » = Heure GMT**, la fenêtre sur **8 h-11 h** et la sortie à **13 h**.

**Capital** : un stop de 20 à 40 pips vaut 2 à 4 $ pour 0,01 lot. Avec 0,5 % de risque, **environ
800 $ suffisent** pour un calcul de lot exact. **Compte** : un compte ECN à bas coûts est
indispensable. Avec 1,3 pip de frais au lieu de 1,0 sur EURUSD, l'avantage fond nettement.

## 5. Paramètres principaux

| Paramètre | Défaut | Rôle |
|---|---|---|
| Profil de sortie | Taux de réussite élevé | Ou « Rendement maximal », ou « Personnalisé » (utilise TP et break-even ci-dessous). |
| Risque par trade (%) | 0,5 | Perte maximale si le SL est touché. 1 % au grand maximum. |
| Fenêtre d'entrée | 10 h - 13 h | Heure serveur. |
| Heure de sortie forcée | 15 h | Avant les statistiques américaines. |
| Trades max par jour | 3 | Par paire. |
| Vente si RSI > | 70 | Niveau du rebond M5. |
| Stop loss = ATR x | 3,0 | Distance du stop (1 R). |
| Sens des trades | Automatique | Ventes EURUSD et GBPUSD. Les sens forcés sur d'autres paires n'ont **pas** été validés. |
| Commission par lot | 0 | Indiquez la commission aller-retour de votre compte (ex. 7) pour un calcul du lot exact. |

## 6. Comment le robot a été vérifié

MetaTrader ne fonctionne pas sous Linux. Nous avons donc construit un **émulateur MQL5**
(`tools/mql5emu/`) qui compile et exécute **le fichier `.mq5` lui-même** :

1. **Contrôle de compatibilité MQL5** et **compilation stricte**, tout avertissement étant traité comme
   une erreur. Elle vérifie les signatures de l'API MQL5, les conversions avec perte, les variables
   masquées, les comparaisons signé/non signé, la concaténation chaîne + nombre et l'écriture dans un
   paramètre. Le contrôleur a été testé en injectant 10 erreurs typiques : toutes ont été détectées.
2. **Moteur de backtest tick par tick** fidèle à MT5 :
   - indicateurs calculés avec les formules de MetaQuotes ;
   - stops level, freeze level, marge, swaps ;
   - historique des transactions, variables globales, calendrier.
3. **18 scénarios automatiques** (rapport :
   [`tools/verify/last_report_fx.md`](tools/verify/last_report_fx.md)) :
   - SL et TP sur 100 % des trades, avec un TP exact ;
   - break-even vérifié sur chaque déplacement ;
   - risque réel ≤ 0,5 %, entrées seulement de 10 h à 13 h, sortie à 15 h ;
   - requotes, courtier IOC ou RETURN seulement, SL refusé par le courtier, stops level élevé ;
   - compte netting et petit capital ;
   - perte journalière, coupe-circuit drawdown et filtre news ;
   - redémarrage avec une position ouverte ;
   - AddressSanitizer et UBSan sur toutes les données.
4. **Validation croisée** : le moteur de recherche (Python) et l'EA réel dans l'émulateur donnent les
   mêmes chiffres.

Défauts trouvés et corrigés grâce à ces tests :
- des modifications refusées étaient renvoyées à chaque tick avec un stops level élevé ;
- le jour du Brexit, une entrée était prise avec un stop de 633 pips : d'où l'ajout du filtre de choc
  de volatilité.

**Ce qui reste à faire de votre côté.** Compilez dans MetaEditor (F7), seule vérification impossible
ici. Lancez ensuite un test dans le **Testeur de stratégie MT5** avec les données de votre courtier
(EURUSD, M5, mode « Chaque tick basé sur les ticks réels »). Puis faites tourner le robot **au moins un
mois sur un compte démo**.

```bash
tools/data/fetch_data.sh        # télécharge les données minute publiques dans data/m1
tools/verify/verify_all.sh      # compile les EA dans l'émulateur + scénarios
build/fx/emu --data data/m1/EURUSD_IS.csv --symbol EURUSD --trades trades.csv    # backtest libre
build/fx/emu ... --set InpProfile=1 --set InpRiskPercent=1.0                     # changer un paramètre
```

## 7. Limites connues

- Avantage **réel mais petit** : environ +0,02 à +0,05 R par trade. Un mois négatif est normal ; sur
  les tests, de la moitié aux deux tiers des mois sont positifs selon la période.
- Très **sensible aux frais** du courtier.
- Le filtre news ne fonctionne pas dans le testeur MT5 : c'est une limite de MetaTrader.
- La recherche est faite sur 2014-2018 et 2026. Un effet de marché peut s'affaiblir avec le temps :
  surveillez les résultats et réduisez le risque si le robot décroche durablement.

## 8. Contenu du dépôt

```
MQL5/Experts/IABot/IABot_FX_M5.mq5   ← robot Forex (EURUSD, GBPUSD)
MQL5/Experts/IABot/IABot_M5.mq5      ← robot Or (XAUUSD), version précédente, voir results/backtest_results.csv
results/                             ← résultats détaillés par paire, profil et période
tools/mql5emu/                       ← émulateur MQL5 (traducteur, API, moteur de backtest)
tools/verify/                        ← scénarios de vérification + rapports
tools/research/                      ← toute la recherche (stratégies testées, scan 24 h, filtre IA)
tools/data/                          ← téléchargement et préparation des données
```

*Ce logiciel est fourni à titre éducatif, sans garantie. Le trading sur marge comporte un risque élevé
de perte en capital.*
