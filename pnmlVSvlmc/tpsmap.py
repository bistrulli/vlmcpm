import pm4py
import xml.parsers.expat
from pm4py.objects.petri_net.obj import PetriNet

xml_tranition=None
xml_tranitions=[]
xml_weight=False

class StochTrans:
    weight=None

    def __init__(self, weight):
        self.weight=weight

    def get_weight(self):
        return self.weight

def start_element(name, attrs):
    global xml_tranition,xml_weight
    if(name=="transition"):
        xml_tranition={"id":attrs["id"]}
    if(name=="property"):
        if(attrs["key"]=="weight"):
            xml_weight=True

def end_element(name):
    global xml_tranition, xml_tranitions
    if(name=="transition"):
        xml_tranitions.append(xml_tranition)
        xml_tranition=None

def char_data(data):
    global xml_weight, xml_tranition
    if(xml_weight):
        xml_tranition["weight"]=float(data)
        xml_weight=False

def getxmlTransition_byname(name):
    for t in xml_tranitions:
        if(t["id"]==name):
            return t

def get_stoch_map(pn,pnmlfile):
    transitions = pn.transitions

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.Parse(open(pnmlfile, "r").read())

    smap={}
    for t in transitions:
        xml_t=getxmlTransition_byname(t.name)
        smap[t]=StochTrans(xml_t["weight"])
    return smap

    #places = pn.places
    #arcs = pn.arcs
    # im = pm4py.generate_marking(pn, {'pI': 1})
    # simulated_log = simulator.apply(pn, im,variant=simulator.Variants.STOCHASTIC_PLAYOUT,
    #     parameters={simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.NO_TRACES: 1,
    #                 simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.STOCHASTIC_MAP: smap})
    # for l in simulated_log:
    #     for s in l:
    #         print(s['concept:name'])
