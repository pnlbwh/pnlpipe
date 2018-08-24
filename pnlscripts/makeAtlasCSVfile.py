#!/usr/bin/env python

import os
import pandas as pd
from plumbum import cli


class MakeCSVfile(cli.Application):
    """Organizes input images and corresponding labelmaps in a csv file
        with proper headers. The output csv file is provided as an input to atlas making algorithm."""

    dataDir = cli.SwitchAttr(
        ['-i', '--input'],
        cli.ExistingDirectory,
        help='Input direcotry with all the images and labelmaps',
        mandatory=True)

    suffixes = cli.SwitchAttr(
        ['-l', '--labels'],
        help='''List of file suffixes in quotations, e.g. "image mask cingr1 cingr2 label1 label2",
                (image suffix, followed by labelmap suffixes), 
                assuming filenames are "#*suffix.extension", 
                ''',
        mandatory=True)

    out = cli.SwitchAttr(
        ['-o', '--out'], help='Output csv file', mandatory=True)

    def main(self):

        allFiles = os.listdir(self.dataDir)


        df1 = pd.DataFrame({})
        headers= self.suffixes.split(' ')

        # putting the images in the first column of the dictionary and
        # corresponding labels in subsequent columns
        for i in range(len(headers)):

            label = headers[i]

            files = []
            for f in allFiles:
                if f.endswith(label + '.nrrd') or f.endswith(label + '.nii') or f.endswith(
                        label + '.nii.gz') or f.endswith(label + '.nhdr'):
                    files.append(os.path.abspath(f))


            df1 = pd.concat([df1, pd.DataFrame({label: files})], axis=1)

        df1.to_csv(self.out, index=False)


if __name__ == '__main__':
    MakeCSVfile.run()




