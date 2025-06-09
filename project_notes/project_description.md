# TextRPG Adventure Generator - Projektbeschreibung

## Projektvision
Ein außergewöhnliches TextRPG entwickeln, das durch generative Kapitel einen hohen Wiederspielwert hat. Das System nutzt zwei spezialisierte AI-Agenten für dynamische, interaktive Geschichten mit echter Player Agency.

## Kernkonzept 

### Spielerflow

* Spielerauswahl: Setting, Charakterklasse und Schwierigkeitsgrad
* Generative Kapitel: Creator Agent erstellt fesselnde Story-Abschnitte
* Interaktive Aktionen: Gamemaster Agent verarbeitet Spielerentscheidungen
* Dynamische Fortsetzung: Nahtloser Wechsel zwischen narrativen und interaktiven Phasen
* Die Anzahl der Schritte pro Phase können vorher nicht bestimmt werden und hängen von der Spieler Interaktion und den Handlungen sowie dem Storyverlauf ab

### Technische Architektur

#### AI-AGENTEN SYSTEM

**Agent 1: Story Creator**

Verantwortlichkeiten:

* Generierung neuer Kapitel (800-1200 Wörter)
* Visuelle Beschreibungen für Kapitelabschnitte
* Charakterdesign (Begleiter, NPCs, Hintergründe)
* Weltbau und Lore-Entwicklung
* Spannungsaufbau und narrative Struktur

Eingabe: Spielerkontext, bisherige Story, Weltstate
Ausgabe: Vollständiges Kapitel mit Cliffhanger

**Agent 2: Gamemaster**

Verantwortlichkeiten:

* Action Resolution (Spieleraktionen verarbeiten)
* Mechanik und Balancing (Würfe, Skill-Checks)
* NPC-Interaktionen und Dialoge
* Handlungsoptionen generieren
* Kurze reaktive Szenen (100-300 Wörter)

Eingabe: Spieleraktion, aktueller Zustand
Ausgabe: Konsequenzen + neue Handlungsoptionen