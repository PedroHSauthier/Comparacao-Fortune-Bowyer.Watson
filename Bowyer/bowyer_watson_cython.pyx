# bowyer_watson_cython.pyx

import math
import time
import tracemalloc
import random
import sys
import numpy as np

# --- Cython Extension Types ---

cdef class Point:
    cdef public double x, y
    def __init__(self, double x, double y):
        self.x = x
        self.y = y

    def __richcmp__(self, other, int op):
        if not isinstance(other, Point):
            return NotImplemented
        cdef Point other_point = other
        cdef bint result
        if op == 0: # <
            result = (self.x, self.y) < (other_point.x, other_point.y)
        elif op == 1: # <=
            result = (self.x, self.y) <= (other_point.x, other_point.y)
        elif op == 2: # ==
            result = self.x == other_point.x and self.y == other_point.y
        elif op == 3: # !=
            result = self.x != other_point.x or self.y != other_point.y
        elif op == 4: # >
            result = (self.x, self.y) > (other_point.x, other_point.y)
        elif op == 5: # >=
            result = (self.x, self.y) >= (other_point.x, other_point.y)
        return result

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


cdef class Edge:
    cdef public Point v1, v2
    def __init__(self, Point v1, Point v2):
        if v1 < v2:
            self.v1 = v1
            self.v2 = v2
        else:
            self.v1 = v2
            self.v2 = v1

    def __richcmp__(self, other, int op):
        if not isinstance(other, Edge):
            return NotImplemented
        cdef Edge other_edge = other
        cdef bint result
        if op == 2: # ==
            result = self.v1 == other_edge.v1 and self.v2 == other_edge.v2
        elif op == 3: # !=
            result = self.v1 != other_edge.v1 or self.v2 != other_edge.v2
        else:
            return NotImplemented
        return result

    def __hash__(self):
        return hash((self.v1, self.v2))

    def __repr__(self):
        return f"Edge({self.v1}, {self.v2})"


cdef class Triangle:
    cdef public tuple vertices
    cdef public Point circumcenter
    cdef public double circumradius_sq

    def __init__(self, Point v1, Point v2, Point v3):
        cdef list temp_vertices = sorted([v1, v2, v3])
        self.vertices = tuple(temp_vertices)
        self._calculate_circumcircle()

    def __richcmp__(self, other, int op):
        if not isinstance(other, Triangle):
            return NotImplemented
        cdef Triangle other_tri = other
        if op == 2: # ==
            return self.vertices == other_tri.vertices
        elif op == 3: # !=
            return self.vertices != other_tri.vertices
        else:
            return NotImplemented

    def __hash__(self):
        return hash(self.vertices)

    cpdef _calculate_circumcircle(self):
        cdef Point p1, p2, p3
        p1, p2, p3 = self.vertices
        
        cdef double D = 2 * (p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y))
        
        if abs(D) < 1e-10:
            self.circumcenter = None
            self.circumradius_sq = float('inf')
            return

        cdef double p1_sq = p1.x**2 + p1.y**2
        cdef double p2_sq = p2.x**2 + p2.y**2
        cdef double p3_sq = p3.x**2 + p3.y**2

        cdef double ux = (p1_sq * (p2.y - p3.y) + p2_sq * (p3.y - p1.y) + p3_sq * (p1.y - p2.y)) / D
        cdef double uy = (p1_sq * (p3.x - p2.x) + p2_sq * (p1.x - p3.x) + p3_sq * (p2.x - p1.x)) / D
        
        self.circumcenter = Point(ux, uy)
        self.circumradius_sq = (p1.x - ux)**2 + (p1.y - uy)**2

    cpdef bint point_in_circumcircle(self, Point point):
        if self.circumcenter is None:
            return False
        cdef double dist_sq = (point.x - self.circumcenter.x)**2 + (point.y - self.circumcenter.y)**2
        return dist_sq < self.circumradius_sq

class BowyerWatsonCython:
    def __init__(self, points):
        self.points = [Point(p[0], p[1]) for p in points]
        self.triangulation = set()
        self.voronoi_edges = []

        self.metrics = {
            "num_sites": len(points),
            "delaunay_triangles": 0,
            "voronoi_vertices": 0,
            "voronoi_edges_created": 0
        }

    def run(self):
        start_time = time.perf_counter()
        tracemalloc.start()

        super_triangle, super_vertices = self._create_super_triangle()
        self.triangulation.add(super_triangle)

        cdef Point point
        cdef set bad_triangles
        cdef Triangle triangle
        cdef set polygon_boundary
        cdef int i
        cdef Point v1, v2
        cdef Edge edge
        cdef Triangle new_triangle

        for point in self.points:
            bad_triangles = set()
            for triangle in self.triangulation:
                if triangle.point_in_circumcircle(point):
                    bad_triangles.add(triangle)

            polygon_boundary = set()
            for triangle in bad_triangles:
                for i in range(3):
                    v1 = triangle.vertices[i]
                    v2 = triangle.vertices[(i + 1) % 3]
                    edge = Edge(v1, v2)
                    if edge in polygon_boundary:
                        polygon_boundary.remove(edge)
                    else:
                        polygon_boundary.add(edge)
            
            self.triangulation -= bad_triangles

            for edge in polygon_boundary:
                new_triangle = Triangle(edge.v1, edge.v2, point)
                self.triangulation.add(new_triangle)

        self.triangulation = {tri for tri in self.triangulation if not any(v in super_vertices for v in tri.vertices)}

        self._derive_voronoi_diagram()

        self.metrics["delaunay_triangles"] = len(self.triangulation)
        self.metrics["voronoi_vertices"] = len(self.triangulation)
        self.metrics["voronoi_edges_created"] = len(self.voronoi_edges)

    def _create_super_triangle(self):
        cdef double min_x, max_x, min_y, max_y
        min_x = min(p.x for p in self.points)
        max_x = max(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_y = max(p.y for p in self.points)

        cdef double dx = max_x - min_x
        cdef double dy = max_y - min_y
        cdef double delta_max = max(dx, dy)
        cdef double mid_x = (min_x + max_x) / 2
        cdef double mid_y = (min_y + max_y) / 2

        cdef Point v1 = Point(mid_x - 20 * delta_max, mid_y - 10 * delta_max)
        cdef Point v2 = Point(mid_x + 20 * delta_max, mid_y - 10 * delta_max)
        cdef Point v3 = Point(mid_x, mid_y + 20 * delta_max)
        
        return Triangle(v1, v2, v3), {v1, v2, v3}

    def _derive_voronoi_diagram(self):
        cdef dict edge_to_triangles = {}
        cdef Triangle tri
        cdef int i
        cdef Point v1, v2
        cdef Edge edge

        for tri in self.triangulation:
            for i in range(3):
                v1 = tri.vertices[i]
                v2 = tri.vertices[(i + 1) % 3]
                edge = Edge(v1, v2)
                if edge not in edge_to_triangles:
                    edge_to_triangles[edge] = []
                edge_to_triangles[edge].append(tri)
        
        cdef list triangles
        cdef Point p1, p2
        for edge, triangles in edge_to_triangles.items():
            if len(triangles) == 2:
                p1 = triangles[0].circumcenter
                p2 = triangles[1].circumcenter
                if p1 and p2:
                    self.voronoi_edges.append((p1, p2))
