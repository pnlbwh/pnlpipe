XML = """<?xml version="1.0" encoding="utf-8"?>
<executable>

  <category>Diffusion</category>
  <title>Measure Tract</title>
  <description>Python module for computing tract measures including FA, Trace, and Mode.
  </description>
  <contributor>  David King, with assistance from Ryan Eckbo and Thomas Ballinger</contributor>
  <parameters>

    <label>IO</label>
    <description>Input/output parameters</description>
    
    

   <geometry>
      <name>inputModel</name>
      <label>Input Model</label>
      <channel>input</channel>
      <index>1</index>
      <description>Input tractography model to be colored</description>
    </geometry>

    <directory>
      <name>outputDirectory</name>
      <longflag>--outputDirectory</longflag> 
      <label>Output Directtory</label>
      <channel>output</channel>
      <description>Directory holding the output measures</description>
      <default>.</default>
    </directory>

    <string>
      <name>outputFilename</name>
      <longflag>--outputFilename</longflag> 
      <label>Output Filename</label>
      <channel>output</channel>
      <description>Output filename (.csv)</description>
      <default>measureTractsOutput.csv</default>
    </string>

  </parameters>


</executable>

"""

def Execute (inputModel, outputDirectory="", outputFilename=""):
    from measureTractsFunctions import printToCSV    
    import os
    fileName = os.path.join(outputDirectory, outputFilename)
    printToCSV([inputModel],fileName)
