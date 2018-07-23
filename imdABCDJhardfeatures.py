#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ircamABCDJhardfeatures.py
#
# Copyright (c) 2018 Geoffroy Peeters <geoffroy.peeters@ircam.fr>

# This file is part of ircamABCDJhardfeatures.

# ircamABCDJhardfeatures is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ircamABCDJhardfeatures is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ircamABCDJhardfeatures.  If not, see <http://www.gnu.org/licenses/>.

# Author: G Peeters <geoffroy.peeters@ircam.fr.fr> http://www.ircam.fr

"""
    ircamABCDJhardfeatures is a python script, a set of function and classes
    developed by IRCAM to compute the "hard" features defined by TU-Belrin
    within the ABC_DJ H2020 project

:author: geoffroy.peeters@ircam.fr
:version: 1.1
:last-edit: 2018/04/30
"""

import glob
import os
import xmltodict
import json
import numpy as np
from collections import OrderedDict
import getopt
import sys

#import ipdb
#import xlrd

import peeaudiolight
import peeTimbreToolbox


exec_d = {}
exec_d['MPG123'] = '/opt/local/bin/mpg123'
# exec_d['MPG123'] = '/usr/local/bin/mpg123'
exec_d['imdABCDJ'] = './_bin/imdABCDJ-1.1.0'



class C_harmonicInformation:
    """
        class definition for chord/harmonic information
    """

    root_l = []
    keyName_l = []
    chordName_l = []
    matChordKey_m = []

    def __init__(self):
        self.root_l = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab',
                  'A', 'Bb', 'B']
        mode_l = ['Maj', 'min']
        type_l = ['maj', 'min', 'dim', 'aug']
        nbRoot = len(self.root_l)
        nbMode = len(mode_l)
        nbType = len(type_l)

        nbChroma = 12
        templateKey_m = np.zeros((nbChroma, nbMode))
        # --- Major mode
        templateKey_m[[0, 2, 4, 5, 7, 9, 11], 0] = 1
        # --- Minor mode
        templateKey_m[[0, 2, 3, 5, 7, 8, 10], 1] = 1

        templateChord_m = np.zeros((nbChroma, nbType))
        # --- Major chord
        templateChord_m[[0, 4, 7], 0] = 1
        # --- minor chord
        templateChord_m[[0, 3, 7], 1] = 1
        # --- diminished chord
        templateChord_m[[0, 3, 6], 2] = 1
        # --- augmented chord
        templateChord_m[[0, 4, 8], 3] = 1

        self.keyName_l = []
        self.chordName_l = []

        matKey_m = np.zeros((nbChroma, nbRoot*nbMode))
        matChord_m = np.zeros((nbChroma, nbRoot*nbType))
        self.matChordKey_m = np.zeros((nbRoot*nbType, nbRoot*nbMode))

        count = 0
        for numMode in range(0, nbMode):
            for numRoot in range(0, nbRoot):
                self.keyName_l.append(self.root_l[numRoot] + mode_l[numMode])
                matKey_m[:, count] = np.roll(templateKey_m[:, numMode], numRoot)
                count += 1

        count = 0
        for numType in range(0, nbType):
            for numRoot in range(0, nbRoot):
                self.chordName_l.append(self.root_l[numRoot] + type_l[numType])
                matChord_m[:, count] = np.roll(templateChord_m[:, numType], numRoot)
                count += 1

        for numChord in range(0, nbRoot*nbType):
            for numKey in range(0, nbRoot*nbMode):
                self.matChordKey_m[numChord,numKey] = np.sum(np.multiply(matChord_m[:, numChord], matKey_m[:,numKey]))==3

        #[self.chordName_l[num] for num in range(0,4*12) if self.matChordKey_m[num,0] ]


    def __setattr__(self, attrName, val):
        if hasattr(self, attrName):
            self.__dict__[attrName] = val
        else:
            raise Exception("self.%s note part of the fields" % attrName)



def F_computeTimbre(audioFile, outTTBFile, myResult):
    """
        Compute features from the TimbreToolbox (TTB)
    """

    if os.path.exists(outTTBFile)==False:
        my = peeaudiolight.C_AudioAnalysis(audioFile, do_stereo2mono=True)

        descHub_d = peeTimbreToolbox.F_computeAllDescriptor(my.data_v[0,:], my.x_sr_hz)
        descHub_d = peeTimbreToolbox.F_temporalModeling(descHub_d)

        peeTimbreToolbox.F_save(descHub_d, outTTBFile)

    descHub_d = peeTimbreToolbox.F_load(outTTBFile)

    # --- 2018/07/09: remove pickle file (request from Stefano)
    os.remove(outTTBFile)

    if True:

        map1_d = {'TTT': 'TEE', 'TTF': 'ERBfft', 'TTG': 'ERBgam', 'TTH': 'Harmonic', 'TTM': 'STFTmag', 'TTP': 'STFTpow'}
        map2_d = {'En': 'RMSEnv',
                    'Sd': 'SpecDecr', 'Sv': 'SpecVar', 'Fe': 'FrameErg', 'Sk': 'SpecKurt', 'Ss': 'SpecSpread', 'Sf': 'SpecFlat', 'Sw': 'SpecSkew', 'Sc': 'SpecCent', 'Sl': 'SpecSlope', 'Sr': 'SpecRollOff', 'St': 'SpecCrest',
                    'He': 'HarmErg', 'No': 'Noisiness', 'F0': 'F0', 'Ih': 'InHarm', 'Hd': 'HarmDev', 'T3': 'TriStim3'}
        map3_d = {'mi': 'min', 'ma': 'max', 'me': 'mean', 'st': 'std'}

        nom_d = ['TTT_Enmi', 'TTT_Enme', 'TTT_Enst']
        for nom in nom_d:
            family = map1_d[nom[0:3]]
            descriptor = map2_d[nom[4:6]]
            temporalModeling = map3_d[nom[6:]]
            num = 0
            #print("%s -> %s/%s/%s/%d" % (nom, family, descriptor, temporalModeling, num))
            myResult[nom] = descHub_d[family][descriptor][temporalModeling][num]

        nom_d = ['TTA_01mi', 'TTA_01ma', 'TTA_02ma', 'TTA_02me', 'TTA_08mi', 'TTA_08me', 'TTA_12mi', 'TTA_12ma']
        nom_d = []
        for nom in nom_d:
            family = 'AS'
            descriptor = 'AutoCorr'
            temporalModeling = map3_d[nom[6:]]
            num = int(nom[4:6])-1
            #print("%s -> %s/%s/%s/%d" % (nom, 'AS', 'AutoCorr', temporalModeling, num))
            myResult[nom] = descHub_d[family][descriptor][temporalModeling][num]

        nom_d = [#'TTF_Sdme', 'TTF_Svma', 'TTF_Svme', 'TTF_Femi', 'TTF_Fema', 'TTF_Feme', 'TTF_Fest', 'TTF_Sfme',
                    #'TTG_Fema', 'TTG_Feme', 'TTG_Fest', 'TTG_Skst', 'TTG_Ssme', 'TTG_Svmi', 'TTG_Swme', 'TTG_Swst',
                    #'TTH_Heme', 'TTH_Noma', 'TTH_Nome', 'TTH_Nost', 'TTH_F0st', 'TTH_Ihma', 'TTH_Ihst', 'TTH_Scmi', 'TTH_Scst', 'TTH_Slma', 'TTH_Slme', 'TTH_Slmi', 'TTH_Slst', 'TTH_Svme', 'TTH_Svst', 'TTH_Swmi', 'TTH_T3me', 'TTH_T3st', 'TTH_Hdma', 'TTH_Hdme',
                    'TTM_Fema', 'TTM_Feme', 'TTM_Fest', 'TTM_Scme', 'TTM_Sdmi', 'TTM_Sfma', 'TTM_Skme', 'TTM_Slme', 'TTM_Srme', 'TTM_Srst', 'TTM_Ssme', 'TTM_Ssmi', 'TTM_Stma', 'TTM_Stmi',
                    'TTP_Fema', 'TTP_Femi', 'TTP_Fest', 'TTP_Sdst', 'TTP_Sfme', 'TTP_Slme', 'TTP_Srmi', 'TTP_Ssmi', 'TTP_Stmi', 'TTP_Stst', 'TTP_Svmi', 'TTP_Swst']
        for nom in nom_d:
            family = map1_d[nom[0:3]]
            descriptor = map2_d[nom[4:6]]
            temporalModeling = map3_d[nom[6:]]
            num = 0
            #print("%s -> %s/%s/%s/%d" % (nom, family, descriptor, temporalModeling, num))
            myResult[nom] = descHub_d[family][descriptor][temporalModeling][num]

    else:
        #myResult['TTB_Fundamental Frequency_Mean'] = descHub_d['Harmonic']['F0']['median']
        #myResult['TTB_Fundamental Frequency_SD'] = descHub_d['Harmonic']['F0']['iqr']

        myResult['TTB_RMS Energy_Envelope (technical, by STFT)_Mean'] = descHub_d['TEE']['RMSEnv']['median'][0]
        myResult['TTB_RMS Energy_Envelope (technical, by STFT)_SD'] = descHub_d['TEE']['RMSEnv']['iqr'][0]
        myResult['TTB_RMS Energy_Envelope (technical, by STFT)_Crest'] = descHub_d['TEE']['RMSEnv']['crest'][0]
        myResult['TTB_Frame_Energy_Mean'] = descHub_d['STFTmag']['FrameErg']['median'][0]
        myResult['TTB_Frame_Energy_SD'] = descHub_d['STFTmag']['FrameErg']['iqr'][0]

        # --- TTB_Temporal_Centroid_Mean
        # --- TTB_Temporal_Centroid_SD

        myResult['TTB_Spectral_Centroid_Mean'] = descHub_d['STFTmag']['SpecCent']['median'][0]
        myResult['TTB_Spectral_Centroid_SD'] = descHub_d['STFTmag']['SpecCent']['iqr'][0]
        myResult['TTB_Spectral_Spread_Mean'] = descHub_d['STFTmag']['SpecSpread']['median'][0]
        myResult['TTB_Spectral_Spread_SD'] = descHub_d['STFTmag']['SpecSpread']['iqr'][0]
        myResult['TTB_Spectral_Skewness_Mean'] = descHub_d['STFTmag']['SpecSkew']['median'][0]
        myResult['TTB_Spectral_Skewness_SD'] = descHub_d['STFTmag']['SpecSkew']['iqr'][0]
        myResult['TTB_Spectral_Kurtosis_Mean'] = descHub_d['STFTmag']['SpecKurt']['median'][0]
        myResult['TTB_Spectral_Kurtosis_SD'] = descHub_d['STFTmag']['SpecKurt']['iqr'][0]
        myResult['TTB_Spectral_Slope_Mean'] = descHub_d['STFTmag']['SpecSlope']['median'][0]
        myResult['TTB_Spectral_Slope_SD'] = descHub_d['STFTmag']['SpecSlope']['iqr'][0]
        myResult['TTB_Spectral_Decrease_Mean'] = descHub_d['STFTmag']['SpecDecr']['median'][0]
        myResult['TTB_Spectral_Decrease_SD'] = descHub_d['STFTmag']['SpecDecr']['iqr'][0]
        myResult['TTB_Spectral_Rolloff_Mean'] = descHub_d['STFTmag']['SpecRollOff']['median'][0]
        myResult['TTB_Spectral_Rolloff_SD'] = descHub_d['STFTmag']['SpecRollOff']['iqr'][0]
        myResult['TTB_Spectro-temporal_variation_Mean'] = descHub_d['STFTmag']['SpecVar']['median'][0]
        myResult['TTB_Spectro-temporal_variation_SD'] = descHub_d['STFTmag']['SpecVar']['iqr'][0]
        myResult['TTB_Spectral_Flatness_Mean'] = descHub_d['STFTmag']['SpecFlat']['median'][0]
        myResult['TTB_Spectral_Flatness_SD'] = descHub_d['STFTmag']['SpecFlat']['iqr'][0]
        myResult['TTB_Spectral_Crest_Mean'] = descHub_d['STFTmag']['SpecCrest']['median'][0]
        myResult['TTB_Spectral_Crest_SD'] = descHub_d['STFTmag']['SpecCrest']['iqr'][0]

    return myResult


def F_parseStruct(jsonData, myResult, startExtract=-1., stopExtract=--1.):
    """
        Compute features related to structure
    """

    struct_l = []

    if type(jsonData['musicdescription']['segment']) is list:
        """ there are several segments => list """

        if (startExtract > -1.) and (stopExtract > -1.):
            """ Look for segment changes in the interval [start, stop] """
            seg_l = []
            for seg in jsonData['musicdescription']['segment']:
                if 'structtype' in seg.keys():
                    start = float(seg['@time'])
                    stop = float(seg['@time']) + float(seg['@length'])
                    if (startExtract <= start) & (start <= stopExtract):
                        # the segment starts in [startExtract, stopExtract]
                        seg_l.append(seg)
                    elif (startExtract <= stop) & (stop <= stopExtract):
                        # the segment stops in [startExtract, stopExtract]
                        seg_l.append(seg)
                    elif (start < startExtract) & (stopExtract < stop):
                        # the segment crosses [startExtract, stopExtract] without stopping
                        seg_l.append(seg)
        else:
            seg_l = [seg for seg in jsonData['musicdescription']['segment'] if ('structtype' in seg.keys())]


        nbSeg = len(seg_l)
        for numSeg in range(0, nbSeg):
            struct_l.append( seg_l[numSeg]['structtype']['@value'] )

    else:
        """ there is only one segment => no list """

        struct_l.append(jsonData['musicdescription']['segment']['structtype']['@value'])

    myResult['ICS_Part_Sequence_Total'] = len(struct_l)
    myResult['ICS_Part_Sequence_Unique'] = len(set(struct_l))

    return myResult


def F_parseRhythm(jsonData, myResult):
    """
        Compute features related to rhythm
    """

    ###myResult['IRC_Length'] = float(jsonData['musicdescription']['global']['@length'])
    ###myResult['ICB_Meter'] = jsonData['musicdescription']['global']['rhythmtype']['meter']

    myResult['ICB_Meter23'] = myResult['ICB_Meter32'] = 0
    if jsonData['musicdescription']['global']['rhythmtype']['meter'] == '23':
        myResult['ICB_Meter23'] = 1
    if jsonData['musicdescription']['global']['rhythmtype']['meter'] == '32':
        myResult['ICB_Meter32'] = 1

    myResult['ICB_BPM_Mean'] = float(jsonData['musicdescription']['global']['rhythmtype']['bpm_mean'])
    myResult['ICB_BPM_SD'] = float(jsonData['musicdescription']['global']['rhythmtype']['bpm_std'])
    myResult['ICB_perc_norm'] = float(jsonData['musicdescription']['global']['rhythmtype']['percussivity'])
    myResult['ICB_complex_norm'] = float(jsonData['musicdescription']['global']['rhythmtype']['complexity'])
    myResult['ICB_speed_norm_A'] = float(jsonData['musicdescription']['global']['rhythmtype']['speedA'])
    myResult['ICB_speed_norm_B'] = float(jsonData['musicdescription']['global']['rhythmtype']['speedB'])
    myResult['ICB_periodicity'] = float(jsonData['musicdescription']['global']['rhythmtype']['periodicity'])
    ###myResult['AccentStruct'] = -999

    return myResult


def F_parseKeyMode(jsonData, myResult, myHarmonicInformation):
    """
        Compute features related to key and mode
    """

    key = jsonData['musicdescription']['global']['harmonictype']['key']
    mode = jsonData['musicdescription']['global']['harmonictype']['mode']

    myResult['ICK_Key_PC'] = myHarmonicInformation.keyName_l.index(key+mode)
    ###myResult['ICK_Key_KN'] = key
    ###myResult['ICK_Key_KM'] = mode
    ###myResult['Key_Changes'] = -999

    myResult['ICK_Key_Pcminor'] = 0
    if mode == 'min':
        myResult['ICK_Key_Pcminor'] = 1

    for x in range(0,11):
        nom = 'ICK_Key_PC' + str(x+1)
        if myHarmonicInformation.root_l[x] == key:
            myResult[nom] = 1
        else:
            myResult[nom] = 0

    return myResult


def F_isIntervalDown(rootNotePrev, rootNoteNext, nbHalfDown):
    """
        Compute ...
    """

    return ((rootNotePrev - rootNoteNext) == nbHalfDown) | ((rootNoteNext - rootNotePrev) == (12-nbHalfDown))


def F_parseChord(jsonData, myResult, myHarmonicInformation):
    """
        Compute features derived from chord estimation (ircamchord)
    """

    do_verbose = False

    duration_sec = float(jsonData['musicdescription']['global']['@length'])
    samplingRate = float(jsonData['musicdescription']['global']['@samplingrate'])

    chord_l = []
    if type(jsonData['musicdescription']['segment']) is list:
        seg_l = [seg for seg in jsonData['musicdescription']['segment'] if 'chordtype' in seg.keys()]

        nbSeg = len(seg_l)

        for numSeg in range(0, nbSeg):
            seg_l[numSeg]['@time']
            seg_l[numSeg]['@length']
            chord_l.append(seg_l[numSeg]['chordtype']['@value'])

    else: # --- there is only one segment
        jsonData['musicdescription']['segment']['@time']
        jsonData['musicdescription']['segment']['@length']
        chord_l.append(jsonData['musicdescription']['segment']['chordtype']['@value'])

    nbChord = 1.0*len(chord_l)
    nbUniqChord = 1.0*len(set(chord_l))
    nbmin = 1.0*sum([chord.find('min') > 0 for chord in chord_l])
    nbMaj = 1.0*sum([chord.find('maj') > 0 for chord in chord_l])


    myResult['Chords_Num_01'] = nbChord / duration_sec
    myResult['Chords_Num_02'] = nbUniqChord / duration_sec
    if nbChord>0.0:
        myResult['Chords_Mode_01'] = nbmin / nbChord
        myResult['Chords_Mode_02'] = nbMaj / nbChord
    else:
        myResult['Chords_Mode_01'] = 0
        myResult['Chords_Mode_02'] = 0

    if nbmin>0.0:
        myResult['Chords_Mode_03'] = nbMaj / nbmin
    else:
        myResult['Chords_Mode_03'] = 0

    """ Ratio of non major or minor-based chords / total number of chords """
    ###myResult['Chords_Mode_04'] = -999
    """ Ratio of pure triads / triads with additional notes """
    ###myResult['Chords_Add_01'] = -999
    """ Ratio of sum of additional notes of all triads /  total number of triads """
    ###myResult['Chords_Add_02'] = -999


    """ Ratio of functional chords / non-functional chords.
    Functional is defined as root note of the chord is on the degree I, ii, iii, IV, V or iv
    where song key mode is 'major or root note of chord is on degree i, III, iv, v, V, VI or VII where song key mode is "minor". """
    nbChordInKey = 0.0
    for chord in chord_l:
        nbChordInKey += myHarmonicInformation.matChordKey_m[myHarmonicInformation.chordName_l.index(chord), myResult['ICK_Key_PC']]
    #myResult['Chords_Func'] = nbChordInKey / (nbChord-nbChordInKey)
    myResult['Chords_Func'] = nbChordInKey / (nbChord)

    """ Ratio of chords with root note as bass note /  chords with different note as bass note """
    ###myResult['Chords_Bass_01'] = -999

    """ Ratio of chords with root note as bass note /  chords with 3 (Third) as bass note """
    ###myResult['Chords_Bass_02'] = -999

    """ Ratio of chords with root note as bass note /  chords with 5 (Fifth) as bass note """
    ###myResult['Chords_Bass_03'] = -999

    """ Ratio of chords with root note as bass note /  chords with 7 (Seventh) as bass note """
    ###myResult['Chords_Bass_04'] = -999

    """ Force a chord list to test the functions below """
    #chord_l = ['Dmaj', 'Gmaj', 'Cmaj']
    #chord_l = ['Amaj', 'Fmaj', 'Cmaj', 'Amaj', 'Fmaj', 'Cmaj', 'Cmaj', 'Amaj', 'Amaj', 'Fmaj', 'Cmaj', 'Cmaj', 'Amaj']

    """ Perfect cadence type 1: Ratio of total number of successions [5, 1] / total
    number of harmony changes (i.e. two subsequent chords having a different root note) """
    """ count number of V -> I """
    rootNoteChanges = 0
    count = 0
    for numChord in range(1, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        rootNoteChanges += rootNote2 != rootNote1

        if F_isIntervalDown(rootNote1, rootNote2, 7):
            if do_verbose: print "(%d) V -> I: %s -> %s" % (numChord, chord_l[numChord-1], chord_l[numChord])
            count += 1

    if rootNoteChanges==0: rootNoteChanges = 1

    myResult['Chords_Cad_01'] = 1.0*count / (1.0*rootNoteChanges)

    """ count number of IV -> V -> I """
    count = 0
    for numChord in range(2, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-2]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote3 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        if F_isIntervalDown(rootNote1, rootNote2, 10) & F_isIntervalDown(rootNote2, rootNote3, 7):
            if do_verbose: print "(%d) IV -> V -> I: %s -> %s -> %s" % (numChord, chord_l[numChord-2], chord_l[numChord-1], chord_l[numChord])
            count += 1

    myResult['Chords_Cad_02'] = 1.0*count / (1.0*rootNoteChanges)

    """ count number of II -> V -> I """
    count = 0
    for numChord in range(2, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-2]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote3 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        if F_isIntervalDown(rootNote1, rootNote2, 7) & F_isIntervalDown(rootNote2, rootNote3, 7):
            if do_verbose: print "(%d) II -> V -> I: %s -> %s -> %s" % (numChord, chord_l[numChord-2], chord_l[numChord-1], chord_l[numChord])
            count += 1

    myResult['Chords_Cad_03'] = 1.0*count / (1.0*rootNoteChanges)

    """ count number of VI -> II -> V -> I """
    count = 0
    for numChord in range(3, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-3]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord-2]) % 12
        rootNote3 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote4 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        if F_isIntervalDown(rootNote1, rootNote2, 7) & F_isIntervalDown(rootNote2, rootNote3, 7) & F_isIntervalDown(rootNote3, rootNote4, 7):
            if do_verbose: print "(%d) VI -> II -> V -> I: %s -> %s -> %s -> %s" % (numChord, chord_l[numChord-3], chord_l[numChord-2], chord_l[numChord-1], chord_l[numChord])
            count += 1

    myResult['Chords_Turn_01'] = 1.0*count / (1.0*rootNoteChanges)

    """ count number of 1, 4, 1, 5, 4, 1 """
    count = 0
    for numChord in range(5, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-5]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord-4]) % 12
        rootNote3 = myHarmonicInformation.chordName_l.index(chord_l[numChord-3]) % 12
        rootNote4 = myHarmonicInformation.chordName_l.index(chord_l[numChord-2]) % 12
        rootNote5 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote6 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        if F_isIntervalDown(rootNote1, rootNote2, 7) & F_isIntervalDown(rootNote2, rootNote3, 5) & F_isIntervalDown(rootNote3, rootNote4, 5) & F_isIntervalDown(rootNote4, rootNote5, 2) & F_isIntervalDown(rootNote5, rootNote6, 5):
            if do_verbose: print "(%d) 1, 4, 1, 5, 4, 1: %s -> %s -> %s -> %s -> %s -> %s" % (numChord, chord_l[numChord-5], chord_l[numChord-4], chord_l[numChord-3], chord_l[numChord-2], chord_l[numChord-1], chord_l[numChord])
            count += 1

    myResult['Chords_Turn_02'] = 1.0*count / (1.0*rootNoteChanges)

    """ count number of I ->V -> II -> IV """
    count = 0
    for numChord in range(3, len(chord_l)):
        rootNote1 = myHarmonicInformation.chordName_l.index(chord_l[numChord-3]) % 12
        rootNote2 = myHarmonicInformation.chordName_l.index(chord_l[numChord-2]) % 12
        rootNote3 = myHarmonicInformation.chordName_l.index(chord_l[numChord-1]) % 12
        rootNote4 = myHarmonicInformation.chordName_l.index(chord_l[numChord]) % 12

        if F_isIntervalDown(rootNote1, rootNote2, 5) & F_isIntervalDown(rootNote2, rootNote3, 5) & F_isIntervalDown(rootNote3, rootNote4, 9):
            if do_verbose: print "(%d) I ->V -> II -> IV: %s -> %s -> %s -> %s" % (numChord, chord_l[numChord-3], chord_l[numChord-2], chord_l[numChord-1], chord_l[numChord])
            count += 1

    myResult['Chords_Turn_03'] = 1.0*count / (1.0*rootNoteChanges)


    firstDegree = myResult['ICK_Key_PC'] % 12
    rootNote_l = [myHarmonicInformation.chordName_l.index(chord) % 12 for chord in chord_l]

    """ compute average length between two successive tonics """
    length_l = F_getInterval(rootNote_l, firstDegree, do_verbose)
    if len(length_l) & False:
        myResult['Chords_TonicDist'] = sum(length_l) / len(length_l)
    else:
        #myResult['Chords_TonicDist'] = -999
        # Get most frequency chord
        count_v = np.zeros(12,)
        for numChord in range(0, len(rootNote_l)): count_v[rootNote_l[numChord]] = count_v[rootNote_l[numChord]] + 1
        firstDegree = np.argmax(count_v)
        length_l = F_getInterval(rootNote_l, firstDegree, do_verbose)
        if len(length_l)==0:
            myResult['Chords_TonicDist'] = 0
        else:
            myResult['Chords_TonicDist'] = sum(length_l) / len(length_l)

    return myResult


def F_getInterval(rootNote_l, firstDegree, do_verbose):
    """
        Compute the length between two successive tonics chords
    """

    start = -1
    length_l = []
    for numChord in range(0, len(rootNote_l)):
        if rootNote_l[numChord] == firstDegree:
            if start == -1:
                start = numChord
            else:
                stop = numChord
                length_l.append(stop-start)
                if do_verbose: print length_l
                start = numChord
    return length_l




def F_computeMfcc(jsonData, myResult):
    """
        Compute MFCC features
    """

    mean_v = [float(aaa) for aaa in jsonData['musicdescription']['global']['lowleveltype'][3]['#text'].split(' ')]
    list_l = ['MFCC_Band_01_MEAN', 'MFCC_Band_02_MEAN', 'MFCC_Band_03_MEAN', 'MFCC_Band_04_MEAN', 'MFCC_Band_05_MEAN', 'MFCC_Band_06_MEAN', 'MFCC_Band_07_MEAN', 'MFCC_Band_08_MEAN', 'MFCC_Band_09_MEAN', 'MFCC_Band_10_MEAN', 'MFCC_Band_11_MEAN', 'MFCC_Band_12_MEAN', 'MFCC_Band_13_MEAN']
    #for num in range(0, 12):
    #for num in range(0, 13):
    for num in [0,1,2,7,8]:
        myResult[list_l[num]] = mean_v[num]

    std_v = [float(aaa) for aaa in jsonData['musicdescription']['global']['lowleveltype'][4]['#text'].split(' ')]
    list_l = ['MFCC_Band_01_SD', 'MFCC_Band_02_SD', 'MFCC_Band_03_SD', 'MFCC_Band_04_SD', 'MFCC_Band_05_SD', 'MFCC_Band_06_SD', 'MFCC_Band_07_SD', 'MFCC_Band_08_SD', 'MFCC_Band_09_SD', 'MFCC_Band_10_SD', 'MFCC_Band_11_SD', 'MFCC_Band_12_SD', 'MFCC_Band_13_SD']
    #for num in range(0, 12):
    #for num in range(0, 13):
    for num in [0,1,4]:
        myResult[list_l[num]] = std_v[num]

    return myResult


def F_parseTag(jsonData, myResult):
    """
        Parse Tag (genre, mood, ...) information
    """

    myLocalResult = OrderedDict()

    list_l = ['genre', 'instrumentation', 'intensity', 'pop-appeal', 'styles', 'timbre', 'vocals-1', 'vocals-2']
    for numDD in range(0,8):
        oneDescriptionDefinition = jsonData['musicdescription']['descriptiondefinition'][numDD+4]
        label_l = [label['@name'] for label in oneDescriptionDefinition['dictionary']['label']]
        ID = oneDescriptionDefinition['@id']
        # print list_l[numDD]
        # print label_l

        tagtype_l = [tagtype for tagtype in jsonData['musicdescription']['global']['tagtype'] if tagtype['@id']==ID]
        value_l = []
        for label in label_l:
            subtagtype_l = [subtagtype for subtagtype in tagtype_l if subtagtype['@value'] == label]
            confidence = float(subtagtype_l[0]['@confidence'])
            myResult[list_l[numDD] + '-' + label.replace('&','N')] = confidence
            value_l.append(confidence)

        if list_l[numDD] == 'pop-appeal':
            myResult['pop-appeal'] = value_l.index(max(value_l)) + 1
        if list_l[numDD] == 'intensity':
            myResult['intensity'] = value_l.index(max(value_l)) + 1

    return myResult


def F_decodeAndCompute(audioFile, TMP_DIR):
    """
        Perform the audio decoding (mp3 to wav), imdABCDJ computation and assign the filepaths
    """

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    rootFileExtract = audioFile.split('/')[-1]

    if audioFile.endswith('.mp3'):
        processAudioFile = TMP_DIR + rootFileExtract.replace('.mp3', '-converted.wav')
        if not os.path.isfile(processAudioFile):
            os.system('%s -w "%s" "%s"' % (exec_d['MPG123'], processAudioFile, audioFile))
        audioFile = processAudioFile

    xmlFile = TMP_DIR + rootFileExtract + '.imd.xml'
    pickleFile = TMP_DIR + rootFileExtract + '.ttb.pickle'
    jsonFile = TMP_DIR + rootFileExtract + '.hardFeatures.json'

    if os.path.exists(xmlFile) is False:
        os.system('%s -i "%s" -o "%s"' % (exec_d['imdABCDJ'], audioFile, xmlFile))
    with open(xmlFile, 'r') as f:
        xmlData = f.read()
    jsonData = xmltodict.parse(xmlData)

    info_d = {'audioFile': audioFile, 'xmlFile': xmlFile, 'jsonData': jsonData, 'pickleFile': pickleFile, 'jsonFile':jsonFile}
    return info_d


def F_computeOneFile(audioFileFull='', audioFileExtract='', xmlFile='', startExtract=-1., stopExtract=-1, jsonFile='', TMP_DIR=''):
    """
        Compute features for a single (pair of) audioFile (full duration and extract)
    """

    import time
    t = time.time()

    myResult = OrderedDict()
    myHarmonicInformation = C_harmonicInformation()

    if len(audioFileFull) and len(audioFileExtract):
        """
            Usage 1: F_computeOneFile(audioFileFull, audioFileExtract, start, stop, jsonFile)
                extract the content from audioFileFull for structure and map it (using start and stop) to audioFileExtract
                extract the rest of the content from audioFileExtract
        """
        full_d = F_decodeAndCompute(audioFileFull, TMP_DIR)
        extract_d = F_decodeAndCompute(audioFileExtract, TMP_DIR)
        myResult['filepath'] = audioFileExtract

        """ STRUCTURE """
        myResult = F_parseStruct(full_d['jsonData'], myResult, startExtract, stopExtract)
        data_d = extract_d

    elif False:
        """
        Usage 2: F_computeOneFile(audioFileFull, jsonFile)
            extract the content of the whole audioFileFull
        """

        full_d = F_decodeAndCompute(audioFileFull, TMP_DIR)
        myResult['filepath'] = audioFileFull

        """ STRUCTURE """
        ###myResult = F_parseStruct(full_d['jsonData'], myResult)
        data_d = full_d

    else:
        rootFileExtract = audioFileFull.split('/')[-1]
        pickleFile = TMP_DIR + rootFileExtract + '.ttb.pickle'

        with open(xmlFile, 'r') as f:
            xmlData = f.read()
        jsonData = xmltodict.parse(xmlData)

        full_d = {'audioFile': audioFileFull, 'xmlFile': xmlFile, 'jsonData': jsonData, 'pickleFile': pickleFile, 'jsonFile':jsonFile}

        myResult['filepath'] = audioFileFull

        """ STRUCTURE """
        ###myResult = F_parseStruct(full_d['jsonData'], myResult)
        data_d = full_d


    """ BEAT """
    myResult = F_parseRhythm(data_d['jsonData'], myResult)

    """ KEY """
    myResult = F_parseKeyMode(data_d['jsonData'], myResult, myHarmonicInformation)

    """ CHORD """
    myResult = F_parseChord(data_d['jsonData'], myResult, myHarmonicInformation)

    del myResult['ICK_Key_PC']

    """ MELODY """
    # print "melody %s" % (audioFile)
    # outMelodyFile = OUTPUT_DIR + rootFile + '.melody.yaml'
    # if os.path.exists(outMelodyFile) is False:
    #    F_computeMelodia(audioFile, outMelodyFile, outMelodyFile + '.txt')

    """ AUDIO QUALITY """
    ###myResult['MonoCompatibility_Mean'] = data_d['jsonData']['musicdescription']['global']['lowleveltype'][5]['#text']
    myResult['MonoCompatibility'] = int(np.round(float(data_d['jsonData']['musicdescription']['global']['lowleveltype'][5]['#text'])))
    ###myResult['SamplingRate'] = float(data_d['jsonData']['musicdescription']['global']['@samplingrate'])

    """ HPSS """
    L1 = 4096./44100.
    tt = time.time()
    myResult['DecSinus'], myResult['DecNoise'], myResult['DecTrans'] = peeaudiolight.C_AudioAnalysis(data_d['audioFile'], do_stereo2mono=True).M_frameAnalysis(window_shape="blackman", L_sec=L1, STEP_sec=L1/4., ).M_cplxFft(zp_factor=1).M_fitzGerald(L_sec=0.08, STEP_sec=0.02)
    print("HPSS %f\n" % (time.time() - tt))

    myResult['Sharpness_Mean'] = float(data_d['jsonData']['musicdescription']['global']['lowleveltype'][6]['#text'])
    myResult['Sharpness_SD'] = float(data_d['jsonData']['musicdescription']['global']['lowleveltype'][7]['#text'])
    myResult['Dist_Loud_Mean'] = float(data_d['jsonData']['musicdescription']['global']['lowleveltype'][0]['#text'])
    myResult['Dist_Loud_SD'] = float(data_d['jsonData']['musicdescription']['global']['lowleveltype'][1]['#text'])

    """ MFCC """
    myResult = F_computeMfcc(data_d['jsonData'], myResult)

    """ TimbreToolbox """
    print("ttb %s" % (data_d['audioFile']))
    myResult = F_computeTimbre(data_d['audioFile'], data_d['pickleFile'], myResult)


    """ TAGS """
    myResult = F_parseTag(data_d['jsonData'], myResult)

    if len(jsonFile) == 0:
        jsonFile = data_d['jsonFile']
    with open(jsonFile, 'w') as fid:
        json.dump(myResult, fid, indent=4)

    print("F_computeOneFile\t%f" % (time.time() - t))

    return


def F_computeAllFile(audioFile_d, TMP_DIR=''):
    """
        Compute the features for all the audiofile in the list
    """

    for key in audioFile_d.keys():

        print "------------------------------------"
        print "processing %s" % (key)
        print "------------------------------------"
        print audioFile_d[key]

        F_computeOneFile(audioFileFull=audioFile_d[key]['full'], audioFileExtract=audioFile_d[key]['extract'], startExtract=-audioFile_d[key]['start'], stopExtract=audioFile_d[key]['stop'], jsonFile='', TMP_DIR=TMP_DIR)

    return


def F_createProcessingList():
    """
        1) Create the list of audioFiles to be processed based on TU-Berlin xls files as used during their experiment
        2) Also connect with start and end time of extract inside the full track
    """


    """ 1 """
    EXT_1_FULL = '.flac'
    DIR_1_FULL = '/Users/peeters/_work/_sound/_projets/201610_heardis/201702_TU-Berlin_full_tracks_183/'
    audioFile_1_Full_l = glob.glob(DIR_1_FULL + '*' + EXT_1_FULL)

    EXT_2_FULL = '.flac'
    DIR_2_FULL = '/Users/peeters/_work/_sound/_projets/201610_heardis/201706_TU-Berlin_full_tracks_366/'
    audioFile_2_Full_l = glob.glob(DIR_2_FULL + '*' + EXT_2_FULL)


    EXT_1_EXTRACT = '.mp3'
    DIR_1_EXTRACT_ = '/Users/peeters/_work/_sound/_projets/201610_heardis/201702_TU-Berlin_stimulus_tracks183/'
    audioFile_1_Extract_l = glob.glob(DIR_1_EXTRACT_ + '*' + EXT_1_EXTRACT)
    EXT_2_EXTRACT = '.mp3'
    DIR_2_EXTRACT_ = '/Users/peeters/_work/_sound/_projets/201610_heardis/201706_TU-Berlin_stimulus_tracks_366/'
    audioFile_2_Extract_l = glob.glob(DIR_2_EXTRACT_ + '*' + EXT_2_EXTRACT)

    audioFile_d = OrderedDict()
    nbTrack = len(audioFile_1_Full_l)
    for numTrack in range(0, nbTrack):
        root = audioFile_1_Full_l[numTrack].split('/')[-1].split('.')[0]
        audioFile_d[root] = {'full': audioFile_1_Full_l[numTrack], 'extract': audioFile_1_Extract_l[numTrack], 'survey': 1}

    nbTrack = len(audioFile_2_Full_l)
    for numTrack in range(0, nbTrack):
        root = audioFile_2_Full_l[numTrack].split('/')[-1].split('_')[0]
        audioFile_d[root] = {'full': audioFile_2_Full_l[numTrack], 'extract': audioFile_2_Extract_l[numTrack], 'survey': 2}


    """ 2 """
    workbook = xlrd.open_workbook('./_list_fileExperiment/20170223_Survey1_Edit-Marks.xlsx')
    worksheet = workbook.sheet_by_index(0)
    for numRow in range(1,worksheet.nrows):
        root = worksheet.cell(numRow, 0).value

        start = worksheet.cell(numRow, 2).value
        start = xlrd.xldate.xldate_as_datetime(start, workbook.datemode)

        stop = worksheet.cell(numRow, 3).value
        stop = xlrd.xldate.xldate_as_datetime(stop, workbook.datemode)

        print "%s %s %s" % (root, start, stop)

        # Warning TU-Berlin is using HH:MM format to repsent MM:SS
        start = start.hour*60 + start.minute
        stop = stop.hour*60 + stop.minute

        audioFile_d[root]['start'] = start
        audioFile_d[root]['stop'] = stop

    workbook = xlrd.open_workbook('./_list_fileExperiment/20170919_Listening Tests Audio Tracks_GP.xlsx')
    worksheet = workbook.sheet_by_index(0)
    for numRow in range(1, worksheet.nrows):
        root = worksheet.cell(numRow, 0).value
        root = str(int(root))

        start = worksheet.cell(numRow, 7).value
        start = xlrd.xldate.xldate_as_datetime(start, workbook.datemode)

        stop = worksheet.cell(numRow, 8).value
        stop = xlrd.xldate.xldate_as_datetime(stop, workbook.datemode)

        print "%s %s %s" % (root, start, stop)

        # Warning TU-Berlin is using HH:MM format to repsent MM:SS
        start = start.hour*60 + start.minute
        stop = stop.hour*60 + stop.minute

        audioFile_d[root]['start'] = start
        audioFile_d[root]['stop'] = stop

    return audioFile_d


def main(argv):
    """
        Main command line function
        Example:  ./imdABCDJhardfeatures.py -i ./50_Minutes-Colours.mp3 -o ./test.json -t ./_blu/
    """

    try:
        opts, args = getopt.getopt(argv, "ha:x:o:t:", ["iaudiofile=", "ixmlfile=", "ojsonfile=", "tmpdir="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-a", "--iaudiofile"):
            inputAudioFile = arg
        elif opt in ("-x", "--ixmlfile"):
            inputXmlFile = arg
        elif opt in ("-o", "--ojsonfile"):
            outputJsonFile = arg
        elif opt in ("-t", "--tmpdir"):
            TMP_DIR = arg
            TMP_DIR = TMP_DIR + '/'
    #audioFile_d = F_createProcessingList()
    #F_computeAllFile(audioFile_d, TMP_DIR=TMP_DIR)

    if len(inputAudioFile) and len(outputJsonFile):
        F_computeOneFile(audioFileFull=inputAudioFile, xmlFile=inputXmlFile, jsonFile=outputJsonFile, TMP_DIR=TMP_DIR)

    return


def usage():
    """
        Usage function
    """
    print 'imdABCDJhardfeatures.py -a <inputAudioFile> -x <inputXmlFile> -o <outputJsonFile -t <tmpDir>'
    return


# ---------------------------------------------
# ---------------------------------------------
# ---------------------------------------------
if __name__ == '__main__':
    main(sys.argv[1:])
