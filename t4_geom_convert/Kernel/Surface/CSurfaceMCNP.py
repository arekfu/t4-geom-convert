# -*- coding: utf-8 -*-
'''
Created on 6 févr. 2019

:author: Sogeti
:data : 06 february 2019
:file : CSurfaceMCNP.py
'''
from ..FileHanlders.Parser.CParseMCNPTransform import CParseMCNPTransform

class CSurfaceMCNP(object):
    '''
    :brief: Class which permit to access precisely to the information of the block SURFACE of MCNP
    '''


    def __init__(self, p_boundaryCondition, p_deux, p_typeSurface, l_paramSurface):
        '''
        Constructor
        :param: p_boundaryCondition : parameter 1 of the boundary condition of the
        surface
        :param: p_deux : parameter 2 of the tuple Surface
        :param: p_typeSurface : string specifying the type of the Surface
        :param: l_paramSurface : list of parameter describing the surface
        '''
        self.boundaryCondition = p_boundaryCondition
        self.deux = p_deux
        self.typeSurface = p_typeSurface
        self.paramSurface = l_paramSurface
        self.dic_transformation = CParseMCNPTransform().m_parsingTransform()