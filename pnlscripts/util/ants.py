#!/usr/bin/env python

# Not used
# Parameters taken from antsRegistrationSyN.sh


def initialStage(f, m):
    return ["--initial-moving-transform", "[" + f + "," + m + ",1]"]


def rigidStage(f, m):
    rigidConvergence = "[1000x500x250x100,1e-6,10]"
    rigidShrinkFactors = "8x4x2x1"
    rigidSmoothingSigmas = "3x2x1x0vox"
    return ["--transform", "Rigid[0.1]", "--metric",
            "MI[" + f + "," + m + ",1,32,Regular,0.25]", "--convergence",
            rigidConvergence, "--shrink-factors", rigidShrinkFactors,
            "--smoothing-sigmas", rigidSmoothingSigmas]


def affineStage(f, m):
    affineConvergence = "[1000x500x250x100,1e-6,10]"
    affineShrinkFactors = "8x4x2x1"
    affineSmoothingSigmas = "3x2x1x0vox"
    return ["--transform", "Affine[0.1]", "--metric",
            "MI[" + f + "," + m + ",1,32,Regular,0.25]", "--convergence",
            affineConvergence, "--shrink-factors", affineShrinkFactors,
            "--smoothing-sigmas", affineSmoothingSigmas]


def synStage(f, m, useCC=True):
    metricCC = ["--metric", "CC[" + f + "," + m + ",1,4]"]
    metricMI = ["--metric", "MI[" + f + "," + m + ",1,32,Regular,0.25]"]
    synConvergence = "[100x70x50x20,1e-6,10]"
    synShrinkFactors = "8x4x2x1"
    synSmoothingSigmas = "3x2x1x0vox"
    metric = metricCC if useCC else metricMI
    return ["--transform", "SyN[0.1,3,0]"] + \
        metric + ["--convergence", synConvergence
                  ,"--shrink-factors", synShrinkFactors
                  ,"--smoothing-sigmas", synSmoothingSigmas
        ]


extraParams = ["--verbose", "1", "--dimensionality", "3", "--float", "1",
               "--interpolation", "Linear", "--use-histogram-matching", "0",
               "--winsorize-image-intensities", "[0.005,0.995]"]


def antsRegistrationSyNParams(moving, fixed, outputs, useCC=True, numcores=32):
    """Return same parameters used by antsRegistrationSyN.sh, with additional
    option of using MI for the final non-linear stage.

    params: 'outputs' is an array: [prefix] or [prefix,warpedoutput.nii.gz] (See
    antsRegistration --help)"""

    return extraParams + \
            ["--output", str([str(x) for x in outputs])] + \
            initialStage(fixed,moving) + \
            rigidStage(fixed,moving) + \
            affineStage(fixed,moving) + \
            synStage(fixed,moving,useCC) + \
            ['-n', numcores]
