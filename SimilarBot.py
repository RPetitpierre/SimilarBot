# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import re
import time

class Place(object):
	""" Classe qui définit un lieu """
	def __init__(self,denomination,weight):
		super(Place, self).__init__()
		self.denomination = denomination
		self.weight = weight
	def __printPlace__(self):
		""" Affiche le lieu """
		print("  " + self.denomination + " : " + str(100*(self.weight))[:3] + "%")

class Person(object):
	""" Classe qui définit une personne possédant une page Wikipast """
	def __init__(self,name,places,lifespan,work,acquaintanceNames):
		super(Person, self).__init__()
		self.name = name
		self.places = places
		self.lifespan = lifespan
		self.work = work
		self.acquaintanceNames = acquaintanceNames
	def __printPlacesWeights__(self):
		""" Affiche tous les lieux relatifs au personnage et leur poids fréquentiels """
		print("Personnage :",self.name)
		for j in self.places:
			j.__printPlace__()

def normalize(dico):
	''' Normalise les poids des dictionnaires de la forme { string : double } '''
	total = 0
	for key,val in dico.items():
		if key != '-':
			total += val
	dicoNorm = dico
	noneIncluded = False
	if total == 0:
		total = 1
	for key,val in dico.items():
		if key != '-':
			dicoNorm[key] = val/total
		else:
			noneIncluded = True
	if noneIncluded:
		del dicoNorm['-']
	return dicoNorm


def computePlaceCorrelation(person1,person2):
	''' Calcule le score de corrélation par rapport aux lieux où les personnages ont vécu. '''
	score = 0.0
	bestScore = 0.0
	bestPlace = ''
	for element1 in person1.places:
		for element2 in person2.places:
			if element1.denomination == element2.denomination:
				score += min(element1.weight,element2.weight)
				if min(element1.weight,element2.weight) > bestScore:
					bestScore = min(element1.weight,element2.weight)
					bestPlace = element1.denomination
	return [score,bestPlace]

def computeWorkCorrelation(person1,person2):
	''' Calcul le score de corrélation lié aux domaines d'activités des personnages. '''
	score, subscore, bestscore, bestsubscore = 0.0, 0.0, 0.0, 0.0

	justif = { 'sport':'sportif', 'arts':'artistique', 'litterature':'littéraire', 'musique':'musical', \
	'cinema':'cinématographique','sciences_nat':'des sciences naturelles', 'sciences_hum':'des sciences sociales',\
	'mathematiques':'des mathématiques', 'politique':'politique','philo-psycho':'de la philosophie et de la psychologie',\
	'medecine':'de la médecine', 'militaire':'militaire' }
	# Pas implémenté pour le moment
	#subjustif = { 'tennis':0.0, 'echecs':0.0, 'football':0.0, 'natation':0.0, 'automobile':0.0, 'peinture':0.0,\
	#'sculpture':0.0,'architecture':0.0, 'romanesque':0.0, 'essais':0.0, 'poesie':0.0, 'classique':0.0, 'moderne':0.0,\
	#'television':0.0, 'cinema':0.0,'theatre':0.0, 'physique-chimie':0.0,'ingenierie':0.0, 'histoire':0.0,\
	#'anthropo-sociologie':0.0, 'democratie':0.0,'monarchie':0.0, 'dictature':0.0,'philo':0.0, 'psycho':0.0 }
	
	cat1, cat2 = (person1.work)[0], (person2.work)[0]
	subcat1, subcat2 = (person1.work)[1], (person2.work)[1]
	ijustif, isubjustif = "", ""

	for category1,value1 in cat1.items():
		for category2,value2 in cat2.items():
			if category1 == category2:
				score += min(value1,value2)
				if bestscore < min(value1,value2):
					bestscore = min(value1,value2)
					ijustif = justif[category1]

	for category1,value1 in subcat1.items():
		for category2,value2 in subcat2.items():
			if category1 == category2:
				subscore += min(value1,value2)

	return [score + 0.5*subscore,ijustif]

def computeLifespanCorrelation(person1,person2):
	''' Calcul le score de corrélation lié à la période où deux personnages ont vécu. '''
	if (person1.lifespan[0] == 0):
		return [0,'0']
	elif (person1.lifespan[1] == 1):
		return [0,'0']
	elif (person2.lifespan[0] == 0):
		return [0,'0']
	elif (person2.lifespan[1] == 1):
		return [0,'0']
	else :
		maxLifespan = max(person1.lifespan[1]-person1.lifespan[0],person2.lifespan[1]-person2.lifespan[0])
		lastBorn = max(person1.lifespan[0],person2.lifespan[0])
		firstDead = min(person1.lifespan[1],person2.lifespan[1])
		yearCount = firstDead - lastBorn
		justif = str(lastBorn)+"-"+str(firstDead)
		score = 0.0
		if yearCount >= 0:
			score = yearCount/maxLifespan
			return [score,justif]
		else:
			return [0,'0']

def computeacquaintanceCorrelation(person1,person2):
	''' Calcule le score de corrélation dans la catégorie "familles, amis et connaissances" '''
	score = 0.0

	for j in person1.acquaintanceNames:
		if j == person2.name:
			score += 1.0
	return score

def computeCorrelation(person1,person2):
	''' Calcule le score total de corrélation entre les personnages '''
	score = 0.0
	cptPlace = computePlaceCorrelation(person1,person2)
	cptLifespan = computeLifespanCorrelation(person1,person2)
	cptWork = computeWorkCorrelation(person1,person2)
	scores = [cptPlace[0],0.8*(cptLifespan[0]),cptWork[0],computeacquaintanceCorrelation(person1,person2)]
	justification = ""
	if max(scores) == scores[0]:
		justification = "Les personnages ont vécu dans les memes lieux. Notamment à "+cptPlace[1]
	elif max(scores) == scores[1]:
		justification = "Les personnages ont été contemporains sur la période "+cptLifespan[1]
	elif max(scores) == scores[2]:
		justification = "Les personnages ont tous deux été actifs dans le domaine "+cptWork[1]
	elif max(scores) == scores[3]:
		justification = "Les personnages se connaissaient."
	return [scores[0]+scores[1]+scores[2]+scores[3],justification]

def getacquaintance(code,inames):
	''' Détermine les interactions entre personnages, à partir du code source de leur biographie. '''
	acquaintanceNames = []
	for iname in inames:
		if (iname.replace('_',' ')) in code:
			acquaintanceNames.append(iname.replace('_',' '))
	return acquaintanceNames

def getPlaces(code):
	''' Détermine, à partir du code source de la biographie, les lieux où le personnage s'est trouvé. '''
	# Code adapté de Biopathbot
	cities = {}
	events = code.split("*")
	for j in events :
		place = re.findall("(?<=/\s\[\[)[A-zÀ-ÿ\-]*(?=\]\])",j)
		if(len(place)==0):
			place = re.findall("(?<=/\[\[)[A-zÀ-ÿ\-]*(?=\]\])",j)
		if len(place) != 0:
			if place[0] in cities:
				cities[place[0]] += 1
			else:
				newCity = {place[0]:1}
				cities.update(newCity)
	cities = normalize(cities)

	places = []
	for denomination,weight in cities.items():
		newPlace = Place(denomination,weight)
		places.append(newPlace)
	return places

def getLifespan(code,name):
	''' Détermine, à l'aide du code source de la biographie, les dates de naissance et de décès du personnage.'''
	birthDate = ["0"]
	deathDate = ["1"]
	events = code.split("*")
	for j in events :
		j = "\n\n"+j
		if (("[[Naissance]] de [["+name.replace('_',' ')+"]]") in j):
			birthDate = []
			birthDate = re.findall("(?<=\[\[)[0-9]*(?=\.[0-9])",j)
			if len(birthDate)==0:
				birthDate = re.findall("(?<=\[\[)[0-9]*(?=\]\])",j)
		
		if ((("[[Décès]] de [["+name.replace('_',' ')+"]]") in j) or \
			(("[[Mort]] de [["+name.replace('_',' ')+"]]") in j)) or \
			(("[[Exécution]] de [["+name.replace('_',' ')+"]]") in j):
			deathDate = []
			deathDate = re.findall("(?<=\[\[)[0-9]*(?=\.[0-9])",j)
			if len(deathDate)==0:
				deathDate = re.findall("(?<=\[\[)[0-9]*(?=\]\])",j)

	if int(birthDate[0]) <= int(deathDate[0]):
		return [int(birthDate[0]),int(deathDate[0])]
	elif (int(birthDate[0]) == 0) and (int(deathDate[0]) != 1):
		birthDate[0] = int(deathDate[0])-60
		return [int(birthDate[0]),int(deathDate[0])]
	elif (int(birthDate[0]) != 0) and (int(deathDate[0]) == 1):
		if int(birthDate[0]) > 1930:
			deathDate[0] = 2018
		else:
			deathDate[0] = int(birthDate[0])+60
		return [int(birthDate[0]),int(deathDate[0])]
	else:
		print("ERREUR dans getLifespan : la date de Deces precede la date de Naissance.")
		return [0,1]


def getWork(code):
	''' Détermine, à l'aide d'une liste de mots clé et du code source de la biographie, les domaines où le personnage était actif'''

	weights = { 'sport':0.0, 'arts':0.0, 'litterature':0.0, 'musique':0.0, 'cinema':0.0,
	'sciences_nat':0.0, 'sciences_hum':0.0, 'mathematiques':0.0, 'politique':0.0,
	'philo-psycho':0.0, 'medecine':0.0, 'militaire':0.0 }
	subweights = { 'tennis':0.0, 'echecs':0.0, 'football':0.0, 'natation':0.0, 'automobile':0.0, 'peinture':0.0,\
	'sculpture':0.0,'architecture':0.0, 'romanesque':0.0, 'essais':0.0, 'poesie':0.0, 'classique':0.0, 'moderne':0.0,\
	'television':0.0, 'cinema':0.0,'theatre':0.0, 'physique-chimie':0.0,'ingenierie':0.0, 'histoire':0.0,\
	'anthropo-sociologie':0.0, 'democratie':0.0,'monarchie':0.0, 'dictature':0.0,'philo':0.0, 'psycho':0.0 }

	keywords = {
	'sport':['sport','olympiq','champion','compétit','victoire','joueur'],
	'arts':['musée','exposition'],
	'litterature':['publication','livre','ouvrage','litté','traduction','écri','académie française','lettre'],
	'musique':['musique','chanson','chant'],
	'cinema':[],
	'sciences_nat':['sciences','biologi','laboratoire','scientifique','EPF','théorie'],
	'sciences_hum':[],
	'mathematiques':['math','théorème','algèbre','géométr','calcul','comptab','statisti'],
	'politique':['socialis','gouverne','communis','capital','traité','chancell','politique','municipal',\
		'cantonal','état','etat','décret','pouvoir','national'],
	'philo-psycho':[],
	'medecine':['médecin','hôpital','anatomie','vaccin','remède','infirm','soin','blessure','blessé','accident',\
		'chirurgie','malad','malaria','médica','croix rouge','variole','épidém'],
	'militaire':['armée','soldat','guerre','militaire','fusil','arme','sergent','lieutenant','major','général',\
		'officier','bombe','maréchal','neutralité','occupation','blindé','cuirass']
	}
	subkeywords = {
	'tennis':['sport','tennis','chelem'],
	'echecs':['sport','échecs'],
	'football':['sport','football'],
	'natation':['sport','natation','nag','piscine','plonge'],
	'automobile':['sport','automobil','Grand Prix','formule un','formule 1'],
	'peinture':['arts','peint','tableau','toile','portrait'],
	'sculpture':['arts','sculpt','buste','statue','marbre'],
	'architecture':['arts','architect','chantier','bâtiment','monument','constru'],
	'romanesque':['litterature','récit','roman'],
	'essais':['litterature','essai','nouvelle'],
	'poesie':['litterature','poésie','poème','poète','alexandrin'],
	'classique':['musique','piano','menuet','sonate','orchestre','opéra','symphonie','clavecin','violon','flûte',\
		'liturgi','choeur','chœur','conservatoire'],
	'moderne':['musique','concert','rap','rock','blues','jazz','hip-hop','CD','festival','album'],
	'television':['cinema','télévis','téléjournal','RTS','TSR'],
	'cinema':['cinema','avant-première','césar','oscar','acteur','actrice','tournage','film'],
	'theatre':['cinema','comédie','tragédie','farce','théâtre','scène'],
	'physique-chimie':['sciences_nat','atom','physique','physicien','radiation','radium','électron','photon'\
		'chimie','proton','radioacti','gravit','espace-temps'],
	'ingenierie':['sciences_nat','électri','mécani','informatique','ordinateur','comput','techn'],
	'histoire':['sciences_hum','histoire','archéo','antiqu','histori','paléo'],
	'anthropo-sociologie':['sciences_hum','ethnolog','civilization','anthropo','sociolog','sciences sociales',\
		'ethni','féminis',"droits de l'Homme"],
	'democratie':['politique','election','élection','vote','votation','conseill','confédération','canton',\
		'société des Nations','ONU','UNESCO','société des nations','USA','maison Blanche','préside','déput',\
		'sénat','libéra','capital','républi','droits','citoyen','civique','européen','paix','pacifisme',\
		'communauté','union','liberté',' socialis'],
	'monarchie':['politique','roi','majesté','monarque','monarchie','royaume','tsar','couronne','trône','duc',\
		'baron','comte','tsar','empire','empereur','impératrice','reine','monarque','noble','aristocrat'],
	'dictature':['politique','dictat','URSS','nazi','fasci','national-social','soviet','soviétique','reich','attentat',\
		'junte','détenu','détention','prison','complot','révolution','révolt','exécution','interdi','autocrat'],
	'philo':['philo-psycho','philosoph'],
	'psycho':['philo-psycho','psych']
	}

	events = code.split("*")
	for j in events :
		for category,words in keywords.items():
			counter = 0
			for word in words:
				counter += j.count(word)+j.count(word.capitalize())
				for subcategory,subwords in subkeywords.items():
					if subwords[0]==category:
						for subword in subwords[1:]:
							counter += j.count(word)+j.count(word.capitalize())
			if counter > 0:
				weights[category] += 1

	for j in events :
		for subcategory,subwords in subkeywords.items():
			counter = 0
			for subword in subwords[1:]:
				counter += j.count(subword)+j.count(subword.capitalize())
			if counter > 0:
				subweights[subcategory] += 1

	return [normalize(weights),normalize(subweights)]

def checkAquaintanceReciprocity(people):
	''' Vérifie et corrige la liste des connaissances de chaque personnage '''
	for item1 in people:
		for item2 in people:
			for acquaintance1 in item1.acquaintanceNames:
				if acquaintance1 == item2.name:
					if (item1.name in item2.acquaintanceNames) == False:
						(item2.acquaintanceNames).append(item1.name)
			for acquaintance2 in item2.acquaintanceNames:
				if acquaintance2 == item1.name:
					if (item2.name in item1.acquaintanceNames) == False:
						(item1.acquaintanceNames).append(item2.name)
	return True

def ranking(people):
	''' Établit le top 3 des meilleures corrélations, puis affiche celles qui présentent un score élevé '''
	for item1 in people :
		bestScore = [0.0,0.0,0.0]
		bestName = ["","",""]
		bestjustif = ["","",""]
		for item2 in people:
			score = computeCorrelation(item1,item2)[0]
			if (score >= bestScore[0]) and (item1.name != item2.name):
				bestScore[2],bestName[2],bestjustif[2] = bestScore[1],bestName[1],bestjustif[1]
				bestScore[1],bestName[1],bestjustif[1] = bestScore[0],bestName[0],bestjustif[0]
				bestScore[0],bestName[0],bestjustif[0] = score,item2.name,computeCorrelation(item1,item2)[1]
			elif (score >= bestScore[1]) and (item1.name != item2.name):
				bestScore[2],bestName[2],bestjustif[2] = bestScore[1],bestName[1],bestjustif[1]
				bestScore[1],bestName[1],bestjustif[1] = score,item2.name,computeCorrelation(item1,item2)[1]
			elif (score >= bestScore[2]) and (item1.name != item2.name):
				bestScore[2],bestName[2],bestjustif[2] = score,item2.name,computeCorrelation(item1,item2)[1]

		print("Recommandation(s) pour",item1.name, ":")
		if bestScore[0] > 0.8:
			print(bestName[0] + ". Matching :", str(bestScore[0])[:4], ".",bestjustif[0])
		else:
			print("aucune")
		if bestScore[1] > 1:
			print(bestName[1] + ". Matching :", str(bestScore[1])[:4], ".",bestjustif[1])
		if bestScore[2] > 1.2:
			print(bestName[2] + ". Matching :", str(bestScore[2])[:4], ".",bestjustif[2])


##############################################################################################################################
############################################################ MAIN ############################################################
##############################################################################################################################

timeInit = time.time()

user='SimilarBot'
passw='dh2018'
baseurl='http://wikipast.epfl.ch/wikipast/'
summary="Test bot"

# Liste des pages biographiques complètes
names=['Adolf_Hitler','Nicolas_II','Albert_Einstein','Jeanne_Hersch','John_Lennon','Victor_Hugo','Fidel_Castro',\
'Bjorn_Borg','Ferdinand_Hodler','Alberto_Giacometti','Auguste_Piccard','Wolfgang_Pauli','Gustave_Ador',\
'Arthur_Honegger','Wolfgang_Amadeus_Mozart','Mao_Zedong','Robert_Oppenheimer','Richard_Wagner','Simone_de_Beauvoir',\
'Le_Corbusier','Joseph_Staline','Paul_Klee','Steffi_Graf','Phil_Collins','Charles_de_Gaulle','Benito_Mussolini',\
'Michael_Jackson','Mahatma_Gandhi','Jean-Paul_Sartre','Jean-Luc_Godard','Charlie_Chaplin','Philippe_Jaccottet',\
'Marguerite_Yourcenar','Marguerite_Duras','Pierre_de_Coubertin','Louise_Michel','Jacques_Chirac','Stanley_Kubrick',\
'Ayrton_Senna','Enzo_Ferrari','Kurt_Cobain','Audrey_Hepburn','Hermann_Hesse','John_Fitzgerald_Kennedy',\
'Maurice_Cosandey','Charles_Aznavour','Michael_Schumacher','Donald_Trump','Henry_Dunant','Sigmund_Freud',\
'Franz_Beckenbauer','Roman_Polanski','Guillaume_Henri_Dufour','Walter_Mittelholzer','Magic_Johnson','Bill_Gates',\
'Gioachino_Rossini','Thomas_Edison','Ernesto_Rafael_Guevara','Philippe_Suchard','Nicolas_Bouvier',\
'Jacques-Yves_Cousteau','Winston_Churchill','Bobby_Fischer','Paul_Maillefer','Claude_Nicollier',\
'Louis_De_Funès','Salvador_Dalí','Louis_Lumière','Henri_Dès','Daniel_Brélaz','Hergé','Nicéphore_Niépce',\
'Élisabeth_II','Lénine']

# Login request
payload={'action':'query','format':'json','utf8':'','meta':'tokens','type':'login'}
r1=requests.post(baseurl + 'api.php', data=payload)

#login confirm
login_token=r1.json()['query']['tokens']['logintoken']
payload={'action':'login','format':'json','utf8':'','lgname':user,'lgpassword':passw,'lgtoken':login_token}
r2=requests.post(baseurl + 'api.php', data=payload, cookies=r1.cookies)

#get edit token2
params3='?format=json&action=query&meta=tokens&continue='
r3=requests.get(baseurl + 'api.php' + params3, cookies=r2.cookies)
edit_token=r3.json()['query']['tokens']['csrftoken']
edit_cookie=r2.cookies.copy()
edit_cookie.update(r3.cookies)
people = []

# Retrouver le contenu et créer un objet Person pour chaque personnage
for name in names:
	result=requests.post(baseurl+'api.php?action=query&titles='+name+'&export&exportnowrap')
	soup=BeautifulSoup(result.text, "html.parser")
	code=''
	for primitive in soup.findAll("text"):
		code+=primitive.string
	someone = Person(name.replace('_',' '),getPlaces(code),getLifespan(code,name),getWork(code),getacquaintance(code,names))
	people.append(someone)

print(len(people))
	#someone.__printPlacesWeights__()
	#print(someone.lifespan)
	#print(someone.work[0])
	#print(someone.work[1])

checkAquaintanceReciprocity(people)

ranking(people)

print("Temps de calcul :",str(time.time()-timeInit)[:4],"s")

##############################################################################################################################
##############################################################################################################################
##############################################################################################################################