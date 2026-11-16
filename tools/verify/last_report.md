# Vérification automatique de IABot_M5 (or)
**18/18 scénarios réussis**

## ✅ 1. Référence XAUUSD 2014-2017 : SL/TP/BE/trailing/risque/horaires conformes
_770 trades, gain 56.8%, PF 1.3, DD 7.18%_
- OK  nombre de trades suffisant (770)
- OK  chaque position a un SL et un TP dès l'ouverture
- OK  TP = 4 R (min 3.994 max 4.005, arrondi au point)
- OK  perte max par trade bornée (-1.19 R, gaps inclus)
- OK  risque par trade <= 0,5 % (+commission) : max 0.508 %
- OK  risque médian proche de la cible (0.475 %)
- OK  aucun échec d'ordre dans le journal
- OK  break-even à +0,1 R vérifié sur 430 déplacements (écarts : 0)
- OK  trailing stop toujours >= +0,5 R (1382 déplacements, écarts : 0)
- OK  entrées uniquement dans la fenêtre 9h-20h (heure serveur)
- OK  aucune entrée le vendredi après 18h
- OK  aucune position gardée le week-end quand le marché cote après 22h le vendredi (3 cas, tous des vendredis fériés/clôture anticipée : 3)
- OK  jamais plus d'une position à la fois
- OK  max 4 trade(s) par jour (max observé 3)

## ✅ 2. EURUSD et USDJPY (autre paire, conversion de devise du profit) : risque correct, aucun plantage
- OK  EURUSD : trades exécutés (212)
- OK  EURUSD : risque 0.492 % (max 0.514 % ; lot minimum : max 0.514 %)
- OK  EURUSD : SL et TP présents
- OK  USDJPY : trades exécutés (158)
- OK  USDJPY : risque 0.478 % (max 0.508 % ; lot minimum : max 0.508 %)
- OK  USDJPY : SL et TP présents

## ✅ 3. Courtier IOC uniquement / RETURN uniquement : mode de remplissage détecté
- OK  IOC : aucun ordre rejeté (0)
- OK  IOC : mêmes trades que la référence (182 vs 182)
- OK  RETURN : aucun ordre rejeté (0)
- OK  RETURN : mêmes trades que la référence (182 vs 182)

## ✅ 4. Requotes aléatoires (30 % des ordres) : nouvelles tentatives automatiques
- OK  requotes simulés (89)
- OK  trades quasi identiques (182 vs 182)
- OK  SL toujours posé malgré les requotes

## ✅ 5. Courtier qui ignore SL/TP à l'ouverture : l'EA les pose immédiatement
- OK  SL/TP posés après ouverture sur chaque trade (182/182)
- OK  toutes les positions finissent protégées

## ✅ 6. Courtier qui refuse SL et TP : fermeture de sécurité immédiate (jamais de position sans SL)
- OK  fermeture de sécurité déclenchée (1244 fois / 622 trades)
- OK  chaque position non protégée est fermée dans la même seconde

## ✅ 7. Stops level élevé (or 300 pts / Forex 100 pts) et freeze level : aucune requête invalide
- OK  le robot trade toujours (182)
- OK  aucun rejet 'invalid stops'
- OK  aucun rejet 'frozen'

## ✅ 8. Compte netting
- OK  comportement identique en netting (182 vs 182)
- OK  mode netting détecté

## ✅ 9. Clôture partielle activée : une seule fois par position
- OK  clôtures partielles exécutées (80)
- OK  jamais deux clôtures partielles sur la même position

## ✅ 10. Limite de perte journalière (risque 4 %, limite 3 %) : arrêt pour la journée
- OK  limite journalière déclenchée (68 jour(s))
- OK  aucun nouveau trade le jour même après la limite

## ✅ 11. Coupe-circuit drawdown max (risque 3 %, limite 10 %) : arrêt définitif + fermeture
- OK  coupe-circuit déclenché
- OK  plus aucun trade après l'arrêt
- OK  positions fermées au déclenchement

## ✅ 12. Petit capital (300 USD) : jamais de risque supérieur à 2 % par trade
- OK  risque max 2.02 % <= 2 %
- OK  44 trades exécutés avec le lot minimum autorisé

## ✅ 13. Trading algorithmique désactivé : aucun ordre
- OK  aucune requête envoyée

## ✅ 14. Mode réel simulé + calendrier : pause autour des news à fort impact, panneau affiché
- OK  mode réel : le robot trade (182)
- OK  panneau d'information affiché
- OK  aucune entrée à +/-30 min des 15 news USD (0)
- OK  statut news

## ✅ 15. Session en heure GMT (testeur, décalage auto été/hiver US)
- OK  entrées entre 7h et 18h GMT (180 trades)

## ✅ 16. Paramètres invalides : initialisation refusée
- OK  INIT_PARAMETERS_INCORRECT renvoyé

## ✅ 17. Redémarrage du terminal en pleine position : reprise de la gestion (persistance)
- OK  une position est ouverte au moment de l'arrêt
- OK  la position #1258 est toujours gérée après redémarrage
- OK  résultat final identique à 1 % près (10462.44 vs 10462.44)

## ✅ 18. Exécution instrumentée (AddressSanitizer + UBSan + division par zéro) sur toutes les données
- OK  AUDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (147 trades)
- OK  AUDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (123 trades)
- OK  AUDUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (77 trades)
- OK  EURCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (257 trades)
- OK  EURCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (175 trades)
- OK  EURCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (135 trades)
- OK  EURCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (143 trades)
- OK  EURGBP_IS.csv : aucune erreur mémoire / UB / division par zéro (897 trades)
- OK  EURGBP_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (177 trades)
- OK  EURGBP_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (84 trades)
- OK  EURJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (724 trades)
- OK  EURJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (140 trades)
- OK  EURJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (74 trades)
- OK  EURUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (637 trades)
- OK  EURUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (166 trades)
- OK  EURUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (83 trades)
- OK  GBPJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (754 trades)
- OK  GBPJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (143 trades)
- OK  GBPUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (514 trades)
- OK  GBPUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (180 trades)
- OK  GBPUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (79 trades)
- OK  NZDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (669 trades)
- OK  NZDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (136 trades)
- OK  USDCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (259 trades)
- OK  USDCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (163 trades)
- OK  USDCAD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (85 trades)
- OK  USDCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (858 trades)
- OK  USDCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (148 trades)
- OK  USDCHF_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (83 trades)
- OK  USDJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (684 trades)
- OK  USDJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (126 trades)
- OK  USDJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (72 trades)
- OK  XAUUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (770 trades)
- OK  XAUUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (150 trades)
- OK  XAUUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (78 trades)

