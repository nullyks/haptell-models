# v07 kuubik — Prusa XL / PLA printimisjuhend

Kuubik on 80 x 80 x 80 mm, R8 ümardustega, kahest poolest. Sees on ainult
ventilaatori kinnitus ning poolte lukustus ja joondus. Peltieri kontaktpinnad
on säilinud 45 x 45 mm ja 1,2 mm paksusena. See versioon ootab testprinti.

## Ava valmis projektid

Kasuta kaustast `output/rounded_cube_box/`:

1. `rounded_cube_bottom_xl_pla.3mf` — põhi, Snug-toed.
2. `rounded_cube_lid_xl_pla.3mf` — kaas, Organic-toed.

Ava fail **projektina koos seadetega**, mitte ainult mudelina. Projekt sisaldab
toe piirkondi: põhjal 15, kaanel 8. Need on eemaldatavate tugede juhised,
mitte kuubiku lisadetailid. Ainult STL ja INI importimine ei taasta neid tugesid.

Mõlemad STL-id on juba õiges asendis: **ava ja ühendusserv all, suur ümardatud
välispind üleval**. Ära pööra põhja v06 juhendi järgi ümber. Põhja prindikõrgus
on 46,8 mm, kaanel 40 mm. Ära prindi koostu eelvaate STL-i.

Valmis G-code on Prusa XL Input Shaper standardse 0,4 mm düüsi ja Generic PLA
jaoks. Teise printeri, düüsi, materjali või tööriistade seadistuse korral vali
oma tegelik printer ning viiluta 3MF uuesti, säilitades selle toe piirkonnad.

## Kontrollitud seaded

| Seade | Mõlemad pooled |
| --- | --- |
| Kihi kõrgus | 0,20 mm STRUCTURAL |
| Perimeetrid | 4 |
| Alumised / ülemised täiskihid | 6 / 6 |
| Täide | 15% Grid |
| Brim | 5 mm väljapoole |
| PLA düüs / alus | 230 °C esimene, 220 °C edasi / 60 °C |
| Toe ülemine / alumine kontaktvahe | 0,25 / 0,25 mm |
| Toe vahe külgsuunas | 0,50 mm |
| Kontaktkihi joontevahe | 0,30 mm |
| Toe mustri joontevahe | 5 mm |
| Sillad | 90°, 25 mm/s, ventilaator 100% |
| Automaatne toe valik | Väljas; kasutatakse projektis olevaid toe piirkondi |

Põhi: **Snug**, toetamine lubatud kõikjal, kontaktkihid üleval/all 2/2.
Kaas: **Organic**, toed ainult aluselt, kontaktkihid 3/2, okste vahe 2 mm,
tiputihedus 30%. Hoia põhja ja kaane profiilid eraldi:
`prusa_xl_04_pla_bottom.ini` ning `prusa_xl_04_pla.ini`.

| Osa | Aja hinnang | PLA kokku | Sellest toed |
| --- | --- | --- | --- |
| Põhi | 5 h 28 min | 95,62 g | 22,21 g |
| Kaas | 4 h 35 min | 70,46 g | 13,90 g |
| Kokku | ligikaudu 10 h 03 min | 166,08 g | 36,11 g |

Need on viilutaja hinnangud. Võrdluseks kulus sama asendi automaatsetele
Snug-tugedele 59,90 g; valitud lahenduses on neid ligi 40% vähem.

## Miks just nii printida?

Suure R8 ümarduse alumine osa ulatuks välispinnaga alus allapoole printides
järsult üle eelmiste kihtide. Välised toed või üleulatuse vajumine võivad
nähtava pinna rikkuda. Valitud asendis puudutavad toed sisepindu ja varjatud
ühendusserva. Suured välispinnad ning ümar üleminek jäävad ülespoole.

Sisepinna alla on jäetud hõre tugiribade võrk, mis lühendab lae sildu. Põhjal
toetatakse eraldi ventilaatori külgi, kruvikõrvu, istmeid ja ühendusserva.
Kaane Organic-toed võtavad vähem materjali. Põhja Organic-katse jättis õhukese
kontaktpinna serva liiga pika vaba lõigu; seetõttu jäi põhja jaoks Snug.

`prusa_v07_supports.png` näitab tegelike tugiradade eestvaadet koos mudeli lõikega: roheline on
eemaldatav tugi, oranž selle kontaktkihid, tumesinine kuubiku lõikejoon.
See ei ole füüsilise pinnakvaliteedi ega toe eemaldatavuse kinnitus.

## Pärast printimist

1. Lase detailidel jahtuda. Eemalda brim ja toed avatud poole kaudu väikeste
   tükkidena. Toeta ventilaatori hoidjat käega; ära kanguta selle vastu.
2. Puhasta ühendusserv, keelte vahed ja lukupesad. Ära lõika ära kaheksat
   püsivat lukustuskeelt, ventilaatori kandureid ega joondusribasid.
3. Kontrolli 1,2 mm Peltieri kontaktpindu: need peavad jääma terveks.
4. Proovi ventilaatorit enne kuubiku sulgemist. Nominaalne korpus on 50 x 50 mm,
   sügavusega kuni 12 mm. Mõõda tegelik kinnitusavade vahe; mudelis eeldatakse
   40 mm. Kasuta sobiva pikkusega M3 kruvisid, mutreid, seibe ja vahedetaile.
5. Hoia juhtmed tiivikust ja lukkudest eemal. Joonda pooled ning suru need
   sirgelt kokku, ilma keeramata. Kontrolli, et kõik kaheksa lukku sulguvad.
6. Esimesel katsel hinda sulgumist ja avanemist ettevaatlikult. Avades vabasta
   serva järk-järgult õhukese plastkiiluga, mitte kõiki lukke korraga rebides.

Uus lukustus on kavandatud tugevamaks, kuid selle jõud ja korduva avamise
vastupidavus pole mõõdetud. Pane testprindi tulemus vastava revisjoni
`print_notes.md` faili: printer/materjal, avamise raskus, toe eemaldamine,
välispinna kvaliteet ning ventilaatori sobivus.

## Uuesti genereerimine

Kasuta selle arvuti `.venv\Scripts\python.exe` faili. Enne geomeetria muutmist
käivita `model_archive.py`; seejärel generaator tavapäraselt. `tools/slice_models.py`
loob uude `.local/slicing/` kausta uued 3MF-id koos toe piirkondade ja
sisseehitatud seadetega. Uue kuju korral kontrolli uuesti ka tugede asukohti
ja prindiradu. Vanad katsemudelid ning prindifailid jäävad arhiivi alles.

Prusa juhised: [kuju ja üleulatused](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135),
[toed](https://help.prusa3d.com/article/support-material_1698),
[Organic-toed](https://help.prusa3d.com/article/organic-supports_480131).
