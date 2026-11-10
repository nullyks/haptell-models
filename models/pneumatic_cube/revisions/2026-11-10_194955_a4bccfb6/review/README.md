# Pneumaatika kuubik — v01

Ühes tükis prinditav, seest tühi **80 × 80 × 80 mm kuubik, R8 välisservadega**.
Igal kuuel küljel on kolm membraani ehk õhupalli osaliseks väljasurumiseks
mõeldud ava. Mudelil ei ole poolitusõmblust, lukke, ventilaatorihoidjat,
Peltieri kontaktpindu ega muid sisemisi lisadetaile.

See on eraldi mudelipere. Testprinti minev Peltieri/ventilaatori kuubik v07 ja
selle prindifailid jäävad muutmata.

## Mõõdud ja ümardused

| Omadus | Väärtus |
| --- | --- |
| Välismõõt | 80 × 80 × 80 mm |
| Välisservad / sisenurgad | R8 / R4 mm |
| Seina nimipaksus | 4 mm |
| Avad | 18 kokku, 3 igal küljel |
| Ava kitsaim läbimõõt | Ø27 mm |
| Ava serv mõlemal pool seina | R1,6 mm ringjooneline ümardus |
| Ava suudme läbimõõt | Ø30,2 mm |
| Kitsaim sild suudmete vahel | 3,2 mm |
| Sirge silindriline osa seina keskel | 0,8 mm |

Kohalikud avakeskmed iga külje keskme suhtes: (-16,7; +16,7),
(+16,7; +16,7), (0; -16,7) mm. Paigutus on kaks üleval, üks all.
Ülemiste avade keskmete vahe on 33,4 mm, samuti ridade kõrguste vahe.
Kõik avasuudmed jäävad R8 serva ümardusest sissepoole, tasasele küljeosale.

Tellija joonisel olid läbimõõt ja ülemiste keskmete vahe mõlemad 35 mm:
nii oleks materjalisild null ning serva ümardused ühineksid. **Kasutaja lubas
2026-11-10 aukude mõõtu ja paigutust kohandada, säilitades 80 mm / R8.**
Ø27 mm ja R1,6 valik jätab eraldi ümarate avade vahele pideva materjali.
Joonise materjalisoovitus ei ole PLA/PETG/ABS prindikatse ega kohustus neid kõiki kasutada.

Ümardused on mõlemal pool seina; need ei ole lihtsalt 45° faasid. Generaator
kasutab mõlemas servas silindri ja seinapinnaga puutujas jätkuvaid veerandkaari.
STL lähendab neid väikeste tahkudega. Prindikihtide, õmbluse ja toe jääkide
karedus tuleb enne membraani kasutamist eraldi eemaldada.

## Valitud printimine

**Servale toetuv asend, 45° ümber X-telje**, 0,15 mm kihiga. Prindiks mõeldud
STL on juba pööratud. Selle ulatus on umbes 80 × 106,51 × 106,51 mm.
Kuubiku tegelik väliskuju jääb 80 mm kõigil kolmel teljel.

Valmis 3MF sisaldab üht prinditavat kuubikut ning kahte mitteprinditavat
toe juhisruumala: välimise algustoe lubaja ja sisemuse toe blokeerija.
Automaatne toe valik on väljas. Snug-toed tekivad ainult alumise serva alla;
**lõplike prindiradade kontrollis kuubiku sees tugesid ei ole**. Neid ei pea
hiljem Ø27 mm aukude kaudu välja murdma. Välimised toed saab eemaldada väljast.

PrusaSlicer 2.9.7 / Prusa XL IS standardne 0,4 mm düüs / Generic PLA:

- 0,15 mm kiht, esimene 0,20 mm; 5 perimeetrit, 6/6 täiskihti.
- Seinamaterjali täide 100% Rectilinear; STL-is määratud õõnsus jääb tühjaks.
- 8 mm väline brim, ilma raftita.
- Snug ainult aluselt, ainult projektis lubatud välises alguspiirkonnas.
- Toe kontaktvahe üleval/all 0,25 mm; XY vahe 0,40 mm.
- Kontaktkihid 2/2, joontevahe 0,30 mm; toe põhijoonte vahe 4 mm.
- Sillad 20 mm/s, jahutus 100%; välisperimeeter 25 mm/s.
- Generic PLA: düüs esimene kiht 230 °C, edasi 220 °C; alus 60 °C.

Lõplik hinnang: **108,95 g / 8 h 34 min 47 s**, sellest toed **1,27 g**.
Toed ulatuvad kuni Z=5,8 mm. See on viilutaja hinnang, mitte mõõdetud prinditulemus.

**Ava 3MF projektina koos seadetega.** Paljas STL koos INI-ga ei sisalda toe
juhisruumalasid. Automaatsete tugede sisselülitamine võib täita sisemuse tugedega.
Teise printeri, düüsi, tööriistaseadistuse või materjali korral viiluta uuesti.

## Võrreldud asendid

Kuus katset: külg, serv ja nurk all, igal automaatne Organic ning ainult välise
algustoe variant. Kõik katsefailid säilivad valitud revisjoni `review/` all.

| Asend, väline algustugi | Tugematerjal | Aeg | Kontrolli tulemus |
| --- | --- | --- | --- |
| Külg all | 1,58 g | 7 h 35 min | Siselaes umbes 42,8 mm vaba silla lõik; kõrvale jäetud |
| Serv all, 45° | 1,27 g | 8 h 35 min | Valitud; sisemisi tugesid 0, hinnatud vaba silla lõik kuni 1,94 mm |
| Nurk all | 0,49 g | 9 h 04 min | Vähem tuge, kuid väiksem algne toetusala ja kõrgem/pikem print |

Serva valik on kompromiss stabiilsuse, aja ja tugede vahel. Nurgaasend kasutas
0,78 g vähem tuge, kuid algne kontakt on punktja ümarnurga all ning prindikõrgus
126,85 mm. Servaasend annab pikema kontaktala ja madalama prindi.

Automaatne Organic samas servaasendis kasutas umbes 24,73 g tuge ning tekitas
tugesid ka õõnsusse. Valitud variant vähendab tugematerjali umbes 95% ja väldib
nende sisemusest eemaldamise probleemi. Valiku aluseks on prindirajad;
toe eemaldamisjõud ja valmis pinna kvaliteet vajavad testprinti.

Sildade analüüs proovib 0,4 mm sammuga nominaalset eelmise kihi materjali ja
tegelikke toe kontaktiradu. Üks pikk G-code liikumine võib läbida mitut toetatud
ala; seetõttu hinnatakse vaba lõiku, mitte ainult käsu kogupikkust.
See arvutus ei tõesta füüsilise silla ega membraani kvaliteeti.

## Failid ja kontrollid

- Generaator: `generate_pneumatic_cube_stl.py`.
- Viimased failid: `output/pneumatic_cube/`.
- `pneumatic_cube.stl`: kuubik tavapärases vaatamisasendis.
- `pneumatic_cube_print.stl`: valitud 45° prindiasend.
- `pneumatic_cube_xl_pla.3mf`: eelistatud printimisprojekt, seaded ja toe juhised kaasas.
- Sama nimega G-code, `prusa_xl_04_pla.ini`, `print_review.json`, `toolpath_checks.json`.
- `validation.json`, mudeli vaated ning tegelike tugiradade joonis.
- [Valitud v01 revisjon](revisions/2026-11-10_194955_a4bccfb6/).
- [Esimene nurgaasendi katse](revisions/2026-11-10_194054_d3c1d48b/).
- [Eestikeelne printimise ja membraani paigaldamise juhend](PRUSA_XL_PLA_JUHEND.md).

Mõlemad STL-id on pärast salvestamist kontrollitud: üks ühendatud kinnine
keha, positiivne ruumala, null lahtist/mitte-manifold serva ja null kõdunud
kolmnurka. Euleri karakteristik -32 vastab 18 eraldi läbivale avale ühe
õõnsusega koorikus. 3MF sisaldab täpselt üht prinditavat mudelit; selle
tipukoordinaadid vastavad prindi-STL-ile alla 0,000003 mm veaga.

## Edasiarendus

Kasuta selle arvuti `.venv\Scripts\python.exe` faili. Enne kuju muutmist käivita
`model_archive.py`; seejärel generaator tavapäraselt. Uus mudel arhiveeritakse
oma mudelipere alla. Näiteks:

```powershell
.\.venv\Scripts\python.exe generate_pneumatic_cube_stl.py
.\.venv\Scripts\python.exe tools\prepare_pneumatic_print.py --output-dir .local\pneumatic_review\uus_katse
.\.venv\Scripts\python.exe tools\check_pneumatic_print.py .local\pneumatic_review\uus_katse
.\.venv\Scripts\python.exe -m pytest -q
```

Vali iga kord uus ülevaatekaust. Geomeetria muutmisel kontrolli uuesti toe
piirkondi, sildasid ja seda, et ükski tugi ei satuks sisemusse.

## Allikad

- [Tellija joonis](references/2026-11-10_client_reference.png).
- [Prusa: kuju ja printimisasendi mõju](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).
- [Prusa: toe seaded ja käsitsi valitavad piirkonnad](https://help.prusa3d.com/article/support-material_1698).
- [Prusa: Organic-toed](https://help.prusa3d.com/article/organic-supports_480131).
