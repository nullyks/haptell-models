# Pneumaatiline kuup v02

Ühes tükis prinditav **85 × 85 × 85 mm** kuup, **R15** välisservad ja
**Ø79 mm** sfääriline õõnsus ühe täispuhutava membraani jaoks. Suletud
tahu keskosas on seina nimipaksus 3 mm. Nurgad on õõnsuse kuju tõttu paksemad.

| Tahud | Välisavad ühe tahu kohta |
| --- | --- |
| Ülemine, tagumine ja vasak | 3 × Ø31,5 mm. Kahe ülemise ava keskvahe on 35 mm. |
| Parem | 2 × Ø34,5 mm, keskvahe 38 mm. |
| Ees | 2 × 64 × 28 mm horisontaalset kapslikujulist ava, nende vahel on 12 mm enne servade ümardust. |
| Alumine | 1 × Ø10 mm, keskel. |

Kokku on 14 eraldi läbivat ava. Ümaravad on 3,5 mm väiksemad kui tellija
joonisel, et säilitada joonise keskvahed ja jätta kahe ümardatud suudme vahele
nominaalselt vähemalt 2,5 mm materjali. Kapslikujulised avad ulatuvad
välisserva R15 ümardusse. Välisavadel on 0,5 mm ümardusvälja raadius ning
avakanalid ahenevad sissepoole ja suubuvad sujuvalt sfäärilisse õõnsusse.
Avade mõõdud kirjeldavad väliseid avaprofiile. Kanalite sisemised ristlõiked
ja pikkused erinevad.

Vaata [mudeli välisvaadet](../../output/pneumatic_cube/pneumatic_cube_overview.png)
ja [kahte lõiget](../../output/pneumatic_cube/pneumatic_cube_section.png).

## Prindifailid

- [Vaatamiseks mõeldud STL](../../output/pneumatic_cube/pneumatic_cube.stl).
- [Prindiasendis STL](../../output/pneumatic_cube/pneumatic_cube_print.stl), 45° serval.
- [Prusa XL ühe tööriistaga 3MF](../../output/pneumatic_cube/pneumatic_cube_xl_pla.3mf).
- [Prusa XL 5T 3MF](../../output/prusa_xl_5t_pla_04/pneumatic_cube_v02_XL5T_0p4_PLA_Tool1.3mf) ja [v02 G-code](../../output/prusa_xl_5t_pla_04/pneumatic_cube_v02_XL5T_0p4_PLA_Tool1.gcode) 0,4 mm düüsile, PLA-le ja tööriistale 1.
- [Prusa XL / PLA juhend](PRUSA_XL_PLA_JUHEND.md).

Mõlemad 3MF-id sisaldavad üht prinditavat mudelit ja kahte tugede juhisruumala.
Valitud prindiasendis oli proovivõtu järgi pikim toestamata sillalõik 4,74 mm.
Viilutatud radades jäid toed väljapoole kuubi ümbrist ja lõppesid 5,8 mm
kõrgusel. XL 5T hinnang on 10 h 50 min 31 s ja 139,74 g PLA-d, sellest
ligikaudu 1,55 g tuge. Füüsiline print, avaäärte viimistlus ja membraani
paisumine vajavad proovimist.

| Asend | Arvutuslik vaba sillalõik | Toed | Ühe tööriistaga töö aeg |
| --- | ---: | ---: | ---: |
| Tahul | 37,66 mm | 2,70 g | 10 h 13 min 51 s |
| Serval, valitud | 4,74 mm | 1,55 g | 10 h 50 min 35 s |
| Nurgal | 3,97 mm | 0,72 g | 11 h 07 min 57 s |

Valiti serv, sest algtoetus ulatub mööda serva ja prindiasend on nurgast madalam.
Sillalõik põhineb prindiradadel ning eelneva kihi ja tugede arvutuslikul
toel. Vaata [tugiradade lõiget](../../output/pneumatic_cube/pneumatic_cube_supports.png).

## Kontrollid ja kordamine

Mõlemad STL-id on pärast serialiseerimist kontrollitud. Mõlemad on ühe
ühendatud kehaga, avatud servade ja nullpindalaga kolmnurkadeta. Euleri
karakteristik −24 vastab ühe õõnsusega 14 eraldi läbivale avale.
Mudeli mõõdud, avade paigutus ja kontrollitulemused on
[validation.json](../../output/pneumatic_cube/validation.json) failis.

- [Valitud v02 arhiivirevisjon](revisions/2026-11-20_134313_71c0bcd8/).
- [Varasem v01 arhiivirevisjon](revisions/2026-11-10_194955_a4bccfb6/).

Geomeetria muutmisel käivita projekti juurkaustas esmalt \`model_archive.py\`
ja seejärel generaator. Viilutus peab minema uude ülevaatuskausta.

~~~powershell
.\.venv\Scripts\python.exe model_archive.py
.\.venv\Scripts\python.exe generate_pneumatic_cube_stl.py
.\.venv\Scripts\python.exe tools/prepare_pneumatic_print.py --output-dir .local/pneumatic_review/uus-katse
.\.venv\Scripts\python.exe tools/check_pneumatic_print.py .local/pneumatic_review/uus-katse
~~~
