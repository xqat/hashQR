# -*- coding: cp1252 -*-

"""
    hashqr.py v1.0
    
    Copyright 2013 hashQR.com / QRC-Designer.com

    Contact: info aet hashQR doet c0m

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 3
    as published by the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    See http://www.gnu.org/licenses/ for a copy of the license.


    todo:
        replace dependencies
        put on github
        improve performance of qrlib

    
"""


import pyqrnative as qrlib
import PIL.Image
import colorsys
import hashlib
import numpy as np
import scipy.ndimage.measurements

def hls_to_np_col(colHls):
    c = colorsys.hls_to_rgb(colHls[0], colHls[1], colHls[2])
    c = np.array(c)
    return c

class Gen(object):        
    def run(self, data, version=5, ecl=0):
        self.qr = qrlib.QRCode(version, ecl)
        self.qr.addData(data)
        self.qr.make()
        Q = np.array(self.qr.export_modules())
        return Q

    def col_from_hash(self, hashTriple, hue1=None):
        col = hashTriple * 1.0 / 255.0
        colHls = colorsys.rgb_to_hls(col[0], col[1], col[2])
        colHls = list(colHls)

        # ensure different hues
        if hue1 and abs(colHls[0] - hue1) < 0.15:
            colHls[0] += 0.15
            colHls[0] %= 1.0            

        # limit saturation
        if colHls[2] > 0.6:
            colHls[2] *= 0.6
            
        # limit lightness
        if colHls[1] > 0.36:
            colHls[1] *= 0.6
        if colHls[1] > 0.36:
            colHls[1] *= 0.6

        # additional darker color
        colHlsD = np.copy(colHls)
        if colHls[1] < 0.18:
            colHls[1] *= 2.0
        else:            
            colHlsD[1] *= 0.5
        
        return hls_to_np_col(colHls), hls_to_np_col(colHlsD), colHls[0]

    def hash_qr(self, url, moduleSize=6):
        if moduleSize > 12:
            moduleSize = 12
        
        lenUrl = len(url)
        if lenUrl > 106:
            raise Exception("Code data length overflow.")
        if not lenUrl:
            raise Exception("Empty URL.")

        # error correction level            
        ecl = 2  #    {"L":1, "M":0, "Q":3, "H":2}
        if lenUrl > 44:
            ecl = 3
        if lenUrl > 60:
            ecl = 0
        if lenUrl > 84:
            ecl = 1        

        # get QR code
        Qraw = self.run(url, ecl=ecl)

        # hash
        urlHash = hashlib.sha512(url).hexdigest()    
        baseCol = urlHash[0:20]
        urlBytes = baseCol.decode("hex")
        aHash = np.frombuffer(urlBytes, dtype=np.uint8)    
        Q = np.zeros((Qraw.shape[0] + 4, Qraw.shape[1] + 4), dtype=np.uint8)
        Q[2:-2,2:-2] = Qraw
        
        # colors
        col1, col2, hue1 = self.col_from_hash(aHash[0:3])
        col3, col4, trash = self.col_from_hash(aHash[3:6], hue1)

        # paint code
        labelled, trash = scipy.ndimage.measurements.label(Q) # enumerate connected areas

        L = np.ones(Q.shape + (3,), dtype=np.uint8) * 255
        labelled = labelled % 4
        L[labelled == 0] = col1 * 255.0
        L[labelled == 1] = col2 * 255.0
        L[labelled == 2] = col3 * 255.0
        L[labelled == 3] = col4 * 255.0

        L[Q == 0] = (255, 255, 255)

        # hash rotate
        L = np.rot90(L, aHash[6] % 4)

        # PIL
        im = PIL.Image.fromarray(L)

        # resize
        im = im.transform((im.size[0] * moduleSize, im.size[1] * moduleSize), PIL.Image.EXTENT, (0,0) + im.size, PIL.Image.NEAREST)
        
        return im

    
gen = Gen()    

if __name__ == "__main__":
    print "standalone"
    
    import random
    url = str(random.random())
    im = gen.hash_qr(url)
    im.show()

