# -*- coding: utf-8 -*-
"""
Created on Thu May  4 18:05:07 2017

@author: Armand
"""

#Importation des librairies nécéssaires au fonctionnement de Qt
import sys, os
from PyQt5 import uic #Pour extraire l'UI du code XML généré avec Qt Designer

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtWidgets
import wave, math, struct, random 
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt

import numpy as np
from scipy.io.wavfile import read
import scipy.signal as sig

#Notes de musique en notation anglosaxone (C = Do, D = Ré, ...)
NOTE_MIDI = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
#Note de musique dans la notation courante
NOTE = {"A":"LA",
        "B":"SI",
        "C":"DO",
        "D":"Ré",
        "E":"MI",
        "F":"FA",
        "G":"SOL",
        "C#":"DO#",
        "D#":"Ré#",
        "F#":"FA#",
        "G#":"SOL#",
        "A#":"LA#",
        }

FREQ_NOTE_4 = {"C": 261.63,
               "C#": 277.18,
               "D": 293.66,
               "D#": 311.13,
               "E": 329.63,
               "F": 349.23,
               "F#": 369.99,
               "G": 392,
               "G#": 415.30,
               "A": 440,
               "A#": 466.16,
               "B": 493.88,
               }


qtCreatedFile ="C:\\Users\\Armand\\Desktop\\software.ui" #Il s'agit de l'Ui créée sur Qt Designer
Ui_Window, QtBaseClass = uic.loadUiType(qtCreatedFile) #On récupère l'Ui dans Ui_MainWindow

class software(QtBaseClass, Ui_Window, QWidget): #Hérite de l'Ui (pour le design) créée et de sa classe (pour les propriétés)
    """ Classe lançant l'interface de notre programme, composée de trois onglets :
            -Le premier concerne la création de sons
            -Le deuxième, l'écriture en partition d'un son pré-enregistré
            -Le troisième, l'écriture d'une partition d'un son joué en direct
            
        ### CREATION DE SON ###
        Cet onglet permet de produire des sons au format .wav, à une fréquence donnée.
        On peut définir la durée du son (par défaut 1s), la fréquence d'échantillonage (par défaut 44.100Hz),
        le nombre de sinusoïde composant le son ainsi que la fréquence de chacun.
        Il permet alors de créer des sons simples, à une fréquence, comme des sons complexes, jusqu'à 5 fréquences.
        Une fois le son créé, on affiche un aperçu de la sinusoïde créé à l'aide de la classe Sinusoide.
        
        ### ECRITURE SON PRE-ENREGISTRE ###
        Cet onglet permet d'analyser notre son pré-enregistré à l'aide de la transformée de Fourrier.
        On peut alors choisir le fichier à analyser, la taille de la fenêtre de Fourrier
        ainsi que l'amplitude minimal à considérer (=Correction). 
        La taille de la fenêtre de Fourrier doit être une puissance de 2, écrit sous la forme
        2**X
        
    """
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.tabSoftware.currentChanged.connect(lambda tab : self.selectionTab(tab))
        
        self.initTabCreationSon()
        self.initTabAnalysePreSaved()
        
        
    def selectionTab(self, tab):
        """Méthode qui nous permettra de redimensionner la fenêtre à chaque fois que l'on change
        de tab, afin d'obtenir un résultat propre entre chaque tab.
        tab vaut 0 si la tab sélectionné est celle de Création de son, 1, si c'est celle
        de l'analyse de son pré-enregistré et 2 si il s'agit de la tab d'analyse de son
        en direct.
        """
        if tab == 0:
            self.setMinimumHeight(200 + (self.nbFrequence-1)*20)
            self.setMinimumWidth(410)
            self.resize(self.minimumWidth(), self.minimumHeight())
            self.tabSoftware.resize(390, 170 + (self.nbFrequence-1)*20)
        elif tab == 1:
            self.tabSoftware.resize(430, 140)
            self.setMinimumHeight(175)
            self.setMinimumWidth(450)
            self.resize(self.minimumWidth(), self.minimumHeight())
    
    def initTabCreationSon(self):
        """Méthode initialisant le premier onglet de notre interface QT
        avec les réglages et signaux souhaités. """
        self.nomSonText.setText("Sound")
        self.dureeText.setText("1")
        self.frequenceEchText.setText("44100")
        self.nbSinus1.setChecked(True)
        self.nbFrequence = 1
        
        
        """Le nombre de fréquences à afficher sera envoyé à la méthode nbFrequence
        lorsque l'on change la valeur du radioButton"""
        self.nbSinus1.toggled.connect(lambda : self.affichageFrequence(1))
        self.nbSinus2.toggled.connect(lambda : self.affichageFrequence(2))
        self.nbSinus3.toggled.connect(lambda : self.affichageFrequence(3))
        self.nbSinus4.toggled.connect(lambda : self.affichageFrequence(4))
        self.nbSinus5.toggled.connect(lambda : self.affichageFrequence(5))
        
        """ Le signal du boutton "Créer"""
        self.creerButton.clicked.connect(self.creationSon)
        
        """ Le signal de la checkBox"""
        self.bruit.stateChanged.connect(lambda state: self.bruitChecked(state))
        
        """
        On créé deux attributs de liste qui contiendront les fréquences n°X ainsi
        que les entrées correspondantes.
        L'utilité est de pouvoir ensuite parcourir ces deux tableaux afin d'afficher ou
        de cacher chaque fréquence et entrée selon le radio boutton sélectionné.
        L'ordre dans lequel les fréquences sont ajouté à la liste est important puisqu'il
        corrspond à l'odre où les fréquences sont affichés à l'écran.
        """
        self.tableauFrequence = []
        self.tableauFrequenceText = []

        self.tableauFrequence.append(self.frequence1)
        self.tableauFrequence.append(self.frequence2)
        self.tableauFrequence.append(self.frequence3)
        self.tableauFrequence.append(self.frequence4)
        self.tableauFrequence.append(self.frequence5)
        
        self.tableauFrequenceText.append(self.frequence1Text)
        self.tableauFrequenceText.append(self.frequence2Text)
        self.tableauFrequenceText.append(self.frequence3Text)
        self.tableauFrequenceText.append(self.frequence4Text)
        self.tableauFrequenceText.append(self.frequence5Text)

        
        self.affichageFrequence() #Un appel initiatique
        
    def affichageFrequence(self, nbFrequence=1):
        """Cette méthode affichera autant de couple label:entrée que vaut
        nbFréquence : cette variable correspond au nombre de sinusoïde que 
        contiendra le signal créé. 
        Par défaut, nbFrequence = 1 car le radio boutton n°1 est selectionné
        par défaut (donc par défaut, on ne créera un son composé que d'une fréquence)
        On redimensionne également la fenêtre selon le nombre de fréquence affichés.
        """
        self.nbFrequence = nbFrequence
        
        for i in range(0,5):
            self.tableauFrequence[i].setVisible(False)
            self.tableauFrequenceText[i].setVisible(False)
        for i in range(0,self.nbFrequence):
            self.tableauFrequence[i].setVisible(True)
            self.tableauFrequenceText[i].setVisible(True)
            
        self.tabSoftware.resize(390, 170 + (self.nbFrequence-1)*20)
        self.setMinimumHeight(200 + (self.nbFrequence-1)*20)
        self.setMinimumWidth(410)
        self.resize(self.minimumWidth(), self.minimumHeight())
        
    def creationSon(self):
        """Cette méthode s'occupe de la création de notre fichier .wav, créé dans le 
        même dossier que notre executable.
        Si un fichier avec le nom spécifié existe déjà, il sera écrasé.
        32767 correspond à une amplitude de 1, -32767 à une amplitude de -1
        
        ### BRUIT ###
        Si la check box "Bruit" est cochée, le son générée sera aléatoire et non sinusoïdal
        Ceci est réalisé indépendament de ou des fréquence(s) renseignée(s)
        
        ### SINUSOIDE ###
        Le son créé sera composé des fréquences renseignées. Le nombre de point dépends
        de la fréquence d'échantillonage indiquée, par défaut 44.100 points.
        On aura en sortie une sinusoïde approximée mais suffisament précise pour
        produire un son parfait.
        courbeAuPointi vaut, en sortie de la deuxième boucle for, au maximum le nombre
        de fréquence (sin est compris entre -1 et 1, et puisqu'on peut additionner 4 fois dans la boucle for)
        c'est pourquoi avant d'écrire dans notre fichier audio à l'aide de .writeframesraw, on
        divise par nbFrequence afin d'obtenir une valeur d'amplitude entre -1 et 1.
        """
        self.statusbar.setStyleSheet("color : blue")
        self.statusbar.showMessage('Processing ...')
        
        wavef = wave.open('{}.wav'.format(self.nomSonText.text()),'w') #Nouveau fichier (Création / écrasement)
        wavef.setnchannels(1) # Son mono-canal
        wavef.setsampwidth(2) #La taille d'un échantillon en bytes
        wavef.setframerate(int(self.frequenceEchText.text())) #Le nombre de fenêtre
        
        if self.bruit.isChecked() :
            for i in range(int(self.dureeText.text()) * int(self.frequenceEchText.text())):
                value = random.uniform(-32767.0, 32767)
                packed_value = struct.pack('<h', value)
                wavef.writeframes(packed_value)
        else:
            for i in range(int(self.dureeText.text()) * int(self.frequenceEchText.text())): #range le nombre d'échantillons totaux
                courbeAuPointi = 0
                for _ in range(0, self.nbFrequence):
                    courbeAuPointi += math.sin(2*int(self.tableauFrequenceText[_].text())*math.pi*float(i)/float(self.frequenceEchText.text()))
                courbeAuPointi = int(32767.0 / self.nbFrequence * courbeAuPointi)
                wavef.writeframesraw( struct.pack('<h', courbeAuPointi ) ) #On incorpore le point dans le signal
            self.sinusoide() #On affiche la sinusoïde obtenue
       
        wavef.writeframes(str.encode('')) #Convertion en bytes
        wavef.close()
        
        self.statusbar.showMessage("Done", 4000)
        self.statusbar.setStyleSheet("color : green; font : italic")
        
        
        
    def bruitChecked(self, state):
        """ Cette méthode correspond au signal de la CheckBox "Bruit"
        Si la checkBox est cochée, on va rendre inutilisable toutes les entrées
        de fréquences puisque nous n'en auront pas besoin pour générer notre fichier .wav
        A l'inverse, si la checkbox est décochée, on active toutes les entrées afin
        que l'utilisateur puisse y entrer des fréquences pour produire le son.
        state peut prendre les valeurs 0 et 2 : 0 signife que la checkBox est décochée
        et 2 signifie qu'elle est cochée.
        """
        if state == 0:
            for _ in range(len(self.tableauFrequenceText)):
                self.tableauFrequenceText[_].setEnabled(True)
        elif state == 2:
            for _ in range(len(self.tableauFrequenceText)):
                self.tableauFrequenceText[_].setEnabled(False)
        
    def sinusoide(self):
        """Cette méthode affiche la sinusoïde obtenue après création dans une 
        QGraphicView. Cette QGraphicsView affichera la sinusoide que l'on dessinera
        dans sceneGraphique, notre QGraphicsScene.
        L'algorithme de calcul du point est le même. La différence
        réside dans le fait que l'on calcule le point i et le point i+1 afin
        de tracer une ligne reliant les deux points.
        courbeAuPointi correspond à notre ordonnée. A chaque tout de boucle on définit
        le niveau 0 à la moitiée de notre GraphicScene.
        On multiplie les incrémentation par 50 pour qu'elle puisse être visible à l'écran,
        on divise par le nombre de fréquence pour ne pas sortir du cadre de la 
        QGraphicView au cas où courbeAuPointi est plus grand que 1 après la deuxième boucle
        for.
        """
        self.sceneGraphique = QtWidgets.QGraphicsScene(0, 0, 1000, 200)
        size = self.sceneGraphique.sceneRect()
        
        for i in range(int(size.width())*int(self.dureeText.text())):
            courbeAuPointi = int(size.height()//2)
            courbeAuPointi1 = courbeAuPointi
            for _ in range(0, self.nbFrequence):
                courbeAuPointi += math.sin(2*int(self.tableauFrequenceText[_].text())*math.pi*float(i)/float(self.frequenceEchText.text()))*100//self.nbFrequence
                courbeAuPointi1 += math.sin(2*int(self.tableauFrequenceText[_].text())*math.pi*float(i+1)/float(self.frequenceEchText.text()))*100//self.nbFrequence
            self.sceneGraphique.addLine(i, courbeAuPointi, i+1, courbeAuPointi1, QPen(Qt.red))
            
        self.graphique.setScene(self.sceneGraphique)
        
        self.legendeGraphique.setText("Aperçu de {}.wav".format(self.nomSonText.text()))
        self.tabSoftware.resize(700, 300)
        self.setMinimumWidth(720)
        self.setMinimumHeight(330)
        
    def initTabAnalysePreSaved(self):
        """Méthode initialisant le deuxième onglet de notre interface QT
        avec les réglages et signaux souhaités. """
        self.FFTsizeText.setText("2**15")
        
        """Signal du bouton "Parcourir..." """
        self.parcourir.clicked.connect(self.selectionnerFichier)
        
        """Signal du bouton "Analyser" """
        self.analyserButton.clicked.connect(self.analyserSon)
        
    def selectionnerFichier(self):
        """Méthode appelée lorsque l'on clique sur le bouton "Parcourir..." 
        Elle ouvre un explorateur de fichiers, par défaut sur le bureau de l'utilisateur"""
        self.fichierChoisi = QtWidgets.QFileDialog().getOpenFileName(self, "Fichier audio à analyser", os.path.expanduser("~\\Desktop"), "Fichier .wav (*.wav)")
        self.fileNameText.setText(self.fichierChoisi[0])

    def analyserSon(self):
        """Cette méthode s'occupe de traiter de l'analyse de  notre son :
        elle utilise l'agorithme de la STFT pour décomposer notre signal.
        On analyse des fenêtre de Fourrier réduite, et non le son en intégralité. 
        Ainsi, on peut déterminer quelle note est jouée des des intervalles
        de temps très court.
        
        ### EXPLICATION DES VARIABLES ###
        - rate : la fréquence d'échantillonage de notre signal
        - signal : les données du sons étudié. Si il est Stéréo, on le reconvertit en mono
        - rééchantillone : le facteur de rééchantillonage, on rééchantillone notre signal
        pour ne le réduire qu'aux fréquences qui nous intéresses dans le cas de la flûte 
        afin d'augmenter le taux de calcul (car moins de points). Généralement, si on
        part de l'hypothèse que les sons sont échantillonés à 44.100 Hz, les fréquences possibles
        jouée par une flûtes son celle de la 4ème et 5ème octave, donc de 250Hz à 1000Hz.
        On peut ainsi rééchantillonné notre son à 4410Hz, il sera certes moins riches en
        fréquences parasites, mais il gardera toujours la bonne fréquence.
        - taille_decalage : il s'agit du nombre de points que l'on déplacera la fenetre de Hanning
        - taille_fenêtre : Nombre de points auxquels on applique la FFT
        - t_max : Longueur du signal étudié
        - total_segments : Nombre de segments (=fenêtres) nécessaires pour parcourir le son en 
        intégralité
        
        """
        rate, self.signal = read(self.fileNameText.text())
        if len(self.signal.shape) != 1:
            self.signal = np.array(self.signal.sum(axis=1), dtype='float64')
            
        
        rééchantillonage = 8
        freqenceEchantillonage = eval(self.FFTsizeText.text())
        
        self.signal = sig.decimate(self.signal, rééchantillonage, ftype='fir') 
        rate = rate // rééchantillonage
        dt = 1./rate 
        
        taille_fenêtre = 800
        taille_decalage = np.int32(np.floor(taille_fenêtre * (1-float(self.overlapText.text()))))
        total_segments = np.int32(np.ceil(len(self.signal) / np.float32(taille_decalage)))
        t_max = len(self.signal) / np.float32(rate)
        fenetreHanning = np.hanning(taille_fenêtre) * float(self.overlapText.text()) * 2 
        inner_pad = np.zeros((freqenceEchantillonage * 2) - taille_fenêtre)
        
        proc = np.concatenate((self.signal, np.zeros(freqenceEchantillonage)))     
        result = np.empty((total_segments, freqenceEchantillonage), dtype=np.float32)
        
        self.reconstitution = []
        self.textTraduction.setPlainText("")
        
        
        for i in range(total_segments):     
            décalage = taille_decalage * i  
            t = (décalage + taille_fenêtre)/rate
            segment = proc[décalage:décalage + taille_fenêtre]
            windowed = segment * fenetreHanning           
            padded = np.append(windowed, inner_pad)
            spectrum = np.fft.fft(padded) / freqenceEchantillonage 
            autopower = np.abs(spectrum * np.conj(spectrum))
            result[i] = autopower[:freqenceEchantillonage]                 
            freqSpectrum = np.fft.fftfreq(spectrum.size, dt)
            
            note = self.frequence_Midi(abs(freqSpectrum[np.argmax(abs(spectrum))])) 
        
#            self.textTraduction.setPlainText(self.textTraduction.toPlainText() + "Entre {}s et {}s : F = {}\n".format( round(décalage/rate, 3), round(t, 3), abs(freqSpectrum[np.argmax(abs(spectrum))]) ) )
#            self.textTraduction.setPlainText(self.textTraduction.toPlainText() + "Note MIDI : {} - ".format(note))
#            self.textTraduction.setPlainText(self.textTraduction.toPlainText() + "Note : {}\n\n".format(self.Midi_Note(note)))

            self.reconstitution.append( [ ['%.3f' % (décalage/rate), '%.3f' % t if t <t_max else t_max], [note, max(result[i])] ] ) 
            
        
        for _ in range(len(self.reconstitution)):
            self.reconstitution[_][1][1] = round(20*np.log10(self.reconstitution[_][1][1]), 0)
            self.reconstitution[_][1][1]= np.clip(self.reconstitution[_][1][1], -10, 200)
            
        self.tabSoftware.resize(700, self.tabSoftware.height() )
        self.setMinimumWidth(720)
        self.setMinimumHeight(175)
        
        self.traduction = self.traduction_reconstitution()
        
        mon_fichier = open("traduction.txt", "w") 
        mon_fichier.write("{}".format(self.traduction))
        mon_fichier.close()
        
        print("\n{}".format(self.traduction) )
     
    def frequence_Midi(self, frequence):
        """Méthode qui renvoit la conversion en MIDI d'une fréquence passée en paramètre
        La formule qu'on affecte à note correspond à celle de la conversion frequence -> MIDI
        Elle retourne la noe et l'octave
        Elle s'aide de la liste NOTE_MIDI définie en début de code"""
        note=int(round((12*(np.log2(np.atleast_1d(frequence))-np.log2(440)) + 69)[0]))
        
        n = int(round(12*(np.log2(np.atleast_1d(frequence))-np.log2(440))[0]))
        
        octave = 4 + n//12
        
        return NOTE_MIDI[note%12]+str(octave)
        
    def Midi_Note(self, note):
        """Méthode qui renvoit la conversion en note conventionnelle d'une note MIDI passée en paramètre
        Elle s'aide de note liste NOTE défini en début de code"""
        return "{}".format(NOTE[note[0]])+"{}".format(note[-1])       
    
    
    def traduction_reconstitution(self):
        """Méthode qui renvoit une "traduction" de la reconstitution :
        On stocke les notes jouées en ignorant les decrescendos et les silences 
        avec leur début et leur fin dans un tableau de tuples de la forme ((début_note, fin_note), note)"""
            
        temps_ecoule = 0
        traduction = []

        for indice in range(len(self.reconstitution) - 1):
            if self.reconstitution[indice][1][0] != self.reconstitution[indice+1][1][0]:
                traduction.append(((temps_ecoule,self.reconstitution[indice][0][1]), self.reconstitution[indice][1]))
                temps_ecoule = self.reconstitution[indice][0][1]
        return traduction
    
if __name__ == '__main__': #Si l'executable est lancé directement
    
    app = QApplication(sys.argv) #On démarre l'interface Qt
    app.aboutToQuit.connect(app.deleteLater) #Ligne nécéssaire pour éviter les erreurs de kernel

    Soft = software() #On démarre notre programme à l'aide de cette commande
    Soft.show()
    app.exec_() #Pour éviter les Warnings