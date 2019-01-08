#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from plumbum import cli
import nrrd

class App(cli.Application):
    '''Plots histogram of voxel intensities before and after epi correction'''

    # before = cli.SwitchAttr(
    #     '--bef', cli.ExistingFile, help='nrrd before epi', mandatory=True)
    # after = cli.SwitchAttr(
    #     '--aft', cli.ExistingFile, help='nrrd after epi', mandatory=True)

    @cli.positional(cli.ExistingFile, cli.ExistingFile)
    def main(self, before, after):

        imgb= nrrd.read(before)[0]
        imga= nrrd.read(after)[0]

        # seqb= [min(imgb.min(), -1), -1, 0, max(imgb.max(), 1)]
        seqb= [-1, 0, 1]
        # histb= np.histogram(imgb, seqb, density= True)
        # hista= np.histogram(imga, seqb, density= True)
        # plt.plot(seqb[:-1], histb[0], 'g:', label= 'before epi')
        # plt.plot(seqb[:-1], hista[0], 'r--', label= 'after epi')


        nb, _, _= plt.hist(imgb.flatten(), seqb, density= True, label= 'before epi', histtype= 'step', color= 'red')
        na, _, _= plt.hist(imga.flatten(), seqb, density= True, label= 'after epi', histtype= 'step', color= 'green')
        plt.grid(True)
        plt.legend()
        plt.xlabel('voxel values')
        plt.ylabel('prob(values)')
        plt.title('epi correction induced artifact')
        plt.show()


if __name__ == '__main__':
    App.run()