# -*- coding: utf-8 -*-
'''
Created on 5 févr. 2019

:author: Sogeti
:data : 05 february 2019
:file : CCellConversion.py
'''

from MIP.geom.semantics import GeomExpression, Surface
from MIP.geom.main import extract_surfaces_list

from .TreeFunctions import isLeaf, isIntersection, isUnion
from .CVolumeT4 import CVolumeT4
from .Lattice import (LatticeSpec, latticeVector, LatticeError,
                      squareLatticeBaseVectors, hexLatticeBaseVectors)
from ..Transformation.Transformation import transformation
from ..Surface.ConversionSurfaceMCNPToT4 import conversionSurfaceParams
from ..Surface.SurfaceCollection import SurfaceCollection


class CCellConversion:
    '''Class which contains methods to convert the Cell of MCNP in T4 Volume'''

    def __init__(self, int_cell, int_surf, d_dictClassT4, d_dictSurfaceT4,
                 d_dicSurfaceMCNP, d_dicCellMCNP, union_ids):
        '''
        Constructor
        :param: int_i : id of the volume created
        :param: d_dictClassT4 : dictionary filled by the methods and which
        contains volumes informations
        '''
        self.new_cell_key = int_cell
        self.new_surf_key = int_surf
        self.dictClassT4 = d_dictClassT4
        self.dictSurfaceT4 = d_dictSurfaceT4
        self.dicSurfaceMCNP = d_dicSurfaceMCNP
        self.dicCellMCNP = d_dicCellMCNP
        self.union_ids = union_ids

    def conversionEQUA(self, list_surface):
        '''Method converting a list of if of surface and return a tuple with
        the informations of the volume EQUA T4'''

        minus_surfs = []
        plus_surfs = []
        seen = set()
        for elt in list_surface:
            assert isinstance(elt, int)
            if elt in seen:
                # do not emit the same surface twice
                continue
            seen.add(elt)
            if elt < 0:
                minus_surfs.append(-elt)
            elif elt > 0:
                plus_surfs.append(elt)
        return plus_surfs, minus_surfs

    def conversionINTUNION(self, op, *ids):
        '''Analyze the type of conversion needed between a T4 INTERSECTION and
        a T4 UNION and return a tuple with the information of the T4 VOLUME'''
        if op == '*':
            pluses = []
            minuses = []
            ops = ('INTE', ids)
        elif op == ':':
            pluses, minuses = self.conversionEQUA([self.union_ids[0],
                                                   -self.union_ids[1]])
            ops = ('UNION', ids)
        else:
            raise ValueError('Converting cell with unexpected operator: {}'
                             .format(op))
        return pluses, minuses, ops

    def postOrderTraversalFill(self, key, dictUniverse):

        cell = self.dicCellMCNP[key]
        if cell.fillid is not None:
            new_cells = []
            to_process = []
            mcnp_key_geom = cell.geometry
            mcnp_key_filltr = cell.filltr
            universe = int(cell.fillid)
            for element in dictUniverse[universe]:
                to_process.extend(self.postOrderTraversalFill(element,
                                                              dictUniverse))
            for element in to_process:
                element_cell = self.dicCellMCNP[element]
                mcnp_element_geom = element_cell.geometry
                self.new_cell_key += 1
                new_key = self.new_cell_key
                new_cell = cell.copy()
                new_cell.fillid = None
                new_cell.materialID = element_cell.materialID
                new_cell.density = element_cell.density
                # new_trcl = element_cell.trcl.copy()
                # if cell.trcl is not None:
                #     new_trcl.extend(cell.trcl)
                # new_cell.trcl = new_trcl
                new_cell.idorigin = element_cell.idorigin.copy()
                new_cell.idorigin.append((element, key))
                self.dicCellMCNP[new_key] = new_cell
                tree = self.postOrderTraversalTransform(mcnp_element_geom,
                                                        mcnp_key_filltr)
                if cell.trcl:
                    tree = self.apply_trcl(cell.trcl, tree)
                self.dicCellMCNP[new_key].geometry = ['*', mcnp_key_geom, tree]
                new_cells.append(new_key)
            return new_cells
        else:
            return [key]


    def postOrderTraversalFlag(self, p_tree):
        '''
        :brief: method which take a tree and return a tuple of tuple with flag
        to decorate each tree in the tree
        '''

        if not isLeaf(p_tree):
            op, *args = p_tree
            new_args = [self.postOrderTraversalFlag(node) for node in args]
            self.new_cell_key += 1
            new_tree = [self.new_cell_key, op]
            new_tree.extend(new_args)
            return new_tree
        else:
            return p_tree

    def postOrderTraversalTransform(self, p_tree, p_transf):
        if not p_transf:
            return p_tree

        if not isLeaf(p_tree):
            op, *args = p_tree
            new_args = [self.postOrderTraversalTransform(node, p_transf) for node in args]
            new_tree = [op]
            new_tree.extend(new_args)
            return new_tree

        surfs = self.dicSurfaceMCNP[abs(p_tree)]
        surf_colls = []
        mcnp_surfs = []
        for surfaceObject, side in surfs:
            p_boundCond = surfaceObject.boundaryCond
            p_typeSurface = surfaceObject.typeSurface
            frame = surfaceObject.paramSurface
            compl_param = surfaceObject.complParam
            idorigin = surfaceObject.idorigin + ['via tr']
            new_mcnp_surf = transformation(p_transf, p_typeSurface, frame,
                                           compl_param, p_boundCond, idorigin)
            mcnp_surfs.append((new_mcnp_surf, side))
            surf_coll = conversionSurfaceParams(p_tree, new_mcnp_surf)
            surf_colls.append((surf_coll, side))

        surf_coll = SurfaceCollection.join(surf_colls)
        aux_ids = []
        for surf, side in surf_coll.surfs[1:]:
            self.new_surf_key += 1
            new_key = self.new_surf_key
            surf.idorigin.append('aux surf')
            self.dictSurfaceT4[new_key] = (surf, [])
            aux_ids.append(side * new_key)

        self.new_surf_key += 1
        new_key = self.new_surf_key
        self.dictSurfaceT4[new_key] = (surf_coll.surfs[0][0], aux_ids)
        self.dicSurfaceMCNP[new_key] = mcnp_surfs

        return Surface(new_key) if p_tree >= 0 else Surface(-new_key)

    def postOrderTraversalConversion(self, p_tree, idorigin):
        '''
        :brief: method which take the tree create by m_postOrderTraversalFlag
        and filled a dictionary (of CVolumeT4 instance)
        '''
        if isLeaf(p_tree):
            self.new_cell_key += 1
            p_id = self.new_cell_key
            pluses, minuses = self.conversionEQUA([p_tree])
            self.dictClassT4[p_id] = CVolumeT4(pluses=pluses, minuses=minuses,
                                               idorigin=idorigin)
            return p_id

        p_id, op, *args = p_tree

        if op == '*':
            surfs = []
            nodes = []
            for arg in args:
                if isLeaf(arg):
                    surfs.append(arg)
                else:
                    nodes.append(arg)
            # here we know that paramsOPER starts as ['EQUA', 'INTE', ...]
            # because op == '*'
            if surfs:
                pluses, minuses = self.conversionEQUA(surfs)
                if nodes:
                    arg_ids = [self.postOrderTraversalConversion(node, idorigin)
                            for node in nodes]
                    pluses2, minuses2, ops = self.conversionINTUNION(op,
                                                                     *arg_ids)
                    pluses += pluses2
                    minuses += minuses2
                else:
                    ops = None
            else:
                # we assume that nodes is not empty
                arg_ids = [self.postOrderTraversalConversion(node, idorigin)
                           for node in nodes]
                pluses, minuses, ops = self.conversionINTUNION(op, *arg_ids)
            self.dictClassT4[p_id] = CVolumeT4(pluses=pluses, minuses=minuses,
                                               ops=ops, idorigin=idorigin)
            return p_id

        # here op == ':'
        if op != ':':
            raise ValueError('Converting cell with unexpected operator: {}'
                             .format(op))
        arg_ids = [self.postOrderTraversalConversion(arg, idorigin)
                    for arg in args]
        pluses, minuses, ops = self.conversionINTUNION(op, *arg_ids)
        self.dictClassT4[p_id] = CVolumeT4(pluses=pluses, minuses=minuses,
                                           ops=ops, idorigin=idorigin)
        return p_id


    def postOrderTraversalOptimisation(self, p_tree):
        '''
        :brief: method which permit to optimize the course of the cells MCNP
        '''

        if isLeaf(p_tree):
            return p_tree
        p_id, op, *args = p_tree
        new_args = [self.postOrderTraversalOptimisation(node) for node in args]
        new_node = [p_id, op]
        for node in new_args:
            if isIntersection(node) and op == '*':
                new_node.extend(node[2:])
            elif isUnion(node) and op == ':':
                new_node.extend(node[2:])
            else:
                new_node.append(node)

        # we check if the cell is an intersection and contains the same surface
        # with opposite signs; in that case we do not emit the cell at all,
        # because it would be empty and because TRIPOLI-4 does not like
        # surfaces to appear with both signs at the same time
        if op != '*':
            return new_node
        pluses = {surf for surf in new_node[2:]
                    if isLeaf(surf) and surf > 0}
        minuses = {-surf for surf in new_node[2:]
                    if isLeaf(surf) and surf < 0}
        if pluses & minuses:
            return None

        return new_node

    def postOrderTraversalReplace(self, p_tree):
        '''Replace collections of surfaces with ASTs representing the
        intersection/union of the collection. Necessary for one-nappe cones and
        macrobodies.
        '''
        if not isLeaf(p_tree):
            p_id, op, *args = p_tree
            new_tree = [p_id, op]
            new_tree.extend(self.postOrderTraversalReplace(node)
                            for node in args)
            return new_tree

        abs_id = abs(p_tree)
        if abs_id not in self.dictSurfaceT4:
            return p_tree

        surfT4 = self.dictSurfaceT4[abs_id]
        if not surfT4[1]:
            return p_tree

        self.new_cell_key += 1
        if p_tree < 0:
            new_node = [self.new_cell_key, '*', p_tree]
            new_node.extend(Surface(-surf) for surf in surfT4[1])
        else:
            new_node = [self.new_cell_key, ':', p_tree]
            new_node.extend(Surface(surf) for surf in surfT4[1])
        return GeomExpression(new_node)

    def postOrderTraversalCompl(self, tree):
        if not isinstance(tree, (list, tuple)):
            return tree
        if tree[0] == '^':
            cell = self.dicCellMCNP[int(tree[1])]
            new_geom = self.postOrderTraversalCompl(cell.geometry)
            return new_geom.inverse()
        new_tree = [tree[0]]
        for node in tree[1:]:
            new_tree.append(self.postOrderTraversalCompl(node))
        result = GeomExpression(new_tree)
        return result

    def extract_surfaces(self, cell):
        surf_ids = extract_surfaces_list(cell.geometry)
        return [(surf.paramSurface, side if surf_id > 0 else -side)
                for surf_id in surf_ids
                for surf, side in self.dicSurfaceMCNP[abs(surf_id)]]

    def developLattice(self, key):
        cell = self.dicCellMCNP[key]
        if cell.lattice is None:
            return
        assert isinstance(cell.fillid, LatticeSpec)
        assert cell.lattice in (1, 2)
        mcnp_element_geom = cell.geometry
        surfaces = self.extract_surfaces(cell)
        try:
            if cell.lattice == 1:
                lat_base_vectors = squareLatticeBaseVectors(surfaces)
            elif cell.lattice == 2:
                lat_base_vectors = hexLatticeBaseVectors(surfaces)
        except LatticeError as err:
            raise LatticeError('{} (in cell {})'.format(err, key)) from None

        # compute the base vectors of the lattice
        domain = cell.fillid
        if len(lat_base_vectors) != len(domain.bounds):
            if len(lat_base_vectors) != domain.bounds.dims():
                msg = ('Problem of domain definition for lattice; expected {} '
                       'non-trivial bounds, got {}'
                       .format(len(lat_base_vectors), domain.bounds.dims()))
                raise LatticeError(msg)
            n_missing_bounds = len(lat_base_vectors) - len(domain.bounds)
            for i in range(n_missing_bounds):
                range_ = domain.bounds[-1-i]
                if range_[0] != range_[1]:
                    msg = ('Problem of domain definition for lattice; '
                           'expected {} non-trivial bounds, but the {}:{} '
                           'bound is not trivial'
                           .format(len(lat_base_vectors), range_[0],
                                   range_[1]))
                    raise LatticeError(msg)

        for index, universe in domain.items():
            if universe == 0:
                continue
            transl = latticeVector(lat_base_vectors, index)
            trnsf = list(transl) + [1., 0., 0., 0., 1., 0., 0., 0., 1.]
            new_cell = cell.copy()
            tree = self.postOrderTraversalTransform(mcnp_element_geom, trnsf)
            new_cell.geometry = tree
            if universe == cell.universe:
                new_cell.fillid = None
                new_cell.materialID = cell.materialID
            else:
                new_cell.fillid = universe
            filltr = new_cell.filltr
            if filltr:
                new_filltr = tuple(x if i > 2 else x + trnsf[i]
                                   for i, x in enumerate(filltr))
            else:
                filltr = [0.0, 0.0, 0.0,
                          1.0, 0.0, 0.0,
                          0.0, 1.0, 0.0,
                          0.0, 0.0, 1.0]
                new_filltr = tuple(x if i > 2 else x + trnsf[i]
                                   for i, x in enumerate(filltr))
            new_cell.filltr = new_filltr
            new_cell.lattice = False
            self.new_cell_key += 1
            self.dicCellMCNP[self.new_cell_key] = new_cell
        del self.dicCellMCNP[key]

    def apply_trcl(self, trcls, geometry):
        '''Apply the given coordinate transformation to the given cell AST
        (`geometry`).

        :returns: the transformed AST
        '''
        if not trcls:
            return geometry
        for trcl in trcls:
            geometry = self.postOrderTraversalTransform(geometry, trcl)
        return geometry
