# sv ARC Vergaderruimte Boekingssysteem
## Gebruikershandleiding

**Versie:** 1.0  
**Datum:** November 2025

---

## Inhoudsopgave

1. [Introductie](#introductie)
2. [Inloggen](#inloggen)
3. [Voor Normale Gebruikers](#voor-normale-gebruikers)
   - [Dashboard Overzicht](#dashboard-overzicht)
   - [Vergadering Boeken](#vergadering-boeken)
   - [Vergadering Bekijken](#vergadering-bekijken)
   - [Vergadering Wijzigen](#vergadering-wijzigen)
   - [Vergadering Verwijderen](#vergadering-verwijderen)
4. [Voor Beheerders](#voor-beheerders)
   - [Admin Pagina Openen](#admin-pagina-openen)
   - [Beschikbaarheid Instellen](#beschikbaarheid-instellen)
   - [Tijdblokken Toevoegen](#tijdblokken-toevoegen)
   - [Tijdblokken Aanpassen](#tijdblokken-aanpassen)
   - [Tijdblokken Verwijderen](#tijdblokken-verwijderen)
   - [Wijzigingen Opslaan](#wijzigingen-opslaan)
5. [Kiosk Modus](#kiosk-modus)
6. [SharePoint Integratie](#sharepoint-integratie)
7. [Veelgestelde Vragen](#veelgestelde-vragen)
8. [Contactinformatie](#contactinformatie)

---

## Introductie

Het sv ARC Vergaderruimte Boekingssysteem is een webapplicatie waarmee leden vergaderruimtes kunnen bekijken en reserveren. Het systeem is gekoppeld aan Microsoft Exchange en toont real-time beschikbaarheid van alle ruimtes.

**Website:** https://svarc.100pctwifi.nl/arcrooms/

**Beschikbare Ruimtes:**
- Business Club
- Bespreekruimte (Bestuur & Commissiekamer)
- Kantine
- Commissiekamer
- Overleg veld 2

---

## Inloggen

### Stap 1: Open de Website
Ga naar: **https://svarc.100pctwifi.nl/arcrooms/**

### Stap 2: Inloggen
- De pagina toont direct het dashboard met alle vergaderingen
- Voor het **boeken** van ruimtes moet u inloggen
- Klik op een beschikbaar tijdvak of gebruik de kloktijd rechtsboven
- U wordt automatisch doorgestuurd naar de Microsoft inlogpagina

### Stap 3: Microsoft Authenticatie
- Log in met uw **sv ARC e-mailadres** (bijvoorbeeld: naam@svarc.nl)
- Gebruik uw normale e-mail wachtwoord
- Na succesvolle inlog wordt u teruggestuurd naar het dashboard

> **Let op:** Alleen geautoriseerde sv ARC leden kunnen inloggen.

---

## Voor Normale Gebruikers

### Dashboard Overzicht

Na het openen van de website ziet u drie secties:

#### 1. Vergaderingen Vandaag (Links)
- Toont alle vergaderingen die **vandaag** gepland zijn
- Per vergadering ziet u:
  - **Tijd:** Starttijd - Eindtijd
  - **Onderwerp:** Naam van de vergadering
  - **Locatie:** Welke ruimte
  - **Organisator:** Wie heeft de vergadering gepland
- Klik op een vergadering om deze in Outlook te openen

#### 2. Deze Week (Rechtsboven)
- Kalenderoverzicht van de **komende 5 werkdagen**
- Elke dag toont:
  - Datum en dag van de week
  - Aantal vergaderingen per dag
  - Kleine preview van de vergaderingen
- Klik op een dag om alle vergaderingen van die dag te zien

#### 3. Beschikbaarheid Komende 10 Dagen (Rechtsonder)
- Raster met alle ruimtes en de komende 10 dagen
- Kleuren betekenis:
  - **Wit/Groen met ✓:** Geheel beschikbaar
  - **Oranje met cijfer:** Gedeeltelijk bezet (aantal vergaderingen)
  - **Rood met cijfer:** Volledig bezet
  - **Grijs met X:** Gesloten (buiten werktijden)
- Elk vak is verdeeld in drie tijdsecties:
  - **Ochtend** (08:00 - 12:00)
  - **Middag** (12:00 - 17:00)
  - **Avond** (17:00 - 22:00)

> **Automatisch Verversen:** De pagina wordt elke 5 minuten automatisch ververst

---

### Vergadering Boeken

#### Stap 1: Tijdslot Selecteren
1. Klik op een **beschikbaar tijdvak** (wit of groen) in het beschikbaarheidsraster
2. Als u niet ingelogd bent, wordt u gevraagd in te loggen
3. Het boekingsformulier verschijnt

#### Stap 2: Gegevens Invullen

**Ruimte:** (Automatisch ingevuld)
- De geselecteerde ruimte

**Datum:** (Automatisch ingevuld)
- De geselecteerde datum

**Starttijd:**
- Selecteer een starttijd uit de dropdown
- Alleen beschikbare tijden worden getoond
- Tijden zijn in 30-minuten intervallen

**Eindtijd:**
- Selecteer een eindtijd uit de dropdown
- Moet na de starttijd zijn
- Alleen tijden binnen de werktijden worden getoond

**Onderwerp:** (Verplicht)
- Geef de vergadering een duidelijke naam
- Bijvoorbeeld: "Bestuursvergadering December"
- Maximaal 255 karakters

**Notities:** (Optioneel)
- Extra informatie over de vergadering
- Bijvoorbeeld: "Agenda per e-mail verstuurd"
- Maximaal 1000 karakters

#### Stap 3: Vergadering Aanmaken
1. Controleer alle gegevens
2. Klik op **"Vergadering Aanvragen"**
3. Even geduld tijdens het verwerken
4. Bij succes:
   - Groene melding: "Vergadering succesvol aangevraagd"
   - De vergadering wordt toegevoegd aan Exchange
   - U ontvangt een e-mail bevestiging in Outlook
5. Bij fout:
   - Rode melding met foutbeschrijving
   - Controleer de ingevoerde gegevens en probeer opnieuw

#### Stap 4: Controle
- De nieuwe vergadering verschijnt direct in het dashboard
- Controleer of deze zichtbaar is in "Vergaderingen Vandaag" of "Deze Week"
- De beschikbaarheid wordt direct bijgewerkt

> **Let op:** Sommige ruimtes vereisen goedkeuring door een beheerder. U ontvangt een e-mail zodra de boeking is goedgekeurd of afgewezen.

---

### Vergadering Bekijken

#### Methode 1: Via Dashboard
1. Zoek de vergadering in "Vergaderingen Vandaag" of "Deze Week"
2. Klik op de vergadering
3. De vergadering opent in **Outlook Web** in een nieuw venster
4. Hier ziet u alle details zoals deelnemers, agenda, etc.

#### Methode 2: Via Outlook
1. Open **Outlook** (desktop of web)
2. Ga naar uw **Agenda**
3. Zoek de vergadering in uw kalender
4. Klik erop om alle details te zien

---

### Vergadering Wijzigen

> **Belangrijk:** U kunt alleen vergaderingen wijzigen die **u zelf heeft aangemaakt**.

#### Optie 1: Via Dashboard (Alleen eigen vergaderingen)
1. Zoek uw vergadering in het dashboard
2. Klik op de vergadering
3. Helaas is wijzigen via het dashboard momenteel niet beschikbaar
4. Gebruik Outlook (zie Optie 2)

#### Optie 2: Via Outlook (Aanbevolen)
1. Open **Outlook**
2. Ga naar uw **Agenda**
3. Open de vergadering
4. Klik op **"Bewerken"**
5. Wijzig de gewenste gegevens:
   - Tijd
   - Onderwerp
   - Locatie
   - Deelnemers
6. Klik op **"Verzenden"** of **"Opslaan"**
7. Wijzigingen worden direct doorgevoerd in het boekingssysteem

---

### Vergadering Verwijderen

> **Belangrijk:** U kunt alleen vergaderingen verwijderen die **u zelf heeft aangemaakt**.

#### Via Outlook (Aanbevolen)
1. Open **Outlook**
2. Ga naar uw **Agenda**
3. Zoek de vergadering
4. Klik met rechtermuisknop op de vergadering
5. Selecteer **"Verwijderen"** of **"Annuleren"**
6. Bevestig de verwijdering
7. Optioneel: Voeg een bericht toe voor de deelnemers
8. De vergadering wordt direct verwijderd uit het systeem

#### Gevolgen van Verwijderen
- De vergadering verdwijnt uit het dashboard
- De ruimte wordt weer beschikbaar voor anderen
- Deelnemers ontvangen een annuleringsmail
- De boeking wordt verwijderd uit Exchange

---

## Voor Beheerders

### Wie is een Beheerder?

U bent beheerder als u **gemachtigd** bent voor één of meer ruimtes in Exchange. Dit wordt ingesteld door de IT-afdeling of systeembeheerder.

**Rechten:**
- Beschikbaarheid instellen voor ruimtes waar u gemachtigd voor bent
- Werktijden bepalen per dag van de week
- Zien wie gemachtigd is voor welke ruimte

---

### Admin Pagina Openen

#### Methode 1: Via Klok
1. Klik op de **klok rechtsboven** in het dashboard
2. U wordt doorgestuurd naar de admin pagina

#### Methode 2: Direct URL
Ga naar: **https://svarc.100pctwifi.nl/arcrooms/admin**

#### Inloggen
- Als u nog niet ingelogd bent, wordt u gevraagd in te loggen
- Na inlog ziet u de admin interface

---

### Beschikbaarheid Instellen

De admin pagina toont alle ruimtes waar u rechten voor heeft.

#### Pagina Overzicht

Voor elke ruimte ziet u:

1. **Ruimtenaam** (bijvoorbeeld: "Business Club")
2. **Toegangsrechten:**
   - 🔓 **Bewerkbaar:** U kunt de tijden aanpassen
   - 🔒 **Alleen lezen:** U kunt alleen kijken
3. **Gemachtigden:**
   - Lijst van personen die deze ruimte mogen beheren
   - Naam, e-mailadres en rol
4. **Week Schema:**
   - 7 rijen voor elke dag (Zondag t/m Zaterdag)
   - Tijdlijn van 00:00 tot 24:00
   - Blauwe blokken tonen beschikbare tijden

---

### Tijdblokken Toevoegen

#### Stap 1: Klik op "+" Knop
1. Zoek de dag waarop u een tijdblok wilt toevoegen
2. Klik op de **groene "+" knop** aan het begin van de rij

#### Stap 2: Nieuw Tijdblok Verschijnt
- Er wordt automatisch een standaard tijdblok aangemaakt
- **Standaard tijd:** 08:00 - 17:00
- Het blok verschijnt als een blauw vak in de tijdlijn

#### Stap 3: Tijd Aanpassen
U kunt de tijd op drie manieren aanpassen:

**Methode A: Slepen**
- Klik en sleep het hele blok naar een andere positie
- Het blok klapt vast op 30-minuten intervallen

**Methode B: Handvatten**
- Sleep het **linker handvat** om de starttijd te wijzigen
- Sleep het **rechter handvat** om de eindtijd te wijzigen
- Ook deze klappen vast op 30-minuten

**Methode C: Direct Invoeren**
- Klik op het tijdblok
- De tijd wordt getoond (bijvoorbeeld: "08:00 - 17:00")
- U kunt deze niet direct bewerken, maar wel via slepen

#### Stap 4: Meerdere Blokken per Dag
- U kunt **meerdere tijdblokken** per dag toevoegen
- Bijvoorbeeld: 08:00-12:00 en 13:00-17:00 (met lunchpauze)
- Blokken mogen **niet overlappen**

---

### Tijdblokken Aanpassen

#### Bestaand Blok Verplaatsen
1. Klik op het blauwe tijdblok
2. Sleep het naar de gewenste positie
3. Het blok klapt vast op 30-minuten intervallen

#### Start- of Eindtijd Wijzigen
1. Beweeg uw muis naar de **linker** of **rechter rand** van het blok
2. De cursor verandert in een resize-cursor
3. Klik en sleep om de tijd aan te passen
4. Laat los om de nieuwe tijd in te stellen

#### Minimale/Maximale Tijden
- **Minimale duur:** 30 minuten
- **Maximale duur:** 24 uur
- **Tijdvakken:** Vanaf 00:00 tot 24:00

---

### Tijdblokken Verwijderen

#### Stap 1: Vind het Blok
Zoek het tijdblok dat u wilt verwijderen

#### Stap 2: Klik op "×" Knop
- Elk tijdblok heeft een **rode "×" knop** rechtsboven
- Klik hierop

#### Stap 3: Bevestiging
- Het tijdblok verdwijnt direct uit de interface
- Dit is nog **niet definitief** - zie "Wijzigingen Opslaan"

---

### Wijzigingen Opslaan

> **Belangrijk:** Wijzigingen worden pas doorgevoerd nadat u op "Opslaan" klikt!

#### Stap 1: Controleer Alle Wijzigingen
- Loop alle dagen na
- Controleer of alle tijden correct zijn
- Let op overlappingen (deze worden voorkomen door het systeem)

#### Stap 2: Klik op "Opslaan"
- Klik op de grote groene knop **"💾 Alle Wijzigingen Opslaan"** bovenaan
- Deze knop is zichtbaar op elke ruimtekaart

#### Stap 3: Verwerking
- Het systeem slaat alle wijzigingen op
- Er verschijnt een melding:
  - **Groen:** "Wijzigingen opgeslagen voor [Ruimtenaam]"
  - **Rood:** Foutmelding (bijvoorbeeld bij ongeldige tijden)

#### Stap 4: Verificatie
1. Ga terug naar het **dashboard**
2. Controleer of de beschikbaarheid correct wordt getoond
3. Gesloten tijden verschijnen nu als **grijs met X**

---

### Best Practices voor Beheerders

#### 1. Standaard Werktijden
Stel voor elke ruimte standaard tijden in:
- **Maandag - Vrijdag:** 08:00 - 17:00
- **Weekend:** Optioneel of gesloten

#### 2. Lunchpauze
Overweeg een lunchpauze:
- **Ochtend:** 08:00 - 12:00
- **Middag:** 13:00 - 17:00

#### 3. Avondgebruik
Voor ruimtes die 's avonds gebruikt worden:
- **Overdag:** 08:00 - 17:00
- **Avond:** 18:00 - 22:00

#### 4. Speciale Dagen
- Sluit ruimtes op feestdagen
- Pas tijden aan voor speciale evenementen
- Communiceer wijzigingen aan leden

#### 5. Regelmatig Controleren
- Check wekelijks of de tijden nog kloppen
- Pas aan op basis van feedback van leden
- Verwijder oude of ongebruikte tijdblokken

---

## Kiosk Modus

### Wat is Kiosk Modus?

Kiosk modus is bedoeld voor **displays bij de vergaderruimtes**. Bijvoorbeeld een tablet of scherm bij de deur dat alleen informatie toont over die specifieke ruimte.

### URL Parameters

U kunt de weergave aanpassen met URL parameters:

#### 1. Zoom Aanpassen (Compacter Weergave)

**Normaal (100%):**
```
https://svarc.100pctwifi.nl/arcrooms/
```

**Compact (75% - voor kleinere schermen):**
```
https://svarc.100pctwifi.nl/arcrooms/?zoom=compact
```
of
```
https://svarc.100pctwifi.nl/arcrooms/?zoom=75
```

**Effect:**
- Kleinere lettertypen
- Minder witruimte
- Meer informatie op één scherm
- Ideaal voor tablets

#### 2. Specifieke Ruimte Filteren

**Alleen Business Club:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_BusinessClub@svarc.nl
```

**Alleen Kantine:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_kantine@svarc.nl
```

**Alleen Bespreekruimte:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_bespreekkamer1@svarc.nl
```

**Effect:**
- Toont alleen vergaderingen van die ruimte
- Filter indicator bovenaan (rood vak met ruimtenaam)
- Week kalender toont alleen die ruimte
- Beschikbaarheidsraster toont alleen die rij

#### 3. Combineren van Parameters

**Kantine in compact modus:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_kantine@svarc.nl&zoom=compact
```

**Business Club compact weergave:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_BusinessClub@svarc.nl&zoom=75
```

### Kiosk Scherm Instellen

#### Hardware Opties:
- **Tablet:** iPad, Samsung Galaxy Tab (10" of groter)
- **Raspberry Pi:** Met 7" touchscreen
- **Chrome device:** Chromebox of Chromecast

#### Aanbevolen Instellingen:

1. **Browser in Kiosk Mode:**
   - Chrome: Start met `--kiosk` flag
   - Firefox: Gebruik F11 voor fullscreen

2. **Auto-refresh:**
   - Pagina ververst elke 5 minuten automatisch
   - Geen extra configuratie nodig

3. **Tablet Stand:**
   - Plaats het scherm bij de deur
   - Op ooghoogte (ongeveer 150cm)
   - Met oplader aangesloten

4. **Browser Cache:**
   - Wis cache als u wijzigingen niet ziet
   - Herlaad met Ctrl+F5 (hard refresh)

#### Voorbeeld URLs voor Elk Scherm:

**Bij Business Club:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_BusinessClub@svarc.nl&zoom=compact
```

**Bij Kantine:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_kantine@svarc.nl&zoom=compact
```

**Bij Bespreekruimte:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=ruimte_bespreekkamer1@svarc.nl&zoom=compact
```

**Bij Commissiekamer:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=commissiekamer@svarc.nl&zoom=75
```

**Bij Overleg veld 2:**
```
https://svarc.100pctwifi.nl/arcrooms/?room=Ruimte_overlegveld2@svarc.nl&zoom=compact
```

---

## SharePoint Integratie

### Het Systeem Inbedden in SharePoint

U kunt het boekingssysteem inbedden in een SharePoint pagina.

#### Stap 1: SharePoint Pagina Bewerken
1. Ga naar de SharePoint pagina waar u het systeem wilt toevoegen
2. Klik op **"Bewerken"** rechtsboven

#### Stap 2: Embed Web Part Toevoegen
1. Klik op **"+"** om een web part toe te voegen
2. Zoek naar **"Embed"** of **"Insluiten"**
3. Selecteer het Embed web part

#### Stap 3: IFrame Code Invoeren
Plak de volgende code:

```html
<iframe 
  src="https://svarc.100pctwifi.nl/arcrooms/" 
  width="100%" 
  height="800px" 
  frameborder="0"
  style="border: none; overflow: hidden;">
</iframe>
```

#### Stap 4: Aanpassen (Optioneel)
- **Hoogte wijzigen:** Verander `height="800px"` naar gewenste hoogte
- **Full-width:** Gebruik `width="100%"`
- **Compact mode:** Wijzig URL naar `?zoom=compact`

#### Stap 5: Opslaan en Publiceren
1. Klik op **"Apply"** of **"Toepassen"**
2. Sla de pagina op
3. Publiceer de pagina

### Authenticatie in SharePoint

**Belangrijk:**
- Gebruikers moeten **inloggen** om te kunnen boeken
- De eerste keer worden ze gevraagd om in te loggen via Microsoft
- Daarna blijven ze ingelogd
- Bekijken van vergaderingen kan zonder inloggen

---

## Veelgestelde Vragen

### Algemeen

**Q: Moet ik altijd inloggen?**  
A: Nee, alleen voor het **boeken** van ruimtes. Bekijken kan zonder inloggen.

**Q: Kan ik op mijn telefoon boeken?**  
A: Ja, de website is responsive en werkt op mobiele apparaten.

**Q: Hoe weet ik of mijn boeking is gelukt?**  
A: U ziet een groene melding en ontvangt een e-mail bevestiging in Outlook.

**Q: Kan ik terugkerende vergaderingen aanmaken?**  
A: Momenteel niet via het systeem. Gebruik Outlook voor terugkerende afspraken.

**Q: Hoelang van tevoren kan ik boeken?**  
A: Er is geen limiet, u kunt maanden vooruit boeken.

### Problemen

**Q: Ik zie geen beschikbare tijden.**  
A: Mogelijke oorzaken:
- De ruimte is volledig gesloten op die dag
- Alle tijden zijn al geboekt
- Controleer of u de juiste dag hebt geselecteerd

**Q: Mijn boeking verschijnt niet in het dashboard.**  
A: Wacht 5 minuten (automatische refresh) of ververs handmatig met F5.

**Q: Ik kan niet inloggen.**  
A: Controleer:
- Gebruikt u uw sv ARC e-mailadres?
- Is uw wachtwoord correct?
- Neem contact op met IT als het probleem aanhoudt

**Q: Ik kan mijn vergadering niet verwijderen.**  
A: U kunt alleen vergaderingen verwijderen die u zelf heeft aangemaakt. Gebruik Outlook.

### Beheer

**Q: Ik ben beheerder maar zie de admin pagina niet.**  
A: Controleer of u gemachtigd bent in Exchange. Neem contact op met IT.

**Q: Mijn wijzigingen worden niet opgeslagen.**  
A: Controleer:
- Heeft u op "Opslaan" geklikt?
- Zijn de tijden geldig (30-minuten intervallen)?
- Overlappen de blokken niet?

**Q: Kan ik ruimtes toevoegen of verwijderen?**  
A: Nee, dit moet door IT in Exchange worden gedaan.

---

## Contactinformatie

### Technische Ondersteuning

**IT Helpdesk sv ARC**  
E-mail: helpdesk@svarc.nl  
Telefoon: [Uw telefoonnummer]

### Voor Vragen Over:

**Boekingen & Gebruik:**
- Neem contact op met het secretariaat
- E-mail: secretariaat@svarc.nl

**Beschikbaarheid & Tijden:**
- Neem contact op met uw beheerder
- Zie de admin pagina voor wie beheerder is

**Technische Problemen:**
- Neem contact op met IT
- Vermeld: URL, browser, foutmelding

**Toegangsrechten:**
- Neem contact op met IT
- Vermeld: welke ruimte, waarom u toegang nodig heeft

---

## Bijlagen

### Overzicht Ruimte E-mailadressen

Voor gebruik in kiosk modus of filtering:

| Ruimte Naam | E-mailadres |
|------------|-------------|
| Business Club | ruimte_BusinessClub@svarc.nl |
| Bespreekruimte (Bestuur & Commissiekamer) | ruimte_bespreekkamer1@svarc.nl |
| Kantine | ruimte_kantine@svarc.nl |
| Commissiekamer | commissiekamer@svarc.nl |
| Overleg veld 2 | Ruimte_overlegveld2@svarc.nl |
| Businessruimte | Businessruimte@svarc.nl |
| Clubhuis Kantine | clubhuiskantine@svarc.nl |

### Sneltoetsen

| Actie | Toets |
|-------|-------|
| Pagina verversen | F5 |
| Hard refresh (cache wissen) | Ctrl + F5 |
| Inloggen | Klik op klok of tijdvak |
| Admin pagina | Klik op klok |
| Volledig scherm | F11 |

---

## Versiegeschiedenis

**Versie 1.0 - November 2025**
- Eerste release gebruikershandleiding
- Ondersteuning voor normale gebruikers en beheerders
- Kiosk modus documentatie
- SharePoint integratie instructies

---

**Einde Gebruikershandleiding**

*Voor de meest recente versie van deze handleiding, zie:*  
*https://github.com/Martijndutch/roommanager*
