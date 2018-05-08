# -*- coding: utf-8 -*-
from   bs4 import BeautifulSoup
import re
import time
import requests



class Place(object):
	""" Classe qui définit un lieu """
	def __init__(self,denomination,weight):
		super(Place, self).__init__()
		self.denomination = denomination
		self.weight = weight
	""" Affiche le lieu """
	def __printPlace__(self):
		print("  " + self.denomination + " : " + str(100*(self.weight))[:4] + "%")

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
		print("Lieux :")
		for j in self.places:
			j.__printPlace__()
	def __printLifespan__(self):
		""" Imprime la période sur laquelle le personnage a probablement vécu """
		print("Période :")
		print("  de",self.lifespan[0],'à',self.lifespan[1])
	def __printWork__(self):
		""" Imprime les coefficients d'activité """
		print("Poids des principaux domaines d'activité :")
		for domain,coef in (self.work[0]).items() :
			if coef > 0.0:
				print (" ",domain," :",str(coef*100)[:4]+"%")
		print("Poids des domaines d'activité secondaires :")
		for domain,coef in (self.work[1]).items() : 
			if coef > 0.0:
				print (" ",domain," :",str(coef*100)[:4]+"%")

	def __printAcquaintanceNames__(self):
		""" Imprime la liste des connaissances """
		print("Connaissances :")
		if len(self.acquaintanceNames) > 1 :
			for acquaintance in self.acquaintanceNames :
				print("  "+acquaintance+",")
		else :
			print("  aucune")


def normalize(dico):
	''' Normalise les poids des dictionnaires de la forme { string : double } '''
	total = 0.0
	for key,val in dico.items():
		if key != '-':
			total += val
	dicoNorm = dico
	noneIncluded = False
	if total == 0.0:
		for key,val in dicoNorm.items():
			dicoNorm[key] = 0.0
		return dicoNorm

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
	''' Calcule le score de corrélation lié aux domaines d'activités des personnages. '''
	score, subscore, bestscore, bestsubscore = 0.0, 0.0, 0.0, 0.0

	# Ce tableau permettra de créer la justification de la proposition de corrélation entre personnages
	justif = { 'sport':'sportif', 'arts':'artistique', 'litterature':'littéraire', 'musique':'musical', \
	'cinema':'cinématographique','sciences_nat':'des sciences naturelles', 'sciences_hum':'des sciences sociales',\
	'mathematiques':'des mathématiques', 'politique':'politique','philo-psycho':'de la philosophie et de la psychologie',\
	'medecine':'de la médecine', 'militaire':'militaire', 'business':'des affaires' }
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
	return [(score + 0.5*subscore)/1.5,ijustif]

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

		iLifespan = person1.lifespan[1]-person1.lifespan[0]
		lastBorn = max(person1.lifespan[0],person2.lifespan[0])
		firstDead = min(person1.lifespan[1],person2.lifespan[1])
		yearCount = firstDead - lastBorn
		justif = "[["+str(lastBorn)+"]]"+"-"+"[["+str(firstDead)+"]]"
		score = 0.0
		if yearCount >= 0:
			score = yearCount/iLifespan
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
	scores = [cptPlace[0],0.8*(cptLifespan[0]),1.5*(cptWork[0]),computeacquaintanceCorrelation(person1,person2)]
	justification = ""
	if max(scores) == scores[0]:
		justification = "Il semble que les personnages aient vécu dans les mêmes lieux. Notamment à [["+cptPlace[1]+"]]."
	elif max(scores) == scores[1]:
		justification = "Il semble que les personnages aient été contemporains sur la période "+cptLifespan[1]+"."
	elif max(scores) == scores[2]:
		justification = "Il semble que les personnages aient tous deux été actifs dans le domaine "+cptWork[1] +"."
	elif max(scores) == scores[3]:
		justification = "Il semble que les personnages se connaissaient."
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
		firstEntry = re.findall("(?<=\[\[)[0-9]*(?=\.[0-9])",j)
		if len(firstEntry)==0:
				firstEntry = re.findall("(?<=\[\[)[0-9]*(?=\]\])",j)
		birthDate[0] = int(firstEntry)
		return [int(birthDate[0]),int(deathDate[0])]
	elif (int(birthDate[0]) != 0) and (int(deathDate[0]) == 1):
		if int(birthDate[0]) > 1930:
			deathDate[0] = 2018
		else:
			deathDate[0] = int(birthDate[0])+70
		return [int(birthDate[0]),int(deathDate[0])]
	else:
		print("ERREUR dans getLifespan : la date de Décès précède la date de Naissance.")
		return [0,1]


def getWork(code):
	''' Détermine, à l'aide d'une liste de mots clé et du code source de la biographie, les domaines où 
		le personnage était actif'''

	weights = { 'sport':0.0, 'arts':0.0, 'litterature':0.0, 'musique':0.0, 'cinema':0.0,
	'sciences_nat':0.0, 'sciences_hum':0.0, 'mathematiques':0.0, 'politique':0.0,
	'philo-psycho':0.0, 'medecine':0.0, 'militaire':0.0, 'business':0.0 }
	subweights = { 'tennis':0.0, 'echecs':0.0, 'football':0.0, 'natation':0.0, 'automobile':0.0, 'peinture':0.0,\
	'sculpture':0.0,'architecture':0.0, 'romanesque':0.0, 'essais':0.0, 'poesie':0.0, 'classique':0.0, 'moderne':0.0,\
	'television':0.0, 'cinema':0.0,'theatre':0.0, 'physique-chimie':0.0,'ingenierie':0.0, 'histoire':0.0,\
	'anthropo-sociologie':0.0, 'democratie':0.0,'monarchie':0.0, 'dictature':0.0,'philo':0.0, 'psycho':0.0 }

	keywords = {
	'sport':['sport','olympiq','champion','compétit','victoire','joueur'],
	'arts':['musée','exposition','photograph','bande dessinée'],
	'litterature':['publication','livre','ouvrage','litté','traduction',' écri','académie française','lettre'],
	'musique':['musique','chanson',' chant ','chanteu'],
	'cinema':['cinéma'],
	'sciences_nat':['sciences','biologi','laboratoire','scientifique','EPF','théorie'],
	'sciences_hum':['sciences humaines'],
	'mathematiques':['math','théorème','algèbre','géométr','calcul','comptab','statisti'],
	'politique':['socialis','gouverne','communis','capital','traité','chancell','politique','municipal',\
		'cantonal','état','etat','décret','pouvoir','national'],
	'philo-psycho':['philosophie-psychologie'],
	'medecine':['médecin','hôpital','anatomie','vaccin','remède','infirm','soin','blessure','blessé','accident',\
		'chirurgie','malad','malaria','médica','croix rouge','variole','épidém'],
	'militaire':['armée','soldat','guerre','militaire','fusil',' arme','sergent','lieutenant','major','général',\
		'officier','bombe','maréchal','neutralité','occupation','blindé','cuirass','armure'],
	'business':['business','entreprise','PDG','multinationale',"chiffre d'affaire",'bénéfice','fortune',\
	'financ','banque','revenu','Wall Street','milliardaire','dollar','investisseur','start-up','entrepreneu',\
	'marché','économie','économique','rouble',' actionnaire']
	}
	subkeywords = {
	'tennis':['sport','tennis','chelem'],
	'echecs':['sport','échecs'],
	'football':['sport','football'],
	'natation':['sport','natation',' nage ','nageu','piscine','plonge'],
	'automobile':['sport','automobil','formule un','formule 1'],
	'peinture':['arts',' peint','tableau',' toile','portrait'],
	'sculpture':['arts','sculpt',' buste','statue','marbre'],
	'architecture':['arts','architect','chantier','bâtiment','monument','constru'],
	'romanesque':['litterature','récit','roman'],
	'essais':['litterature','essai','nouvelle'],
	'poesie':['litterature','poésie','poème','poète','alexandrin'],
	'classique':['musique','piano','menuet','sonate','orchestre','opéra','symphonie','clavecin','violon','flûte',\
		'liturgi','choeur','chœur','conservatoire'],
	'moderne':['musique','concert','rap ','rappeu','rock','blues','jazz','hip-hop','CD','festival','album',\
	'vinyl','guitare'],
	'television':['cinema','télévis','téléjournal','RTS','TSR'],
	'cinema':['cinema','cinéma','avant-première','acteur','actrice','tournage','film'],
	'theatre':['cinema','comédie','tragédie','farce','théâtre','scène','drame'],
	'physique-chimie':['sciences_nat','atom','physique','physicien','radiation','radium','électron','photon'\
		'chimie','proton','radioacti','gravité','gravitation','espace-temps'],
	'ingenierie':['sciences_nat','électri','mécani','informatique','ordinateur','comput','techn','invente','invention'],
	'histoire':['sciences_hum','histoire','archéo','antiqu','histori','paléo'],
	'anthropo-sociologie':['sciences_hum','ethnolog','civilization','anthropo','sociolog','sciences sociales',\
		'ethni','féminis',"droits de l'Homme"],
	'democratie':['politique','election','élection','vote','votation','conseill','confédération','canton',\
		'société des Nations','ONU','UNESCO','société des nations','USA','maison Blanche','préside','déput',\
		'sénat','libéra','capital','républi','droits','citoyen','civique','européen','paix','pacifisme',\
		'communauté','union','liberté',' socialis','assemblée','indépendan'],
	'monarchie':['politique',' roi ',' Roi ','majesté','monarque','monarchie','royaume','tsar','couronne','trône',\
	' duc ',' Duc ','duchesse','duché','baron','comte','tsar','empire','empereur','impératrice','reine','monarque',\
	'noble','aristocrat'],
	'dictature':['politique','dictat','URSS','nazi','fascis','national-social','soviet','soviétique','reich','attentat',\
		'junte','détenu','détention','prison','complot','révolution','révolt','exécution','interdi','autocrat'],
	'philo':['philo-psycho','philosoph'],
	'psycho':['philo-psycho','psych']
	}

	events = code.split("*")
	for j in events :
		# À chaque fois qu'une ligne de la biographie est reliée à une catégorie d'activité par un des 
		# mot-clés s'y rapportant, augmente l'importance de cette catégorie pour le personnage concerné. 
		for category,words in keywords.items():
			counter = 0
			
			for word in words:
				counter += j.count(word)+j.count(word.capitalize())
				'''
				# DEBUG : permet de vérifier les mots-clé repérés, voir aussi la suite du code DEBUG plus bas
				if (j.count(word)+j.count(word.capitalize())) >= 1 :
					print(word)
				'''

			# Idem pour les mots clés des sous-catégories
			for subcategory,subwords in subkeywords.items():
				subcounter = 0
				if subwords[0]==category:
					for subword in subwords[1:]:
						searchCount = j.count(subword)+j.count(subword.capitalize())
						counter += searchCount
						subcounter += searchCount
						'''
						# DEBUG : permet de vérifier les mots-clé repérés (suite)
						if searchCount >= 1 :
							print(subword)
						'''
				if subcounter > 0:
					subweights[subcategory] += 1
			if counter > 0:
				weights[category] += 1

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

def ranking(people, item1):
	''' Établit le top 3 des meilleures corrélations, puis affiche celles qui présentent un score élevé '''
	similarBotRanking = ""
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

	similarBotRanking += "\n== Recommandation(s) automatique(s) pour " + person.name + " == \n"
	if bestScore[0] > 0.8:
		similarBotRanking += "* [[" + bestName[0] + "]]. Recouvrement : " + str(bestScore[0]/0.043)[:4] 
		similarBotRanking += "%." + " " +bestjustif[0] + "\n"
	else:
		similarBotRanking += "Aucune recommandation proposée. \n"
	if bestScore[1] > 1:
		similarBotRanking += "* [[" + bestName[1] + "]]. Recouvrement : " + str(bestScore[1]/0.043)[:4] 
		similarBotRanking += "%." + " " +bestjustif[1] + "\n"
	if bestScore[2] > 1.2:
		similarBotRanking += "* [[" + bestName[2] + "]]. Recouvrement : " + str(bestScore[2]/0.043)[:4] 
		similarBotRanking += "%." + " " +bestjustif[2] + "\n"

	return similarBotRanking

def getInfo(people):
	for person in people :
		print("\n")
		print("Nom :",person.name)
		person.__printLifespan__()
		person.__printPlacesWeights__()
		person.__printWork__()
		person.__printAcquaintanceNames__()
	return True


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

	codeToConsider = code
	# éviter de lire la section Recommandations déjà écrite, ainsi que les éventuelles autres sections réalisées
	# par des Bots, comme SummarizingBot.
	recomText = "== Recommandation(s) automatique(s) pour "
	if ("== Biographie ==" in code) :
		codeToConsider = code[code.find("== Biographie ==")+len("== Biographie =="):]
		codeToConsider = codeToConsider[:codeToConsider.find("==")]
	elif (recomText in code) :
		codeToConsider = code[:code.find(recomText)+len(recomText)]
	
	code = codeToConsider

	someone = Person(name.replace('_',' '),getPlaces(codeToConsider),getLifespan(code,name),getWork(code),getacquaintance(code,names))
	people.append(someone)
	
''' fonction getInfo pour le DEBUG '''
#getInfo(people)

checkAquaintanceReciprocity(people)

for person in people:
	time.sleep(3)

	similarBotRanking = ranking(people, person)

	result=requests.post(baseurl+'api.php?action=query&titles='+(person.name).replace(' ','_')+'&export&exportnowrap')
	soup=BeautifulSoup(result.text, "html.parser")
	code=''
	for primitive in soup.findAll("text"):
		code+=primitive.string
	intro = "\n== Recommandation(s) automatique(s) pour " + person.name + " =="

	# si SimilarBot a déjà été utilisé, simplement mettre à jour la section avec les nouvelles recommandations
	if (intro in code):
		afterCode = code[code.find(intro)+len(intro):]
		otherSection = re.findall("==",afterCode)
		if len(otherSection) >= 1:
			afterCode = afterCode[afterCode.find("=="):]
		else:
			afterCode = ""
		beforeCode = code[:code.find(intro)]
		content= beforeCode + similarBotRanking + afterCode
		payload={'action':'edit','assert':'user','format':'json','utf8':'','text':content,'summary':summary,\
		'title':(person.name).replace(' ','_'),'token':edit_token}
		r4=requests.post(baseurl+'api.php',data=payload,cookies=edit_cookie)
		print(r4.text)

	elif ("== Biographie ==" in code):
		afterCode = code[code.find("== Biographie ==")+len("== Biographie =="):]
		otherSection = re.findall("==",afterCode)
		# s'il n'y a pas d'autres sections dans la page que Biographie, juste ajouter à la fin de la page
		if len(otherSection) == 0:
			content = similarBotRanking
			payload={'action':'edit','assert':'user','format':'json','utf8':'','appendtext':content,'summary':summary,\
			'title':(person.name).replace(' ','_'),'token':edit_token}
			r4=requests.post(baseurl+'api.php',data=payload,cookies=edit_cookie)
			print(r4.text)
		# si la section Biographie existe et que d'autres sections existent également, la recommandation est placée 
		# juste après la Biographie
		else:
			afterCode = code[code.find("== Biographie ==")+len("== Biographie =="):]
			afterCode = afterCode[afterCode.find("=="):]
			beforeCode = code[:code.find(afterCode)]
			content= beforeCode + similarBotRanking + afterCode
			payload={'action':'edit','assert':'user','format':'json','utf8':'','text':content,'summary':summary,\
			'title':(person.name).replace(' ','_'),'token':edit_token}
			r4=requests.post(baseurl+'api.php',data=payload,cookies=edit_cookie)
			print(r4.text)
	# Si aucun de ces cas n'est repéré, SimilarBot ajoute simplement la recommandation à la fin de la page Wikipast
	else:
		content=similarBotRanking
		payload={'action':'edit','assert':'user','format':'json','utf8':'','appendtext':content,'summary':summary,\
		'title':(person.name).replace(' ','_'),'token':edit_token}
		r4=requests.post(baseurl+'api.php',data=payload,cookies=edit_cookie)
		print(r4.text)
		

print("\n","TEMPS DE CALCUL :",str(time.time()-timeInit)[:4],"s")

##############################################################################################################################
##############################################################################################################################
##############################################################################################################################