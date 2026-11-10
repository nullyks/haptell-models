# Pneumaatika kuubik v01 — printimine ja viimistlus

See on üks õõnes kuubik, mitte kaks kokkupandavat poolt. Välismõõt 80 mm,
välisümardus R8; 18 ava, kitsaimast kohast Ø27 mm. Avade sisemised ja välimised
servad on mudelis R1,6 ümardusega. Õhupalli vastupidavust ei ole veel katsetatud.

## Printimine

1. Ava `output/pneumatic_cube/pneumatic_cube_xl_pla.3mf` **projektina koos seadetega**.
   Mudel on juba 45° servale kallutatud. Ära aseta suurt külge vastu alust.
2. Kontrolli tegelikku printerit ja materjali: salvestatud projekt on Prusa XL IS,
   standardne 0,4 mm düüs, Generic PLA. Muude seadmete/materjalide jaoks viiluta uuesti.
3. Säilita 0,15 mm kihid, 5 perimeetrit, 100% seinatäide ja 8 mm brim.
   Seesmine õõnsus ei saa täidet, sest see on STL-is tühi.
4. Säilita **Snug-toed ainult aluselt ja ainult toe lubaja piirkonnas**.
   Automaatne toe valik peab jääma välja. Projektis on üks toe lubaja alumise
   serva juures ja üks sisemuse blokeerija; need ei ole kuubiku prinditavad osad.
5. Toe vahed: üleval/all 0,25 mm, külgsuunas 0,40 mm; kontaktkihid 2/2,
   joontevahe 0,30 mm; põhitoe joontevahe 4 mm. Rafti ei kasutata.
6. Eelvaates peavad toed jääma alumise serva alla, umbes esimese 5,8 mm juurde.
   Ülejäänud kuubiku sees ei tohi olla tugipuid ega võret. Kui näed neid,
   taasta projekt ja selle seaded enne printimist.

Mõõt prindialusel on umbes 80 × 106,51 mm, kõrgus 106,51 mm. Hinnang:
8 h 35 min, 108,95 g PLA, sellest 1,27 g tuge. Düüs 230 °C esimesel kihil,
edasi 220 °C; alus 60 °C. Sillad 20 mm/s ja 100% ventilaator.

Ainult STL ja INI ei taasta toe juhisruumalasid. Kasuta 3MF-i või loo uus projekt
`tools/prepare_pneumatic_print.py` abil ning kontrolli tegelikud prindirajad.
`pneumatic_cube.stl` on tavapärases vaatamisasendis; `pneumatic_cube_print.stl`
on prindiks pööratud. Korraga prinditakse ainult üks kuubik, mitte mõlemad STL-id.

## Tugede eemaldamine

Lase kuubikul jahtuda. Eemalda brim ja väikesed välimised algustoed väljastpoolt,
toetades seina sõrmedega. Valitud failis pole sisemisi tugesid, mida tuleks
aukudest välja murda. Ära lõika ega kanguta avade vahelist kitsamat materjalisilda.

Kui kasutasid oma seadeid, kontrolli taskulambi abil kõik 18 ava ja kogu sisemus.
Kõik toe tükid ning lahtised niidid peavad olema eemaldatud enne õhupalli sisestamist.

## Servade viimistlus enne õhupalli

Ümar geomeetria üksi ei taga, et FDM-prindi pind membraani ei hõõru.

1. Eemalda niidid, õmblusenukid ja toe jäägid. Viimistle **iga ava mõlemat serva**
   ning ümbrust; säilita olemasolev ümar profiil, ära lõika uut teravat faasi.
2. Silu vajaduse korral peene abrasiiviga või painduva lihvimispadjaga. Hoia
   padja all pehmet ümarat tuge, et mitte teha avaservale lamedat teravat rantti.
   Aukudest pääseb sisemiste servade juurde väikese ümara tööriistaga.
3. Kontrolli kogu kontakti teed sõrme ja pehme õhukese kangaga. Kui kangas
   takerdub või tunned karedat nukki, jätka silumist. Eemalda lihvimistolm.
4. Sisesta tühi õhupall ühe ava kaudu. Selle kaela või vooliku võib juhtida
   sobivast olemasolevast avast välja; eraldi niplit ega klambrit pole mudelisse lisatud.
5. Esimesel katsel täida järk-järgult, jälgides kõiki osaliselt välja pressivaid
   piirkondi. Kontrolli pärast tühjendamist membraanil hõõrdumisjälgi.

Ballooni materjali, seinapaksust, töörõhku ega soovitud väljasopistuse ulatust
pole määratud. Mudelil ei ole kinnitatud rõhu- ega vastupidavusnäitu.
Esimene test peab hindama, kas valitud avasuurus ja viimistlus sobivad tegeliku õhupalliga.

Kirjuta tulemus revisjoni `2026-11-10_194955_a4bccfb6/print_notes.md` faili:
printer/materjal, toe eemaldamine, sise- ja välispinna kvaliteet, servade
viimistlus, membraani tüüp ning katse tulemus. Arhiivi STL-i, lähtekoodi ja
manifesti ei muudeta; uus kuju saab uue revisjoni.
