# Proovimudelite püsiv arhiiv

Kõik praegused ja edaspidised proovimudelid säilivad mudelipere kaupa.
`output/` sisaldab jätkuvalt viimaseid tööfaile. Arhiivist saab varasema
katsetuse STL-id otse viilutajasse avada.

Kõigi mudeliperede ühine põhiharu on `master`. Uued muudatused tehakse sellest
loodud ajutistes `codex/<muudatuse-nimi>` harudes ja ühendatakse pärast kontrolli
tagasi `master`-harusse koos generaatori, STL-ide ja arhiiviga. Senised
mudelipõhised arendusharud jäävad ajaloolisteks viideteks.

```text
models/
  README.md
  egg_box/
    revisions/
      2026-10-10_120000_ab12cd34/   # UTC aeg ja unikaalne tunnus (näide)
        stl/                     # selle katsetuse STL-failid
        source/                  # generaatorid, abikood ja requirements.txt
        manifest.json            # päritolu, aeg ja failide SHA-256 kontrollsummad
        print_notes.md           # soovi korral prinditagasiside
  balance_shift/revisions/...
  rounded_cube_box/revisions/...
  perforated_sphere/revisions/...
```

STL-failide nimed jäävad iga katsetuse sees samaks. Katsetuse identiteedi annab
kaustanimi, seega ei pea generaatori versiooninumbrit iga pisimuudatuse järel
muutma. Manifesti `family` näitab mudeliperet ning `generator` õiget käivitusskripti.

## Töökorraldus

1. Enne generaatori muutmist käivita projekti juurkaustas `python model_archive.py`.
   See kopeerib praegused STL-id ja lähtekoodi arhiivi midagi ümber genereerimata.
2. Muuda generaatorit ja käivita see tavapäraselt. Kõik neli generaatorit
   arhiveerivad olemasolevad väljundid enne nende ülekirjutamist ning uued
   väljundid pärast edukat jooksu. Arhiveerimise vea korral töö katkeb.
3. Täpselt sama STL- ja lähtekoodikomplekti kordussalvestamisel kasutatakse
   olemasolevat arhiivikirjet. Muutunud geomeetria või lähtekood saab uue kausta.
4. Lisa prinditagasiside vastava katsetuse `print_notes.md` faili: mida katsetati,
   printer ja materjal, sobivus, tugevus ning järgmise muudatuse põhjus.
5. Salvesta Git-is generaatori muudatused, viimased väljundid ja uued
   arhiivikaustad koos. Arhiiv peab jõudma ka tavapärasesse varundusse.

Arhiivi STL-e, lähtekoodi ja manifesti ei muudeta ega kustutata. Uus katsetus
tähendab uut kausta. Arhiivi maht kasvab teadlikult koos katsetuste arvuga.
Ka ebaõnnestunud katsetuse olemasolevad STL-id säilitatakse enne järgmist jooksu;
katkise jooksu osalisi väljundeid ei märgita edukalt genereeritud komplektiks.

## Olemasolevate failide päritolu

Esimesed koopiad säilitavad praegused failid baithaaval. Nende manifestis on
`generated_with_captured_source: false`, sest olemasoleva STL-i vastavust
praegusele generaatorile ei saa üksnes faili olemasolu põhjal kinnitada.
Uue eduka genereerimise koopial on see väärtus `true`. Git-i commit on ainult
viide; täpne salvestatud töökood asub `source/` kaustas.

Varasemad `v01`, `v02` ja `rounded-cube-v02` sildid ning arendusharud jäävad
samuti alles Git-i ajaloos. Käesolev arhiiv algab praegu kettal olevatest neljast
mudeliperest; see ei kopeeri automaatselt kõiki varasemaid Git-i commit'e.

## Vana katsetuse kordamine

Kopeeri soovitud katsetuse `source/` eraldi töökausta, paigalda selle
`requirements.txt` sõltuvused ning käivita manifestis nimetatud generaator.
Ära käivita generaatorit arhiivikaustas ega kirjuta selle STL-ide peale.
Sõltuvuste versioonipiirid säilivad, kuid paigaldatud teekide versioonid pole
lukustatud; kordusgenereerimine ei pruugi anda baithaaval identseid STL-e.
Originaalsed arhiveeritud STL-id jäävad katsetuse kindlaks võrdlusaluseks.

Uue mudelipere jaoks lisa eraldi väljundkaust, kirje `model_archive.FAMILIES`
loendisse ning `@preserve_models("pere_nimi")` generaatori `main` funktsioonile.
