# Kohalik arenduskeskkond ja projekti ülevaade

Üle vaadatud 2026-11-10. Aluseks on `master`, commit
`0d6d2028a191239ee7cfdcdc31c748a37b358afe`.

Pärast esialgset ülevaatust paigaldatud arendustööriistad ja lisatud
kontrollikäsud on kirjeldatud [tööriistade juhendis](development_tools.md).

## Kohalik keskkond

- Repo: `C:\Users\Nullyks\Documents\ChatGPT\Haptell models`
- GitHub: <https://github.com/nullyks/haptell-models>
- `origin` on seadistatud; kohalik `master` jälgib `origin/master` haru.
- Täielik ajalugu, kaugserveri ajaloolised harud ning sildid `v01` ja `v02`
  on kohalikus kloonis olemas.
- Projekti `.venv`: Python 3.12.16, NumPy 2.5.4, manifold3d 3.5.4.
  Ka `pip` on keskkonnas olemas ning sõltuvuste kontroll läbis edukalt.
- Arvuti vaikimisi `python` on 3.9.1. Kasuta selle projekti jaoks allpool
  näidatud `.venv` Pythonit; süsteemi vaikimisi Pythonit ei muudetud.

Käsud käivitatakse repo juurkaustas. Keskkonna aktiveerimine ei ole vajalik:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe generate_rounded_cube_box_stl.py
```

## Mudeliperekonnad

| Pere | Kehtiv generaator / versioon | Oluline seis |
| --- | --- | --- |
| Muna | `generate_egg_box_stl.py`, v03 | 90 mm läbimõõt, 130 mm pikkus; viis ühesugust 10 × 4,05 mm haptikamootori pesa. Kolm ümber ülemise poole ning üks kummaski tipus. |
| Balance-shift muna | `generate_balance_shift_stl.py`, balance-shift-v03-simple-ms24-mount | Kasutab muna geomeetria abifunktsioone. Kaks lihtsat servokinnituslatti; massikeskme õla raadius 29,4 mm. Väljastab ainult kaks prinditavat poolt. |
| Ümardatud kuup | `generate_rounded_cube_box_stl.py`, v06-reinforced-open-up-bottom | 76 × 76 × 76 mm, R2,5, neli klõpslukku, ventilaatori ja elektroonika kinnitused. Viimane muudatus tugevdas põhja kinnitusi ja muutis põhja prindisuuna avausega üles. |
| Perforeeritud sfäär | `generate_perforated_sphere_stl.py`, v03 | 91 mm sfäär; kuus külgava ja peidetud keermesliide. |

Muna generaator koostab kolmnurkvõrgu NumPy abil. Balance-shift kasutab sama
võrgu- ja profiililoogikat. Kuup ja sfäär kasutavad ruumiliste kehade
ühendamiseks/lõikamiseks `manifold3d` teeki. Mõõdud on generaatorite alguses
millimeetrites; eraldi kasutajaliidest ega parameetrifaili ei ole.

`output/` hoiab viimaseid tööfaile. `models/<pere>/revisions/` on püsiv
katsetuste arhiiv koos STL-ide, lähtekoodi ja kontrollsummadega.
`model_archive.py` rakendab kõigile neljale generaatorile automaatset
arhiveerimist enne ja pärast genereerimist.

## Edasiarenduse töökorraldus

1. Loe [AGENTS.md](../AGENTS.md) ja vastava pere kehtiv üleandmisjuhis.
2. Alusta ajutist `codex/<muudatuse-nimi>` haru ajakohasest `master` harust.
3. Enne geomeetria muutmist säilita olemasolev seis:

   ```powershell
   .\.venv\Scripts\python.exe model_archive.py
   ```

4. Muuda generaatorit ja käivita vastav skript tavapäraselt. Arhiveerimist
   ei tohi vahele jätta. STL-e käsitsi ei muudeta.
5. Kontrolli mõõte, võrgu kvaliteeti, koostu sobivust ja mudelipõhiseid
   nõudeid. Kuubi geomeetria muutmisel tuleb uuendada ka viilutatud
   3MF/G-code faile ning kontrollida õiget prindiprofiili.
6. Generaator, uued tööfailid ja uued arhiivikirjed kuuluvad samasse
   muudatusse. Olemasolevaid arhiivifaile ega ajaloolisi Git-viiteid ei muudeta.

Kehtivad juhised:

- Muna: [v03 seis](v03_current_state.md).
- Balance-shift: [praegune seis](balance_shift_current_state.md).
- Kuup: [mudeli seis](../models/rounded_cube_box/README.md) ja
  [Prusa XL / PLA juhend](../models/rounded_cube_box/PRUSA_XL_PLA_JUHEND.md).
- Sfäär: [geomeetria ja printimine](perforated_sphere_printing.md).

Kuubi vana `docs/rounded_cube_printing.md` kirjeldab ajaloolist 91 mm
keermestatud varianti. Praeguse kuubi README pealkirjas olev v04 on samuti
vananenud; generaator ja juhise põhisisu kirjeldavad v06. Vanemates muna
üleandmisjuhistes nimetatud arendusharud on ajaloolised viited; uus töö algab
ühisest `master` harust.

## Kohaliku kontrolli tulemused

- Kõik neli generaatorit laaditi ja käivitati edukalt eraldi kontrollkaustas
  `.git/local-check/`, kasutades muutmata lähtekoodi ja tavalist
  arhiveerimisega käivitusviisi.
- Kõik 11 genereeritud STL-faili olid baithaaval identsed repo vastavate
  `output/` failidega. Projekti olemasolevaid väljundeid ei kirjutatud üle.
- Kõigi 31 arhiiviversiooni manifestides ning kuubi ülevaatuse
  kontrollsummade failis kontrolliti kokku 306 failiviidet; lahknevusi ei olnud.
- Kuubi sisseehitatud kontrollid läbisid: üks ühendatud keha kummagi poole
  kohta, koostu mõõt 76 mm igal teljel, poolte ja nominaalsete komponentide
  kokkupõrgete puudumine, komponentide sisestusteed ning 1,2 mm termopadjad.
- Täiendavas salvestatud STL-failide kontrollis olid kuubi ja sfääri
  prinditavad pooled ilma avatud servade, nullpindalaga kolmnurkade ja
  rohkem kui kahe kolmnurga vahel jagatud servadeta.

### Leitud olemasolev kontrollipuudus muna perekonnas

Muna ja balance-shift mudelite kummaski prinditavas pooles on **448
nullpindalaga kolmnurka**. Need esinevad ka repos olevates STL-ides;
kohalik kontroll taastas olemasolevad failid täpselt.

Muna generaator lisab sisemise kupliprofiili nullraadiusega lõpu terve
224 tipuga rõngana ning sulgeb selle kaanega. Kokkulangevad tipud tekitavad
degenereerunud kolmnurki. Sama konstruktsiooni kasutab balance-shift.
`boundary_edge_count` loendab servi tippude indeksite alusel ega tuvasta
kokkulangevaid koordinaate või nullpindala, mistõttu selle tulemus `0`
ei kinnita üksi salvestatud STL-i täielikku korrektsust.

Edasise paranduse siht: käsitleda sisemist nullraadiusega lõppu ühe
poolusena ning kontrollida ka salvestatud STL-i kolmnurkade pindala ja
koordinaatide järgi ühendatud servi. Käesoleva ülevaatuse käigus geomeetriat
ei muudetud. Mõõtmised on `.git/local-check/serialized_checks.json` failis.

### Edasiste kontrollide piirid

Generaatorite käivitus ja failikontroll ei olnud uus füüsiline prindikatse
ega viilutaja kontroll. Kuubi ventilaatori kinnitusavade samm ning osa
elektroonika kõrgusi on jätkuvalt eeldused. Balance-shift servo nominaalne
vaba ruum korpuse nurgas on ainult ligikaudu 0,06 mm. Nende praktiline
sobivus vajab päris komponentide ja prindiga kinnitamist.

Esialgses lähteharus puudus eraldi automaattestide komplekt ja CI seadistus.
Tööriistade paigalduse käigus lisati STL- ja arhiivikontrolli testid.
Sõltuvustel on ainult alampiirid; ülal on kirjas kontrollis kasutatud
versioonid. Baithaaval taastatavus kinnitati selle keskkonna ja praeguste
mudelite kohta.
