# ADAM organizmas: TikTok automatizacija

## 1. Kaip viskas sujungta

```
ADAM (kiprasb2b.github.io/Frankenstein)
   │  užrašai saugomi GitHub repo „ADAM-vault“ (sinchronizacija per GitHub API)
   │  mygtukas / komanda „Vykdyk planą“
   ▼
GitHub Actions (ADAM-vault repo) ──► Claude Code (claude-code-action)
   │  • randa video užrašus su statusu „paruošta“
   │  • parsiunčia video iš Drive, uždeda dainos priedainį po balsu + FOLLOW FOR MORE
   │  • parašo caption ir pinned, jei jų nėra
   │  • įdeda video į media/ (viešas URL per GitHub Pages)
   │  • augina organizmą: naujas „Paleidimas“ užrašas + gijos į kanalą ir dainą
   ▼
Statusas „laukia-planavimo“ → Claude pokalbyje (Cowork) su Metricool jungtimi
   suplanuoja video ir pažymi „suplanuota“
```

**Kodėl Metricool lieka pokalbyje:** Metricool jungtis veikia tik Claude programėlėje, o GitHub Actions jos nemato. Todėl Actions atlieka sunkų darbą (video, tekstus, grafą), o pats planavimas vyksta vienu sakiniu čia: „suplanuok ADAM eilę“.

---

## 2. Ką padarai tu (vieną kartą, ~20 min)

1. **Sukurk naują GitHub repo `ADAM-vault`** (Public, nes video turi būti viešai pasiekiami Metricool'ui).
   - Asmeninių užrašų ten nedėk. Jiems vėliau galima susikurti atskirą privatų vault.
2. **Įkelk šio rinkinio failus** į repo šaknį: `.github/`, `tools/`, `vault/`, `media/`, `.nojekyll`.
3. **Dainas** (mp3) sudėk į `vault/TikTok/Dainos/`. Kiekvienai dainai sukurk užrašą, kaip `SHOTTAS.md` (laukas `failas:` turi sutapti su mp3 pavadinimu).
4. **GitHub Pages:** repo → Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
5. **Claude raktas Actions'ams:**
   - kompiuteryje, kur įdiegtas Claude Code, paleisk `claude setup-token` ir nukopijuok tokeną;
   - repo → Settings → Secrets and variables → Actions → *New secret*: `CLAUDE_CODE_OAUTH_TOKEN`.
   - Alternatyva: `ANTHROPIC_API_KEY` (mokama atskirai). Tada workflow faile pakeisk eilutę į `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}`.
6. **GitHub tokenas ADAM'ui:** GitHub → Settings → Developer settings → *Fine-grained tokens* → tik `ADAM-vault` repo, teisės **Contents: Read & write** ir **Actions: Read & write**. Jį įvesi ADAM nustatymuose (lieka tik tavo naršyklėje).
7. **Claude Code** atidaryk Frankenstein repo ir įklijuok žemiau esantį **PROMPT A**.

---

## 3. PROMPT A: ADAM ↔ GitHub vault + „Vykdyk planą“ + organizmo grafas

> Įklijuok į Claude Code, atidaręs `kiprasB2B/Frankenstein` repo.

```
Projektas: ADAM (Frankenstein) – Vite + TypeScript užrašų programa. Saugyklos abstrakcija yra
src/storage/adapter.ts (StorageAdapter: list/read/readBinary/write/exists/mkdir/remove/rename),
yra fsAdapter ir idbAdapter. Visa sąsaja lietuviškai, laikykis esamo stiliaus (juodas fonas,
plonos pilkos linijos, melsvai žydras švytėjimas).

Sukurk 4 dalykus:

1) GitHubAdapter (src/storage/githubAdapter.ts), įgyvendinantį StorageAdapter per GitHub REST API
   (Contents API + Git Trees API list'ui). Nustatymuose (settingsDialog): repo "savininkas/vardas",
   šaka (main), aplankas vault'ui (vault/) ir fine-grained tokenas, saugomas localStorage
   (try/catch; aiškiai parašyk, kad tokenas lieka tik šioje naršyklėje). Picker'yje pridėk
   trečią variantą „GitHub vault“. Kešuok sha, rašymus grupuok (debounce 1,5 s), konfliktų atveju
   (409/422) perskaityk iš naujo ir parodyk pranešimą. Mygtukas „Sinchronizuoti dabar“.

2) Komanda ir mygtukas „Vykdyk planą“ (ikonų juostoje + komandų paletėje + Ctrl+Shift+Enter):
   - atidaro mažą langą su teksto lauku (numatyta reikšmė „vykdyk planą“) – čia galima rašyti
     ir kitas komandas laisvu tekstu;
   - kviečia POST /repos/{owner}/{repo}/actions/workflows/adam-vykdyk.yml/dispatches
     su inputs.komanda;
   - rodo būseną: „Siunčiama → Vykdoma → Baigta/Klaida“ (polling /actions/runs kas 10 s),
     nuorodą į GitHub run'ą, o baigus – automatiškai sinchronizuoja vault ir praneša,
     kiek užrašų pasikeitė.
   - Komanda „Pažymėti suplanuotais“: visiems vault/TikTok/Video užrašams su
     statusas: laukia-planavimo → statusas: suplanuota (frontmatter keitimas).

3) TikTok skydelis (nauja šoninė panelė „TikTok“): sąrašas iš vault/TikTok/Video/*.md
   (frontmatter: kanalas, data, statusas, daina, video_url) sugrupuotas pagal statusą
   (idėja / paruošta / laukia-planavimo / suplanuota / paskelbta / klaida), spalvinis
   ženkliukas, paspaudus atidaro užrašą; mygtukas „+ Naujas video“ sukuria užrašą pagal
   šabloną vault/TikTok/Video/Leonida naktis.md.

4) Organizmo režimas grafe (jungiklis 2D/3D grafo įrankių juostoje):
   - mazgų tipai iš frontmatter `tipas`: tiktok-kanalas = didelis pulsuojantis „širdies“
     branduolys; tiktok-video = ląstelės (spalva pagal statusą); daina = „nervų“ mazgai;
     paleidimas (vault/TikTok/Paleidimai) = maži švytintys impulsai;
   - laiko slankiklis apačioje: mazgai atsiranda pagal sukūrimo datą (frontmatter data arba
     failo mtime) – paspaudus ▶ organizmas „užauga“ per ~10 s animaciją;
   - naujos gijos (nuorodos) po paleidimo trumpai sušvyti.
   Naudok esamus forceLayout2d/3d ir canvasRenderer – nekurk naujo grafo variklio.

Po kiekvieno žingsnio: npm run build turi praeiti be klaidų. Atnaujink README skiltį „GitHub vault ir
Vykdyk planą“. Commit'ink kiekvieną dalį atskirai lietuviškais pranešimais.
```

---

## 4. Kaip naudoti kasdien

1. ADAM'e spausk **„+ Naujas video“**: įklijuok Drive nuorodą, pasirink kanalą, datą ir dainą (arba palik tuščią). Statusą nustatyk `paruošta`.
2. Spausk **„Vykdyk planą“**. Po ~3–5 min (vienam video) ADAM praneš „Baigta“, o grafe atsiras naujos gijos.
3. Pokalbyje su manimi parašyk: **„suplanuok ADAM eilę“**. Perskaitysiu `vault/TikTok/Eile.md` ir suplanuosiu Metricool'e.
4. ADAM'e spausk **„Pažymėti suplanuotais“**.

---

## 5. Saugumas ir ribos

- **Tokenai:** GitHub tokeną ribok tik vienu repo. Claude tokenas saugomas GitHub Secrets ir į ADAM kodą niekada nepatenka.
- **Viešumas:** `ADAM-vault` yra viešas, nes Metricool'ui reikia viešų video nuorodų. Privačius užrašus laikyk atskirame privačiame repo.
- **Kaina:** Actions viešiems repo nemokami, o Claude naudojimas eina iš tavo plano limitų (arba API, jei naudosi `ANTHROPIC_API_KEY`).
- **Metricool:** planuoja tik Claude pokalbyje, nes kol kas tai vienintelė vieta, kur veikia jungtis.
