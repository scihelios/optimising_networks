import json
import math
import multiprocessing
import random
import time
import tkinter as tk
from multiprocessing import Pool, cpu_count
from tkinter import *

import ffmpeg
import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits import mplot3d
from shapely.geometry import Point, Polygon

#initialize and declare global variable
debut_fin = []
aug = []
global surplus_list, insufficient_list
surplus_list = []
insufficient_list = []


for i in range(-10,11):
    for j in range(-10,11):
    	aug += [(i,j)]

global compteur_reccurence
compteur_reccurence=0

#reating random historic data
def createhistoricdata(points):
	data=[]
	for i in range(15):
		data.append([random.randint(-20,20) for k in points])
	return data	

#compress the graph to make it easiear to process ; look at the report to understand the theory behing it even more
def reconfigure_graph(preliminaire_set,list_of_allpoint,allpaths):
	global  graph

	midgraph={i:set() for i in preliminaire_set}
	for i in allpaths:
		for j in range(len(i)-1):
			midgraph[i[j]].add(i[j+1])
		i=i[::-1]	
		for j in range(len(i)-1):
			midgraph[i[j]].add(i[j+1])
	midgraph={i:list(midgraph[i]) for i in midgraph}
	for j in range(6):
		g=midgraph.copy()
		for i in g:
			if len(midgraph[i])==2 and i not in set(list_of_allpoint):
				a=midgraph[i][0]
				b=midgraph[i][1]
				midgraph[a]=list(set([k for k in midgraph[a] if k!=i]+[b]))
				midgraph[b]=list(set([k for k in midgraph[b] if k!=i]+[a]))
				midgraph.pop(i)			

	for i in midgraph:
		if i in list_of_allpoint:	
			plt.plot(i[0],i[1],'yo',markersize=12)
		else:
			plt.plot(i[0],i[1],'go',markersize=8)
		#for j in midgraph[i]:
			#plt.plot([i[0],j[0]],[i[1],j[1]],c='green')
	print(len(midgraph))
	plt.show()
	newgraph=midgraph
	print(newgraph)		
	return newgraph

def assign_production():
	global identify
	global surplus_list
	global insufficient_list
	global compteur_reccurence
	global texta
	global value 

	if compteur_reccurence==0:
		#create the window and set title
		value = Tk()
		value.title("value")

		# input dimensons of the wndow
		value.geometry('100x100')

		# no idea what this do ! 
		value.option_add("*tearOff", False)

		value.tk.call("source","azure.tcl")

		value.tk.call("set_theme","dark")
		texta = Entry(value,width=10,font=("Arial Bold", 15))
		texta.place(relx=0.5, rely=0.2, anchor=CENTER)
		btnassi = Button(value, text="assigner", command=assign_production)
		btnassi.place(relx=0.5, rely=0.7, anchor=CENTER)
		
	if compteur_reccurence==1:
		assigned_production=float(texta.get())
		if identify==0:
			surplus_list+=[assigned_production]
		if identify==1:
			insufficient_list+=[assigned_production]	

		value.destroy()
	compteur_reccurence=1


def optimise_transport(localgraph,values,important_points):
	global graph

	#initialize each matrix and array
	S={important_points[i]:values[i] for i in range(len(important_points))}
	M=[[0 for i in range(sum([len(localgraph[k]) for k in localgraph])//2)] for j in localgraph]
	Dc=[[0 for i in range(sum([len(localgraph[k]) for k in localgraph])//2)]for j in range(sum([len(localgraph[k]) for k in localgraph])//2)]

	#add the surplus or lack of each point in the graoh to the dict S
	for i in localgraph:
		if i not in important_points:
			S[i]=0
	S=[S[i] for i in S] #turn the dict S into an array

	allpoints=[i for i in localgraph]
	colone=0 #used to iterate through the columbs of the matrices M and Dc

	for i in range(len(allpoints)):
		for j in range(len(allpoints)):
			a=allpoints[i]
			b=allpoints[j]
			if b in localgraph[a] and a<b:
				M[i][colone]=1
				M[j][colone]=-1
				Dc[colone][colone]=math.sqrt((a[1]-b[1])**2+(a[0]-b[0])**2)
				colone+=1

	#make M and Dc an np.array to make computing the formula more efficient
	Dc=np.array(Dc)
	M=np.array(M)	

	x0=np.dot(np.linalg.inv(Dc+1000000*(M.T@M)),(1000000*np.dot(M.T,S))) #see the report to understand the formula
	
	return (x0, sum([Dc[i][i]*x0[i]**2 for i in range(len(x0))]))

#find distance and path between two points using djikstra
def find_distance(graph,start,end):
	chemin=djikstra(graph,start,end)
	plt.plot([i[0] for i in chemin[0]],[i[1] for i in chemin[0]],c='blue')
	return chemin

def simulation() :
	global list_of_lacking,insufficient_list
	global list_of_loaded ,surplus_list
	global x0,graph,allpaths,ani

	list_of_allpoint=list_of_loaded+list_of_lacking
	allpaths=[]
	colone=0
	preliminaire_set=set()
	for i in range(len(list_of_allpoint)):
		for j in range(i+1,len(list_of_allpoint)):
			onepath=find_distance(graph,list_of_allpoint[i],list_of_allpoint[j])[0]
			preliminaire_set=preliminaire_set.union(set(onepath))
			allpaths+=[onepath]		
	newgraph=reconfigure_graph(preliminaire_set,list_of_allpoint,allpaths)		

	data=createhistoricdata(list_of_allpoint)
	realscore=sum([optimise_transport(newgraph,i,list_of_allpoint)[1] for i in data ])
	print(realscore)
	best_path=([],realscore)
	colone=0
	for i in newgraph:
		for j in newgraph:
			colone+=1
			if i!=j and (j not in newgraph[i]) and(i<j):
				g=newgraph.copy()
				g[i]=g[i]+[j]
				g[j]=g[j]+[i]
				cout=sum([optimise_transport(g,k,list_of_allpoint)[1] for k in data ])
				
				if best_path[1] > cout:
					best_path=([i,j],cout)
				print(colone*100/len(newgraph)**2)

	print((best_path[1]/realscore))
		
	return

#append points chosen by a mouse click (must be valide points !)
def onclick(event):
	global debut_fin, aug, graph
	global list_of_lacking, list_of_loaded
	global identify, compteur_reccurence

	#xdata and ydata contains coordinates related to the graph 
	print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
		('double' if event.dblclick else 'single', event.button,
		event.x, event.y, event.xdata, event.ydata)) 
	debut_fin=debut_fin+[(math.trunc(event.xdata), math.trunc(event.ydata))]
	compt=0	
	j=0

	#try to find the closest point to the mouse click that actually belongs to the graph 
	while compt==0 and (j<len(aug)-1):
		i=aug[j]
		if (debut_fin[-1][0]+i[0],debut_fin[-1][1]+i[1]) in graph[1] :
			debut_fin[-1]=(debut_fin[-1][0]+i[0],debut_fin[-1][1]+i[1])
			compt=1
		j+=1	
	
	#using identify to know if the point is a surplus point or not
	if identify==0:
		list_of_loaded=debut_fin
		compteur_reccurence=0
		assign_production()
	else:
		list_of_lacking=debut_fin
		compteur_reccurence=0
		assign_production()

	return	
 
def link():
	global list_of_lacking,insufficient_list
	global list_of_loaded ,surplus_list
	global x0,graph,allpaths,ani

	#merge all points in one list
	list_of_allpoint=list_of_loaded+list_of_lacking
	#same but for values
	list_of_values=surplus_list+insufficient_list
	
	allpaths=[] #we put here all the paths between each couple of points using djikstra
	preliminaire_set=set()
	
	#creating paths
	for i in range(len(list_of_allpoint)):
		for j in range(i+1,len(list_of_allpoint)):
			onepath=find_distance(graph,list_of_allpoint[i],list_of_allpoint[j])[0]
			preliminaire_set=preliminaire_set.union(set(onepath))
			allpaths+=[onepath]		

	#comressing the graph we already have to make calculation more doable
	newgraph=reconfigure_graph(preliminaire_set,list_of_allpoint,allpaths)		
	
	#x0 takes the result of optimising the efficiency in the etwork 
	x0=optimise_transport(newgraph,list_of_values ,list_of_allpoint)[0]
	
	allpaths=[] #we reset the paths to reorient them in the direction of transmission they actually experience (stays the same if x_i > 0)
	index=0 #used to iterate through the list of values of each edge

	for a in newgraph:
		for b in newgraph:
			if b in newgraph[a] and a<b:
				if x0[index]<0:
					allpaths+=[find_distance(graph,a,b)[0]]
				else:
					allpaths+=[find_distance(graph,b,a)[0]]
				index+=1
	
	ani = animation.FuncAnimation(fig, animate, frames=max([len(i) for i in allpaths])//10, blit = False, interval=30, repeat=True, )			
	ani.save("animation.gif", writer="imagemagick")
	return 

def choose_lacking_points():
	global list_of_lacking, debut_fin,identify
	identify=1
	debut_fin=[]
	list_of_lacking=[]
	return

def choose_overloaded():
	global list_of_loaded,identify
	identify=0
	list_of_loaded=[]
	return


#make a graph with all coord ; a graph in oython is made with dict 
#go back to project report to get more explanation
def make_graph(coord):
	G={}
	set_points=set()
	set_of_coord=set(coord)
	for i in coord:
		p=(round(i[0]),round(i[1]))
		set_points.add(p)
		#if points next to p are also in the set_of_coord then add it as a point connected to p  
		G.update({p:[(p[0]+xax,p[1]+yax) for xax in range(-2,3) for yax in range(-2,3) if (xax!=0 or yax!=0) and ((p[0]+xax,p[1]+yax) in set_of_coord)]})
	return (G,set_points)


#gives the shortest path bestween two points (must input G as a graph): djikstra is a very known algorithm that you can just google it
def djikstra(G,start,end):
	trace={}
	set_used_points=set()
	set_unused_points=G[1].copy()
	tab_dist={}
	tab_dist.update({i:999999 for i in set_unused_points})
	set_tab_dist={start}
	if start in set_unused_points:
		tab_dist[start]=0
		while end in set_unused_points and set_tab_dist!=set() :
			min_dist=min([tab_dist[k] for k in set_tab_dist ])
			for k in set_tab_dist:
				if tab_dist[k]==min_dist:
					u=k
					break
			set_unused_points.remove(u)
			set_used_points.add(u)
			set_tab_dist.remove(u)
			for j in G[0][u]:		
				if tab_dist[u]+(math.sqrt((j[0]-u[0])**2+(j[1]-u[1])**2)) < tab_dist[j]:
					tab_dist[j]=tab_dist[u]+math.sqrt((j[0]-u[0])**2+(j[1]-u[1])**2)
					trace[j]=u
					set_tab_dist.add(j)
	chemin=[]
	e=end
	while end!=start and (end in trace):
		try:
			chemin+=[trace[end]]
			end=trace[end]	
		except:
			break

	chemin=[e]+chemin
	return (chemin,sum([math.sqrt((chemin[i][0]-chemin[i+1][0])**2+(chemin[i][1]-chemin[i+1][1])**2) for i in range(len(chemin)-1)]))


#merge points that are too close to each other by creating sort of a grid and assigning the esach point to the closest point on the grid
#we multiply each coordinates by 100 and round to get its new place on the grid 
def merge(coord_array,prec):
	new_coord_list=[]
	for i in coord_array:
		new_coord_list+=[(int(round(i[0]*prec)),int(round(i[1]*prec)))]
	return new_coord_list

#create gif animation for how the power gets transmited ; the bigger the dots the more energy gets transmited
def animate(frames): 
	global allpaths
	global x0

	#add dots to the transmission line to make it look like a mooving flow
	for i in range(len(allpaths)):
		plt.plot([j[0] for j in allpaths[i][0:frames*10:10]],[j[1] for j in allpaths[i][0:frames*10:10]],'bo',markersize=math.sqrt(abs(x0[i]))*1.2)

	#we clear the plt with plt.cla() then recreate the whole graph to make the illusion of a repeating mouvment 
	if frames==max([len(i) for i in allpaths])//10-1:
		plt.cla()
		allcoord=[]
		for i in data1:
			try:
				coord=i['fields']['geo_shape']['coordinates']
				tension=i['fields']['tension']
				if tension=='400kV':
					coord=merge(coord,100)
					ax.plot([p[0] for p in coord ],[p[1] for p in coord ],c='red')
					allcoord+=coord
			except:
				True
		for i in data2:
			try:
				coord=i['fields']['geo_point_enceinte']
				tension=i['fields']['tension']
				if tension=='400kV':
					ax.plot(coord[0]*100,coord[1]*100,'ro')
			except:
				True


#import electric lines data
lines=open('datalines.json')
data1=json.load(lines)

#import electric generators data
generateur=open('datapost.json')
data2=json.load(generateur)

#creating a figure (plot) where we can see what happens 
fig=plt.figure()
ax=fig.add_subplot()

#connecting the mouse to the plot (or canvas) to make points selection possible
cid = fig.canvas.mpl_connect('button_press_event', onclick)

#make a list where i put all the geographical coordinates of lines and posts after cleaning the data 
#we are going only to take 400kV infrastracture
allcoord=[]   
for i in data1:
	try:
		coord=i['fields']['geo_shape']['coordinates']
		tension=i['fields']['tension']
		if tension=='400kV':
			coord=merge(coord,100)
			ax.plot([p[0] for p in coord ],[p[1] for p in coord ],c='red')
			allcoord+=coord
	except:
		True
for i in data2:
	try:
		coord=i['fields']['geo_point_enceinte']
		tension=i['fields']['tension']
		if tension=='400kV':
			ax.plot(coord[0]*100,coord[1]*100,'ro')
	except:
		True

#creating a graph with the list of coordinates
graph=make_graph(allcoord)


#create the window and set title
window = Tk()
window.title("window")

# input dimensons of the wndow
window.geometry('300x300')

# no idea what this do ! 
window.option_add("*tearOff", False)

window.tk.call("source","azure.tcl")

#make dark theme
window.tk.call("set_theme","dark")


#create buttons and labels for the window
lbli = Label(window, text="choix de départ" )
lbli.place(relx=0.2, rely=0.25, anchor=CENTER)
lblm = Label(window, text="choix d'arrivé")
lblm.place(relx=0.2, rely=0.5, anchor=CENTER)
btn1 = Button(window, text="Choisir", command=choose_overloaded)
btn1.place(relx=0.7, rely=0.25, anchor=CENTER)
btn2 = Button(window, text="Choisir", command=choose_lacking_points)
btn2.place(relx=0.7, rely=0.5, anchor=CENTER)

#link is used if you assign values to your points and you want to see how electricity will go around
btn3 = Button(window, text="-LINK ALL-", command=link)
btn3.place(relx=0.5, rely=0.75, anchor=CENTER)

#simulation is to find the best esdge to add to make a selection of points more effiecient based on historic DATA
btn3 = Button(window, text="simulation", command=simulation)
btn3.place(relx=0.5, rely=0.9, anchor=CENTER)

plt.show()

window.mainloop()



'''
commentaire pour les premiére 100 ligne

Ligne 14 : vous définissez une fonction create_historicdata() qui prend en argument une liste de points et qui retourne une liste de 15 données aléatoires associées à ces points.
Ligne 16 : vous définissez une fonction reconfigure_graph() qui prend en argument une liste de points (preliminaire_set), une liste de tous les points du graphe (list_of_allpoint) et une liste de chemins dans le graphe (allpaths).
Lignes 18 à 21 : vous créez un dictionnaire vide (midgraph) qui contiendra les points du graphe et les points auxquels ils sont connectés. Vous utilisez la boucle for pour parcourir la liste de points (preliminaire_set) et ajouter chaque point comme clé du dictionnaire, avec pour valeur un ensemble vide (set()).
Lignes 23 à 25 : vous parcourez la liste de chemins (allpaths) et ajoutez chaque point suivant dans l'ensemble des points connectés au point en cours d'analyse.
Lignes 26 à 29 : vous inversez chaque chemin et ajoutez chaque point suivant dans l'ensemble des points connectés au point en cours d'analyse.
Lignes 31 à 33 : vous transformez chaque ensemble en liste et mettez à jour le dictionnaire midgraph.
Lignes 35 à 41 : vous utilisez une boucle for pour supprimer les points du graphe qui n'ont qu'un seul lien. Si un point du graphe a deux points connectés et qu'il n'est pas un point du graphe principal (list_of_allpoint), vous supprimez ce point et mettez à jour les connections des points qui lui étaient connectés en les reliant directement entre eux.
Lignes 43 à 46 : vous utilisez une boucle for pour parcourir le graphe modifié (midgraph) et afficher chaque point sous forme de cercle (en jaune pour les points du graphe principal et en vert pour les autres).
Ligne 48 : vous affichez le nombre de points restants dans le graphe modifié.
Ligne 50 : vous affichez le graphe modifié sous forme de plot.
Ligne 52 : vous mettez à jour le graphe en assignant sa valeur à une nouvelle variable (newgraph).
Ligne 54 : vous affichez le graphe mis à jour.
Ligne 55 : vous retournez le graphe mis à jour.
Ligne 57 : vous définissez une fonction assign_production() qui vous permet d'assigner une valeur de production à chaque point du graphe principal.
Lignes 59 à 61 : vous déclarez des variables globales qui seront utilisées dans cette fonction.
Lignes 63 à 67 : vous vérifiez si c'est la première fois que vous
Lignes 69 à 81 : vous créez une fenêtre (value) qui vous permettra d'entrer les valeurs de production pour chaque point du graphe principal. Vous définissez également un titre pour cette fenêtre et ses dimensions.
Lignes 83 à 87 : vous ajoutez un menu déroulant (texta) à la fenêtre qui vous permettra de sélectionner le point du graphe auquel vous souhaitez assigner une valeur de production.
Lignes 89 à 91 : vous créez un bouton (bouton_valider) qui vous permettra de valider votre sélection et d'assigner une valeur à un point du graphe.
Lignes 93 à 95 : vous créez une boucle infinie qui attend que vous cliquiez sur le bouton bouton_valider pour exécuter le reste de la fonction.
Lignes 97 à 99 : vous récupérez la valeur sélectionnée dans le menu déroulant et l'assignez au point du graphe correspondant.
Lignes 101 à 105 : vous mettez à jour la liste des points du graphe qui ont un surplus de production (surplus_list) et celle des points qui ont un besoin de production (insufficient_list).
Lignes 107 à 109 : vous incrémentez le compteur de récurrence 
'''