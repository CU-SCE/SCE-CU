# -*- coding: utf-8 -*-
"""
| ----------------------------------------------------------------------------------------------------------------------
| Date                : March 2020
| Copyright           : © 2020 by Ann Crabbé (KU Leuven)
| Email               : acrabbe.foss@gmail.com
| Acknowledgements    : Translated from VIPER Tools 2.0 (UC Santa Barbara, VIPER Lab).
|                       Dar Roberts, Kerry Halligan, Philip Dennison, Kenneth Dudley, Ben Somers, Ann Crabbé
|
| This file is part of the MESMA plugin and python package.
|
| This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
| License as published by the Free Software Foundation, either version 3 of the License, or any later version.
|
| This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
| warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
|
| You should have received a copy of the GNU General Public License (COPYING.txt). If not see www.gnu.org/licenses.
| ----------------------------------------------------------------------------------------------------------------------
"""
import numpy as np
from mesma.core.mesma import MesmaCore
from mesma.core.hard_classification import HardClassification
from mesma.core.shade_normalisation import ShadeNormalisation
from mesma.hubdc.applier import ApplierOperator
from mesma.hubdc.progressbar import ProgressBar
from qgis.PyQt.QtWidgets import QProgressBar


class MesmaOperator(ApplierOperator):
    """
    The Applier wrapper for our MESMA algorithm: allows to run mesma block-wise over a large image.
    Requires the user to set the input and output images before usage.
    """

    def ufunc(self, image_scale, library, look_up_table, em_per_class, unique_classes, lib_name,
              constraints=(-0.05, 1.05, 0., 0.8, 0.025, -9999, -9999), shade_spectrum=None,
              fusion_value=0.007, residual_image=False,
              use_band_weighing=False, use_band_selection=False, bands_selection_values=(0.99, 0.01), n_cores=1):
        """ Implement ufunc from the parent class. """

        # get image block without bad bands and with reflectance scaled to 0..1
        image = np.float32(self.inputRaster.raster(key='raster').array())

        if 'ENVI' in self.inputRaster.raster(key='raster').metadataDict().keys():
            bbl = self.inputRaster.raster(key='raster').metadataItem(key='bbl', domain='ENVI')
            if bbl is not None:
                bbl = np.where(np.array(bbl) == '1')[0]
                image = image[bbl, :, :]
            else:
                bbl = np.ones(len(image), dtype=int)
        else:
            bbl = np.ones(len(image), dtype=int)

        image /= image_scale

        # get pixel indices with no data values
        image_no_data_values = self.inputRaster.raster(key='raster').noDataValues()
        valid = self.full(value=True, dtype=bool)[0]
        for band, noDataValue in zip(image, image_no_data_values):
            if noDataValue is not None:
                valid *= band != noDataValue
        invalid = 1 - valid
        no_data_pixels = np.where(invalid)
        assert isinstance(no_data_pixels, tuple)

        # run mesma on the image block
        models, fractions, rmse, residuals = MesmaCore(n_cores).execute(image=image,
                                                                        library=library,
                                                                        look_up_table=look_up_table,
                                                                        em_per_class=em_per_class,
                                                                        no_data_pixels=no_data_pixels,
                                                                        constraints=constraints,
                                                                        shade_spectrum=shade_spectrum,
                                                                        fusion_value=fusion_value,
                                                                        residual_image=residual_image,
                                                                        use_band_weighing=use_band_weighing,
                                                                        use_band_selection=use_band_selection,
                                                                        bands_selection_values=bands_selection_values)

        # edit output
        self.outputRaster.raster(key='models').setArray(array=models)
        self.outputRaster.raster(key='fractions').setArray(array=fractions)
        self.outputRaster.raster(key='rmse').setArray(array=rmse)
        if residual_image:
            self.outputRaster.raster(key='residuals').setArray(array=residuals)

        self.outputRaster.raster(key='models').setNoDataValue(value=-2)
        self.outputRaster.raster(key='rmse').setNoDataValue(value=9998)

        for i, band_name in enumerate(unique_classes):
            self.outputRaster.raster(key='models').band(i).setDescription(band_name)
            self.outputRaster.raster(key='fractions').band(i).setDescription(band_name + '_fraction')
        self.outputRaster.raster(key='fractions').band(len(unique_classes)).setDescription('shade_fraction')
        self.outputRaster.raster(key='rmse').band(0).setDescription('rmse')

        self.outputRaster.raster(key='models').setMetadataItem(key='spectral_library', value=lib_name, domain='ENVI')
        self.outputRaster.raster(key='fractions').setMetadataItem(key='spectral_library', value=lib_name, domain='ENVI')
        self.outputRaster.raster(key='rmse').setMetadataItem(key='spectral_library', value=lib_name, domain='ENVI')

        if residual_image:
            if 'ENVI' in self.inputRaster.raster(key='raster').metadataDict().keys():
                band_names = self.inputRaster.raster(key='raster').metadataItem(key='band_names', domain='ENVI')
                band_names = np.array(band_names)[bbl]
                wavelengths = self.inputRaster.raster(key='raster').metadataItem(key='wavelength', domain='ENVI')
                wavelengths = np.array(wavelengths)[bbl]
                wavelengths = [float(x) for x in wavelengths]
                for i, band_name in enumerate(band_names):
                    self.outputRaster.raster(key='residuals').band(i).setDescription(band_name)
                self.outputRaster.raster(key='residuals').setMetadataItem(key='wavelength', domain='ENVI',
                                                                          value=wavelengths)


class HardClassificationOperator(ApplierOperator):
    """
    The Applier wrapper for our HardClassification algorithm: allows to run the algorithm block-wise over a large image.
    Requires the user to set the input and output images before usage.
    """

    def ufunc(self, band_names: list, shade_band: int = -1):
        """ Implement ufunc of the parent class. """
        image = np.float32(self.inputRaster.raster(key='raster').array())

        # run HardClassification on the image block
        new_image = HardClassification().execute(mesma_fraction_image=image, shade_band=shade_band)

        # edit output
        self.outputRaster.raster(key='classification').setArray(array=new_image)

        description = ""
        for i, name in enumerate(band_names):
            description += str(i) + "=" + name + ";"
        self.outputRaster.raster(key='classification').band(0).setDescription(description)


class ShadeNormalisationOperator(ApplierOperator):
    """
    The Applier wrapper for our ShadeNormalisation algorithm: allows to run the algorithm block-wise over a large image.
    Requires the user to set the input and output images before usage.
    """

    def ufunc(self, band_names: list, shade_band: int = -1):
        """ Implement ufunc of the parent class. """
        image = np.float32(self.inputRaster.raster(key='raster').array())

        # run ShadeNormalisation on the image block
        new_image = ShadeNormalisation().execute(mesma_fraction_image=image, shade_band=shade_band)

        # edit output
        self.outputRaster.raster(key='fractions').setArray(array=new_image)

        band_names_local = band_names[:]
        band_names_local.pop(shade_band)
        for i, band_name in enumerate(band_names_local):
            self.outputRaster.raster(key='fractions').band(i).setDescription(band_name + '_normalised')


class CLIProgressBar(ProgressBar):

    def setPercentage(self, percentage):
        percentage = int(percentage)
        if percentage == 100:
            print('100%')
        else:
            print('{}%..'.format(percentage), end='')

    def setText(self, text):
        print(text)


class GUIProgressBar(CLIProgressBar):

    def __init__(self, q_progress_bar: QProgressBar):
        self.q_progress_bar = q_progress_bar

    def setPercentage(self, percentage):
        percentage = int(percentage)
        self.q_progress_bar.setValue(percentage)
        print('{}%..'.format(percentage))
