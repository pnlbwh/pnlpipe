#!/usr/bin/env python
import sys
import argparse
import os
from measureTractsFunctions import printToCSV

def main():
    parser = argparse.ArgumentParser(description='computes various tract measures including FA and mode and saves the data to a ".csv"')
    parser.add_argument('-i', '--input', dest='files', nargs='+', required=True, help='enter the VTK files you wish to analyze separated by spaces')
    parser.add_argument('-c', '--columns', dest='extra_header', nargs='+',required=False, default=[], help='Extra column headers')
    parser.add_argument('-v', '--values', dest='extra_values', nargs='+',required=False, default=[], help='Extra column values to prepend to every row')
    parser.add_argument('-o', '--output', dest='fileName', required=True, help='name the output that you wish to save your data to')
    parser.add_argument('-f', '--force', default=False, dest='force', required=False, action='store_true', help='specify in order to automatically overwrite any file that shares the name of your output file')
    args = parser.parse_args()

    for fileNum in range(len(args.files)):
        if not os.path.exists(args.files[fileNum]):
            print("sorry, no file found at" + args.files[fileNum])
    if os.path.isfile(args.fileName) and args.force==False:
        print("The file " + args.fileName + " already exists. Are you sure you want to append? [y/n]")
        if raw_input()=='n':
            sys.exit()
    if os.path.isdir(args.fileName):
        print("Sorry, but the file output name you've entered is already the name of a directory. Please rerun with a different output name")
        sys.exit()
    if '.csv' not in args.fileName:
        print("Please enter an output with extension .csv")

        sys.exit()
    printToCSV(args.files, str(args.fileName), args.extra_header, args.extra_values)


if __name__=="__main__":
    main()
