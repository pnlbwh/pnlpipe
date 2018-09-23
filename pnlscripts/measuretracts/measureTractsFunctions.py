import numpy as np
import os.path

def tracer(currentTensor):
    trace=sum(currentTensor.diagonal(offset=0, axis1=0, axis2=1))
    return trace

def computeLPSFromTensorEigenvalues(ev):
    if ev[0]==0:
        #all eigenvalues are zero; so this is a perfect trivial sphere
        retLi=0
        retPl=0
        retSp=1
    else:
        retLi=(ev[0]-ev[1])/ev[0]
        retPl=(ev[1]-ev[2])/ev[0]
        retSp=(ev[2])/ev[0]
    return retLi, retPl, retSp
    fileName = 'slicerMeasureTest'

def computeRAFromTensorEigenvalues(ev):
    denom = (2**.5*(ev[1]+ev[2]+ev[0]))
    if denom > 0:
        ret = float(((ev[0]-ev[1])**2 + (ev[1]-ev[2])**2 + (ev[0]-ev[2])**2 )**0.5)/denom
    else:
        #this is a perfectly trivial sphere
        ret=0
    return ret

def computeModeFromTensor(currentTensor):
    eye3=np.array([[1,0,0],[0,1,0],[0,0,1]])
    AT=currentTensor-(1/3.0)*tracer(currentTensor)*eye3
    normAT=(AT[0,0]**2 + 2*AT[0,1]**2 + 2*AT[0,2]**2 + AT[1,1]**2 + 2*AT[1,2]**2 + AT[2,2]**2)**0.5;
    #mat=((AT)/normAT)
    #determinant=mat[0,0]*mat[1,1]*mat[2,2]-mat[0,0]*mat[1,2]*mat[2,1]-mat[0,1]*mat[1,0]*mat[2,2]+mat[0,1]*mat[1,2]*mat[2,0]+mat[0,2]*mat[1,0]*mat[2,1]-mat[2,0]*mat[1,1]*mat[2,0]
    if(normAT>0):
        mode=3*((6)**0.5)*np.linalg.det((AT)/normAT)
    else:
        mode=0
    return mode

def computeFAFromTensorEigenvalues(ev):
    denom = ((2*(ev[1]**2+ev[2]**2+ev[0]**2))**0.5)
    if denom == 0:
        ret = 0
    else:
        ret = float(((ev[1]-ev[2])**2+(ev[2]-ev[0])**2+(ev[1]-ev[0])**2)**0.5)/denom
    return ret

#print "Enter the file name you want to import"
    #VTK=raw_input()
def getData(nodeID):

    if 'MRMLFiberBundle' in nodeID:
        Slicer = __import__ ( "Slicer" ) #weird import
        slicer = Slicer.slicer
        scene = slicer.MRMLScene
        node = scene.GetNodeByID(nodeID)

        data = node.GetPolyData()
        points = data.GetPointData()
        tensors = points.GetTensors()
        length = data.GetNumberOfPoints()
        num_fibers = data.GetNumberOfLines()

        pTract = np.zeros([length, 9])
        for num in range(length):
            pTract[num] = np.array(tensors.GetTuple9(num))
    else:
        import getTensorData
        pTract = getTensorData.get_all_tensors(nodeID)
        length = len(pTract)
        num_fibers = getTensorData.get_num_fibers(nodeID)

    results = {'Linear':{},'Planar':{},'Spherical':{},'RA':{},'FA':{},
               'trace':{},'mode':{},'axial':{},'radial':{}}

    for num in results.keys():
        results[num]['values'] = np.zeros(length)

#    fileName = 'slicerMeasureTest.csv'
    retLi = np.zeros(length)
    retSp = np.zeros(length)
    retPl = np.zeros(length)

    for i in range(length):

            currentTensor=np.array(pTract[i]).reshape((3,3))
            ev=np.linalg.eig(currentTensor)[0]

            for num in range(1,len(ev)):#eliminate negative numbers
                if ev[num]<0:
                    ev[num]=0

            ev.sort()
            ev2=np.copy(ev)
            ev[0]=ev2[2]
            ev[2]=ev2[0]

            results['mode']['values'][i]=computeModeFromTensor(currentTensor)
            results['trace']['values'][i]=tracer(currentTensor)
            [retLi[i], retPl[i], retSp[i]]=computeLPSFromTensorEigenvalues(ev)
            results['Linear']['values'][i]=retLi[i]
            results['Planar']['values'][i]=retPl[i]
            results['Spherical']['values'][i]=retSp[i]
            #results['RA']['values'][i]=computeRAFromTensorEigenvalues(ev)
            results['FA']['values'][i]=computeFAFromTensorEigenvalues(ev)
            results['axial']['values'][i]=1000*ev[0]
            results['radial']['values'][i]=1000*(ev[1]+ev[2])/2
    i=0
    for measure in results.keys():
            data=results[measure]['values']
            results[measure]['mean'] = 1000*sum(data)/length
            results[measure]['minimum'] = 1000*min(data)
            results[measure]['maximum'] = 1000*max(data)
            results[measure]['stDev'] = 1000*data.std()

    rawValues = {}
    for measure in results.keys():
        rawValues = results[measure]['values']
        del results[measure]['values']

    #if not 'MRMLFiberBundle' in nodeID:
    results['num_fibers'] = {'num_fibers': num_fibers}
    return results

def printToCSV(nodes,fileName,extra_header=[],extra_values=[]):
    """files is the list of VTKs that will be analyzed, fileName is the name that the CSV will be saved as"""

    import csv
    import os
    if os.path.exists(fileName):
        fileOut=csv.writer(open(fileName, 'wa'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')
    else:
        fileOut=csv.writer(open(fileName, 'w'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC, quotechar='"')

    nodeID=nodes[0]
    firstNode=getData(nodeID)

    operation=[]
    data=[]

    for tag in firstNode.keys():
        for key in firstNode[tag].keys():
            operation.append(key)
            data.append(tag)
    length=len(data)
    measureTags = [0]*length
    for num in range(length):
        if operation[num] == "num_fibers":
            measureTags[num] = "num"
        else:
            measureTags[num] = data[num]+'_'+operation[num]
    import re
    #printTags=re.sub('\[', '',str(measureTags),count=0)
    #printTags=re.sub('\]', '',str(printTags),count=0)
    #printTags = ','.join(measureTags)
    print("Computing the following measures")
    print(','.join(measureTags))

    header = extra_header + ['tract'] + measureTags
    fileOut.writerow(header)

    measureNums = [0]*length
    numberOfInputs=len(nodes)
    import numpy
    #rows=[]
    lineNum=0
    for node in nodes:
        results=getData(node)
        tally=0
        measureNums = [0]*length
        for tag in results.keys():
            for key in results[tag].keys():
                measureNums[tally] = results[tag][key]
                tally=tally+1

        #rows.append([node, measureNums])
        #printNums=re.sub('\]', '',str(rows[lineNum]),count=0)
        #printNums=re.sub('\[', '',str(rows[lineNum]),count=0)
        #printNums = ','.join(map(str,rows[lineNum]))
        #fileOut.writerow(printNums)
        basename = os.path.basename(node)
        basename = os.path.splitext(basename)[0]
        #row = extra_values + ['"' + basename + '"'] + measureNums
        row = extra_values + [basename] + measureNums
        fileOut.writerow(row)
        lineNum=lineNum+1
        print("Finished computing measures for '%s'\n" % node)

    print("Made " + fileName)
