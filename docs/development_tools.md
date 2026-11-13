# Arendustööriistad

Paigaldatud ja kontrollitud 2026-11-10. Tööriistade arendusharu on
`codex/development-tools`. Korpuste geomeetriat, olemasolevaid `output/`
faile ega püsiva arhiivi sisu selle paigalduse käigus ei muudetud.

## Paigaldatud versioonid

| Tööriist | Versioon | Kasutus |
| --- | --- | --- |
| Python | 3.12.16 | Projekti `.venv` |
| NumPy / manifold3d | 2.5.4 / 3.5.4 | Senised generaatorid |
| Trimesh | 5.2.0 | Salvestatud STL-ide sõltumatu kontroll |
| SciPy / Rtree | 1.18.1 / 1.4.1 | Geomeetria abiteegid |
| pytest | 9.2.0 | Kontrollitööriista testid |
| CadQuery | 2.8.0 | Parameetriline CAD ja STEP-väljundi võimalus |
| PrusaSlicer | 2.9.7 | Uus projekti kasutatav viilutaja |
| FreeCAD | 1.1.4 | CAD-programm |
| FreeCAD MCP | 0.1.30 | Codexi ühendus FreeCADiga |
| Blender | 4.5.16 LTS | Visuaalsed 3D-kontrollid ja koostepildid |
| MCP for Blender | 2.2.7, lisaprotokoll 15 | Codexi ühendus Blenderiga |
| uv | 0.13.7 | Eraldi tööriistakeskkondade haldus |

PrusaSlicer, FreeCAD ja Blender on ametlikest pakettidest paigaldatud kasutaja
kausta `%LOCALAPPDATA%\Haptell\Tools\`. Pakettide SHA-256 kontrollsummad
kontrolliti enne lahtipakkimist. Programmid leiab Windowsi Start-menüü
**Haptell** kaustast. Varasem süsteemi PrusaSlicer 2.9.3 on alles;
projekti uus viilutamiskäsk kasutab selgesõnaliselt versiooni 2.9.7.

Paigaldatud programmide täpsed asukohad ja pakettide kontrollsummad on
`%LOCALAPPDATA%\Haptell\Reports\tools.json` failis.
MCP ühendused kasutavad eraldi `uv tool` keskkondi ega lisa oma sõltuvusi
mudelite Pythoni keskkonda. Nende lähtekoodikloonid on sama `Tools` kausta all:

- FreeCAD MCP: `ec8abf21fb9e9ed4bbcbba497515e088423ad251`.
- MCP for Blender: `2e4b0bc294694b1570d76ed01be657c22e6d02a0`.

## Igapäevased käsud

Käivita käsud projekti juurkaustas. Keskkonna aktiveerimine pole vajalik.

### Kontrolli STL-e ja arhiivi

```powershell
.\.venv\Scripts\python.exe tools\verify_models.py
```

Kontroll loeb vaikimisi kaheksat prinditavat poolt. See ei paranda ega kirjuta
STL-e ümber. Kontrollitakse nullpindalaga ja korduvaid kolmnurki, täpsete
koordinaatide järgi ühendatud servi, suletust, pindade suunda ning positiivset
ruumala. Lisaks
kontrollitakse arhiivi manifestide ning ülevaatuste failide kontrollsummasid.
Raport: `.local/reports/model_checks.json`.

**Praegune tulemus ei ole kõigi mudelite puhul roheline:** muna ja
balance-shift kumbki pool sisaldab 448 nullpindalaga kolmnurka ning vastavaid
servavigu. Kontroll lõpetab seetõttu koodiga 1. Kuubi ja sfääri prinditavad
pooled läbivad kontrolli. 31 arhiiviversiooni 306 failiviidet klapivad.
Geomeetriaparandus on eraldi töö ning peab järgima tavalist arhiveerimist.

Üksiku faili kontrollimiseks:

```powershell
.\.venv\Scripts\python.exe tools\verify_models.py output\rounded_cube_box\rounded_cube_bottom.stl
```

Kooste eelvaated lisanduvad lipuga `--include-previews`. Need on vaatamiseks;
puutuvad ja kattuvad koostepinnad võivad anda eraldi võrguhoiatusi.

### Tee kuubi prooviviilutus

```powershell
.\.venv\Scripts\python.exe tools\slice_models.py
```

Iga jooks saab uue `.local/slicing/<UTC-aeg>_<tunnus>/` kausta, kuhu salvestuvad
G-code, logid ja `summary.json`. Senised prinditööd jäävad `output/` kausta.
Põhi kasutab `prusa_xl_04_pla_bottom.ini` profiili, kaas
`prusa_xl_04_pla.ini` profiili. Käsk ei saada tööd printerisse.

Kontrollviilutuse tulemus PrusaSlicer 2.9.7-ga:

| Pool | Materjal | Hinnanguline prindiaeg |
| --- | ---: | --- |
| Põhi | 73,13 g | 3 h 44 min 50 s |
| Kaas | 85,00 g | 3 h 11 min 16 s |

Need on viilutaja hinnangud. Kuubi senised mõõdu-, kokkupõrke-, sisestustee-
ja termopadja kontrollid ning tegelik prindikatse jäävad endiselt vajalikuks.

### Käivita kontrollitööriista testid

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Viis testi läbivad: korrektne suletud võrk, nullpindalaga kolmnurga tuvastus,
avatud servade tuvastus, pahupidi keha tuvastus ja arhiivi muutmise tuvastus. Testid kasutavad
ajutisi kontrollfaile ja jätavad püsiva arhiivi puutumata.
CadQuery paigaldust kontrolliti eraldi 10 × 20 × 30 mm keha loomise ning
6000 mm³ mahu kontrolliga.

## FreeCAD ja Blender Codexis

Kasutaja Codexi seadistuses on kaks uut ühendust:

- `haptell_freecad`: 17 tööriista; kohalik FreeCADi server pordil 9875.
- `haptell_blender`: kontrollkliendile 9 põhitööriista; kohalik server pordil 9876.

Enne ühenduse kasutamist ava Blender või FreeCAD ise. ChatGPT avamisel
käivitub ainult ühenduse abiprogramm. Käivitaja asub
`%LOCALAPPDATA%\Haptell\Tools\launch_cad_bridge.py` failis ja töötab ka repo
haru vahetamise järel. Ühenduste algkäivituse piir
on 90 sekundit, tööriistakutse piir 120 sekundit. Mõlemad kuulavad ainult
`127.0.0.1` aadressil. Blenderi telemeetria on välja lülitatud.

FreeCADi lisa asub `%APPDATA%\FreeCAD\v1-1\Mod\FreeCADMCP\` kaustas.
Blenderi lisa asub `%APPDATA%\Blender Foundation\Blender\4.5\scripts\addons\`
kaustas ning on kasutaja eelistustes sisse lülitatud.

2026-11-10 paigalduse kontrollis prooviti mõlemat ühendust päris MCP-kliendiga.
FreeCADis loodi kontrollkeha ja saadi 640 × 480 pilt. Kontrollkeha dokument
suleti salvestamata. Blenderis kontrolliti stseeni info päringut.
Kohalikud raportid on `.local/reports/freecad_connection.json` ja
`.local/reports/blender_connection.json`.

Uute ühenduste laadimiseks taaskäivita Codex. Varasem Codexi seadistus
varundati `%LOCALAPPDATA%\Haptell\Backups\` kausta; senine `node_repl`
ühendus säilis.

## Keskkonna taastamine

Otsevajadused on failis `requirements-dev.txt`. Selle arvuti kogu kontrollitud
Pythoni keskkond on lukustatud failis `requirements-dev.lock.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Kolme 3D-programmi paigaldused ja MCP kasutajaseaded on selle arvuti kohalikud
seaded. Git-repo kopeerimine üksi neid teise arvutisse ei paigalda.
