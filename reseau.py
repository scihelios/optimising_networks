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

debut_fin=[]
aug=[]
global surplus_list, insufficient_list
surplus_list=[]
insufficient_list=[]
for i in range(-10,11):
    for j in range(-10,11):
    	aug+=[(i,j)]

global compteur_reccurence
compteur_reccurence=0

def createhistoricdata(points):
	data=[]
	for i in range(15):
		data.append([random.randint(-20,20) for k in points])
	return data	


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

	S={important_points[i]:values[i] for i in range(len(important_points))}
	allpaths=[]
	M=[[0 for i in range(sum([len(localgraph[k]) for k in localgraph])//2)] for j in localgraph]
	Dc=[[0 for i in range(sum([len(localgraph[k]) for k in localgraph])//2)]for j in range(sum([len(localgraph[k]) for k in localgraph])//2)]

	for i in localgraph:
		if i not in important_points:
			S[i]=0
	S=[S[i] for i in S]
	allpoints=[i for i in localgraph]
	colone=0
	for i in range(len(allpoints)):
		for j in range(len(allpoints)):
			a=allpoints[i]
			b=allpoints[j]
			if b in localgraph[a] and a<b:
				M[i][colone]=1
				M[j][colone]=-1
				Dc[colone][colone]=math.sqrt((a[1]-b[1])**2+(a[0]-b[0])**2)
				colone+=1
	Dc=np.array(Dc)
	M=np.array(M)	
	x0=np.dot(np.linalg.inv(Dc+1000000*(M.T@M)),(1000000*np.dot(M.T,S)))
	

	return (x0, sum([Dc[i][i]*x0[i]**2 for i in range(len(x0))]))

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

#find path between two points chosen by a mouse click (must be valide ppoints !)
def onclick(event):
	global debut_fin
	global graph
	global aug
	global list_of_lacking
	global list_of_loaded
	global identify
	global compteur_reccurence
	print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
		('double' if event.dblclick else 'single', event.button,
		event.x, event.y, event.xdata, event.ydata)) 
	debut_fin=debut_fin+[(math.trunc(event.xdata), math.trunc(event.ydata))]
	compt=0	
	j=0
	while compt==0 and (j<len(aug)-1):
		i=aug[j]
		if (debut_fin[-1][0]+i[0],debut_fin[-1][1]+i[1]) in graph[1] :
			debut_fin[-1]=(debut_fin[-1][0]+i[0],debut_fin[-1][1]+i[1])
			compt=1
		j+=1	
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

	list_of_allpoint=list_of_loaded+list_of_lacking
	list_of_values=surplus_list+insufficient_list
	allpaths=[]
	colone=0
	preliminaire_set=set()
	for i in range(len(list_of_allpoint)):
		for j in range(i+1,len(list_of_allpoint)):
			onepath=find_distance(graph,list_of_allpoint[i],list_of_allpoint[j])[0]
			preliminaire_set=preliminaire_set.union(set(onepath))
			allpaths+=[onepath]		
	newgraph=reconfigure_graph(preliminaire_set,list_of_allpoint,allpaths)		

	x0=optimise_transport(newgraph,list_of_values ,list_of_allpoint)[1]
	plt.show()
	k=input('')
	allpaths=[]
	colone=0
	for i in range(newgraph):
		for j in range(newgraph):
			a=newgraph[i]
			b=newgraph[j]
			if b in newgraph[a] and a<b:
				if x0[colone]<0:
					allpaths+=[find_distance(graph,a,b)[0]]
				else:
					allpaths+=[find_distance(graph,b,a)[0]]
				colone+=1
	
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


#make a graph with all coord
def make_graph(coord,prec):
	G={}
	set_points=set()
	set_of_coord=set(coord)
	for i in coord:
		p=(round(i[0]),round(i[1]))
		set_points.add(p)
		G.update({p:[(p[0]+xax,p[1]+yax) for xax in range(-2,3) for yax in range(-2,3) if (xax!=0 or yax!=0) and ((p[0]+xax,p[1]+yax) in set_of_coord)]})
	return (G,set_points)


#gives the shortest path bestween two points (must input G as a graph)
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


#merge points that are too close to each other
def merge(coord_array,prec):
	new_coord_list=[]
	for i in coord_array:
		new_coord_list+=[(int(round(i[0]*prec)),int(round(i[1]*prec)))]
	coord_array=[]
	for i in new_coord_list:
		coord_array+=[i]
	return coord_array

def animate(frames): 
	global allpaths
	global x0

	for i in range(len(allpaths)):
		plt.plot([j[0] for j in allpaths[i][0:frames*10:10]],[j[1] for j in allpaths[i][0:frames*10:10]],'bo',markersize=math.sqrt(abs(x0[i]))*1.2)

	
	if frames==max([len(i) for i in allpaths])//10-1:
		plt.cla()
		allcoord=[]
		for i in data1:
			try:
				coord=i['fields']['geo_shape']['coordinates']
				tension=i['fields']['tension']
				#if tension=='225kV':
				#	plt.plot([p[0] for p in coord ],[p[1] for p in coord ],c='blue')
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
				#if tension=='225kV':
				#	plt.plot(coord[0],coord[1],'bo')
				if tension=='400kV':
					ax.plot(coord[0]*100,coord[1]*100,'ro')
			except:
				True

	


#scrap csv file to get all coordinates
#coord_data=scrapcsv('datalines.csv')
lines=open('datalines.json')

data1=json.load(lines)

generateur=open('datapost.json')

data2=json.load(generateur)

fig=plt.figure()
ax=fig.add_subplot()
cid = fig.canvas.mpl_connect('button_press_event', onclick)

allcoord=[]   

for i in data1:
	try:
		coord=i['fields']['geo_shape']['coordinates']
		tension=i['fields']['tension']
		#if tension=='225kV':
		#	plt.plot([p[0] for p in coord ],[p[1] for p in coord ],c='blue')
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
		#if tension=='225kV':
		#	plt.plot(coord[0],coord[1],'bo')
		if tension=='400kV':
			ax.plot(coord[0]*100,coord[1]*100,'ro')
	except:
		True


graph=make_graph(allcoord,100)


#create the window and set title
window = Tk()
window.title("window")

# input dimensons of the wndow
window.geometry('300x300')

# no idea what this do ! 
window.option_add("*tearOff", False)

window.tk.call("source","azure.tcl")

window.tk.call("set_theme","dark")


#create buttons for selection
lbli = Label(window, text="choix de départ" )
lbli.place(relx=0.2, rely=0.25, anchor=CENTER)
lblm = Label(window, text="choix d'arrivé")
lblm.place(relx=0.2, rely=0.5, anchor=CENTER)
btn1 = Button(window, text="Choisir", command=choose_overloaded)
btn1.place(relx=0.7, rely=0.25, anchor=CENTER)
btn2 = Button(window, text="Choisir", command=choose_lacking_points)
btn2.place(relx=0.7, rely=0.5, anchor=CENTER)

btn3 = Button(window, text="-LINK ALL-", command=link)
btn3.place(relx=0.5, rely=0.75, anchor=CENTER)
btn3 = Button(window, text="simulation", command=simulation)
btn3.place(relx=0.5, rely=0.9, anchor=CENTER)




plt.show()






window.mainloop()






#plt.plot([p[0] for p in allcoord ],[p[1] for p in allcoord ],c='red')


'''def scrapcsv(fichier):

	#open csv file and exctract coordinates
	with open(fichier,"r") as file:
		list_of_coord=[]
		verify=0
		for ligne in file:
			if verify==0:
				verify=1
			else:	
				#inverse line because coordonates are at the end of the ligne
				ligne=ligne[::-1]
				coord=''

				#extract coordinates
				for i in ligne:
					if i==';':
						break
					coord+=i

				#re-reverse the string to get it back to normal
				coord=coord[::-1]	
				coordx=''
				coordy=''	
				for i in coord:
					if i==',':
						break
					coordx+=i

				coordy=coord[len(coordx)+1:len(coord)-1]
				try:
					list_of_coord+=[(float(str(coordx)),float(str(coordy)))]
					
				except:
					print('')
	return list_of_coord











	for j in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:
			if (i[0]+j[0],i[1]+j[1]) in preliminaire_set:


	'''