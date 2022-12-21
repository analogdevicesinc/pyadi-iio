# coding: utf-8
""" reproducible code for EIT2016 """
# Based on Benyuan Liu. All Rights Reserved. https://github.com/liubenyuan/pyEIT
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np
import matplotlib.pyplot as plt
# pyEIT 2D algorithm modules
import pyeit.mesh as mesh
from pyeit.eit.fem import Forward
from pyeit.eit.interp2d import sim2pts
from pyeit.eit.utils import eit_scan_lines

import pyeit.eit.greit as greit
import pyeit.eit.bp as bp
import pyeit.eit.jac as jac

def parse_line(lines):
    try:
        _, data = lines.split(":", 1)
    except ValueError:
        return None

    items = []
    for item in data.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None
    return np.array(items)

class EITPlot():
    def __init__(self,el=None,h0=None,f0=None,f1=None):
        self.f0=f0
        self.f1=f1
        self.h0=h0
        self.el=el
        self.pts=[]
        self.tri=[]
        self.mesh_obj=[]
        self.el_pos=None
        self.eit=None


    def buildMesh(self,el,h0=0.08,dist=1,step=1):
        """ 0. construct mesh structure """
        self.mesh_obj, self.el_pos = mesh.create(el, h0=h0)
        # setup EIT scan conditions
        self.dist=dist
        self.step=step
        self.ex_mat = eit_scan_lines(el, dist)

    def setup(self,p=0.5,lamb=0.5,reconstruction="jac"):
        self.reconstruction=reconstruction
        if reconstruction=="bp":
            """ BP """
            self.eit = bp.BP(self.mesh_obj, self.el_pos, ex_mat=self.ex_mat, step=self.step, parser='std')
            #ds = eit.solve(f1.v, f0.v, normalize=True)
            #ds_bp = ds
        elif (reconstruction=="jac"):
            """ JAC """
            self.eit = jac.JAC( self.mesh_obj,
                                self.el_pos,
                                ex_mat=self.ex_mat,
                                step=self.step,
                                perm=1.,
                                parser='std')
            # parameter tuning is needed for better EIT images 0.5, 0.5
            #0.8 0.5
            self.eit.setup(p=p, lamb=lamb, method='kotre')
        elif (reconstruction=="greit"):
            """ GREIT """
            self.eit = greit.GREIT(self.mesh_obj, self.el_pos, ex_mat=self.ex_mat, step=self.step, parser='std')
            # parameter tuning is needed for better EIT images
            self.eit.setup(p=p, lamb=lamb)
            #ds = eit.solve(f1.v, f0.v, normalize=False)
            #x, y, ds_greit = eit.mask_value(ds, mask_value=np.NAN)
        
    def readInput(self,file1,file0):
        text_file = open(file1,'r')
        lines1 = text_file.readlines()
        text_file = open(file0,'r')
        lines0 = text_file.readlines()
        self.f1=np.array(parse_line(lines1[0]))
        self.f0=np.array(parse_line(lines0[0]))

    def setBaseline(self,f0):
        self.f0=np.empty_like(f0)
        self.f0[:]=f0

    def setCurrentData(self,f1):
        self.f1=np.empty_like(f1)
        self.f1[:]=f1

    def compute(self,figure):
        """ Setup display"""
        axis_size = [-1.2, 1.2, -1.2, 1.2]
        figure.clear()
        self.ax=figure.add_subplot(111)
        
        if self.reconstruction=="bp":
            """ BP """
            ds = self.eit.solve(self.f1, self.f0, normalize=False)
            ds_bp = ds
            bp_max = np.max(np.abs(ds_bp))
            im = self.ax.tripcolor( self.mesh_obj['node'][:, 0],
                                    self.mesh_obj['node'][:, 1],
                                    self.mesh_obj['element'],
                                    np.real(ds_bp),
                                    cmap=plt.cm.jet,
                                    vmin=-bp_max,
                                    vmax=bp_max)
            
            self.ax.set_title(r'BP')
            self.ax.axis(axis_size)
            self.ax.set_aspect('equal')
            figure.colorbar(im)
 
        elif (self.reconstruction=="jac"):
            """ JAC """
            ds = self.eit.solve(self.f1, self.f0, normalize=False)
            ds_jac = sim2pts(self.mesh_obj['node'], self.mesh_obj['element'], ds)
            jac_max = np.max(np.abs(ds_jac))
            im=self.ax.tripcolor(   self.mesh_obj['node'][:, 0], 
                                    self.mesh_obj['node'][:, 1], 
                                    self.mesh_obj['element'], 
                                    np.real(ds_jac),
                                    cmap=plt.cm.jet, 
                                    vmin=-100, 
                                    vmax=100)
            self.ax.set_title(r'JAC')
            self.ax.axis(axis_size)
            self.ax.set_aspect('equal')
            figure.colorbar(im, ax=self.ax)

        elif (self.reconstruction=="greit"):
            """ GREIT """
            ds = self.eit.solve(self.f1, self.f0, normalize=False)
            x, y, ds_greit = self.eit.mask_value(ds, mask_value=np.NAN)
            im_size = [-2, 34, -2, 34]
            gr_max = np.max(np.abs(ds_greit))
            im = self.ax.imshow(    np.real(ds_greit),
                                    interpolation='nearest',
                                    cmap=plt.cm.jet,
                                    vmin=-gr_max,
                                    vmax=gr_max)
            self.ax.set_title(r'GREIT')
            self.ax.axis(im_size)
            self.ax.set_aspect('equal')
            figure.colorbar(im)
    
        self.ax.axis('off')
    def close(self):
        plt.close()
