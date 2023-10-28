import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import scipy
import pathlib
import argparse
from tqdm import tqdm

import scipy.stats as stats

def readDCDR(filepath):
	dcdt_file=open(filepath,"r")
	lines=dcdt_file.readlines()
	dcdt_file.close()

	data={}
	for t in lines:
		word=t.strip().replace(",,","")
		if(word in data):
			data[word]+=1
		else:
			data[word]=1

	return data

if __name__ == '__main__':
	dataPM=readDCDR(pathlib.Path("petri_sim.dcdt"))
	dataSet=readDCDR(pathlib.Path("/Users/emilio-imt/eclipse-workspace/SSSA_IMT/data/converted/process.dcdt"))
	dataVLMC=readDCDR(pathlib.Path("/Users/emilio-imt/eclipse-workspace/SSSA_IMT/out.mat"))

	totPM=0
	totVLMC=0
	for w in dataPM:
		totPM+=dataPM[w]*1.0
	for w in dataVLMC:
		totVLMC+=dataVLMC[w]*1.0

	gtw=sorted(list(dataSet.keys()))
	pnw=sorted(list(dataPM.keys()))
	vlmcw=sorted(list(dataVLMC.keys()))

	gt=np.zeros([1,len(gtw)])
	pn=np.zeros([1,len(gtw)])
	vlmc=np.zeros([1,len(gtw)])
	idx=0
	pnerror=0
	for w in gtw:
		if(w in dataSet):
			gt[0,idx]=dataSet[w]
		if(w in dataPM):
			pn[0,idx]=dataPM[w]
		else:
			pnerror+=1
		if(w in dataVLMC):
			vlmc[0,idx]=dataVLMC[w]
		idx+=1

	print(len(gtw),len(pnw),"(%d)"%pnerror,len(vlmcw),)

	totGT=np.sum(gt[0,:])


	P=gt[0,:]*1.0/totGT
	P_pn=pn[0,:]*1.0/totPM
	P_vlmc=vlmc[0,:]*1.0/totVLMC
	
	print(np.sum(P),np.sum(P_pn),np.sum(P_vlmc))
	#print(P.shape,P_vlmc.shape)
	print(np.sum(scipy.special.kl_div(P,P_vlmc)),np.sum(scipy.special.kl_div(P,P_pn)))

	ksvlmc=stats.ks_2samp(P, P_vlmc)
	kspn=stats.ks_2samp(P, P_pn)
	print(ksvlmc[1])
	print(kspn[1])

	plt.figure()
	plt.step(np.linspace(0,gt.shape[1],gt.shape[1]),P,label="Data",linewidth=1.5)
	plt.step(np.linspace(0,gt.shape[1],gt.shape[1]),P_pn,label="GSPN",linewidth=1.5, alpha=0.5)
	plt.step(np.linspace(0,gt.shape[1],gt.shape[1]),P_vlmc,label="VLMC",linewidth=1.5, alpha=0.5)
	plt.grid()
	plt.legend()
	plt.show()



	#print(len(dataPM.keys()))
	#print(len(dataSet.keys()))