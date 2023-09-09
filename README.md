# Handelsregister API 

Das Handelsregister stellt ein öffentliches Verzeichnis dar, das im Rahmen des Registerrechts Eintragungen über die angemeldeten Kaufleute in einem bestimmten geografischen Raum führt. 
Eintragungspflichtig sind die im HGB, AktG und GmbHG abschließend aufgezählten Tatsachen oder Rechtsverhältnisse. Eintragungsfähig sind weitere Tatsachen, wenn Sinn und Zweck des Handelsregisters die Eintragung erfordern und für ihre Eintragung ein erhebliches Interesse des Rechtsverkehrs besteht.

Die Einsichtnahme in das Handelsregister sowie in die dort eingereichten Dokumente ist daher gemäß § 9 Abs. 1 HGB jeder und jedem zu Informationszwecken gestattet, wobei es unzulässig ist, mehr als 60 Abrufe pro Stunde zu tätigen (vgl. [Nutzungsordnung](https://www.handelsregister.de/rp_web/information.xhtml)). Die Recherche nach einzelnen Firmen, die Einsicht in die Unternehmensträgerdaten und die Nutzung der Handelsregisterbekanntmachungen ist kostenfrei möglich.

**Achtung:** Das Registerportal ist regelmäßig das Ziel automatisierter Massenabfragen. Den Ausführungen der [FAQs](https://www.handelsregister.de/rp_web/information.xhtml) zufolge erreiche die Frequenz dieser Abfragen sehr häufig eine Höhe, bei der die Straftatbestände der Rechtsnormen §§303a, b StGB vorliege. Mehr als 60 Abrufe pro Stunde widersprechen der Nutzungsordnung.


## Handelsregister

### Datenstruktur

***URL:*** https://www.handelsregister.de/rp_web/erweitertesuche.xhtml

Das gemeinsame Registerportal der Länder ermöglicht jeder und jedem die Recherche nach einzelnen Firmen zu Informationszwecken. Einträge lassen sich dabei über verschiedene Parameter im Body eines POST-request filtern:


**Parameter:** *schlagwoerter*  (Optional)

Schlagwörter (z.B. Test). Zulässige Platzhalterzeichen sind für die Suche nach genauen Firmennamen (siehe Parameter *schlagwortOptionen*) \* und ? - wobei das Sternchen für beliebig viele (auch kein) Zeichen steht, das Fragezeichen hingegen für genau ein Zeichen. 


**Parameter:** *schlagwortOptionen*  (Optional)
- 1
- 2
- 3

Schlagwortoptionen: 1=alle Schlagwörter enthalten; 2=mindestens ein Schlagwort enthalten; 3=den genauen Firmennamen enthalten.


**Parameter:** *suchOptionenAehnlich*  (Optional)
- true

true=ähnlich lautende Schlagwörter enthalten. Unter der Ähnlichkeitssuche ist die sogenannte phonetische Suche zu verstehen. Hierbei handelt es sich um ein Verfahren, welches Zeichenketten und ähnlich ausgesprochene Worte als identisch erkennt. Grundlage für die Vergleichsoperation ist hier die insbesondere im Bereich der öffentlichen Verwaltung angewandte sogenannte Kölner Phonetik.


**Parameter:** *suchOptionenGeloescht*  (Optional)
- true

true=auch gelöschte Formen finden.


**Parameter:** *suchOptionenNurZNneuenRechts*  (Optional)
- true

true=nur nach Zweigniederlassungen neuen Rechts suchen.


**Parameter:** *btnSuche*  (Optional)
- Suchen

Button "Suchen"


**Parameter:** *suchTyp*  (Optional)
- n
- e

Suchtyp: n=normal; e=extended. Die normale Suche erlaubt eine Suche über den gesamten Registerdatenbestand der Länder anhand einer überschaubaren Anzahl von Suchkriterien. Die erweiterte Suche bietet neben den Auswahlkriterien der normalen Suche die selektive Suche in den Datenbeständen ausgewählter Länder, die Suche nach Rechtsformen und die Suche nach Adressen an.


**Parameter:** *ergebnisseProSeite*  (Optional)
- 10
- 25
- 50
- 100

Ergebnisse pro Seite.


**Parameter:** *niederlassung*  (Optional)

Niederlassung / Sitz. Zulässige Platzhalterzeichen sind \* und ? - wobei das Sternchen für beliebig viele (auch kein) Zeichen steht, das Fragezeichen hingegen für genau ein Zeichen. 


**Parameter:** *bundeslandBW*  (Optional)
- on

Einträge aus Baden-Württemberg


**Parameter:** *bundeslandBY*  (Optional)
- on

Einträge aus Bayern


**Parameter:** *bundeslandBE*  (Optional)
- on

Einträge aus Berlin


**Parameter:** *bundeslandBR*  (Optional)
- on

Einträge aus Bradenburg


**Parameter:** *bundeslandHB*  (Optional)
- on

Einträge aus Bremen


**Parameter:** *bundeslandHH*  (Optional)
- on

Einträge aus Hamburg


**Parameter:** *bundeslandHE*  (Optional)
- on

Einträge aus Hessen


**Parameter:** *bundeslandMV*  (Optional)
- on

Einträge aus Mecklenburg-Vorpommern


**Parameter:** *bundeslandNI*  (Optional)
- on

Einträge aus Niedersachsen


**Parameter:** *bundeslandNW*  (Optional)
- on

Einträge aus Nordrhein-Westfalen


**Parameter:** *bundeslandRP*  (Optional)
- on

Einträge aus Rheinland-Pfalz


**Parameter:** *bundeslandSL*  (Optional)
- on

Einträge aus Saarland


**Parameter:** *bundeslandSN*  (Optional)
- on

Einträge aus Sachsen


**Parameter:** *bundeslandST*  (Optional)
- on

Einträge aus Sachsen-Anhalt


**Parameter:** *bundeslandSH*  (Optional)
- on

Einträge aus Schleswig-Holstein


**Parameter:** *bundeslandTH*  (Optional)
- on

Einträge aus Thüringen


**Parameter:** *registerArt*  (Optional)
- alle
- HRA
- HRB
- GnR
- PR
- VR

Registerart (Angaben nur zur Hauptniederlassung): alle; HRA; HRB; GnR; PR; VR.


**Parameter:** *registerNummer*  (Optional)

Registernummer (Angaben nur zur Hauptniederlassung).


**Parameter:** *registerGericht*  (Optional)

Registergericht (Angaben nur zur Hauptniederlassung). Beispielsweise D3201 für Ansbach


**Parameter:** *rechtsform*  (Optional)
- 1
- 2
- 3
- 4
- 5
- 6
- 7
- 8
- 9
- 10
- 12
- 13
- 14
- 15
- 16
- 17
- 18
- 19
- 40
- 46
- 48
- 49
- 51
- 52
- 53
- 54
- 55

Rechtsform (Angaben nur zur Hauptniederlassung). 1=Aktiengesellschaft; 2=eingetragene Genossenschaft; 3=eingetragener Verein; 4=Einzelkauffrau; 5=Einzelkaufmann; 6=Europäische Aktiengesellschaft (SE); 7=Europäische wirtschaftliche Interessenvereinigung; 8=Gesellschaft mit beschränkter Haftung; 9=HRA Juristische Person; 10=Kommanditgesellschaft; 12=Offene Handelsgesellschaft; 13=Partnerschaft; 14=Rechtsform ausländischen Rechts GnR; 15=Rechtsform ausländischen Rechts HRA; 16=Rechtsform ausländischen Rechts HRb; 17=Rechtsform ausländischen Rechts PR; 18=Seerechtliche Gesellschaft; 19=Versicherungsverein auf Gegenseitigkeit; 40=Anstalt öffentlichen Rechts; 46=Bergrechtliche Gesellschaft; 48=Körperschaft öffentlichen Rechts; 49= Europäische Genossenschaft (SCE); 51=Stiftung privaten Rechts; 52=Stiftung öffentlichen Rechts; 53=HRA sonstige Rechtsformen; 54=Sonstige juristische Person; 55=Einzelkaufmann/Einzelkauffrau


**Parameter:** *postleitzahl*  (Optional)

Postleitzahl (Angaben nur zur Hauptniederlassung). Beispielsweise 90537 für Feucht. Zulässige Platzhalterzeichen sind \* und ? - wobei das Sternchen für beliebig viele (auch kein) Zeichen steht, das Fragezeichen hingegen für genau ein Zeichen. 



**Parameter:** *ort*  (Optional)

Ort (Angaben nur zur Hauptniederlassung). Beispielsweise Feucht. Zulässige Platzhalterzeichen sind \* und ? - wobei das Sternchen für beliebig viele (auch kein) Zeichen steht, das Fragezeichen hingegen für genau ein Zeichen. 



**Parameter:** *strasse*  (Optional)

Straße (Angaben nur zur Hauptniederlassung). Beispielsweise Teststraße 2. Zulässige Platzhalterzeichen sind \* und ? - wobei das Sternchen für beliebig viele (auch kein) Zeichen steht, das Fragezeichen hingegen für genau ein Zeichen. 

### Installation with poetry
Example installation and execution with [poetry](https://python-poetry.org/):
```commandline
git clone https://github.com/bundesAPI/handelsregister.git
cd handelsregister
poetry install
poetry run python handelsregister.py -s "deutsche bahn" -so all
```
Run tests:
```commandline
poetry run python -m pytest
```


### Command-line Interface

Das CLI ist _work in progress_ und 

```
usage: handelsregister.py [-h] [-d] [-f] -s SCHLAGWOERTER [-so {all,min,exact}]

A handelsregister CLI

options:
  -h, --help            show this help message and exit
  -d, --debug           Enable debug mode and activate logging
  -f, --force           Force a fresh pull and skip the cache
  -s SCHLAGWOERTER, --schlagwoerter SCHLAGWOERTER
                        Search for the provided keywords
  -so {all,min,exact}, --schlagwortOptionen {all,min,exact}
                        Keyword options: all=contain all keywords; min=contain at least one
                        keyword; exact=contain the exact company name.
```
