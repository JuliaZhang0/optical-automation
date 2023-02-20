import bisect
import math
import os

import numpy as np
from scipy import interpolate
from scipy.integrate import nquad

# =========================================
# Speos BSDF Help files
# https://ansyshelp.ansys.com/account/secured?returnurl=/Views/Secured/corp/v222/en/Optis_UG_LAB/Optis/UG_Lab/structure_of_anisotropic_bsdf_files_81025.html
# Zemax BSDF Help files
# https://support.zemax.com/hc/en-us/articles/1500005486801-BSDF-Data-Interchange-file-format-specification
# =========================================


def convert_normal_to_specular_using_cartesian(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cartesian coordinates
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
    """

    # spherical coordinates in normal reference
    theta_i *= math.pi / 180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = math.sin(theta_i) * math.cos(phi_i)
    y_i = math.sin(theta_i) * math.sin(phi_i)
    z_i = math.cos(theta_i)
    # Conversion to new specular cartesian coordinates
    x_o = x_i * math.cos(angle_inc * math.pi / 180) - z_i * math.sin(angle_inc * math.pi / 180)
    y_o = y_i
    z_o = x_i * math.sin(angle_inc * math.pi / 180) + z_i * math.cos(angle_inc * math.pi / 180)
    # Normalization
    norm = math.sqrt(x_o * x_o + y_o * y_o + z_o * z_o)
    x_o *= 1 / norm
    y_o *= 1 / norm
    z_o *= 1 / norm
    # Conversion to new spherical coordinates
    theta_o = math.acos(z_o) * (180 / math.pi)

    if x_o == 0:
        if y_o == 0:
            phi_o = 0
        if y_o > 0:
            phi_o = 90
        if y_o < 0:
            phi_o = 270
    else:
        phi_o = math.atan(y_o / x_o) * (180 / math.pi)
        if x_o < 0:
            phi_o = 180 + phi_o
        if x_o > 0 and y_o < 0:
            phi_o = 360 + phi_o

    # added lines to change phi ref
    if phi_o < 180:
        phi_o = phi_o + 180
    else:
        phi_o = phi_o - 180

    return (theta_o, phi_o)


def convert_specular_to_normal_using_cartesian(theta_i, phi_i, angle_inc):
    """
    That function converts from specular to normal reference using cartesian coordinates
    Specular reference: phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the specular reference
    phi_i : float
        Scattered azimuthal angle in the specular reference
    angle_inc : float
        Angle of incidence
    """

    # spherical coordinates in normal reference
    theta_i *= math.pi / 180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = math.sin(theta_i) * math.cos(phi_i)
    y_i = math.sin(theta_i) * math.sin(phi_i)
    z_i = math.cos(theta_i)
    # Conversion to new normal cartesian coordinates
    x_o = -x_i * math.cos(angle_inc * math.pi / 180) + z_i * math.sin(angle_inc * math.pi / 180)  # to check
    y_o = y_i
    z_o = x_i * math.sin(angle_inc * math.pi / 180) + z_i * math.cos(angle_inc * math.pi / 180)  # to check
    # Normalization
    norm = math.sqrt(x_o * x_o + y_o * y_o + z_o * z_o)
    x_o *= 1 / norm
    y_o *= 1 / norm
    z_o *= 1 / norm
    # Conversion to new spherical coordinates
    theta_o = math.acos(z_o) * (180 / math.pi)

    if round(x_o, 2) == 0:
        if round(y_o, 0) == 0:
            phi_o = phi_i * (180 / math.pi)
        if y_o > 0:
            phi_o = 270
        if y_o < 0:
            phi_o = 90
    else:
        phi_o = abs(math.atan2(y_o, x_o) * (180 / math.pi))
        if round(y_o, 3) > 0:
            phi_o = 360 - phi_o

    theta_o = round(theta_o, 2)
    phi_o = round(phi_o, 2)

    return (theta_o, phi_o)


def convert_normal_to_specular_using_cylindrical(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cylindrical cartesian conversion
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
    """

    # cylindrical coordinates
    # theta_i*=math.pi/180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = (theta_i) * math.cos(phi_i)
    y_i = (theta_i) * math.sin(phi_i)
    # Conversion to new cartesian coordinates
    x_o = x_i - angle_inc
    y_o = y_i
    # Conversion to new cylindrical coordinates
    theta_o = math.sqrt(x_o * x_o + y_o * y_o)

    if x_o == 0:
        if y_o == 0:
            phi_o = 0
        if y_o > 0:
            phi_o = 90
        if y_o < 0:
            phi_o = 270
    else:
        phi_o = math.atan(y_o / x_o) * (180 / math.pi)
        if x_o < 0:
            phi_o = 180 + phi_o
        if x_o > 0 and y_o < 0:
            phi_o = 360 + phi_o

    return (theta_o, phi_o)


def convert_normal_to_specular_using_cylindrical_phiref(theta_i, phi_i, angle_inc):
    """
    That function converts from normal to specular reference using cylindrical cartesian conversion
    phi=0 for OpticStudio is phi=180 for speos
    phi = 0 top of the plot

    Parameters
    ----------
    theta_i : float
        Scattered polar angle in the normal reference
    phi_i : float
        Scattered azimuthal angle in the normal reference
    angle_inc : float
        Angle of incidence
    """

    # cylindrical coordinates
    # theta_i*=math.pi/180
    phi_i *= math.pi / 180
    # Conversion to cartesian coordinates
    x_i = (theta_i) * math.cos(phi_i)
    y_i = (theta_i) * math.sin(phi_i)
    # Conversion to new cartesian coordinates
    x_o = x_i - angle_inc
    y_o = y_i
    # Conversion to new cylindrical coordinates
    theta_o = math.sqrt(x_o * x_o + y_o * y_o)

    if x_o == 0:
        if y_o == 0:
            phi_o = 0
        if y_o > 0:
            phi_o = 90
        if y_o < 0:
            phi_o = 270
    else:
        phi_o = math.atan(y_o / x_o) * (180 / math.pi)
        if x_o < 0:
            phi_o = 180 + phi_o
        if x_o > 0 and y_o < 0:
            phi_o = 360 + phi_o

    # added lines to change phi ref
    if phi_o < 180:
        phi_o = phi_o + 180
    else:
        phi_o = phi_o - 180

    return (theta_o, phi_o)


def read_zemax_bsdf(inputFilepath, bool_log):
    """
    That function reads Zemax BSDF file

    Parameters
    ----------
    inputFilepath : string
        BSDF filename
    bool_log : boolean
        0 --> no report / 1 --> reports values
    """

    bfile = open(inputFilepath, "r")

    # Read the header
    if bool_log == 1:
        print("Reading header of Zemax BSDF.....")
    # Source type
    sourceLine = bfile.readline()
    while sourceLine[0] == "#":
        sourceLine = bfile.readline()
    # source = sourceLine[8:-1]
    source = sourceLine[6:-1]
    source = source.strip()
    if bool_log == 1:
        print("Source = " + str(source))
    # Symmetry type
    symmetryLine = bfile.readline()
    while symmetryLine[0] == "#":
        symmetryLine = bfile.readline()
    # symmetry = symmetryLine[10:-1]
    symmetry = symmetryLine[8:-1]
    symmetry = symmetry.strip()
    if bool_log == 1:
        print("Symmetry = " + str(symmetry))
    # Spectral content type
    spectralContentLine = bfile.readline()
    while spectralContentLine[0] == "#":
        spectralContentLine = bfile.readline()
    # spectralContent = spectralContentLine[17:-1]
    spectralContent = spectralContentLine[15:-1]
    spectralContent = spectralContent.strip()
    if bool_log == 1:
        print("Spectral content = " + str(spectralContent))
    # Scatter type
    scatterTypeLine = bfile.readline()
    while scatterTypeLine[0] == "#":
        scatterTypeLine = bfile.readline()
    # scatterType = scatterTypeLine[13:-1]
    scatterType = str(scatterTypeLine[11:-1])
    scatterType = scatterType.strip()
    if bool_log == 1:
        print("Scatter type = " + str(scatterType))
    # Number sample rotation
    sampleRotationLine = bfile.readline()
    while sampleRotationLine[0] == "#":
        sampleRotationLine = bfile.readline()
    # nbSampleRotation = int(sampleRotationLine[16:-1])
    nbSampleRotation = int(sampleRotationLine[14:-1])
    if bool_log == 1:
        print("Nb sample rotation = " + str(nbSampleRotation))
    # Sample rotation values
    sampleRotationLine = bfile.readline()
    while sampleRotationLine[0] == "#":
        sampleRotationLine = bfile.readline()
    # sampleRotation = sampleRotationLine[:-1].split('\t')
    sampleRotationString = sampleRotationLine[:-1].split()
    while sampleRotationString[-1] == "":
        sampleRotationString = sampleRotationString[:-1]
    if len(sampleRotationString) != nbSampleRotation:
        print(".....WARNING: Wrong data for sample rotation values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        sampleRotation = [float(i) for i in sampleRotationString]
        if bool_log == 1:
            print("Sample rotation angle values : " + str(sampleRotationString))
    # Number angle incidence
    angleIncidenceLine = bfile.readline()
    while angleIncidenceLine[0] == "#":
        angleIncidenceLine = bfile.readline()
    # nbAngleIncidence = int(angleIncidenceLine[18:-1])
    nbAngleIncidence = int(angleIncidenceLine[16:-1])
    if bool_log == 1:
        print("Nb angle incidence = " + str(nbAngleIncidence))
    # Angle incidence values
    angleIncidenceLine = bfile.readline()
    while angleIncidenceLine[0] == "#":
        angleIncidenceLine = bfile.readline()
    # Split can be tabular or white spaces
    # angleIncidence = angleIncidenceLine[:-1].split('\t')
    angleIncidenceString = angleIncidenceLine[:-1].split()
    while angleIncidenceString[-1] == "":
        angleIncidenceString = angleIncidenceString[:-1]
    if len(angleIncidenceString) != nbAngleIncidence:
        print(".....WARNING: Wrong data for angle incidence values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        angleIncidence = [float(i) for i in angleIncidenceString]
        if bool_log == 1:
            print("Angle incidence angle values : " + str(angleIncidenceString))
    # Number scatter azimuth
    scatterAzimuthLine = bfile.readline()
    while scatterAzimuthLine[0] == "#":
        scatterAzimuthLine = bfile.readline()
    # nbScatterAzimuth = int(scatterAzimuthLine[15:-1])
    nbScatterAzimuth = int(scatterAzimuthLine[14:-1])
    if bool_log == 1:
        print("Nb scatter azimuth = " + str(nbScatterAzimuth))
    # Scatter azimuth values
    scatterAzimuthLine = bfile.readline()
    while scatterAzimuthLine[0] == "#":
        scatterAzimuthLine = bfile.readline()
    # scatterAzimuth = scatterAzimuthLine[:-1].split('\t')
    scatterAzimuthString = scatterAzimuthLine[:-1].split()
    while scatterAzimuthString[-1] == "":
        scatterAzimuthString = scatterAzimuthString[:-1]
    if len(scatterAzimuthString) != nbScatterAzimuth:
        print(".....WARNING: Wrong data for scatter azimuth values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        scatterAzimuth = [float(i) for i in scatterAzimuthString]
        if bool_log == 1:
            print("Scatter azimuth angle values : " + str(scatterAzimuthString))
    # Number scatter radial
    scatterRadialLine = bfile.readline()
    while scatterRadialLine[0] == "#":
        scatterRadialLine = bfile.readline()
    # nbScatterRadial = int(scatterRadialLine[14:-1])
    nbScatterRadial = int(scatterRadialLine[13:-1])
    if bool_log == 1:
        print("Nb scatter radial = " + str(nbScatterRadial))
    # Scatter radial values
    scatterRadialLine = bfile.readline()
    while scatterRadialLine[0] == "#":
        scatterRadialLine = bfile.readline()
    # scatterRadial = scatterRadialLine[:-1].split('\t')
    scatterRadialString = scatterRadialLine[:-1].split()
    while scatterRadialString[-1] == "":
        scatterRadialString = scatterRadialString[:-1]
    if len(scatterRadialString) != nbScatterRadial:
        print(".....WARNING: Wrong data for scatter radial values")
        # tempVariable = input(".....Press Enter to continue")
    else:
        scatterRadial = [float(i) for i in scatterRadialString]
        if bool_log == 1:
            print("Scatter radial angle values : " + str(scatterRadialString))
    if bool_log == 1:
        print(".....Header was correctly read\n")
    # tempVariable = input('Press Enter to continue\n')

    if bool_log == 1:
        print("Reading BSDF content.....")
    dataLine = bfile.readline()
    while dataLine[0:9] != "DataBegin":
        dataLine = bfile.readline()
    # Initialization of a matrix bsdfData
    # Initialization of a vector tisData to save the TIS at each sample rotation and angle of incidence
    # Initialization of a vector normalizationBsdf to normalize the BSDF block
    # The normalization is done vs the BSDF data from the first angle of incidence
    # TIS = integral(BSDF x cos(theta)sin(theta) dtheta dphi)

    bsdfData = np.zeros((nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial))
    tisData = np.zeros((nbSampleRotation, nbAngleIncidence))

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            # Reading TIS (Total Integrated Scatter) value
            tisLine = bfile.readline()
            tisData[i][j] = float(tisLine[4:-1])
            for k in range(nbScatterAzimuth):
                dataLine = bfile.readline()
                bsdfData[i][j][k] = dataLine.split()
    if bool_log == 1:
        print(".....BSDF data was correctly read\n")

    return (
        scatterType,
        symmetry,
        nbSampleRotation,
        nbAngleIncidence,
        nbScatterAzimuth,
        nbScatterRadial,
        angleIncidence,
        sampleRotation,
        scatterRadial,
        scatterAzimuth,
        tisData,
        bsdfData,
    )


def read_speos_bsdf(inputFilepath, bool_log):
    """
    That function reads Speos BSDF file

    Parameters
    ----------
    inputFilepath : string
        BSDF filename
    bool_log : boolean
        0 --> no report / 1 --> reports values

    """

    bool_success = 1
    nb_reflection_transmission = 1

    bfile = open(inputFilepath, "r")
    filesize = os.fstat(bfile.fileno()).st_size

    input_file_extension = os.path.splitext(inputFilepath)[1].lower()[0:]
    if "brdf" in input_file_extension:
        symmetry = "Asymmetrical"
    # Read the header
    if bool_log == 1:
        print("Reading header of Speos BSDF.....")
    # Row 1 : header
    headerLine = bfile.readline()
    header = headerLine[:-1].split(" ")
    version = header[len(header) - 1]
    if float(version[1:]) < 8.0:
        bool_success = 0
        print(".....WARNING: The format is not supported.")
        print(".....Open and save the file with the BSDF viewer to update the format.")
        tempVariable = input(".....Press Enter to continue")
        exit()
    if bool_log == 1:
        print("Header = " + str(headerLine))
    # Row 2 : text 0 or binary 1
    textorbinaryLine = bfile.readline()
    textorbinary = textorbinaryLine[:-1].split("\t")
    if textorbinary[0] == 0:
        bool_success = 0
        print(".....WARNING: The BSDF data cannot be read. It is not a text.")
        tempVariable = input(".....Press Enter to continue")
        exit()
    else:
        if bool_log == 1:
            print("Text = " + str(textorbinaryLine))
    # Row 3 : Comment line
    commentLine = bfile.readline()
    # Row 4 : Number of characters to read for the measurement description. Several lines are allowed
    nbmeasurementLine = bfile.readline()
    nbmeasurement = nbmeasurementLine[:-1].split("\t")
    # Row 5 : Measurement description (cannot be edited from the viewer).
    measurementdescriptionLine = bfile.readline()
    # Row 6: Contains two boolean values (0=false and 1=true) - reflection / transmission data
    reflectionortransmissionLine = bfile.readline()
    reflectionortransmission = reflectionortransmissionLine[:-1].split("\t")
    # Reflection: false or true
    if reflectionortransmission[0] == "1":
        scatterType = "BRDF"
    if reflectionortransmission[1] == "1":
        scatterType = "BTDF"
    if reflectionortransmission[0] == "1" and reflectionortransmission[1] == "1":
        nb_reflection_transmission = 2
        #print(".....WARNING: The BSDF cannot be converted.")
        #print(".....It contains transmission and reflection data.")
        #tempVariable = input(".....Press Enter to continue")
        #exit()
    # Row 7: Contains a boolean value describing the type of value stored in the file: 1 bsdf / 0 intensity
    typeLine = bfile.readline()
    # Row 8: Number of incident angles and number of wavelength samples (in nanometer).
    nbAngleIncidenceWavelengthLine = bfile.readline()
    nbAngleIncidenceWavelength = nbAngleIncidenceWavelengthLine[:-1].split("\t")
    nbAngleIncidence = int(nbAngleIncidenceWavelength[0])
    nbWavelength = int(nbAngleIncidenceWavelength[1])
    # Row 9: List of the incident angles.
    angleIncidenceLine = bfile.readline()
    angleIncidenceString = angleIncidenceLine[:-1].split("\t")
    angleIncidence = [float(i) for i in angleIncidenceString]
    # Row 10: List of the wavelength samples.
    wavelengthLine = bfile.readline()
    wavelengthString = wavelengthLine[:-1].split("\t")
    wavelength = [float(i) for i in wavelengthString]
    # Row 11: Reflection (or transmission) percentage for BRDF wavelength data normalization, for the first table.
    # NormalizationLine = bfile.readline()

    # Row 12: Number of angles measured for Theta and Phi, for the incident angle N°1 and the wavelength N°1 of the incident angle N°1.
    # nbthetaphiLine = bfile.readline()
    # nbthetaphi = nbthetaphiLine[:-1].split(' ')
    # nbScatterRadial = int(nbthetaphi[0])
    # nbScatterAzimuth = int(nbthetaphi[1])
    # Row 13: table
    # scatterAzimuthLine = bfile.readline()
    # scatterAzimuth = scatterAzimuthLine[:-1].split('\t')

    if bool_log == 1:
        print(".....Header was correctly read\n")
    # tempVariable = input('Press Enter to continue\n')

    if bool_log == 1:
        print("Reading BSDF content.....")

    scatterRadial_list = []
    scatterAzimuth_list = []
    nbScatterRadial_list = []
    nbScatterAzimuth_list = []
    tisData = np.zeros((nb_reflection_transmission * nbAngleIncidence, nbWavelength))

    # tisData[0][0] = float(NormalizationLine)

    bsdfData_list = []

    for i in range(nb_reflection_transmission * nbAngleIncidence):
        for j in range(nbWavelength):
            tisData[i][j] = float(bfile.readline())
            nbthetaphiLine = bfile.readline()
            nbthetaphi = nbthetaphiLine[:-1].split(" ")
            nbScatterRadial = int(nbthetaphi[0])
            nbScatterAzimuth = int(nbthetaphi[1])
            nbScatterRadial_list.append(nbScatterRadial)
            nbScatterAzimuth_list.append(nbScatterAzimuth)

            scatterAzimuthLine = bfile.readline()
            scatterAzimuthLineString = (scatterAzimuthLine[:-1].strip()).split("\t")
            scatterAzimuth = [float(i) for i in scatterAzimuthLineString]
            scatterAzimuth_list.append(scatterAzimuth)

            bsdfDataBlock = np.zeros((nbScatterRadial, nbScatterAzimuth))
            scatterRadial = np.zeros(nbScatterRadial)

            for k in range(nbScatterRadial):
                dataLine = bfile.readline()
                data = dataLine.split()
                scatterRadial[k] = float(data[0])
                bsdfDataBlock[k] = data[1:]
            scatterRadial_list.append(scatterRadial)
            bsdfData_list.append(np.transpose(bsdfDataBlock))

    if bool_log == 1:
        print(".....BSDF data was correctly read\n")

    #    return scatterType, BSDFType, nbSampleRotation, nbAngleIncidence, nbScatterAzimuth, nbScatterRadial, \
    #           angleIncidence, wavelength, scatterRadial, scatterAzimuth, tisData, bsdfData
    nbSampleRotation = nbWavelength

    return (
        bool_success,
        nb_reflection_transmission,
        scatterType,
        symmetry,
        nbSampleRotation,
        nbAngleIncidence,
        angleIncidence,
        wavelength,
        scatterRadial_list,
        scatterAzimuth_list,
        tisData,
        bsdfData_list,
    )


def write_speos_header_bsdf(
    binaryMode,
    anisotropyVector,
    scatterType,
    nbSampleRotation,
    nbAngleIncidence,
    sampleRotation,
    angleIncidence,
    tisData,
):
    """
    That function writes the header of Speos BSDF file

    Parameters
    ----------
    binaryMode : boolean
        Text or binary mode - only text for now
    anisotropyVector : vector
        Anisotropy vector
    scatterType : string
        BRDF or BTDF
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    sampleRotation : list
        list of sample rotations
    angleIncidence : float
        list of angles of incidences
    tisData : float
        list of tis values
    """

    measurementDescription = "Measurement description"
    comment = "Comment"

    # Header
    nLines = ["OPTIS - Anisotropic BSDF surface file v7.0\n"]
    # Binary mode
    nLines.append(str(binaryMode) + "\n")
    # Comment
    nLines.append(comment + "\n")
    # Measurement description
    nLines.append(str(len(measurementDescription)) + "\n")
    nLines.append(measurementDescription + "\n")
    # Anisotropy vector
    nLines.append(str(anisotropyVector[0]) + "\t" + str(anisotropyVector[1]) + "\t" + str(anisotropyVector[2]) + "\n")
    # Scatter type (BRDF/BTDF)
    # Type of values
    # 1 means the data is proportional to the BSDF data
    # 0 means the data is proportional to the measured intensity
    # For BTDF: valuesType = 0 because of a bug
    if scatterType == "BRDF":
        nLines.append("1" + "\t" + "0" + "\n")
        valuesType = 1
        nLines.append(str(valuesType) + "\n")
    elif scatterType == "BTDF":
        nLines.append("0" + "\t" + "1" + "\n")
        valuesType = 0
        nLines.append(str(valuesType) + "\n")
    else:
        print(".....WARNING: Original data file has no valid ScatterType")
        # tempVariable = input(".....Press Enter to continue")
    # Anisotropy angles (SampleRotations)
    nLines.append(str(nbSampleRotation) + "\n")
    for i in range(nbSampleRotation):
        nLines.append(str(sampleRotation[i]) + "\t")
    if nbSampleRotation != 0:
        nLines.append("\n")
    # Incident angles (AngleIncidence)
    for k in range(nbSampleRotation):
        nLines.append(str(nbAngleIncidence) + "\n")
        for i in range(nbAngleIncidence):
            nLines.append(str(angleIncidence[i]) + "\t")
        if nbAngleIncidence != 0:
            nLines.append("\n")
    # theta and phi for measurement
    nLines.append(str(angleIncidence[0]) + "\t" + "0\n")
    # Spectrum description
    nLines.append("\n")
    # Number of wavelength
    nLines.append("2" + "\n")
    # Wavelength measurements
    nLines.append("350" + "\t" + str(100 * tisData[0][0]) + "\n")
    nLines.append("850" + "\t" + str(100 * tisData[0][0]) + "\n")

    return nLines


def write_zemax_header_bsdf(
    scatterType,
    symmetry,
    currentwavelength,
    nbSampleRotation,
    nbAngleIncidence,
    sampleRotation,
    angleIncidence,
    line_theta,
    line_phi,
):
    """
    That function writes the header of Zemax BSDF file

    Parameters
    ----------
    scatterType : string
        BRDF or BTDF
    symmetry : string
        Asymmetrical or Asymmetrical4D
    currentwavelength : float
        Current wavelength
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    sampleRotation : list
        list of sample rotations
    angleIncidence : float
        list of angles of incidences
    line_theta : list
        list of theta / radial angles
    line_phi : list
        list of phi / azimuthal angles
    """

    # Header
    nLines = ["#Data converted from Speos data\n"]
    # Wavelength
    comment = "#Wavelength (nm) = " + str(currentwavelength)
    nLines.append(str(comment) + "\n")
    # Source
    comment = "Source  Measured"
    nLines.append(str(comment) + "\n")
    # Symmetry
    nLines.append("Symmetry  " + str(symmetry) + "\n")
    # SpectralContent
    spectralcontent = "SpectralContent  Monochrome"
    nLines.append(str(spectralcontent) + "\n")
    # ScatterType
    ScatterType = "ScatterType  " + scatterType
    nLines.append(ScatterType + "\n")
    # SampleRotation
    nLines.append("SampleRotation  " + str(nbSampleRotation) + "\n")
    # List of SampleRotation
    for i in range(nbSampleRotation):
        nLines.append(str(sampleRotation[i]) + "\t")
    nLines.append("\n")
    # AngleOfIncidence
    nLines.append("AngleOfIncidence  " + str(nbAngleIncidence) + "\n")
    # List of AngleOfIncidence
    for i in range(nbAngleIncidence):
        nLines.append(str(angleIncidence[i]) + "\t")
    nLines.append("\n")
    # List of ScatterAzimuth
    nLines.append("ScatterAzimuth " + str(len(line_phi)) + "\n")
    for i in range(len(line_phi)):
        nLines.append(str(line_phi[i]) + "\t")
    nLines.append("\n")
    # List of ScatterRadial
    nLines.append("ScatterRadial " + str(len(line_theta)) + "\n")
    for i in range(len(line_theta)):
        nLines.append(str(line_theta[i]) + "\t")
    nLines.append("\n")
    # A few more lines
    nLines.append("\n")
    nLines.append("Monochrome\n")
    nLines.append("DataBegin\n")

    return nLines


def convert_zemax_speos_bsdf_data(
    nb_reflection_transmission,
    symmetry,
    scatterType,
    nbSampleRotation,
    nbAngleIncidence,
    sampleRotation,
    angleIncidence,
    scatterRadial,
    scatterAzimuth,
    bsdfData,
    precisionTheta,
    precisionPhi,
    bool_speos_brdf,
):
    """
    That function converts the block data from Zemax to Speos

    Parameters
    ----------
    nb_reflection_transmission : integer
        1 if data=BRDF or BTDF and 2 if both
    symmetry : string
        PlaneSymmetric or ASymmetrical4D
    scatterType : string
        BTDF or BRDF
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angles of incidences
    sampleRotation : float
        List of sample rotations
    angleIncidence : float
        List of angles of incidence
    scatterRadial : float
        List of radial angles
    scatterAzimuth : float
        List of azimuthal angles
    bsdfData : float
        Array with Zemax BSDF data
    precisionTheta : float
        Precision of theta in Speos BSDF
    precisionPhi : float
        Precision of Phi in Speos BSDF
    bool_speos_brdf : boolean
        bool = 1 if speos BRDF data to convert, 0 otherwise
    """

    # BSDF data
    nbTheta = int(90 / precisionTheta + 1)
    nbPhi = int(360 / precisionPhi + 1)

    # Initialization
    # If BRDF
    # SampleRotation stands for angle of incidence
    # Angle of incidence stands for wavelength
    temp_bsdfData = np.zeros((nb_reflection_transmission * nbSampleRotation, nbAngleIncidence, nbTheta, nbPhi))
    bsdfDataSpeos = np.zeros((nb_reflection_transmission * nbSampleRotation, nbAngleIncidence, nbTheta, nbPhi))

    if bool_speos_brdf == 1:
        scatterRadial_save = scatterRadial
        scatterAzimuth_save = scatterAzimuth

    index = 0
    #Sample rotation or Wavelength
    for i in range(nb_reflection_transmission * nbSampleRotation):
        currentSampleRot = sampleRotation[i%nbSampleRotation]
        for j in range(nbAngleIncidence):
            currentAngleInc = angleIncidence[j]
            for k in range(nbTheta):
                currentTheta = k * precisionTheta
                for l in range(nbPhi):
                    currentPhi = l * precisionPhi
                    # Convert the angles to the "specular" definition
                    if bool_speos_brdf == 1:
                        newTheta, newPhi = convert_specular_to_normal_using_cartesian(
                            currentTheta, currentPhi, currentSampleRot
                        )
                    else:
                        newTheta, newPhi = convert_normal_to_specular_using_cartesian(
                            currentTheta, currentPhi, currentAngleInc
                        )
                    # newTheta, newPhi = convert_cylindrical(currentTheta, currentPhi, currentAngleInc)
                    # newTheta, newPhi = convert_cylindrical_phiref(currentTheta, currentPhi, currentAngleInc)
                    if newTheta > 90 or newTheta < 0:
                        bsdfDataSpeos[i][j][k][l] = 0
                    else:
                        # Added the case where symmetry == PlaneSymmetrical
                        if symmetry == "PlaneSymmetrical" and newPhi > 180:
                            newPhi = 360 - newPhi
                        # Look in scatterRadial to find scatterRadial[indexInfTheta] = newTheta
                        # Theta
                        if bool_speos_brdf == 1:
                            scatterRadial = scatterRadial_save[index]
                            scatterAzimuth = scatterAzimuth_save[index]

                        indexInfTheta = bisect.bisect_left(scatterRadial, newTheta)

                        if indexInfTheta == 0:
                            indexSupTheta = indexInfTheta
                            coeffTheta = 0
                        elif indexInfTheta <= (len(scatterRadial) - 1):
                            # Sandrine: added +1
                            indexInfTheta = indexInfTheta - 1
                            indexSupTheta = indexInfTheta + 1
                            thetaInf = scatterRadial[indexInfTheta]
                            thetaSup = scatterRadial[indexSupTheta]
                            coeffTheta = (newTheta - thetaInf) / (thetaSup - thetaInf)
                        else:
                            indexInfTheta = indexInfTheta - 1
                            indexSupTheta = indexInfTheta
                            coeffTheta = 0
                        # Phi
                        indexInfPhi = bisect.bisect_left(scatterAzimuth, newPhi)
                        if indexInfPhi == 0:
                            indexSupPhi = indexInfPhi
                            coeffPhi = 0
                        elif indexInfPhi <= (len(scatterAzimuth) - 1):
                            indexInfPhi = indexInfPhi - 1
                            indexSupPhi = indexInfPhi + 1
                            phiInf = scatterAzimuth[indexInfPhi]
                            phiSup = scatterAzimuth[indexSupPhi]
                            coeffPhi = (newPhi - phiInf) / (phiSup - phiInf)
                        else:
                            indexInfPhi = indexInfPhi - 1
                            indexSupPhi = indexInfPhi + 1

                            coeffPhi = 0
                        # Defining the BSDF values
                        if bool_speos_brdf == 0:
                            bsdf1 = bsdfData[i][j][indexInfPhi][indexInfTheta]
                            bsdf2 = bsdfData[i][j][indexInfPhi][indexSupTheta]
                            bsdf3 = bsdfData[i][j][indexSupPhi][indexInfTheta]
                            bsdf4 = bsdfData[i][j][indexSupPhi][indexSupTheta]
                        else:
                            bsdf_temp = bsdfData[index]
                            bsdf1 = bsdf_temp[indexInfPhi][indexInfTheta]
                            bsdf2 = bsdf_temp[indexInfPhi][indexSupTheta]
                            bsdf3 = bsdf_temp[indexSupPhi][indexInfTheta]
                            bsdf4 = bsdf_temp[indexSupPhi][indexSupTheta]

                        # Linear interpolation to find the BSDF data
                        bsdfN1 = bsdf1 * (1 - coeffTheta) + bsdf2 * coeffTheta
                        bsdfN2 = bsdf3 * (1 - coeffTheta) + bsdf4 * coeffTheta
                        bsdfValue = bsdfN1 * (1 - coeffPhi) + bsdfN2 * coeffPhi
                        temp_bsdfData[i][j][k][l] = bsdfValue
                        # if scatterType == "BRDF":
                        # bsdfDataSpeos[i][j][k][l]=bsdfValue
                        # else:
                        # bsdfDataSpeos[i][j][nbTheta - 1 - k][l] = bsdfValue
            index = index + 1

    if bool_speos_brdf == 1 or scatterType == "BRDF":
        bsdfDataSpeos = temp_bsdfData
        line_theta = [(precisionTheta * k) for k in range(nbTheta)]
    else:
        line_theta = [(90 + precisionTheta * k) for k in range(nbTheta)]
        for i in range(nbSampleRotation):
            for j in range(nbAngleIncidence):
                for k in range(nbTheta):
                    bsdfDataSpeos[i][j][k] = temp_bsdfData[i][j][nbTheta - 1 - k]

    line_phi = [(precisionPhi * x) for x in range(nbPhi)]
    temp_bsdfData = []

    return bsdfDataSpeos, line_theta, line_phi


def normalize_bsdf_data(
    nbSampleRotation, nbAngleIncidence, line_theta, line_phi, tisData, bsdfData, bool_zemax0_speos1, bool_log
):
    """
    That function normalizes the BSDF data vs the TIS values

    Parameters
    ----------
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidences
    line_theta : list
        List of theta angles
    line_phi : list
        List of phi angles
    tisData : list
        List of TIS values
    bsdfData : matrix
        Raw BSDF data matrix - values to be normalized
    bool_log : boolean
        0 --> no report / 1 --> reports values
    Returns
    -------
    normalizationBsdf : list of values
        List of the normalization values for each angle of incidence / sample rotation
    """

    # BRDF: theta goes from 0 to 90
    # BTDF: theta goes from 90 to 180

    if bool_log == 1:
        print("Computing normalization...")
        print("nbSampleRotation nbAngleIncidence IntegralValue IntegralError Zemax_TIS_value NormalizationFactor")

    # Initialization
    normalizationBsdf = np.zeros((nbSampleRotation, nbAngleIncidence))

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            block_data = bsdfData[i, j, :, :]
            if bool_zemax0_speos1 == 1:
                block_data = block_data.transpose()

            theta_rad, phi_rad = np.radians(line_theta), np.radians(line_phi)  # samples on which integrande is known
            integrande = (
                (1 / math.pi) * block_data * np.sin(theta_rad) * np.cos(theta_rad)
            )  # *theta for polar integration
            # Linear interpolation of the values
            # interp2d is apparently deprecated
            # Look for alternatives f = interpolate.bisplrep(theta_rad, phi_rad, integrande)
            f = interpolate.interp2d(theta_rad, phi_rad, integrande, kind="linear", bounds_error=False, fill_value=0)

            # calculation of the integral
            # r = nquad(f, [[0, math.pi / 2], [0, 2 * math.pi]], opts=[{"epsabs": 0.1}, {"epsabs": 0.1}])
            r = nquad(
                f,
                [[min(theta_rad), max(theta_rad)], [min(phi_rad), max(phi_rad)]],
                opts=[{"epsabs": 0.1}, {"epsabs": 0.1}],
            )
            IntegralValue = abs(r[0])
            IntegralError = r[1]

            # Normalization of the data
            if IntegralValue > 0:
                normalizationBsdf[i][j] = tisData[i][j] / (IntegralValue)
            else:
                normalizationBsdf[i][j] == 1
                print("Integral = 0!!!!")

            if bool_log == 1:
                print(
                    i,
                    " ",
                    j,
                    " ",
                    round(IntegralValue, 3),
                    " ",
                    round(IntegralError, 3),
                    " ",
                    tisData[i][j],
                    " ",
                    round(normalizationBsdf[i][j], 3),
                )

            bsdfData[i][j][:][:] = bsdfData[i, j, :, :] * normalizationBsdf[i][j]

    return normalizationBsdf, bsdfData


def write_speos_data_bsdf(nLines, scatterType, nbSampleRotation, nbAngleIncidence, line_theta, line_phi, bsdfDataSpeos):
    """
    That function writes the main data of Speos BSDF file

    Parameters
    ----------
    nLines : text
        Text containing the BSDF Speos header
    scatterType : string
        BRDF or BTDF
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    line_theta : list
        list of theta angles
    line_phi : list
        list of phi angles
    bsdfDataSpeos : matrix of float
        BSDF data values
    """
    nbTheta = len(line_theta)
    nbPhi = len(line_phi)

    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            nLines.append(str(int(nbTheta)) + " " + str(int(nbPhi)) + "\n")

            # Write the 1st line of the block with the Phi values
            for x in range(nbPhi):
                currentPhi = line_phi[x]
                nLines.append("\t" + str(currentPhi))
            nLines.append("\n")
            for k in range(nbTheta):
                currentTheta = line_theta[k]
                nLines.append(str(currentTheta))
                for phi_idx in range(nbPhi):
                    if scatterType == "BRDF":
                        nLines.append("\t" + str(bsdfDataSpeos[i][j][k][phi_idx]))
                    elif scatterType == "BTDF":
                        thetas_cosine = math.cos((180 - currentTheta) * math.pi / 180)
                        nLines.append("\t" + str(thetas_cosine * bsdfDataSpeos[i][j][k][phi_idx]))
                nLines.append("\n")
    nLines.append("End of file")
    nLines.append("\n")

    return nLines


def write_zemax_data_bsdf(index_wavelength, index_RT, nbSampleRotation, nbAngleIncidence, tisData, bsdfData):
    """
    That function writes the main data of Zemax BSDF file

    Parameters
    ----------
    index_wavelength : integer
        Index of the wavelength
    index_RT : integer
    nbSampleRotation : integer
        Number of sample rotations
    nbAngleIncidence : integer
        Number of angle of incidence
    tisData : list
        TIS data values
    bsdfData : matrix of float
        BSDF data values

    Returns
    -------
    nLines = string
        Text containing the formatted header
    """
    nLines=[]
    for i in range(nbSampleRotation):
        for j in range(nbAngleIncidence):
            index_angle = j + nbAngleIncidence*index_RT
            nLines.append("TIS " + str(round(tisData[j][index_wavelength] / 100,3)) + "\n")
            for k in range(bsdfData.shape[3]):
                for l in range(bsdfData.shape[2] - 1):
                    scientific_notation = "{:.3e}".format(bsdfData[index_angle][index_wavelength][l][k])
                    nLines.append(str(scientific_notation) + "\t")
                l = bsdfData.shape[2] - 1
                scientific_notation = "{:.3e}".format(bsdfData[index_angle][index_wavelength][l][k])
                nLines.append(str(scientific_notation) + "\n")
    nLines.append("DataEnd\n")

    return nLines


def write_file(outputFilepath, nLines):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    nLines : text
        Text containing the data
    outputFilepath : filename
        file to write
    """
    nFile = open(outputFilepath, "w")
    nFile.writelines(nLines)
    nFile.close()
    print("The file " + str(outputFilepath) + " is ready!\n")

def phi_theta_recommended_precision(scatterRadial, scatterAzimuth, symmetry):
    """
    That function writes the text nLines in the file

    Parameters
    ----------
    scatterRadial : list
        List of radial / theta angles
    scatterAzimuth : list
        List of azimuthal / phi angles
    symmetry : string
        PlaneSymmetrical, Asymmetrical, Asymmetrical4D
    """
    nbTheta_max = 1000
    nbPhi_max = 1000
    theta_max = 90
    phi_max = 360
    multiple = 0.5

    if symmetry == "PlaneSymmetrical":
        phi_max = 180
        nbPhi_max = 500

    precisionTheta = theta_max / len(scatterRadial)
    if len(scatterRadial) > nbTheta_max:
        precisionTheta = round(theta_max / (nbTheta_max - 1), 1)
    else:
        precisionTheta = round(theta_max / (len(scatterRadial) - 1), 1)
    precisionTheta = round_to_multiple(precisionTheta, multiple)

    precisionPhi = phi_max / len(scatterAzimuth)
    if len(scatterAzimuth) > nbTheta_max:
        precisionPhi = round(phi_max / (nbPhi_max - 1), 1)
    else:
        precisionPhi = round(phi_max / (len(scatterAzimuth) - 1), 1)
    precisionPhi = round_to_multiple(precisionPhi, multiple)

    print("Precision Theta = ", precisionTheta)
    print("Precision Phi = ", precisionPhi)

    return precisionTheta, precisionPhi


def round_to_multiple(number, multiple):
    return multiple * round(number / multiple)


def convert_zemax_to_speos_bsdf(inputFilepath):
    """
    That function converts a Zemax BSDF file into a Speos BSDF file

    Parameters
    ----------
    inputFilepath : filename
        Zemax BSDF file to read
    """

    print("This Python code converts ZEMAX BSDF file to SPEOS BSDF format\n")

    # Reading Zemax file
    print("Reading Zemax BSDF file: " + str(inputFilepath) + "...\n")
    bool_log = 0

    (
        scatterType,
        symmetry,
        nbSampleRotation,
        nbAngleIncidence,
        nbScatterAzimuth,
        nbScatterRadial,
        angleIncidence,
        sampleRotation,
        scatterRadial,
        scatterAzimuth,
        tisData,
        bsdfData,
    ) = read_zemax_bsdf(inputFilepath, bool_log)

    # Recommended precisionTheta and precisionPhi
    precisionTheta, precisionPhi = phi_theta_recommended_precision(scatterRadial, scatterAzimuth, symmetry)

    # Converting Zemax data to Speos data
    print("Converting Zemax data to Speos data...\n")
    binaryMode = 0
    anisotropyVector = [0, 1, 0]
    nb_reflection_transmission = 1
    bool_speos_brdf = 0
    bsdfDataSpeos, line_theta, line_phi = convert_zemax_speos_bsdf_data(
        nb_reflection_transmission,
        symmetry,
        scatterType,
        nbSampleRotation,
        nbAngleIncidence,
        sampleRotation,
        angleIncidence,
        scatterRadial,
        scatterAzimuth,
        bsdfData,
        precisionTheta,
        precisionPhi,
        bool_speos_brdf,
    )
    # Normalization
    print("Computing Speos normalization...\n")
    bool_log = 1
    bool_zemax0_speos1 = 1
    normalizationBsdf, bsdfDataSpeos = normalize_bsdf_data(
        nbSampleRotation, nbAngleIncidence, line_theta, line_phi, tisData, bsdfDataSpeos, bool_zemax0_speos1, bool_log
    )

    # Writing Speos file content in nLines
    print("Writing Speos header data\n")
    nLines = write_speos_header_bsdf(
        binaryMode,
        anisotropyVector,
        scatterType,
        nbSampleRotation,
        nbAngleIncidence,
        sampleRotation,
        angleIncidence,
        tisData,
    )
    print("Writing Speos main data\n")
    nLines = write_speos_data_bsdf(
        nLines, scatterType, nbSampleRotation, nbAngleIncidence, line_theta, line_phi, bsdfDataSpeos
    )
    # Writing Speos file content (nLines) in a file
    print("Writing Speos BSDF file\n")
    # Speos output file
    outputFilepath = (
        os.path.splitext(inputFilepath)[0].lower()
        + "_"
        + str(precisionTheta)
        + "_"
        + str(precisionPhi)
        + ".anisotropicbsdf"
    )
    write_file(outputFilepath, nLines)

    print("The file " + str(outputFilepath) + " is ready!\n")
    print(".....End of process\n")


def convert_speos_to_zemax_bsdf(inputFilepath, bool_speos_brdf):
    """
    That function converts a Speos BSDF file into a Zemax BSDF file

    Parameters
    ----------
    inputFilepath : filename
        Speos BSDF file to read
    bool_speos_brdf : boolean
        bool = 1 if file extension = brdf
    """

    print("This Python code converts SPEOS BSDF file to ZEMAX BSDF format\n")

    # Reading Zemax file
    print("Reading Speos BSDF file: " + str(inputFilepath) + "...\n")
    bool_log = 0
    (
        bool_success,
        nb_reflection_transmission,
        scatterType,
        symmetry,
        nbWavelength,
        nbAngleIncidence,
        angleIncidence,
        wavelength,
        scatterRadial,
        scatterAzimuth,
        tisData,
        bsdfData,
    ) = read_speos_bsdf(inputFilepath, bool_log)

    if bool_success == 1:
        # Recommended precisionTheta and precisionPhi
        precisionTheta, precisionPhi = phi_theta_recommended_precision(scatterRadial[0], scatterAzimuth[0], symmetry)

        # Converting Speos data to Zemax data
        print("Converting Speos data to Zemax data...\n")
        # angle of incidence --> block of wavelength
        bsdfDataZemax, line_theta, line_phi = convert_zemax_speos_bsdf_data(
            nb_reflection_transmission,
            symmetry,
            scatterType,
            nbAngleIncidence,
            nbWavelength,
            angleIncidence,
            wavelength,
            scatterRadial,
            scatterAzimuth,
            bsdfData,
            precisionTheta,
            precisionPhi,
            bool_speos_brdf,
        )

        # Writing a Zemax file for each wavelength
        print("Writing Zemax data\n")
        text_RT = ["BRDF","BTDF"]
        for index_wavelength in range(nbWavelength):
            nbSampleRotation = 1
            sampleRotation = [0]

            for index_RT in range(nb_reflection_transmission):
                if nb_reflection_transmission > 1:
                    scatterType = text_RT[index_RT]
                nLines_header = write_zemax_header_bsdf(
                    scatterType,
                    symmetry,
                    wavelength[index_wavelength],
                    nbSampleRotation,
                    nbAngleIncidence,
                    sampleRotation,
                    angleIncidence,
                    line_theta,
                    line_phi,
                )

                nLines_data = write_zemax_data_bsdf(
                    index_wavelength,
                    index_RT,
                    nbSampleRotation,
                    nbAngleIncidence,
                    tisData,
                    bsdfDataZemax)

                # Writing Zemax file content (nLines) in a file
                outputFilepath = (
                        os.path.splitext(inputFilepath)[0].lower()
                        + "_"
                        + str(wavelength[index_wavelength])
                        + "_"
                        + str(scatterType)
                        + "_"
                        + str(precisionTheta)
                        + "_"
                        + str(precisionPhi)
                        + ".bsdf"
                )
                write_file(outputFilepath, nLines_header+nLines_data)

    print(".....End of process\n")
