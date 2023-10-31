"""
Simple Python wrapper for the toothpaste miner Haskell implementation.
"""

import os.path
import subprocess
import multiprocessing as mp
import sys
import time

import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator

import pathlib
import argparse
from tqdm import tqdm

import tpsmap

TBIN="toothpaste"
CLASSIFIER="concept:name"
DELIM=",,"
logfile=None
outfile=None


"""
Mine the logfile using the toothpaste miner. The resulting stochastic labelled
Petri net is returned as a pm4py PetriNet object, and written to outfile. This
convenience method is implemented as an external call to a toothpaste binary
executable, which must be on the PATH. Note that three other files are 
written to the directory of the outfile: a PNML stochastic Petri net model, a 
PTREE Probabilistic Process Tree, and an intermediate log. If outfile is None, 
the files are written to the logfile directory with the prefix from the 
logfile. 

For richer parameters, such as noise reduction, see the command line help
for Toothpaste miner.
"""
def mine(logfile,outfile=None,noise="0"):
    ofile = outfile
    if ofile is None:
        bname =  logfile.name.split(".")[0]
        outdir =  str(logfile.parent) 
    else:
        bname = outfile.name.split(".")[0]
        outdir = str(outfile.parent)  

    dfile = os.path.join( logfile.parent, logfile.name.split(".")[0] + ".dcdt")
    pnfile = os.path.join( outdir, bname + ".pnml")
    ptfile = os.path.join( outdir, bname + ".ptree")
    tdist= os.path.join( outdir, bname + ".dist")

    if(logfile.name.split(".")[1]=="xes"):
        xestodcdt(str(logfile),dfile)

    subprocess.run([TBIN,
                    "--logformat=dcdt",
                    "--eventlog", dfile,
                    "--noise=%s"%(noise),
                    "--pnetfile", pnfile,
                    "--ptreefile", ptfile] )
    pn,im, fm = pm4py.read_pnml(pnfile)

    return (pn,pnfile)

def minerVersion():
    subprocess.run([TBIN, "--version"])

def xestodcdt(xesfile,outfile):
    log = xes_importer.apply(xesfile)
    with open(outfile,'w') as outf:
        for line in log:
            outline = line[0][CLASSIFIER]
            for entry in line[1:]:
                outline += DELIM + entry[CLASSIFIER]
            outline += "\n"
            outf.write(outline)

def dcdttoxes(dcdtfile):
    pass

def getCliArgs():
    global logfile,outfile
    parser = argparse.ArgumentParser(description="A simple script to compare VLMC miner vs Toothpaste")

    parser.add_argument("--logfile", type=str, help="The input event log file,", required=True)
    parser.add_argument("--outfile", type=str, help="The output pnml file",required=False)

    # Parse the command-line arguments
    args = parser.parse_args()

     # Access the parsed strings
    logfile_path = args.logfile
    outfile_path = args.outfile
    logfile=pathlib.Path(logfile_path)
    if(outfile_path is not None):
        outfile=pathlib.Path(outfile_path)
    else:
        outfile=None

def learnSPN(noise="0"):
    (pn,pnfile) = mine(logfile,outfile,noise)
    #pm4py.view_petri_net(pn)

def simSPN(pnfile=None,queue=None,nrun=1,lock=None,value=None):
    pn=None
    if(type(pnfile)==str):
        pn,im, fm = pm4py.read_pnml(pnfile)
    else:
        pn=pnfile

    im = pm4py.generate_marking(pn, {'pI': 1})
    smap=tpsmap.get_stoch_map(pn,str(pnfile))

    simulated_log = simulator.apply(pn, im,variant=simulator.Variants.STOCHASTIC_PLAYOUT,
        parameters={simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.NO_TRACES: nrun,
                    simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.STOCHASTIC_MAP:smap  })

    if(lock is not None):
        lock.acquire()
        value.value+=1
        lock.release()

    if(queue is not None):
        queue.put(simulated_log[0])
    else:
        return simulated_log

def printProress(value,total):
    while(value.value<total-1):
        print("\r"+str(value.value))
        time.sleep(0.5)

def saveSimLog(log=None,outlogFile=None):
    print(outlogFile)
    outtraces=open(outlogFile,"w+")
    for t in log:
        trace=""
        for t1 in t:
            if(t1["concept:name"]=="tau"):
                pass
            else:
                if(trace==""):
                    trace=t1["concept:name"]
                else:
                    trace+=",,"+t1["concept:name"]
        outtraces.write(trace+"\n")
    outtraces.close()
    

if __name__ == "__main__":
    getCliArgs()
    #learnSPN(noise="0")

    pnfile=None
    if(outfile is None):
        pnfile="%s/%s.pnml"%(logfile.parent(),logfile.name().split(".")[0])
    else:
        pnfile=outfile

    mp.set_start_method('spawn')
    manager = mp.Manager()
    lock = manager.Lock()
    value = manager.Value(float, 0.0)
    logqueue = manager.Queue()

    nrun=20
    #run monitor process
    p = mp.Process(target=printProress,args=(value,nrun,))
    p.start()

    # create a default process pool
    pool = mp.Pool(5)
    st=time.time()
    pool.starmap(simSPN, [(str(pnfile),logqueue,1,lock,value) for i in range(nrun)])
    print(time.time()-st)
    pool.close()
    pool.join()

    outlogFile=pathlib.Path("%s/%s_sim.dcdt"%(pnfile.parent,pnfile.name.split(".")[0]))
    results = []
    while not logqueue.empty():
        results.append(logqueue.get())

    saveSimLog(results,outlogFile)


    manager.shutdown()
    


