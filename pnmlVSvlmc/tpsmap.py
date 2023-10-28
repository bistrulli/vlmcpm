import pm4py
import xml.parsers.expat

xml_tranition=None
xml_tranitions=[]
xml_weight=False

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

def get_stoch_map(pnmlfile):
    #"/Users/emilio-imt/git/toothpaste/pnmlVSvlmc/test.pnml"
    pn, im, fm=pm4py.read_pnml(pnmlfile)
    im = pm4py.generate_marking(pn, {'pI': 1})

    places = pn.places
    transitions = pn.transitions
    arcs = pn.arcs

    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data
    p.Parse(open(pnmlfile, "r").read())

    smap={}

    for place in places:
        totw=0
        for arc in place.out_arcs:
            xml_t=getxmlTransition_byname(arc.target.name)
            totw+=xml_t["weight"]
        for arc in place.out_arcs:
            xml_t=getxmlTransition_byname(arc.target.name)
            smap[xml_t["id"]]=xml_t["weight"]/totw
    return smap

    # simulated_log = simulator.apply(pn, im,variant=simulator.Variants.STOCHASTIC_PLAYOUT,
    #     parameters={simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.NO_TRACES: 1,
    #                 simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.STOCHASTIC_MAP: smap})
    # for l in simulated_log:
    #     for s in l:
    #         print(s['concept:name'])
