#!/usr/bin/env python
"""Work in progress: gets all tensors for David King's Summer 2011 project

Right now this only gets all in the volume tensors;
plan on it getting individual fibers eventually.  This is just to
get David started"""
import vtk
import sys

def get_num_fibers(filename):
    #reader = vtk.vtkDataSetReader()
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(filename)
    reader.Update()
    nlines = reader.GetOutput().GetNumberOfLines()
    return nlines

def get_tensor_array(filename):
    """Returns vtk tensor array object which can have 'GetTuple9(i)' called on it."""
    print("Reading " + filename)
    reader = vtk.vtkDataSetReader()
    reader.SetFileName(filename)
    reader.Update()

    output = reader.GetOutput()
    print('npoints:', output.GetNumberOfPoints())
    print('ncells:', output.GetNumberOfCells())
    print('nscalars:', reader.GetNumberOfScalarsInFile())
    print('ntensors:', reader.GetNumberOfTensorsInFile())
    print('ScalarName:', reader.GetScalarsNameInFile(0))
    print('TensorName:', reader.GetTensorsNameInFile(0))

    output = reader.GetOutput()
    pointdata = output.GetPointData()
    #scalar_array = pointdata.GetArray('scalar')
    tensor_array = pointdata.GetTensors()
    if not tensor_array:
        tensor_array = pointdata.GetArray('tensor')
    if not tensor_array:
        tensor_array = pointdata.GetArray('tensors')
    if not tensor_array:
        tensor_array = pointdata.GetArray('Tensors_')
    if not tensor_array:
        tensor_array = pointdata.GetArray('tensor1')
    if not tensor_array:
        print("Cannot find tensors in %s" % filename)
        sys.exit(1)
    return tensor_array

def get_all_tensors(filename):
    """Returns a list of 9-tuples representing the tensor at each vtk point"""
    tensor_array = get_tensor_array(filename)
    num_tensors = tensor_array.GetNumberOfTuples()
    output = []
    for i in range(num_tensors):
        output.append(tensor_array.GetTuple9(i))
    return output

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for vtk_file in sys.argv[1:]:
            get_all_tensors(vtk_file)
    else:
        test_vtk_file= '/projects/schiz/pnlpipe_software/scripts/measureTracts/0403-uncinate-left-curv.vtk'
        test_vtk_file= '/projects/schiz/ra/tomb/sylvainFibers/fibers-1000_1001_-1_not_-1_something.vtk'
        test_vtk_file= '/projects/schiz/ra/tomb/nrrd/caseD0704_fornix_tracts_left_0.vtk'
        print(get_all_tensors(test_vtk_file))
        print(len(get_all_tensors(test_vtk_file)))
        get_all_tensors(test_vtk_file)
