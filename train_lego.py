from SimpleCV import *
from SimpleCV.Features import FeatureExtractorBase
import time, os, orange,orngSVM, string


class Trainlego():
    """Een class genaamd trainlego
        Hierin wordt de lego getrained

        __init__ is de constructor

        getExtractors is een functie die de extractors van simplecv Krijgt wij gebruiken de HueHistogram en de Edge histogram extractors

        getClassifiers is een functie die meerdere classifiers returned svm en tree classifiers met onze extractors
            dit was omdat ik ze beiden wou uitproberen daarom gebruiken we hiervan ook alleen de tree

        Trainen is een functie die de features extract van de fotos en deze in een boom plaatst

        Testen is een functie waarmee de accuratie meteen getest kan  worden zonder camera

        ResultNaarFoto is een functie die kan worden gebruikt om test data opnieuw te saven met de identified classe erop geschreven in het rood
    """
    def __init__(self, classes, trainLocaties):
        self.classes = classes
        self.trainLocaties = trainLocaties

    def getExtractors(self):
        hhfe = HueHistogramFeatureExtractor()
        ehfe = EdgeHistogramFeatureExtractor()
        return [hhfe, ehfe]

    def getClassifiers(self, extractors):
        svm = SVMClassifier(extractors)
        tree = TreeClassifier(extractors)
        return [svm, tree]

    def trainen(self):
        self.classifiers = self.getClassifiers(self.getExtractors())
        for classifier in self.classifiers:
            classifier.train(self.trainLocaties, self.classes, verbose=False)

    def testen(self, testPaths):
        for classifier in self.classifiers:
            print classifier.test(testPaths, self.classes, verbose=False)


    def resultNaarfoto(self, classifier, afbeeldingen):
        i = 0
        for afb in afbeeldingen:
            i = i+1
            className = classifier.classify(afb)
            afb.drawText(className, 10, 10, fontsize=60, color=Color.BLUE)
            afb.save('result/test' + str(i) + '.jpg')
            