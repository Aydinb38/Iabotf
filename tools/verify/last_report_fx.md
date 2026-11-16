# Vérification automatique de IABot_FX_M5 (Forex)
**18/18 scénarios réussis**

## ✅ 1. Référence EURUSD 2014-2017 : SL/TP/BE/trailing/risque/horaires conformes
_1005 trades, gain 53.0%, PF 1.19, DD 5.97%_
- OK  nombre de trades suffisant (1005)
- OK  chaque position a un SL et un TP dès l'ouverture
- OK  TP = 3 R (min 2.990 max 3.011, arrondi au point)
- OK  perte max par trade bornée (-1.00 R, gaps inclus)
- OK  risque par trade <= 0,5 % (+commission) : max 0.529 %
- OK  risque médian proche de la cible (0.499 %)
- OK  aucun échec d'ordre dans le journal
- OK  break-even à +0,1 R vérifié sur 225 déplacements (écarts : 0)
- OK  trailing désactivé par défaut : aucun déplacement de trailing
- OK  entrées uniquement dans la fenêtre 10h-13h (heure serveur)
- OK  toutes les positions fermées au plus tard à 15h le jour même
- OK  aucune entrée le vendredi après 18h
- OK  aucune position gardée le week-end quand le marché cote après 22h le vendredi (0 cas, tous des vendredis fériés/clôture anticipée : 0)
- OK  jamais plus d'une position à la fois
- OK  max 1 trade(s) par jour (max observé 1)

## ✅ 2. GBPUSD et EURJPY (autre paire, conversion de devise du profit) : risque correct, aucun plantage
- OK  GBPUSD : trades exécutés (256)
- OK  GBPUSD : risque 0.482 % (max 0.509 % ; lot minimum : max 0.509 %)
- OK  GBPUSD : SL et TP présents
- OK  EURJPY : trades exécutés (256)
- OK  EURJPY : risque 0.480 % (max 0.514 % ; lot minimum : max 0.514 %)
- OK  EURJPY : SL et TP présents

## ✅ 3. Courtier IOC uniquement / RETURN uniquement : mode de remplissage détecté
- OK  IOC : aucun ordre rejeté (0)
- OK  IOC : mêmes trades que la référence (255 vs 255)
- OK  RETURN : aucun ordre rejeté (0)
- OK  RETURN : mêmes trades que la référence (255 vs 255)

## ✅ 4. Requotes aléatoires (30 % des ordres) : nouvelles tentatives automatiques
- OK  requotes simulés (195)
- OK  trades quasi identiques (255 vs 255)
- OK  SL toujours posé malgré les requotes

## ✅ 5. Courtier qui ignore SL/TP à l'ouverture : l'EA les pose immédiatement
- OK  SL/TP posés après ouverture sur chaque trade (255/255)
- OK  toutes les positions finissent protégées

## ✅ 6. Courtier qui refuse SL et TP : fermeture de sécurité immédiate (jamais de position sans SL)
- OK  fermeture de sécurité déclenchée (510 fois / 255 trades)
- OK  chaque position non protégée est fermée dans la même seconde

## ✅ 7. Stops level élevé (or 300 pts / Forex 100 pts) et freeze level : aucune requête invalide
- OK  le robot trade toujours (255)
- OK  aucun rejet 'invalid stops'
- OK  aucun rejet 'frozen'

## ✅ 8. Compte netting
- OK  comportement identique en netting (255 vs 255)
- OK  mode netting détecté

## ✅ 9. Clôture partielle activée : une seule fois par position
- OK  clôtures partielles exécutées (44)
- OK  jamais deux clôtures partielles sur la même position

## ✅ 10. Limite de perte journalière (risque 4 %, limite 3 %) : arrêt pour la journée
- OK  limite journalière déclenchée (71 jour(s))
- OK  aucun nouveau trade le jour même après la limite

## ✅ 11. Coupe-circuit drawdown max (risque 3 %, limite 10 %) : arrêt définitif + fermeture
- OK  coupe-circuit déclenché
- OK  plus aucun trade après l'arrêt
- OK  positions fermées au déclenchement

## ✅ 12. Petit capital (300 USD) : jamais de risque supérieur à 2 % par trade
- OK  risque max 1.98 % <= 2 %
- OK  244 trades exécutés avec le lot minimum autorisé

## ✅ 13. Trading algorithmique désactivé : aucun ordre
- OK  aucune requête envoyée

## ✅ 14. Mode réel simulé + calendrier : pause autour des news à fort impact, panneau affiché
- OK  mode réel : le robot trade (255)
- OK  panneau d'information affiché
- OK  aucune entrée à +/-30 min des 15 news USD (0)
- OK  statut news

## ✅ 15. Session en heure GMT (testeur, décalage auto été/hiver US)
- OK  entrées entre 8h et 11h GMT (255 trades)

## ✅ 16. Paramètres invalides : initialisation refusée
- OK  INIT_PARAMETERS_INCORRECT renvoyé

## ✅ 17. Redémarrage du terminal en pleine position : reprise de la gestion (persistance)
- OK  une position est ouverte au moment de l'arrêt
- OK  la position #1318 est toujours gérée après redémarrage
- OK  résultat final identique à 1 % près (10274.86 vs 10274.86)

## ✅ 18. Exécution instrumentée (AddressSanitizer + UBSan + division par zéro) sur toutes les données
- OK  AUDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  AUDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  AUDUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURGBP_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  EURUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (1005 trades)
- OK  EURUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (192 trades)
- OK  EURUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (109 trades)
- OK  GBPJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  GBPUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (1004 trades)
- OK  GBPUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (190 trades)
- OK  GBPUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (108 trades)
- OK  NZDUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  NZDUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCAD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDCHF_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  USDJPY_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_IS.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_OOS2018.csv : aucune erreur mémoire / UB / division par zéro (0 trades)
- OK  XAUUSD_OOS2026.csv : aucune erreur mémoire / UB / division par zéro (0 trades)

