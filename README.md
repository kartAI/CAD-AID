Repository for praksisstudentene ved Norkart
# Objektdeteksjon i byggesakstegninger
## Beskrivelse
Prosjektet ble gjennomført av en praksisstudent fra integrert master i kunstig intelligens ved UiA, Grimstad.  
Formålet med prosjektet var å undersøke hvordan kunstig intelligens kan brukes til å detektere feil og mangler i byggesakstegninger.

I dette prosjektet ble det trent en YOLOv8 modell for å detektere og klassifisere type tegning, som kan potensielt brukes til å sjekke hvilke tegninger er med i søknaden. Videre arbeid i prosjektet vil innebære å trene modellen på å detektere opplysninger som er påkrevde i de ulike tegningstypene. 


## Requirements
- Python
- Python PIP
- Numpy
- OpenCv
- pdf2image
- PIL
- ultralytics
- Flask

## Setup guide
### 1. Klon repoet

### 2. Installer pakker
#### OpenCv
Installer OpenCv ved å skrive følgende kommando i terminal:  
`pip install opencv-python`
#### pdf2image
##### Windows:  

- Installer pdf2image i terminalen:
  
  `pip install pdf2image`

- Installer poppler:
1. Last ned nyeste versjon: (https://github.com/oschwartz10612/poppler-windows/releases/)
2. Ekstraher zip filen ved ønsket lokasjon
3. Kopier stien til /bin mappa som ligger i poppler, åpne miljøvariabler i Windows, "Path" og rediger, trykk på "Ny" og lim inn stien til /bin mappa.


##### MacOS:  

- Installer pdf2image i terminalen slik som i Windows.

- Installer poppler: skriv kommandoen i terminalen `brew install poppler`

 
#### Ultralytics
Installer med pip kommando: `pip install ultralytics`

#### Flask
`pip install flask`
#### LabelImg
Følg installasjonsguiden: https://github.com/HumanSignal/labelImg

## Dokumentasjon
#### Datasettet  
Datasettet består av tegninger i "images" mappa der hver fil har en tilhørende .txt fil i "labels" mappa som inneholder bounding box koordinater i YOLO-format og klassen. Hver klasse har en egen id.   

Det er 4 typer tegninger (klasser) i datasettet:  
- Plantegninger
- Snittegninger
- Situasjonskart
- Fasadetegninger

I tillegg er det lagt inn "bakgrunnsbilder"/støy som modellen ikke skal detektere. Eksempler på slike bilder er 
dokumenter og foto av hus/andre objekter som ofte følger med søknader.

Et eksempel på .txt fil tilhørende en tegning som inneholder 4 fasader og 1 snittegning:  

<img width="471" alt="Skjermbilde 2023-11-02 kl  09 44 28" src="https://github.com/kartAI/praksisprosjekt-uia-2023/assets/58601228/66c7b683-0a10-461f-a0ce-3914dff06d56">
  
Tegningene er hentet fra Kristiansand kommune byggesaksarkiv: [link](https://opengov.360online.com/Cases/KRSANDEBYGG)  
 
  
### YOLOv8 modell

#### Mappestruktur
```

CAD-AID/
    ├──data/
    │   ├── test/
    │   │   └── images/
    │   │   └── labels/
    │   │          
    │   │
    │   ├──train/
    │   │   └── images/
    │   │   └── labels
    │   │
    │   ├──val/
    │   │  └── images/
    │   │  └── labels/
    │   └── data.yaml
    │
    ├── runs/
    │   └── detect/
    │       └── train
    │            └── weights/
    │                 └── best.pt
    │               
    ├──data_prep/
    │  └── convertFromPDF.py
    │  └── folder_split.py
    │
    ├──images/
    │
    ├── yolo_model.py
```

##### data.yaml
For å trene med eget datasett, må vi ha en data.yaml fil som definerer "pathen" til treningsdata, antall klasser og navnet på alle labels:
```
path: ../data
train: ../data/train/images
test: ../data/val/images
val: ../data/test/images

nc: 4
names: ["fasade","plantegning","situasjonskart", "snitt"]
```
Endre "nc" (number classes) dersom flere klasser legges til og navnet på nye labels i "names". 
#### Trene modellen
Treningen på eget datasett ble initiert med vekter fra yolo8s.pt , en pretrent modell på COCO datasettet.  

```
model = YOLO("yolov8s.pt")  
model.train(data="data/data.yaml", epoch=20,batch=8)
```
Oppdaterte vekter lagres under `runs/detect/train/weights/best.pt` etter hver trening. Det lages en ny "train" mappe etter hver trening, eksempelvis `..\detect\train1\..`  

For videre trening, bruk vektene fra modellen som ga best resultat. Eksempel:
```
model = YOLO("runs/detect/train6/weights/best.pt")  
model.train(data="data/data.yaml", epoch=20,batch=8)
```
#### Valider den nye modellen
```
model = YOLO("runs/detect/train6/weights/best.pt")  
model.train(data="data/data.yaml", epoch=20,batch=8)
metrics = model.val()
```

#### Analyser resultater
* mAP (mean avarage precision) score: regnes ut i fra den faktisk bounding boksen og den predikerte. Sier noe om hvor nøyaktig modellen er. mAP score i "results.csv" viser resulatene etter hver epoch, mens mAP i "PR_curve.png" viser resultatet på valideringsdata etter at modellen er ferdig å trene.
* PR (precision recall) kurve: presisjon langs y-aksen måler hvor nøyaktig modellen predikerer positive klasser, dvs hvor mange av alle positive prediksjoner er riktig klassifisert som positive. "Recall" (følsomhet) langs x-aksen angir det totale antallet faktiske positive klasser som ble riktig klassifiser, sier noe om hvor effektivt modellen kan identifisere de positive klassene. 
* F1 score: måler modellens nøyaktighet basert på en balanse mellom "precision" og "recall", som gir god indikasjon på modellens "performance". F1 kurven viser hvilke "confidence score" som gir optimal balanse mellom precision og recall.
* P kurve og R kurve: viser hvordan presisjon og recall varierer når konfidens verdien endres.

#### Prediksjon

#### Lag ny treningsdata
##### Konverter til jpg
1. Last ned PDF-filene fra byggesaksakrivet i "images" mappen. 
2. Kjør scriptet "convertFromPDF.py" for å konvertere til jpg
3. Lable tegningene i LabelImg. Se guide under.
4. Kjør scriptet "folder_split.py" for å dele datasettet i trenings-,validerings- og testdata


##### LabelImg
1. Åpne labelImg ved å navigere til labelImg mappa i terminalen og skriv kommandoen `python labelImg.py` 
2. Trykk "open dir" og velg mappa "images"
3. Trykk "Change save dir" og velg mappa "labels"
4. Velg YOLO-format

##### Legge til flere labels
1. For å legge til flere labels i LabelImg, gå til /data/predefined_classes.txt i LabelImg mappa.
2. Endre data.yaml i prosjektmappa.



### Flask demo
En demo av modellens resultater er visualisert i en enkel Flask webapplikasjon.  

Appens funksjonalitet:  
* Last opp flere bilder samtidig
* Kjør prediksjon ved å trykke på "Analyser" som viser objektdeteksjonen i et nytt vindu.
* Tilbakeknapp for gå tilbake til startvinduet
* "Slett alle bilder"-knapp som sletter alle bilder dersom man vil starte på nytt
* Alle bildene som lastes opp lagres i "uploads" mappa, og slettes når programmet stopper
* I "uploads/logo/norkart_logo.png er det lagt inn en logo, denne vil ikke slettes. 
#### Mappestruktur

```
flask_app/
│
├── static/
│   │
│   └── uploads/
│       └── logo/
│           └── logo_norkart.png
│
├── templates/
│   │
│   ├── index.html
│   └── predictions.html
│
└── app.py


```
#### Koden
#### app.py
Kjør denne fila for å teste demoen.  

Håndterer opplastning av bilder, sletting av bilder i "uploads" mappa og YOLO-modellen.
#### index.html
HTML koden til den første siden som vises.

#### prediction.html
HTML koden som håndterer vinduet der resultatene fra prediksjonen vises. 

## Resultater og videre arbeid
Modellen som ga best resultat ble trent på mer enn 250 bilder over 30 epochs. Vektene fra siste trening ligger under ´runs/detect/train/weights/best.pt´  
Denne modellen løser første del av prosjektet som er å detektere hvilke tegninger er med i søknaden.  
Ut i fra resultatene så langt, har modellen noe problemer med å skille 
snittegninger og fasadetegninger, som kan løses ved å lable mer data.  


### Lable mer data
* Lable flere tegninger slik at datasettet blir balansert. Oversikt over antall labels i datasettet kan du finne under `runs\detect\train3\labels.jpg`.
* Lable flere typer tegninger: terrengprofil, perspektivtegninger osv


### Legge til flere bakgrunnsbilder
Legge til flere bilder som modellen ikke skal detektere, feks tekstdokumenter fra byggesaker, bilder av hus osv.
Bildene legges i samme mappe som datasettet, og lag tomme .txt filer i labels ved å trykke "verify" i LabelImg
uten å tegne bounding bokser.
### Trene modellen på å finne feil/mangler i tegningene
Neste del av prosjektet er å eksperimentere om modellen kan detektere
komponenter i tegningene ut i fra de generelle kravene til hva 
byggesøknadstegninger skal inneholder. En liste kan du finner her:
https://sdkconsult.no/krav-til-byggesoknadstegninger-tegninger/

Fokuser på én type tegning, og implementer én type label av gangen i modellen.
#### Plantegninger
Eksempler på nye labels:
* romnavn
* romareal
* etasje


#### Snittegning
* Høyder
* Takvinkel

#### Fasadetegning
* Himmelretning
* Målestokk

### Tegninger med dårlig kvalitet
Noen av tegningene blir ikke godtkjent på grunn av dårlig kvalitet. Videre
arbeid kan derfor også innebære å undersøke hvordan modellen skal håndtere
slike tegninger.  
Å finne slike eksempler i byggesaksarkivet kan være tidskrevende på grunn
av få eksempler.   

Et tips kan være å lagre disse bildene i mappa "low_quality_drawings"
dersom man finner slike eksempler fortløpende under prosjektarbeidet.
Det er allerede lagt inn noen få eksempler på slike tegninger.
### Flask app
* Legge til funksjon slik at det kan lastes opp PDF filer i appen som omgjøres til jpg. Sjekk om "convertFromPDF.py" i mappa "dataPrep" kan skrives litt om og brukes i appen.
* Modellens path som brukes i "app.py" er den samme fra "yolo_model.py". Fiks i koden for å unngå å endre stien i to ulike filer. 
